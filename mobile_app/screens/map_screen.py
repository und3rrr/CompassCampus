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
                self._show_search_results(results)
            else:
                self._show_info_popup("Не найдено")
        except Exception as e:
            logger.error(f"Search failed: {e}")
            self._show_error_popup(str(e))

    def _show_search_results(self, results: list):
        """Показать результаты поиска"""
        content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))

        for node in results:
            btn = Button(
                text=f'{node.name} (Этаж {node.floor})',
                size_hint_y=None,
                height=dp(50),
                background_color=(0.3, 0.6, 1.0, 1.0)
            )
            btn.node = node
            btn.bind(on_press=self.on_node_selected_from_search)
            content.add_widget(btn)

        popup = Popup(
            title='Результаты поиска',
            content=content,
            size_hint=(0.9, 0.6)
        )
        popup.open()

    def on_node_selected_from_search(self, instance):
        """Обработка выбора узла из поиска"""
        node = instance.node
        self.end_node = node
        self.map_widget.set_end_node(node)

        # Автоматически переходим на этаж узла
        self.floor_spinner.text = str(node.floor)

        # Пытаемся построить маршрут если есть стартовая точка
        if self.start_node:
            self._calculate_route()

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
                self._show_error_popup("Ошибка: нет данных о здании")
                return
            
            # Конвертируем Node объекты в словари для графа
            nodes_dicts = []
            nodes_map = {}
            for node in self.building.nodes:
                node_dict = {
                    'Id': node.id,
                    'Name': node.name,
                    'Floor': node.floor,
                    'Type': node.type,
                    'X': node.x,
                    'Y': node.y
                }
                nodes_dicts.append(node_dict)
                nodes_map[str(node.id)] = node
            
            # Строим граф
            edges = GraphBuilder.build_edges_from_nodes(nodes_dicts)
            
            # Находим кратчайший путь
            path_result = GraphBuilder.find_shortest_path(
                str(self.start_node.id),
                str(self.end_node.id),
                edges,
                {nd['Id']: nd for nd in nodes_dicts}
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
                    id="local",
                    building_id=self.building.id,
                    start_node=self.start_node,
                    end_node=self.end_node,
                    nodes=route_nodes,
                    distance=distance,
                    estimated_time=distance / 1.4,  # ~1.4 м/мин пешком
                    floor_changes=0
                )
                
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
            else:
                self._show_error_popup("Маршрут не найден (нет пути между точками)")
                
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
