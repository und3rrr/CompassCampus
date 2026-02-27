"""
Экран карты с навигацией с поддержкой SVG/PNG планов этажей
Версия 3.0 - Переработанный интерфейс, Modern Bottom Sheet, загрузка последнего корпуса
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
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
from kivy.graphics import Color, RoundedRectangle
from widgets.map_widget import MapWidget
from widgets.bottom_popup import BottomPopup
from widgets.modern_bottom_sheet import ModernBottomSheet
from services.api_client import get_api_client, Building, Node, Route
from services.cache_service import get_cache_service
from services.route_closure_service import RouteClosureService
from services.floor_plan_manager import FloorPlanManager
from services.graph_builder import GraphBuilder, GraphEdge
import logging
import threading
import os
import time

logger = logging.getLogger(__name__)


class MapScreen(Screen):
    """Экран карты с навигацией - версия 3.0"""

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
        
        # Менеджер планов этажей
        self.floor_plan_manager = FloorPlanManager(
            plans_folder=os.path.join(os.path.dirname(__file__), '../assets/floor_plans')
        )
        self.current_floor = 1
        self._initialized_on_enter = False  # Флаг для отложенной инициализации
        self.buildings_list = []  # Список загруженных корпусов
        self.building_names_map = {}  # Маппинг имя -> id для корпусов

        # === ОСНОВНОЙ ЛЕЙАУТ - БЕЗ FloatLayout ===
        main_layout = BoxLayout(orientation='vertical', padding=dp(0), spacing=dp(0))
        
        # === ВЕРХНЯЯ ПАНЕЛЬ (современный дизайн) ===
        header = BoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(90),
            padding=dp(10),
            spacing=dp(8)
        )
        
        # Фон заголовка (светло-синий цвет)
        with header.canvas.before:
            Color(0.95, 0.97, 1.0, 1.0)  # Очень светло-синий
            RoundedRectangle(size=header.size, pos=header.pos, radius=[0, 0, dp(15), dp(15)])
        header.bind(size=self._update_header_bg, pos=self._update_header_bg)
        
        # Название экрана и выбор этажа на одной строке
        top_row = BoxLayout(size_hint=(1, None), height=dp(35), spacing=dp(10))
        
        # СПИННЕР ВЫБОРА КОРПУСА (слева)
        building_layout = BoxLayout(size_hint_x=0.35, spacing=dp(5))
        building_label = Label(
            text='Корпус:',
            size_hint_x=0.3,
            font_size='12sp',
            color=(0.3, 0.3, 0.3, 1.0)
        )
        building_layout.add_widget(building_label)
        
        self.building_spinner = Spinner(
            text='Выбрать',
            values=(),  # Will be populated in on_enter
            size_hint_x=0.7,
            background_color=(0.2, 0.6, 0.3, 1.0),
            color=(1, 1, 1, 1.0)
        )
        # Привязка будет добавлена в on_enter()
        building_layout.add_widget(self.building_spinner)
        top_row.add_widget(building_layout)
        
        title = Label(
            text='Карта корпуса',
            size_hint_x=0.3,
            font_size='18sp',
            bold=True,
            color=(0.1, 0.1, 0.1, 1.0)
        )
        top_row.add_widget(title)
        
        # Спиннер этажа (современный стиль)
        floor_layout = BoxLayout(size_hint_x=0.35, spacing=dp(5))
        floor_label = Label(
            text='Этаж:',
            size_hint_x=0.4,
            font_size='12sp',
            color=(0.3, 0.3, 0.3, 1.0)
        )
        floor_layout.add_widget(floor_label)
        
        self.floor_spinner = Spinner(
            text='1',
            values=('-1', '1', '2', '3'),
            size_hint_x=0.6,
            background_color=(0.2, 0.4, 0.9, 1.0),
            color=(1, 1, 1, 1.0)
        )
        self.floor_spinner.bind(text=self.on_floor_changed)
        floor_layout.add_widget(self.floor_spinner)
        top_row.add_widget(floor_layout)
        
        header.add_widget(top_row)
        
        # Поле поиска
        search_layout = BoxLayout(size_hint=(1, None), height=dp(40), spacing=dp(8))
        
        self.search_input = TextInput(
            hint_text='Поиск помещения...',
            multiline=False,
            size_hint_x=0.85,
            background_color=(1, 1, 1, 1.0),
            foreground_color=(0.1, 0.1, 0.1, 1.0),
            padding=dp(8),
            font_size='13sp'
        )
        search_layout.add_widget(self.search_input)
        
        search_btn = Button(
            text='Поиск',
            size_hint_x=0.15,
            background_color=(0.2, 0.8, 0.3, 1.0),
            font_size='16sp'
        )
        search_btn.bind(on_press=self.on_search)
        search_layout.add_widget(search_btn)
        
        header.add_widget(search_layout)
        main_layout.add_widget(header)
        
        # === РЕЗУЛЬТАТЫ ПОИСКА (dropdown) ===
        self.search_results_container = BoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=0,
            spacing=dp(2),
            padding=dp(5)
        )
        main_layout.add_widget(self.search_results_container)
        
        # === КАРТА ===
        self.map_widget = MapWidget(size_hint=(1, 1))
        main_layout.add_widget(self.map_widget)
        
        # === БЛОК УПРАВЛЕНИЯ (нижний) ===
        control_panel = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(50),
            padding=dp(8),
            spacing=dp(8)
        )
        
        # Фон управления
        with control_panel.canvas.before:
            Color(0.95, 0.95, 0.95, 1.0)
            RoundedRectangle(size=control_panel.size, pos=control_panel.pos, radius=[dp(15), dp(15), 0, 0])
        control_panel.bind(size=self._update_control_bg, pos=self._update_control_bg)
        
        reset_btn = self._create_control_btn('Сброс', self.on_reset_view)
        control_panel.add_widget(reset_btn)
        
        zoom_in_btn = self._create_control_btn('Увеличить', self.on_zoom_in)
        control_panel.add_widget(zoom_in_btn)
        
        zoom_out_btn = self._create_control_btn('Уменьшить', self.on_zoom_out)
        control_panel.add_widget(zoom_out_btn)
        
        cancel_btn = self._create_control_btn('Отмена', self.on_cancel_selection)
        control_panel.add_widget(cancel_btn)
        
        back_btn = self._create_control_btn('Выход', self.on_back)
        control_panel.add_widget(back_btn)
        
        main_layout.add_widget(control_panel)
        
        self.main_layout = main_layout
        self.add_widget(main_layout)
        
        # Загружаем последний выбранный корпус при старте
        self._load_last_building()

    def _update_header_bg(self, instance, value):
        """Обновить фон заголовка при изменении размера"""
        if hasattr(instance, 'canvas'):
            instance.canvas.before.clear()
            with instance.canvas.before:
                Color(0.95, 0.97, 1.0, 1.0)
                RoundedRectangle(size=instance.size, pos=instance.pos, radius=[0, 0, dp(15), dp(15)])

    def _update_control_bg(self, instance, value):
        """Обновить фон управления при изменении размера"""
        if hasattr(instance, 'canvas'):
            instance.canvas.before.clear()
            with instance.canvas.before:
                Color(0.95, 0.95, 0.95, 1.0)
                RoundedRectangle(size=instance.size, pos=instance.pos, radius=[dp(15), dp(15), 0, 0])

    def _create_control_btn(self, text: str, callback):
        """Создать кнопку управления с современным стилем"""
        btn = Button(
            text=text,
            background_color=(0.2, 0.4, 0.9, 1.0),
            color=(1, 1, 1, 1.0),
            font_size='13sp',
            bold=True,
            size_hint_x=0.2
        )
        btn.bind(on_press=callback)
        return btn
    
    def _load_last_building(self):
        """Загрузить последний выбранный корпус из кэша"""
        try:
            # Получаем ID последнего здания из кэша
            last_building_id = self.cache_service.get('last_building_id')
            
            thread = threading.Thread(
                target=self._fetch_last_building,
                args=(last_building_id,)
            )
            thread.daemon = True
            thread.start()
        except Exception as e:
            logger.warning(f"Could not load last building: {e}")
            # Загружаем первое здание как fallback
            self._load_building_data()

    def _fetch_last_building(self, last_building_id):
        """Получить последний выбранный корпус"""
        try:
            if last_building_id:
                # Пытаемся найти здание с сохранённым ID
                buildings = self.api_client.get_buildings()
                for building in buildings:
                    if building.id == last_building_id:
                        self.building = building
                        logger.info(f"Loaded last building: {building.id}")
                        Clock.schedule_once(lambda dt: self._load_building_data(), 0)
                        return
            
            # Если не найдено, загружаем первое здание
            logger.warning("Last building not found, loading first building")
            self._load_building_data()
        except Exception as e:
            logger.error(f"Failed to load last building: {e}")
            self._load_building_data()

    def _load_buildings_list(self):
        """Загрузить список всех доступных корпусов"""
        try:
            buildings = self.api_client.get_buildings()
            self.buildings_list = buildings
            
            # Создаём маппинг имя -> id
            self.building_names_map = {b.name: b.id for b in buildings}
            
            # Обновляем спиннер
            building_names = [b.name for b in buildings]
            logger.info(f"[MapScreen] Loaded {len(buildings)} buildings: {building_names}")
            
            Clock.schedule_once(
                lambda dt: self._update_building_spinner(building_names), 0
            )
        except Exception as e:
            logger.error(f"Failed to load buildings list: {e}")

    def _update_building_spinner(self, building_names):
        """Обновить спиннер выбора корпуса"""
        if building_names:
            self.building_spinner.values = tuple(building_names)
            if self.building:
                # Устанавливаем текущий корпус в спиннер
                self.building_spinner.text = self.building.name
            else:
                self.building_spinner.text = building_names[0]

    def _fetch_last_building(self, last_building_id):
        """Получить последний выбранный корпус"""
        try:
            if last_building_id:
                # Пытаемся найти здание с сохранённым ID
                buildings = self.api_client.get_buildings()
                for building in buildings:
                    if building.id == last_building_id:
                        self.building = building
                        logger.info(f"Loaded last building: {building.id}")
                        Clock.schedule_once(lambda dt: self._load_building_data(), 0)
                        return
            
            # Если не найдено, загружаем первое здание
            logger.warning("Last building not found, loading first building")
            self._load_building_data()
        except Exception as e:
            logger.error(f"Failed to load last building: {e}")
            self._load_building_data()

    def set_building(self, building: Building):
        """Установить активное здание и сохранить в кэше"""
        logger.info(f"[MapScreen.set_building] Called with building: {building.name}")
        self.building = building
        
        # Сохраняем ID выбранного здания
        try:
            self.cache_service.set('last_building_id', building.id)
            logger.info(f"[MapScreen.set_building] Saved last building ID: {building.id}")
        except Exception as e:
            logger.warning(f"[MapScreen.set_building] Could not save last building ID: {e}")
        
        if self.building:
            logger.info("[MapScreen.set_building] Updating floor spinner...")
            # Обновляем спиннер этажей с поддержкой -1
            floors = []
            if any(n.floor == -1 for n in self.building.nodes):
                floors.append('-1')
            floors.extend([str(i) for i in range(1, self.building.floors + 1)])
            self.floor_spinner.values = floors
            self.floor_spinner.text = '1'
            
            # Загружаем данные здания
            logger.info("[MapScreen.set_building] Calling _load_building_data()...")
            self._load_building_data()
            logger.info("[MapScreen.set_building] Done!")

    def _load_building_data(self):
        """Загрузить данные здания"""
        logger.info("[MapScreen._load_building_data] Starting background thread...")
        thread = threading.Thread(target=self._fetch_building_data)
        thread.daemon = True
        thread.start()
        logger.info("[MapScreen._load_building_data] Thread started, returning...")

    def _fetch_building_data(self):
        """Получить данные здания с API"""
        logger.info("[MapScreen._fetch_building_data] Starting...")
        try:
            # Если building ещё не установлено, загружаем первое здание
            if not self.building:
                logger.info("[MapScreen._fetch_building_data] Building not set, fetching from API...")
                buildings = self.api_client.get_buildings()
                if buildings:
                    self.building = buildings[0]
                    logger.info(f"[MapScreen._fetch_building_data] Loaded building: {self.building.id}")
                else:
                    logger.warning("[MapScreen._fetch_building_data] No buildings available")
                    return
            else:
                logger.info(f"[MapScreen._fetch_building_data] Building already set: {self.building.id}")
            
            # 🔍 ОТЛАДКА: логируем состояние графа
            if self.building:
                logger.info(f"[MapScreen._fetch_building_data] Building graph state: {len(self.building.nodes)} nodes, {len(self.building.edges) if self.building.edges else 0} edges")
            
            # Обновляем UI в главном потоке через Clock
            logger.info("[MapScreen._fetch_building_data] Scheduling UI update...")
            Clock.schedule_once(lambda dt: self._update_map_display(), 0)
            
            # Также устанавливаем callback для выбора узлов
            logger.info("[MapScreen._fetch_building_data] Scheduling callback setup...")
            Clock.schedule_once(lambda dt: self._setup_map_callbacks(), 0)
            logger.info("[MapScreen._fetch_building_data] Done!")
        except Exception as e:
            logger.error(f"[MapScreen._fetch_building_data] Failed to load building data: {e}")
            error_message = f"Ошибка загрузки: {str(e)}"
            Clock.schedule_once(lambda dt, msg=error_message: self._show_error_popup(msg), 0)

    def _setup_map_callbacks(self):
        """Установить обработчики событий карты"""
        logger.info("[MapScreen._setup_map_callbacks] Starting...")
        # Установить callback для выбора узлов на карте
        self.map_widget.on_node_selected_callback = self.on_map_node_selected
        
        # Обновляем спиннер этажей если здание загружено
        if self.building and self.building.floors:
            logger.info("[MapScreen._setup_map_callbacks] Updating floor spinner...")
            # Добавляем все доступные этажи, включая -1 (подвал)
            floors = []
            if any(n.floor == -1 for n in self.building.nodes):
                floors.append('-1')
            floors.extend([str(i) for i in range(1, self.building.floors + 1)])
            self.floor_spinner.values = floors
            self.floor_spinner.text = '1'
        logger.info("[MapScreen._setup_map_callbacks] Done!")

    def _update_map_display(self):
        """Обновить отображение карты"""
        logger.info("[MapScreen._update_map_display] Starting...")
        if self.building and self.building.nodes:
            logger.info("[MapScreen._update_map_display] Building has nodes, filtering by floor...")
            # Фильтруем узлы по текущему этажу
            current_floor = int(self.floor_spinner.text)
            self.current_floor = current_floor
            floor_nodes = [n for n in self.building.nodes if n.floor == current_floor]
            logger.info(f"[MapScreen._update_map_display] Found {len(floor_nodes)} nodes on floor {current_floor}")

            logger.info("[MapScreen._update_map_display] Calling map_widget.set_nodes()...")
            self.map_widget.set_nodes(floor_nodes)
            
            # ========== ЗАГРУЗКА ПЛАНА ЭТАЖА (SVG/PNG) ==========
            # Проверяем наличие плана этажа и загружаем его как фон
            logger.info("[MapScreen._update_map_display] Loading floor plan...")
            plan_file = self.floor_plan_manager.get_plan_file(current_floor)
            if plan_file and os.path.exists(plan_file):
                try:
                    # Для всех файлов используем set_background_image
                    # которая автоматически конвертирует SVG → PNG если нужно
                    logger.info(f"[MapScreen._update_map_display] Setting background image: {plan_file}")
                    self.map_widget.set_background_image(plan_file)
                    logger.info(f"[MapScreen._update_map_display] Loaded floor plan for floor {current_floor}: {plan_file}")
                except Exception as e:
                    logger.warning(f"[MapScreen._update_map_display] Could not load floor plan for floor {current_floor}: {e}")
                    self.map_widget.set_background_image(None)
            else:
                # Если плана нет, очищаем фон
                logger.info("[MapScreen._update_map_display] No floor plan found, clearing background...")
                self.map_widget.set_background_image(None)
            
            # Добавляем edges - связи между узлами
            if not self.building.nodes:
                logger.info("[MapScreen._update_map_display] No nodes, returning...")
                return
                
            logger.info("[MapScreen._update_map_display] Building edges from nodes...")
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
            logger.info("[MapScreen._update_map_display] Calling GraphBuilder.build_edges_from_nodes()...")
            builder = GraphBuilder()
            edges = builder.build_edges_from_nodes(nodes_dicts)
            logger.info(f"[MapScreen._update_map_display] Built {len(edges)} total edges")
            
            # Фильтруем edges по текущему этажу
            logger.info("[MapScreen._update_map_display] Filtering edges by floor...")
            floor_edges = []
            node_ids = {n.id for n in floor_nodes}
            for edge in edges:
                if edge.from_id in node_ids and edge.to_id in node_ids:
                    floor_edges.append((edge.from_id, edge.to_id))
            
            logger.info(f"[MapScreen._update_map_display] Setting {len(floor_edges)} floor edges...")
            self.map_widget.set_edges(floor_edges)

            # Если есть сервис закрытий, показываем закрытые маршруты
            if self.closure_service:
                logger.info("[MapScreen._update_map_display] Setting closed routes...")
                closed_edges = self.closure_service.get_closed_edges()
                closed_nodes = self.closure_service.get_closed_nodes()
                self.map_widget.set_closed_routes(closed_edges, closed_nodes)
            logger.info("[MapScreen._update_map_display] Done!")
        else:
            logger.warning("[MapScreen._update_map_display] Building or nodes not available")

    def on_enter(self):
        """Load last building when screen is opened (deferred from __init__)"""
        logger.info("[MapScreen.on_enter] Starting...")
        
        # Привязываем обработчик клавиатуры для админ меню (Ctrl+A)
        Window.bind(on_keyboard=self._on_keyboard)
        
        # Привязываем обработчик спиннера выбора корпуса (первый вход)
        try:
            self.building_spinner.bind(text=self.on_building_changed)
        except:
            pass  # Уже привязано
        
        # Загружаем список корпусов для спиннера
        if not self.buildings_list:
            thread = threading.Thread(target=self._load_buildings_list)
            thread.daemon = True
            thread.start()
        
        if not self._initialized_on_enter:
            logger.info("[MapScreen.on_enter] Loading last building")
            self._load_last_building()
            self._initialized_on_enter = True
        else:
            # При повторном входе на карту (например, после редактора) - перезагружаем данные
            logger.info("[MapScreen.on_enter] Refreshing building data from cache")
            if self.building:
                # Пытаемся перезагрузить здание из кэша
                try:
                    cached_building = self.cache_service.load_building(self.building.id)
                    if cached_building:
                        self.building = cached_building
                        logger.info(f"[MapScreen.on_enter] Reloaded building from cache: {len(self.building.nodes)} nodes, {len(self.building.edges)} edges")
                        # Обновляем отображение карты с новыми данными
                        Clock.schedule_once(lambda dt: self._update_map_display(), 0)
                except Exception as e:
                    logger.warning(f"[MapScreen.on_enter] Failed to reload from cache: {e}")
        
        logger.info("[MapScreen.on_enter] Done")

    def on_building_changed(self, spinner, text):
        """Обработка выбора корпуса"""
        if text and text != 'Выбрать':
            building_id = self.building_names_map.get(text)
            if building_id:
                self.cache_service.set('last_building_id', building_id)
                # Загружаем выбранный корпус
                thread = threading.Thread(
                    target=self._load_building_by_id,
                    args=(building_id,)
                )
                thread.daemon = True
                thread.start()

    def _load_building_by_id(self, building_id: str):
        """Загрузить корпус по ID"""
        try:
            building = self.api_client.get_building(building_id)
            self.building = building
            logger.info(f"[MapScreen] Loaded building: {building.id} - {building.name}")
            # Обновляем этажи на основе нового здания
            Clock.schedule_once(lambda dt: self._update_floor_spinner(), 0)
            Clock.schedule_once(lambda dt: self._load_building_data(), 0.1)
        except Exception as e:
            logger.error(f"[MapScreen] Failed to load building {building_id}: {e}")

    def _update_floor_spinner(self):
        """Обновить спиннер этажей в соответствии с выбранным корпусом"""
        if self.building and self.building.floors:
            floors = []
            # Для нижнего корпуса: -1, 1, 2, 3
            # Для остальных: 1, 2, 3, 4, 5
            if self.building.id.lower() in ['lower', 'нижний']:
                floors = ['-1', '1', '2', '3']
            else:
                floors = ['1', '2', '3', '4', '5'][:self.building.floors]
            
            self.floor_spinner.values = tuple(floors)
            self.floor_spinner.text = floors[0] if floors else '1'
            self.current_floor = int(self.floor_spinner.text)

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
                
                # Если есть стартовая точка, строим маршрут
                if self.start_node:
                    self._calculate_route()
                    logger.info(f"Route from QR: {self.start_node.name} → {node_name}")
                else:
                    # Выбираем стартовую точку автоматически (первый узел)
                    if self.building.nodes:
                        self.start_node = self.building.nodes[0]
                        self.map_widget.set_start_node(self.start_node)
                        self._calculate_route()
                        logger.info(f"Route auto-start from QR: {self.start_node.name} → {node_name}")
                        self._calculate_route()
                
                logger.info(f"QR: Set end node {node_name} (ID: {node_id})")
            else:
                logger.warning(f"Node with ID {node_id} not found in building")
        except Exception as e:
            logger.error(f"Error setting end node from QR: {e}")

    def on_map_node_selected(self, node: Node):
        """Обработка выбора узла на карте - показываем Modern Bottom Sheet"""
        sheet = ModernBottomSheet(
            node=node,
            on_from_selected=self._set_from_node,
            on_to_selected=self._set_to_node,
            size_hint=(1, 0.35),
            pos_hint={'x': 0, 'y': 0}
        )
        self.main_layout.add_widget(sheet)
        sheet.open()

    def _set_from_node(self, node: Node):
        """Установить точку ОТСЮДА"""
        self.start_node = node
        self.map_widget.set_start_node(node)
        
        if self.end_node:
            status = f'Маршрут: {node.name} → {self.end_node.name}'
        else:
            status = f'ОТСЮДА: {node.name}\nВыберите конечную точку «СЮДА»'
        
        logger.info(f"Start node set (ОТСЮДА): {node.name}")
        
        if self.end_node:
            self._calculate_route()

    def _set_to_node(self, node: Node):
        """Установить точку СЮДА"""
        if self.start_node is None:
            # Если стартовая точка не выбрана, выбираем конец и автоматически старт
            self.start_node = self.building.nodes[0] if self.building and self.building.nodes else node
            if self.start_node != node:
                self.map_widget.set_start_node(self.start_node)
        
        self.end_node = node
        self.map_widget.set_end_node(node)
        
        status = f'Маршрут: {self.start_node.name} → {node.name}'
        
        # Переходим на нужный этаж
        if hasattr(node, 'floor'):
            self.floor_spinner.text = str(node.floor)
        
        self._highlight_graph()
        self._calculate_route()
        logger.info(f"End node set (СЮДА): {node.name}")
    
    # Для совместимости со старыми вызовами
    def _set_start_node(self, node: Node):
        """Установить стартовую точку (deprecated, используйте _set_from_node)"""
        self._set_from_node(node)

    def _set_end_node(self, node: Node):
        """Установить конечную точку (deprecated, используйте _set_to_node)"""
        self._set_to_node(node)

    def _calculate_route(self):
        """Вычислить маршрут между стартом и концом"""
        if not self.start_node or not self.end_node:
            return

        thread = threading.Thread(target=self._fetch_route)
        thread.daemon = True
        thread.start()

    def _fetch_route(self):
        """Получить маршрут с API или использовать локальный граф
        
        Оптимизация: если API не отвечает быстро (2 сек), используем локальный поиск
        """
        api_start = time.time()
        try:
            logger.info(f"Calculating route from {self.start_node.id} to {self.end_node.id}")
            
            # Временно переопределяем таймаут для этого запроса (2 сек вместо 10)
            original_timeout = self.api_client.timeout
            self.api_client.timeout = 2  # 2 сек для быстрого fallback
            
            try:
                route = self.api_client.get_route(
                    self.building.id,
                    self.start_node.id,
                    self.end_node.id
                )
                api_time = (time.time() - api_start) * 1000
                logger.info(f"Route from API: {api_time:.1f}ms")
                
                self.current_route = route
                self.map_widget.set_route(route)

                # Логируем информацию о маршруте
                logger.info(
                    f'✓ Маршрут (API): {self.start_node.name} → {self.end_node.name} | '
                    f'Расстояние: {route.distance:.0f}м | '
                    f'Время: {route.estimated_time:.0f}мин | '
                    f'Переходов: {route.floor_changes}'
                )
            finally:
                # Восстанавливаем оригинальный таймаут
                self.api_client.timeout = original_timeout

        except Exception as e:
            api_time = (time.time() - api_start) * 1000
            logger.warning(f"Failed to get route from API ({api_time:.1f}ms): {e}")
            logger.info("Falling back to local graph-based pathfinding...")
            self._calculate_route_locally()

    def _calculate_route_locally(self):
        """Использовать локальный граф для построения маршрута (fallback)"""
        try:
            if not self.building or not self.building.nodes:
                Clock.schedule_once(lambda dt: self._show_error_popup("Ошибка: нет данных о здании"), 0)
                return
            
            # ПРОФИЛИРОВАНИЕ: общее время
            total_start = time.time()
            
            # ПРОФИЛИРОВАНИЕ: конвертация
            convert_start = time.time()
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
            convert_time = (time.time() - convert_start) * 1000
            
            # ПРОФИЛИРОВАНИЕ: построение граф
            graph_start = time.time()
            
            # 🔑 ВАЖНО: использовать сохранённые рёбра из редактора вместо автогенерирования!
            if self.building.edges:
                # Пользуемся рёбрами из редактора (которые сохранены)
                edge_objects = []
                for from_id, to_id in self.building.edges:
                    from_node = nodes_map.get(str(from_id))
                    to_node = nodes_map.get(str(to_id))
                    
                    if from_node and to_node:
                        distance = GraphBuilder.calculate_distance(
                            from_node.x, from_node.y,
                            to_node.x, to_node.y
                        )
                        edge_objects.append(GraphEdge(
                            from_id=str(from_id),
                            to_id=str(to_id),
                            weight=distance
                        ))
                
                edges = edge_objects
                logger.info(f"✓ Using {len(edges)} edges from building graph (editor)")
            else:
                # Fallback: если нет рёбер, использовать автогенерирование (но это плохой вариант)
                edges = GraphBuilder.build_edges_from_nodes(nodes_dicts)
                logger.warning(f"⚠️ No edges from building graph, using auto-generated {len(edges)} edges (may be incorrect!)")
            
            graph_time = (time.time() - graph_start) * 1000
            
            # Находим кратчайший путь
            # Создаём словарь с ID в виде строк для совместимости
            nodes_dict_for_search = {str(nd['Id']): nd for nd in nodes_dicts}
            
            # ПРОФИЛИРОВАНИЕ: поиск маршрута
            search_start = time.time()
            path_result = GraphBuilder.find_shortest_path(
                str(self.start_node.id),
                str(self.end_node.id),
                edges,
                nodes_dict_for_search
            )
            search_time = (time.time() - search_start) * 1000
            
            total_time = (time.time() - total_start) * 1000
            cache_size = GraphBuilder.get_cache_size()
            
            # Логируем детальное профилирование
            logger.info(
                f"Route calculation breakdown: "
                f"Convert={convert_time:.2f}ms | "
                f"BuildGraph={graph_time:.2f}ms | "
                f"Dijkstra={search_time:.2f}ms | "
                f"Total={total_time:.2f}ms | "
                f"RouteCacheSize={cache_size} | "
                f"GraphCacheSize={GraphBuilder.get_graph_cache_size()}"
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
                    
                    # Логируем информацию о маршруте
                    logger.info(
                        f'✓ Маршрут (локальный): {self.start_node.name} → {self.end_node.name} | '
                        f'Расстояние: {distance:.0f}м | '
                        f'Время: {distance/1.4:.0f}мин'
                    )
                    
                    # Логируем производительность
                    is_cached = "(кэшировано)" if search_time < 0.001 else ""
                    logger.info(f"Pathfinding: {search_time*1000:.2f}ms {is_cached} | Cache size: {cache_size} | Path length: {len(route_nodes)} nodes")
                
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

    def _on_keyboard(self, window, key, scancode, codepoint, modifier):
        """Обработка клавиатуры для горячих клавиш"""
        # Ctrl+A или Ctrl+Shift+A - открыть админ панель
        if key == 97 and 'ctrl' in modifier:  # Ctrl+A
            logger.info("[MapScreen] Opening admin panel (Ctrl+A)")
            self.manager.current = 'admin'
            return True
        
        # Ctrl+E - открыть редактор графа
        if key == 101 and 'ctrl' in modifier:  # Ctrl+E
            if self.building:
                logger.info("[MapScreen] Opening graph editor (Ctrl+E)")
                editor_screen = self.manager.get_screen('graph_editor')
                editor_screen.building = self.building
                self.manager.current = 'graph_editor'
                return True
        
        return False

    def on_leave(self):
        """Отписка от событий при выходе"""
        logger.info("[MapScreen.on_leave] Unbinding keyboard")
        try:
            Window.unbind(on_keyboard=self._on_keyboard)
        except:
            pass  # Может быть уже отписано

    def on_back(self, instance):
        """Вернуться на главный экран"""
        self.manager.current = 'home'

    def on_cancel_selection(self, instance):
        """Отменить выбор начальной точки"""
        self.start_node = None
        self.end_node = None
        self.current_route = None
        self.map_widget.clear_selection()
        logger.info("Selection cancelled")

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
