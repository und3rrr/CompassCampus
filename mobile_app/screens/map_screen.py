"""
Экран карты с навигацией
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.clock import Clock
from widgets.map_widget import MapWidget
from services.api_client import get_api_client, Building, Node, Route
from services.cache_service import get_cache_service
from services.route_closure_service import RouteClosureService
from services.graph_builder import GraphBuilder
import logging
import threading

logger = logging.getLogger(__name__)


class MapScreen(Screen):
    """Экран карты с навигацией"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.building: Building = None
        self.api_client = get_api_client()
        self.cache_service = get_cache_service()
        self.current_route: Route = None
        self.start_node: Node = None
        self.end_node: Node = None
        # Сервис закрытых маршрутов будет установлен позже
        self.closure_service = None

        # Основной лейаут
        main_layout = BoxLayout(orientation='vertical', padding=dp(5), spacing=dp(5))

        # Верхняя панель с управлением
        top_panel = BoxLayout(orientation='vertical', size_hint_y=0.2, spacing=dp(5))

        # Строка выбора этажа
        floor_layout = BoxLayout(size_hint_y=0.5, spacing=dp(5))
        floor_label = Label(text='Этаж:', size_hint_x=0.3)
        floor_layout.add_widget(floor_label)
        self.floor_spinner = Spinner(
            text='1',
            values=('1', '2', '3', '4', '5'),
            size_hint_x=0.7
        )
        self.floor_spinner.bind(text=self.on_floor_changed)
        floor_layout.add_widget(self.floor_spinner)
        top_panel.add_widget(floor_layout)

        # Строка поиска
        search_layout = BoxLayout(size_hint_y=0.5, spacing=dp(5))
        self.search_input = TextInput(
            hint_text='Поиск помещения...',
            multiline=False,
            size_hint_x=0.7
        )
        search_layout.add_widget(self.search_input)

        search_btn = Button(text='🔍', size_hint_x=0.3)
        search_btn.bind(on_press=self.on_search)
        search_layout.add_widget(search_btn)
        top_panel.add_widget(search_layout)

        # Список результатов поиска (dropdown под поиском)
        self.search_results_container = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=0,  # Скрыт по умолчанию
            spacing=dp(2)
        )
        top_panel.add_widget(self.search_results_container)

        main_layout.add_widget(top_panel)

        # Карта в центре
        self.map_widget = MapWidget(size_hint_y=0.6)
        main_layout.add_widget(self.map_widget)

        # Панель маршрута (нижняя)
        self.route_panel = BoxLayout(orientation='vertical', size_hint_y=0.2, spacing=dp(5))
        self.route_panel.padding = dp(5)
        self.route_info_label = Label(
            text='Нажмите на две точки для построения маршрута',
            size_hint_y=0.5
        )
        self.route_panel.add_widget(self.route_info_label)

        # Кнопки внизу
        button_layout = GridLayout(cols=5, size_hint_y=0.5, spacing=dp(5))

        reset_btn = Button(text='Сброс')
        reset_btn.bind(on_press=self.on_reset_view)
        button_layout.add_widget(reset_btn)

        zoom_in_btn = Button(text='Зум+')
        zoom_in_btn.bind(on_press=self.on_zoom_in)
        button_layout.add_widget(zoom_in_btn)

        zoom_out_btn = Button(text='Зум-')
        zoom_out_btn.bind(on_press=self.on_zoom_out)
        button_layout.add_widget(zoom_out_btn)

        cancel_btn = Button(text='Отмена')
        cancel_btn.bind(on_press=self.on_cancel_selection)
        button_layout.add_widget(cancel_btn)

        back_btn = Button(text='Назад')
        back_btn.bind(on_press=self.on_back)
        button_layout.add_widget(back_btn)

        self.route_panel.add_widget(button_layout)
        main_layout.add_widget(self.route_panel)

        self.add_widget(main_layout)
    def set_building(self, building: Building):
        """Установить активное здание"""
        self.building = building
        self.start_node = None
        self.end_node = None
        self.current_route = None
        
        # Установить callback для выбора узлов на карте
        self.map_widget.on_node_selected_callback = self.on_map_node_selected

        # Обновляем спиннер этажей
        if building.floors:
            self.floor_spinner.values = [str(i) for i in range(1, building.floors + 1)]
            self.floor_spinner.text = '1'

        # Загружаем данные здания
        self._load_building_data()

    def _load_building_data(self):
        """Загрузить данные здания"""
        thread = threading.Thread(target=self._fetch_building_data)
        thread.daemon = True
        thread.start()

    def _fetch_building_data(self):
        """Получить данные здания с API"""
        try:
            logger.info(f"Loading building data: {self.building.id}")
            # Данные уже есть в building объекте
            # Обновляем UI в главном потоке через Clock
            Clock.schedule_once(lambda dt: self._update_map_display(), 0)
        except Exception as e:
            logger.error(f"Failed to load building data: {e}")
            error_message = f"Ошибка загрузки: {str(e)}"
            Clock.schedule_once(lambda dt, msg=error_message: self._show_error_popup(msg), 0)

    def _update_map_display(self):
        """Обновить отображение карты"""
        if self.building and self.building.nodes:
            # Фильтруем узлы по текущему этажу
            current_floor = int(self.floor_spinner.text)
            floor_nodes = [n for n in self.building.nodes if n.floor == current_floor]

            self.map_widget.set_nodes(floor_nodes)
            
            # Добавляем edges - связи между узлами
            if not self.building.nodes:
                return
                
            from services.graph_builder import GraphBuilder
            
            # Конвертируем Node объекты в словари для GraphBuilder
            nodes_dicts = [
                {
                    'Id': node.id,
                    'Name': node.name,
                    'X': node.x,
                    'Y': node.y,
                    'Floor': node.floor,
                    'Type': node.node_type
                }
                for node in self.building.nodes
            ]
            
            # Строим edges
            builder = GraphBuilder()
            edges = builder.build_edges_from_nodes(nodes_dicts)
            
            # Фильтруем edges по текущему этажу
            floor_edges = []
            node_ids = {n.id for n in floor_nodes}
            for edge in edges:
                if edge.from_id in node_ids and edge.to_id in node_ids:
                    floor_edges.append((edge.from_id, edge.to_id))
            
            self.map_widget.set_edges(floor_edges)

            # Если есть сервис закрытий, показываем закрытые маршруты
            if self.closure_service:
                closed_edges = self.closure_service.get_closed_edges()
                closed_nodes = self.closure_service.get_closed_nodes()
                self.map_widget.set_closed_routes(closed_edges, closed_nodes)

    def on_floor_changed(self, spinner, text):
        """Обработка изменения этажа"""
        self._update_map_display()

    def on_search(self, instance):
        """Поиск помещения"""
        query = self.search_input.text.strip()
        if not query:
            return

        thread = threading.Thread(
            target=self._perform_search,
            args=(query,)
        )
        thread.daemon = True
        thread.start()

    def _perform_search(self, query: str):
        """Выполнить поиск"""
        try:
            results = self.api_client.search_nodes(self.building.id, query)
            if results:
                # Показываем результаты в попапе
                Clock.schedule_once(lambda dt: self._show_search_results(results), 0)
            else:
                Clock.schedule_once(lambda dt: self._show_info_popup("Не найдено"), 0)
        except Exception as e:
            logger.warning(f"API search failed: {e}, trying local search...")
            # Fallback на локальный поиск
            self._perform_local_search(query)

    def _perform_local_search(self, query: str):
        """Выполнить локальный поиск по названиям узлов"""
        try:
            if not self.building or not self.building.nodes:
                Clock.schedule_once(lambda dt: self._show_error_popup("Нет данных о здании"), 0)
                return
            
            # Ищем узлы по названию (case-insensitive)
            query_lower = query.lower()
            results = []
            for node in self.building.nodes:
                if query_lower in node.name.lower():
                    results.append(node)
            
            if results:
                Clock.schedule_once(lambda dt: self._show_search_results(results), 0)
            else:
                Clock.schedule_once(lambda dt: self._show_info_popup(f"Не найдено: '{query}'"), 0)
        except Exception as e:
            logger.error(f"Local search failed: {e}")
            Clock.schedule_once(lambda dt: self._show_error_popup(f"Ошибка поиска: {str(e)}"), 0)

    def _show_search_results(self, results: list):
        """Показать результаты поиска в dropdown под поиском"""
        # Очищаем предыдущие результаты
        self.search_results_container.clear_widgets()
        
        if not results:
            self.search_results_container.height = 0
            return
        
        # Добавляем кнопки результатов
        for node in results:
            btn = Button(
                text=f'{node.name} (Этаж {node.floor})',
                size_hint_y=None,
                height=dp(45),
                background_color=(0.3, 0.6, 1.0, 1.0)
            )
            btn.node = node
            btn.bind(on_press=self.on_node_selected_from_search)
            self.search_results_container.add_widget(btn)
        
        # Вычисляем высоту контейнера (не более 150px для dropdown)
        max_height = min(len(results) * dp(45), dp(150))
        self.search_results_container.height = max_height

    def on_node_selected_from_search(self, instance):
        """Обработка выбора узла из поиска"""
        node = instance.node
        self.end_node = node
        self.map_widget.set_end_node(node)

        # Закрываем dropdown результатов
        self.search_results_container.height = 0
        self.search_input.text = ''  # Очищаем поле поиска

        # Автоматически переходим на этаж узла
        self.floor_spinner.text = str(node.floor)

        # Пытаемся построить маршрут если есть стартовая точка
        if self.start_node:
            self._calculate_route()

    def set_end_node_from_qr(self, node_id: str, node_name: str, floor: int):
        """Установить конечный узел из QR кода"""
        try:
            # Получаем все узлы из кэша
            if self.building is None:
                self.building = self.cache_service.get_building()
            
            if not self.building or not self.building.nodes:
                logger.warning("Building or nodes not loaded")
                return
            
            # Ищем узел по ID
            end_node = None
            for node in self.building.nodes:
                if node.node_id == node_id:
                    end_node = node
                    break
            
            if end_node:
                self.end_node = end_node
                self.map_widget.set_end_node(end_node)
                
                # Переходим на нужный этаж
                self.floor_spinner.text = str(floor)
                
                # Показываем информацию о найденном узле
                self.route_info_label.text = f'Целевое помещение: {node_name}\nЭтаж: {floor}'
                
                # Если есть стартовая точка, строим маршрут
                if self.start_node:
                    self._calculate_route()
                else:
                    # Выбираем стартовую точку автоматически (первый узел)
                    if self.building.nodes:
                        self.start_node = self.building.nodes[0]
                        self.map_widget.set_start_node(self.start_node)
                        self.route_info_label.text = f'Старт: {self.start_node.name}\nЦель: {node_name}'
                        self._calculate_route()
                
                logger.info(f"QR: Set end node {node_name} (ID: {node_id})")
            else:
                logger.warning(f"Node with ID {node_id} not found in building")
        except Exception as e:
            logger.error(f"Error setting end node from QR: {e}")

    def on_map_node_selected(self, node: Node):
        """Обработка выбора узла на карте"""
        if self.start_node is None:
            self.start_node = node
            self.map_widget.set_start_node(node)
            self.route_info_label.text = f'Старт: {node.name}\nВыберите конец маршрута (нажмите Отмена чтоб переselect)'
        elif self.end_node is None:
            self.end_node = node
            self.map_widget.set_end_node(node)
            # Показываем граф при выборе конца
            self._highlight_graph()
            self._calculate_route()

    def _calculate_route(self):
        """Вычислить маршрут между стартом и концом"""
        if not self.start_node or not self.end_node:
            return

        thread = threading.Thread(target=self._fetch_route)
        thread.daemon = True
        thread.start()

    def _fetch_route(self):
        """Получить маршрут с API или использовать локальный граф"""
        try:
            logger.info(f"Calculating route from {self.start_node.id} to {self.end_node.id}")
            route = self.api_client.get_route(
                self.building.id,
                self.start_node.id,
                self.end_node.id
            )
            self.current_route = route
            self.map_widget.set_route(route)

            # Обновляем информацию о маршруте
            info_text = (
                f'Маршрут: {self.start_node.name} → {self.end_node.name}\n'
                f'Расстояние: {route.distance:.0f}м | '
                f'Время: {route.estimated_time:.0f}мин | '
                f'Переходов между этажами: {route.floor_changes}'
            )
            self.route_info_label.text = info_text

        except Exception as e:
            logger.warning(f"Failed to get route from API: {e}")
            logger.info("Falling back to local graph-based pathfinding...")
            self._calculate_route_locally()

    def _calculate_route_locally(self):
        """Использовать локальный граф для построения маршрута (fallback)"""
        try:
            if not self.building or not self.building.nodes:
                Clock.schedule_once(lambda dt: self._show_error_popup("Ошибка: нет данных о здании"), 0)
                return
            
            # Конвертируем Node объекты в словари для графа
            nodes_dicts = []
            nodes_map = {}
            for node in self.building.nodes:
                node_dict = {
                    'Id': str(node.id),  # Убеждаемся что ID строка
                    'Name': node.name,
                    'Floor': node.floor,
                    'Type': node.node_type,  # Исправлено: node_type вместо type
                    'X': node.x,
                    'Y': node.y
                }
                nodes_dicts.append(node_dict)
                nodes_map[str(node.id)] = node
            
            # Строим граф
            edges = GraphBuilder.build_edges_from_nodes(nodes_dicts)
            
            # Находим кратчайший путь
            # Создаём словарь с ID в виде строк для совместимости
            nodes_dict_for_search = {str(nd['Id']): nd for nd in nodes_dicts}
            
            path_result = GraphBuilder.find_shortest_path(
                str(self.start_node.id),
                str(self.end_node.id),
                edges,
                nodes_dict_for_search
            )
            
            if path_result:
                path_ids, distance = path_result
                
                # Создаём объект Route с локально найденным маршрутом
                route_nodes = []
                for node_id in path_ids:
                    for node in self.building.nodes:
                        if str(node.id) == node_id:
                            route_nodes.append(node)
                            break
                
                # Создаём простой Route объект
                route = Route(
                    path=route_nodes,
                    distance=distance,
                    estimated_time=distance / 1.4,  # ~1.4 м/мин пешком
                    floor_changes=0
                )
                
                # Выполняем UI операции в главном потоке
                def update_route():
                    self.current_route = route
                    self.map_widget.set_route(route)
                    
                    # Обновляем информацию о маршруте
                    info_text = (
                        f'Маршрут (локальный): {self.start_node.name} → {self.end_node.name}\n'
                        f'Расстояние: {distance:.0f}м | '
                        f'Время: {distance/1.4:.0f}мин'
                    )
                    self.route_info_label.text = info_text
                    logger.info(f"Local pathfinding successful: {len(route_nodes)} nodes")
                
                Clock.schedule_once(lambda dt: update_route(), 0)
            else:
                Clock.schedule_once(lambda dt: self._show_error_popup("Маршрут не найден (нет пути между точками)"), 0)
                
        except Exception as e:
            logger.error(f"Local pathfinding failed: {e}")
            self._show_error_popup(f"Ошибка построения маршрута: {str(e)}")

    def on_reset_view(self, instance):
        """Сброс панорамы и масштаба"""
        self.map_widget.reset_view()

    def on_zoom_in(self, instance):
        """Увеличить масштаб"""
        self.map_widget.zoom_in()

    def on_zoom_out(self, instance):
        """Уменьшить масштаб"""
        self.map_widget.zoom_out()

    def on_back(self, instance):
        """Вернуться на главный экран"""
        self.manager.current = 'home'

    def on_cancel_selection(self, instance):
        """Отменить выбор начальной точки"""
        self.start_node = None
        self.end_node = None
        self.current_route = None
        self.map_widget.clear_selection()
        self.route_info_label.text = 'Нажмите на две точки для построения маршрута'

    def _highlight_graph(self):
        """Подсветить граф между выбранными точками"""
        if self.start_node and self.end_node:
            # График автоматически отрисовывается при set_route в _calculate_route
            pass

    def _show_error_popup(self, message: str):
        """Показать ошибку (вызывается из потока, используем Clock)"""
        def show_popup():
            content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
            label = Label(text=message)
            content.add_widget(label)

            btn = Button(text='OK', size_hint_y=0.3)
            content.add_widget(btn)

            popup = Popup(
                title='Ошибка',
                content=content,
                size_hint=(0.8, 0.4)
            )
            btn.bind(on_press=popup.dismiss)
            popup.open()
        
        # Планируем UI операцию в главном потоке
        Clock.schedule_once(lambda dt: show_popup(), 0)

    def _show_info_popup(self, message: str):
        """Показать информационное сообщение (вызывается из потока, используем Clock)"""
        def show_popup():
            content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
            label = Label(text=message)
            content.add_widget(label)

            btn = Button(text='OK', size_hint_y=0.3)
            content.add_widget(btn)

            popup = Popup(
                title='Информация',
                content=content,
                size_hint=(0.8, 0.4)
            )
            btn.bind(on_press=popup.dismiss)
            popup.open()
        
        # Планируем UI операцию в главном потоке
        Clock.schedule_once(lambda dt: show_popup(), 0)
