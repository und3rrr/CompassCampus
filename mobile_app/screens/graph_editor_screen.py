"""
Экран редактора графов для визуального редактирования узлов и рёбер
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.clock import Clock
from widgets.visual_graph_editor import VisualGraphEditor
from services.api_client import get_api_client, Building, Node
from services.cache_service import get_cache_service
from services.floor_plan_manager import FloorPlanManager
import logging
import json
import os
import threading

logger = logging.getLogger(__name__)


class GraphEditorScreen(Screen):
    """Экран редактора графов с удобным UI"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.building: Building = None
        self.api_client = get_api_client()
        self.cache_service = get_cache_service()
        self.background_image = None
        
        # Режимы редактирования
        self.current_mode = 'select'  # select, link, delete, corridor
        self.mode_colors = {
            'select': (0.3, 0.7, 0.3, 1.0),    # Зелёный
            'link': (0.3, 0.5, 1.0, 1.0),      # Синий
            'delete': (1.0, 0.4, 0.4, 1.0),    # Красный
            'corridor': (1.0, 0.8, 0.3, 1.0)   # Жёлтый
        }
        
        # Менеджер планов этажей - инициализируется при первом доступе
        self.floor_plan_manager = None
        self._floor_plan_manager_initialized = False
        
        # История действий для undo/redo
        self.history = []
        self.history_index = -1
        self.action_batch_timeout = 0.5
        self.last_action_time = 0
        self.batching_actions = False
        
        # Флаг для отложенной инициализации при входе на экран
        self._initialized_on_enter = False
        
        # Основной лейаут
        main_layout = BoxLayout(orientation='vertical', padding=dp(5), spacing=dp(5))

        # ===== ВЕРХНЯЯ ПАНЕЛЬ: Выбор этажа и управление =====
        top_panel = BoxLayout(size_hint_y=0.08, spacing=dp(5))
        
        floor_label = Label(text='Этаж:', size_hint_x=0.07)
        top_panel.add_widget(floor_label)
        
        self.floor_spinner = Spinner(
            text='1',
            values=('-1', '1', '2', '3', '4', '5'),
            size_hint_x=0.08
        )
        self.floor_spinner.bind(text=self._on_floor_changed)
        top_panel.add_widget(self.floor_spinner)
        
        # Кнопка инструкций
        help_btn = Button(text='ℹ️ Помощь', size_hint_x=0.1)
        help_btn.bind(on_press=self._show_help)
        top_panel.add_widget(help_btn)
        
        # 🔍 ЗУМИРОВАНИЕ
        zoom_minus_btn = Button(text='Уменьшить', size_hint_x=0.08)
        zoom_minus_btn.bind(on_press=self._zoom_out)
        top_panel.add_widget(zoom_minus_btn)
        
        self.zoom_label = Label(text='100%', size_hint_x=0.08)
        top_panel.add_widget(self.zoom_label)
        
        zoom_plus_btn = Button(text='Увеличить', size_hint_x=0.08)
        zoom_plus_btn.bind(on_press=self._zoom_in)
        top_panel.add_widget(zoom_plus_btn)
        
        zoom_reset_btn = Button(text='⟲ 1x', size_hint_x=0.08)
        zoom_reset_btn.bind(on_press=self._zoom_reset)
        top_panel.add_widget(zoom_reset_btn)
        
        # Undo/Redo
        self.undo_btn = Button(text='↶', size_hint_x=0.07)
        self.undo_btn.bind(on_press=self._undo)
        top_panel.add_widget(self.undo_btn)
        
        self.redo_btn = Button(text='↷', size_hint_x=0.07)
        self.redo_btn.bind(on_press=self._redo)
        top_panel.add_widget(self.redo_btn)
        
        # Кнопка сохранения (вправо)
        save_btn = Button(text='💾 Сохр', size_hint_x=0.1)
        save_btn.bind(on_press=self._save_graph)
        top_panel.add_widget(save_btn)
        
        back_btn = Button(text='Назад', size_hint_x=0.1)
        back_btn.bind(on_press=self.on_back)
        top_panel.add_widget(back_btn)
        
        main_layout.add_widget(top_panel)

        # ===== РЕЖИМЫ РЕДАКТИРОВАНИЯ =====
        # Контейнер для двух строк кнопок режимов
        modes_container = BoxLayout(orientation='vertical', size_hint_y=0.16, spacing=dp(5), padding=dp(5))
        
        # ПЕРВАЯ СТРОКА КНОПОК
        modes_row1 = BoxLayout(size_hint_y=0.5, spacing=dp(5))
        
        # Режим выбора
        self.select_mode_btn = Button(text='☝️ Выбрать', background_color=self.mode_colors['select'])
        self.select_mode_btn.bind(on_press=self._set_mode)
        modes_row1.add_widget(self.select_mode_btn)
        
        # Режим соединения
        self.link_mode_btn = Button(text='🔗 Связать', background_color=self.mode_colors['link'])
        self.link_mode_btn.bind(on_press=self._set_mode)
        modes_row1.add_widget(self.link_mode_btn)
        
        # Режим удаления
        self.delete_mode_btn = Button(text='✕ Удалить', background_color=self.mode_colors['delete'])
        self.delete_mode_btn.bind(on_press=self._set_mode)
        modes_row1.add_widget(self.delete_mode_btn)
        
        modes_container.add_widget(modes_row1)
        
        # ВТОРАЯ СТРОКА КНОПОК
        modes_row2 = BoxLayout(size_hint_y=0.5, spacing=dp(5))
        
        # Режим коридора
        self.corridor_mode_btn = Button(text='➕ Коридор', background_color=self.mode_colors['corridor'])
        self.corridor_mode_btn.bind(on_press=self._set_mode)
        modes_row2.add_widget(self.corridor_mode_btn)
        
        # Кнопка добавления точки
        add_node_btn = Button(text='+ Точка')
        add_node_btn.bind(on_press=self._show_new_node_dialog)
        modes_row2.add_widget(add_node_btn)
        
        # Кнопка удаления связок
        delete_edges_btn = Button(text='✕ Связки', background_color=(1.0, 0.6, 0.3, 1.0))
        delete_edges_btn.bind(on_press=self._delete_edges_mode)
        modes_row2.add_widget(delete_edges_btn)
        
        modes_container.add_widget(modes_row2)
        
        main_layout.add_widget(modes_container)

        # ===== РЕДАКТОР ГРАФОВ =====
        self.graph_editor = VisualGraphEditor(size_hint_y=0.7)
        self.graph_editor.on_node_created_callback = self._on_node_created
        self.graph_editor.on_node_deleted_callback = self._on_node_deleted
        self.graph_editor.on_edge_created_callback = self._on_edge_created
        self.graph_editor.on_node_moved_callback = self._on_node_moved
        self.graph_editor.editor_mode = self.current_mode
        main_layout.add_widget(self.graph_editor)

        # ===== ИНФОРМАЦИОННАЯ ПАНЕЛЬ =====
        info_panel = BoxLayout(size_hint_y=0.08, spacing=dp(5))
        self.info_label = Label(
            text='Выберите режим редактирования выше',
            size_hint_y=1.0
        )
        info_panel.add_widget(self.info_label)
        main_layout.add_widget(info_panel)

        self.main_layout = main_layout  # Сохраняем для пересчета в on_size
        self.add_widget(main_layout)
        
        # Привязываем пересчет лейаута при изменении размера
        self.bind(size=self._on_size)

    def _on_size(self, instance, value):
        """Обновить лейаут при изменении размера"""
        # Пересчитываем размеры всех элементов
        if hasattr(self, 'main_layout'):
            self.main_layout.do_layout()
            logger.debug(f"GraphEditorScreen: layout recalculated, size={value}")

    def _set_mode(self, button):
        """Установить режим редактирования"""
        mode_map = {
            'select': '☝️ Выбрать',
            'link': '🔗 Связать',
            'delete': '✕ Удалить',
            'corridor': '➕ Коридор'
        }
        
        for mode, btn_text in mode_map.items():
            if button.text == btn_text:
                self.current_mode = mode
                self.graph_editor.editor_mode = mode
                self._update_mode_buttons()
                logger.info(f"Mode changed to: {mode}")
                break
        
        self._update_mode_info()

    def _update_mode_buttons(self):
        """Обновить цвета кнопок режимов"""
        buttons = {
            'select': self.select_mode_btn,
            'link': self.link_mode_btn,
            'delete': self.delete_mode_btn,
            'corridor': self.corridor_mode_btn
        }
        
        for mode, btn in buttons.items():
            if mode == self.current_mode:
                btn.background_color = (1.0, 1.0, 1.0, 1.0)  # Белый = активный
            else:
                btn.background_color = self.mode_colors[mode]

    def _delete_edges_mode(self, instance):
        """Перейти в режим удаления рёбер (связок)"""
        if not self.building or not self.building.edges:
            self._show_info_popup("Нет связок для удаления")
            return
        
        # Создаём popup для выбора рёбер
        popup_layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(5))
        
        # Список рёбер
        scroll = ScrollView()
        edges_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(2))
        edges_layout.bind(minimum_height=edges_layout.setter('height'))
        
        selected_edges = []
        
        def toggle_edge(edge_btn, edge_data):
            if edge_btn.state == 'down':
                selected_edges.append(edge_data)
                edge_btn.background_color = (1, 0, 0, 1)  # Красный = выбран
            else:
                if edge_data in selected_edges:
                    selected_edges.remove(edge_data)
                edge_btn.background_color = (0.5, 0.5, 0.5, 1)
        
        for i, edge in enumerate(self.building.edges):
            # Находим имена узлов
            node1 = next((n for n in self.building.nodes if n.id == edge[0]), None)
            node2 = next((n for n in self.building.nodes if n.id == edge[1]), None)
            if node1 and node2:
                edge_btn = Button(
                    text=f'{node1.name} → {node2.name}',
                    size_hint_y=None,
                    height=dp(40),
                    background_color=(0.5, 0.5, 0.5, 1),
                    group=f'edge_{i}'
                )
                edge_btn.bind(on_press=lambda btn, e=edge: toggle_edge(btn, e))
                edges_layout.add_widget(edge_btn)
        
        scroll.add_widget(edges_layout)
        popup_layout.add_widget(scroll)
        
        # Кнопки подтверждения
        buttons_layout = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(5))
        
        def delete_selected():
            if selected_edges:
                for edge in selected_edges:
                    if edge in self.building.edges:
                        self.building.edges.remove(edge)
                self._auto_save_graph()
                self._show_info_popup(f"Удалено {len(selected_edges)} связок")
                logger.info(f"[GraphEditorScreen] Deleted {len(selected_edges)} edges")
            popup.dismiss()
        
        delete_btn = Button(text='Удалить', size_hint_x=0.5)
        delete_btn.bind(on_press=lambda x: delete_selected())
        buttons_layout.add_widget(delete_btn)
        
        cancel_btn = Button(text='Отмена', size_hint_x=0.5)
        cancel_btn.bind(on_press=lambda x: popup.dismiss())
        buttons_layout.add_widget(cancel_btn)
        
        popup_layout.add_widget(buttons_layout)
        
        popup = Popup(
            title='Удалить связки',
            content=popup_layout,
            size_hint=(0.9, 0.8)
        )
        popup.open()

    def _update_mode_info(self):
        """Обновить текст информации в зависимости от режима"""
        mode_info = {
            'select': '☝️ Режим выбора: Click = выбрать | Drag = переместить | Shift+Click = мультивыбор',
            'link': '🔗 Режим связи: Click первую точку → Click вторую точку для соединения',
            'delete': '✕ Режим удаления: Click на точку для её удаления',
            'corridor': '➕ Режим коридора: [ДВОЙНОЙ КЛИК] начало → [ДВОЙНОЙ КЛИК] конец + ребро автоматически'
        }
        self.info_label.text = mode_info.get(self.current_mode, '')

    def _show_help(self, instance):
        """Показать окно помощи с инструкциями"""
        help_text = """ИНСТРУКЦИЯ ПО РЕДАКТОРУ ГРАФОВ

🎯 РЕЖИМЫ РЕДАКТИРОВАНИЯ:

☝️ ВЫБОР (Select):
  • Click: Выбрать одну точку
  • Shift+Click: Добавить/убрать из множественного выбора
  • Drag: Переместить выбранную(ые) точку(и)
  • Колёсико вверх/вниз: Приблизить/отдалить

🔗 СВЯЗЬ (Link):
  • Click на первую точку
  • Click на вторую точку
  • Соединяет две точки рёбером

✕ УДАЛЕНИЕ (Delete):
  • Click на точку которую нужно удалить
  • Удаляет точку и все её соединения

➕ КОРИДОР (Corridor) - 🔑 НОВАЯ ЛОГИКА:
  [ЭТАП 1] СОЗДАНИЕ КОРИДОРА:
  • 🔑 ДВОЙНОЙ КЛИК в пустоту = начальная точка коридора
  • 🔑 ЕЩЁ ДВОЙНОЙ КЛИК в пустоту = конечная точка + автоматическое ребро!
  • Итого: 1 коридор = 2 точки (начало/конец) + 1 ребро
  
  [ЭТАП 2] ПОДКЛЮЧЕНИЕ КАБИНЕТОВ:
  • Нажми кнопку [➕ Коридор] для режима
  • Click на КАБИНЕТ (Room) в этом режиме
  • Кабинет АВТОМАТИЧЕСКИ подключится к ближайшей точке коридора
  • 🎯 РЕЗУЛЬТАТ: Кабинет подключен к конец или началу коридора!
  • Так маршруты проходят: Кабинет → Коридор → Другой Кабинет

📍 ТИПЫ ТОЧЕК:
  • Room: Обычный кабинет
  • Corridor: Коридор (для промежуточных узлов)
  • Staircase: Лестница
  • Elevator: Лифт

🔍 ЗУМИРОВАНИЕ:
  • 🔍+ кнопка: Приблизить (Zoom In)
  • 🔍− кнопка: Отдалить (Zoom Out)
  • ⟲ 1x кнопка: Сброс зума на 100%
  • Колёсико мыши: Также работает для зумирования
  • Показывает текущий процент зума

💡 СОВЕТЫ:
  • Используй Undo (↶) и Redo (↷) при ошибках
  • Фон этажа загружается автоматически
  • Сохрани часто (💾)
  • Двойной клик в режиме коридора = новый коридор быстро!
"""
        
        dialog_layout = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))
        
        # Скроллируемый текст
        scroll = ScrollView()
        help_label = Label(text=help_text, size_hint_y=None, markup=True)
        help_label.bind(texture_size=help_label.setter('size'))
        scroll.add_widget(help_label)
        dialog_layout.add_widget(scroll)
        
        # Кнопка закрытия
        close_btn = Button(text='Закрыть', size_hint_y=0.15)
        close_btn.bind(on_press=lambda x: popup.dismiss())
        dialog_layout.add_widget(close_btn)
        
        popup = Popup(
            title='📖 ИНСТРУКЦИЯ РЕДАКТОРА',
            content=dialog_layout,
            size_hint=(0.95, 0.95)
        )
        popup.open()

    def set_building(self, building: Building):
        """Установить активное здание"""
        if building is None:
            logger.warning("[GraphEditorScreen.set_building] Building is None, skipping.")
            return
        logger.info(f"[GraphEditorScreen.set_building] Called with building: {building.name}")
        self.building = building
        
        # Поддерживаем полный набор этажей: подвал (-1), 1-5 этажи
        # Не перезаписываем значения, так как они уже установлены в __init__
        # Просто убеждаемся, что текущий этаж допустим
        if not self.floor_spinner.text or int(self.floor_spinner.text) not in [-1, 1, 2, 3, 4, 5]:
            self.floor_spinner.text = '1'
        
        logger.info("[GraphEditorScreen.set_building] Calling _load_building_graph()...")
        self._load_building_graph()
        logger.info("[GraphEditorScreen.set_building] Done!")

    def _get_floor_plan_manager(self):
        """Lazy-initialize FloorPlanManager"""
        if not self._floor_plan_manager_initialized:
            logger.info("[GraphEditorScreen] Initializing FloorPlanManager...")
            self.floor_plan_manager = FloorPlanManager(
                plans_folder=os.path.join(os.path.dirname(__file__), '../assets/floor_plans')
            )
            self.floor_plan_manager.scan_folder()
            self._floor_plan_manager_initialized = True
        return self.floor_plan_manager

    def _load_building_graph(self):
        """Загрузить граф здания и автоматически загрузить план этажа"""
        import threading
        def _load_in_background():
            try:
                if not self.building:
                    logger.warning("No building loaded for graph editor")
                    return
                
                # Убедимся что floor_spinner инициализирован
                if not hasattr(self, 'floor_spinner') or not self.floor_spinner:
                    logger.warning("floor_spinner not initialized")
                    return
                
                floor = int(self.floor_spinner.text)
                floor_nodes = [n for n in self.building.nodes if n.floor == floor]
                
                logger.info(f"Loading graph: {len(floor_nodes)} nodes on floor {floor}")
                
                # Обновляем UI в главном потоке
                Clock.schedule_once(lambda dt: self.graph_editor.set_nodes(floor_nodes), 0)
                
                # Загружаем рёбра
                edges = []
                if self.building.edges:
                    edges = [(f, t) for f, t in self.building.edges]
                Clock.schedule_once(lambda dt: self.graph_editor.set_edges(edges), 0)
                
                # 🔑 АВТОМАТИЧЕСКИ загружаем план этажа (уже асинхронный для SVG)
                fpm = self._get_floor_plan_manager()
                plan_file = fpm.get_plan_file(floor)
                if plan_file and os.path.exists(plan_file):
                    Clock.schedule_once(lambda dt: self.graph_editor.set_background_image(plan_file), 0)
                    logger.info(f"Auto-loaded floor plan for floor {floor}: {plan_file}")
                
                # Обновляем информацию
                Clock.schedule_once(lambda dt: self._update_info(), 0)
                Clock.schedule_once(lambda dt: self._save_state(), 0)
                logger.info(f"Graph loaded: {len(floor_nodes)} nodes on floor {floor}, {len(edges)} edges")
            except Exception as e:
                logger.error(f"Error loading graph: {e}", exc_info=True)
        
        # Запускаем в отдельном потоке чтобы не блокировать UI
        thread = threading.Thread(target=_load_in_background, daemon=True)
        thread.start()


    def _save_state(self):
        """Сохранить текущее состояние в историю"""
        try:
            import time
            current_time = time.time()
            
            if current_time - self.last_action_time > self.action_batch_timeout:
                if self.batching_actions:
                    self.batching_actions = False
                    self.last_action_time = current_time
                
                if self.history_index < len(self.history) - 1:
                    self.history = self.history[:self.history_index + 1]
                
                state = {
                    'nodes': [{'id': n.id, 'name': n.name, 'x': n.x, 'y': n.y, 'floor': n.floor, 'type': n.node_type}
                              for n in self.graph_editor.nodes],
                    'edges': list(self.graph_editor.edges)
                }
                self.history.append(state)
                self.history_index = len(self.history) - 1
                
                if len(self.history) > 50:
                    self.history = self.history[-50:]
                    self.history_index = len(self.history) - 1
                
                self.batching_actions = False
            else:
                if len(self.history) > 0:
                    state = {
                        'nodes': [{'id': n.id, 'name': n.name, 'x': n.x, 'y': n.y, 'floor': n.floor, 'type': n.node_type}
                                  for n in self.graph_editor.nodes],
                        'edges': list(self.graph_editor.edges)
                    }
                    self.history[self.history_index] = state
                self.batching_actions = True
            
            self.last_action_time = current_time
            self._update_buttons()
        except Exception as e:
            logger.error(f"Error saving state: {e}")

    def _undo(self, instance=None):
        """Отменить последнее действие"""
        if self.history_index > 0:
            self.history_index -= 1
            self._restore_state(self.history[self.history_index])
            self.info_label.text = "↶ Отмена выполнена"
            logger.info(f"Undo: now at state {self.history_index}")

    def _redo(self, instance=None):
        """Вернуть отменённое действие"""
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self._restore_state(self.history[self.history_index])
            self.info_label.text = "↷ Возврат выполнен"
            logger.info(f"Redo: now at state {self.history_index}")

    def _restore_state(self, state):
        """Восстановить состояние из истории"""
        try:
            nodes = []
            for node_data in state['nodes']:
                node = Node(
                    id=node_data['id'],
                    name=node_data['name'],
                    x=node_data['x'],
                    y=node_data['y'],
                    floor=node_data['floor'],
                    node_type=node_data['type']
                )
                nodes.append(node)
            
            edges = state['edges']
            
            self.graph_editor.nodes = nodes
            self.graph_editor.edges = edges
            self.graph_editor._update_canvas()
            
            self._update_info()
            self._update_buttons()
        except Exception as e:
            logger.error(f"Error restoring state: {e}")

    def _update_buttons(self):
        """Обновить состояние кнопок undo/redo"""
        self.undo_btn.disabled = self.history_index <= 0
        self.redo_btn.disabled = self.history_index >= len(self.history) - 1
        
        # Обновляем лейбл зума
        zoom_percent = int(self.graph_editor.zoom * 100)
        self.zoom_label.text = f'{zoom_percent}%'

    def _zoom_in(self, instance=None):
        """Приближение (zoom in)"""
        self.graph_editor.zoom_in()
        zoom_percent = int(self.graph_editor.zoom * 100)
        self.zoom_label.text = f'{zoom_percent}%'
        self.info_label.text = f'Приближение: {zoom_percent}%'
        logger.info(f"Zoom in: {zoom_percent}%")

    def _zoom_out(self, instance=None):
        """Отдаление (zoom out)"""
        self.graph_editor.zoom_out()
        zoom_percent = int(self.graph_editor.zoom * 100)
        self.zoom_label.text = f'{zoom_percent}%'
        self.info_label.text = f'Отдаление: {zoom_percent}%'
        logger.info(f"Zoom out: {zoom_percent}%")

    def _zoom_reset(self, instance=None):
        """Сброс зума на 100%"""
        self.graph_editor.reset_zoom()
        self.zoom_label.text = '100%'
        self.info_label.text = 'Зум сброшен на 100%'
        logger.info(f"Zoom reset to 100%")

    def _on_floor_changed(self, spinner, text):
        """При изменении этажа - загружаем новый этаж и его план"""
        self._load_building_graph()

    def _show_new_node_dialog(self, instance):
        """Показать диалог для создания нового узла с выбором типа"""
        dialog_layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        # Поле для имени
        name_layout = BoxLayout(size_hint_y=0.2, spacing=dp(5))
        name_layout.add_widget(Label(text='Имя:', size_hint_x=0.25))
        name_input = TextInput(multiline=False, size_hint_x=0.75, text='Кабинет')
        name_layout.add_widget(name_input)
        dialog_layout.add_widget(name_layout)
        
        # Выбор типа
        type_layout = BoxLayout(size_hint_y=0.2, spacing=dp(5))
        type_layout.add_widget(Label(text='Тип:', size_hint_x=0.25))
        type_spinner = Spinner(
            text='Room',
            values=('Room', 'Corridor', 'Staircase', 'Elevator'),
            size_hint_x=0.75
        )
        type_layout.add_widget(type_spinner)
        dialog_layout.add_widget(type_layout)
        
        # Кнопки
        btn_layout = BoxLayout(size_hint_y=0.2, spacing=dp(10))
        
        def on_add():
            try:
                if not name_input.text.strip():
                    logger.warning("Node name is empty")
                    return
                # Координаты центра экрана в мировых координатах
                center_x = self.graph_editor.width / 2
                center_y = self.graph_editor.height / 2
                world_x, world_y = self.graph_editor._screen_to_world(center_x, center_y)
                new_id = f"node_{len(self.building.nodes) + 1}"
                new_node = Node(
                    id=new_id,
                    name=name_input.text,
                    x=world_x,
                    y=world_y,
                    floor=int(self.floor_spinner.text),
                    node_type=type_spinner.text
                )
                # 🔑 ВАЖНО: добавляем в building первым
                self.building.nodes.append(new_node)
                # Затем синхронизируем граф с building
                self._load_building_graph()
                # 🔑 Автоматически сохраняем на диск
                self._auto_save_graph()
                self.info_label.text = f"✓ Добавлена точка: {new_node.name} ({type_spinner.text})"
                logger.info(f"Node created: {new_node.name} ({type_spinner.text}) at ({world_x:.1f}, {world_y:.1f})")
                popup.dismiss()
            except Exception as e:
                logger.error(f"Error creating node: {e}")
                self.info_label.text = f"✗ Ошибка: {str(e)}"
        
        add_btn = Button(text='✓ Добавить', size_hint_x=0.5)
        add_btn.bind(on_press=lambda x: on_add())
        btn_layout.add_widget(add_btn)
        
        cancel_btn = Button(text='✕ Отмена', size_hint_x=0.5)
        cancel_btn.bind(on_press=lambda x: popup.dismiss())
        btn_layout.add_widget(cancel_btn)
        
        dialog_layout.add_widget(btn_layout)
        
        popup = Popup(
            title='➕ Добавить новую точку',
            content=dialog_layout,
            size_hint=(0.85, 0.6)
        )
        popup.open()

    def _placeholder_save_graph_removed(self):
        """Функция _save_graph переместилась ниже"""
        pass

    def _on_node_deleted(self, node):
        """Callback при удалении узла - синхронизируем с building"""
        if self.building:
            # Удаляем узел из building
            self.building.nodes = [n for n in self.building.nodes if n.id != node.id]
            # Удаляем все рёбра, связанные с узлом
            self.building.edges = [
                (f, t) for f, t in self.building.edges 
                if f != node.id and t != node.id
            ]
            logger.info(f"Node deleted from building: {node.name}")
            self._save_state()
            # 🔑 Автоматически сохраняем на диск после удаления
            self._auto_save_graph()
        self.info_label.text = f"✓ Удалена точка: {node.name}"

    def _on_node_created(self, node):
        """Callback при создании нового узла (например, узла коридора) - синхронизируем с building"""
        if self.building and node:
            # Добавляем узел в building если его там нет
            if node.id not in [n.id for n in self.building.nodes]:
                self.building.nodes.append(node)
                logger.info(f"Node added to building: {node.name} at ({node.x:.1f}, {node.y:.1f}), type={node.node_type}")
                self._save_state()
                # 🔑 Автоматически сохраняем на диск после создания узла
                self._auto_save_graph()
                self.info_label.text = f"✓ Создана точка коридора"

    def _on_edge_created(self, edge):
        """Callback при создании рёбра - синхронизируем с building"""
        if self.building:
            # Всегда синхронизируем ВСЕ рёбра из graph_editor в building
            # (это необходимо для разбивки коридорных рёбер)
            self.building.edges = list(self.graph_editor.edges)
            if edge:
                logger.info(f"Edge created: {edge}, total edges: {len(self.building.edges)}")
            else:
                logger.info(f"Edges synchronized: {len(self.building.edges)} edges")
        
        self._save_state()
        # 🔑 Автоматически сохраняем на диск после создания ребра
        self._auto_save_graph()
        self.info_label.text = f"✓ Создана связь"

    def _auto_save_graph(self):
        """Автоматическое сохранение графа на диск без UI обновления"""
        try:
            if self.building:
                # Сохраняем в кэш
                cache_saved = self.cache_service.save_building(self.building)
                if cache_saved:
                    logger.info(f"Auto-saved building: {len(self.building.nodes)} nodes, {len(self.building.edges)} edges")
                else:
                    logger.warning("Auto-save to cache failed")
        except Exception as e:
            logger.error(f"Error in auto-save: {e}")
    
    def _on_node_moved(self, node):
        """Callback при движении узла (для undo/redo с группировкой)"""
        # Обновляем координаты в здании для синхронизации
        if self.building:
            building_node = next((n for n in self.building.nodes if n.id == node.id), None)
            if building_node:
                building_node.x = node.x
                building_node.y = node.y
                logger.debug(f"Node moved and synced: {node.name} -> ({node.x:.1f}, {node.y:.1f})")
        
        # Сохраняем состояние с группировкой
        self._save_state()

    def _update_info(self):
        """Обновить информационную панель"""
        num_nodes = len(self.graph_editor.nodes)
        num_edges = len(self.graph_editor.edges)
        self.info_label.text = f'Точек: {num_nodes} | Связей: {num_edges}'

    def _save_state(self):
        """Сохранить текущее состояние в историю"""
        try:
            import time
            current_time = time.time()
            
            # Если прошло достаточно времени с последнего действия, начинаем новый пакет
            if current_time - self.last_action_time > self.action_batch_timeout:
                # Завершаем предыдущий пакет и начинаем новый
                if self.batching_actions:
                    self.batching_actions = False
                    self.last_action_time = current_time
                
                # Удаляем всё после текущей позиции (если были undo)
                if self.history_index < len(self.history) - 1:
                    self.history = self.history[:self.history_index + 1]
                
                # Сохраняем состояние
                state = {
                    'nodes': [{'id': n.id, 'name': n.name, 'x': n.x, 'y': n.y, 'floor': n.floor, 'type': n.node_type}
                              for n in self.graph_editor.nodes],
                    'edges': list(self.graph_editor.edges)
                }
                self.history.append(state)
                self.history_index = len(self.history) - 1
                
                # Ограничиваем историю до 50 действий
                if len(self.history) > 50:
                    self.history = self.history[-50:]
                    self.history_index = len(self.history) - 1
                
                self.batching_actions = False
            else:
                # Мы в режиме группировки - обновляем последнее состояние
                if len(self.history) > 0:
                    state = {
                        'nodes': [{'id': n.id, 'name': n.name, 'x': n.x, 'y': n.y, 'floor': n.floor, 'type': n.node_type}
                                  for n in self.graph_editor.nodes],
                        'edges': list(self.graph_editor.edges)
                    }
                    self.history[self.history_index] = state
                self.batching_actions = True
            
            self.last_action_time = current_time
            self._update_buttons()
        except Exception as e:
            logger.error(f"Error saving state: {e}")

    def _undo(self, instance=None):
        """Отменить последнее действие"""
        if self.history_index > 0:
            self.history_index -= 1
            self._restore_state(self.history[self.history_index])
            self.info_label.text = "↶ Отмена выполнена"
            logger.info(f"Undo: now at state {self.history_index}")

    def _redo(self, instance=None):
        """Вернуть отменённое действие"""
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self._restore_state(self.history[self.history_index])
            self.info_label.text = "↷ Возврат выполнен"
            logger.info(f"Redo: now at state {self.history_index}")

    def _restore_state(self, state):
        """Восстановить состояние из истории"""
        try:
            nodes = []
            for node_data in state['nodes']:
                node = Node(
                    id=node_data['id'],
                    name=node_data['name'],
                    x=node_data['x'],
                    y=node_data['y'],
                    floor=node_data['floor'],
                    node_type=node_data['type']
                )
                nodes.append(node)
            
            edges = state['edges']
            
            self.graph_editor.nodes = nodes
            self.graph_editor.edges = edges
            self.graph_editor._update_canvas()
            
            self._update_info()
            self._update_buttons()
        except Exception as e:
            logger.error(f"Error restoring state: {e}")

    def _update_buttons(self):
        """Обновить состояние кнопок undo/redo"""
        self.undo_btn.disabled = self.history_index <= 0
        self.redo_btn.disabled = self.history_index >= len(self.history) - 1

    def _undo(self, instance=None):
        """Отменить последнее действие"""
        if self.history_index > 0:
            self.history_index -= 1
            self._restore_state(self.history[self.history_index])
            logger.info(f"Undo: now at state {self.history_index}")

    def _redo(self, instance=None):
        """Вернуть отменённое действие"""
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self._restore_state(self.history[self.history_index])
            logger.info(f"Redo: now at state {self.history_index}")

    def _restore_state(self, state):
        """Восстановить состояние из истории"""
        try:
            # Восстанавливаем узлы
            nodes = []
            for node_data in state['nodes']:
                node = Node(
                    id=node_data['id'],
                    name=node_data['name'],
                    x=node_data['x'],
                    y=node_data['y'],
                    floor=node_data['floor'],
                    node_type=node_data['type']
                )
                nodes.append(node)
            
            # Восстанавливаем рёбра
            edges = state['edges']
            
            # Обновляем редактор
            self.graph_editor.nodes = nodes
            self.graph_editor.edges = edges
            self.graph_editor._update_canvas()
            
            self._update_info()
            self._update_buttons()
        except Exception as e:
            logger.error(f"Error restoring state: {e}")

    def _update_buttons(self):
        """Обновить состояние кнопок undo/redo"""
        self.undo_btn.disabled = self.history_index <= 0
        self.redo_btn.disabled = self.history_index >= len(self.history) - 1

    def _on_floor_changed(self, spinner, text):
        """При изменении этажа"""
        self._load_building_graph()
        
        # Автоматически загружаем план для этого этажа
        try:
            floor = int(text)
            plan_file = self.floor_plan_manager.get_plan_file(floor)
            
            if plan_file and os.path.exists(plan_file):
                self.graph_editor.set_background_image(plan_file)
                logger.info(f"Loaded floor plan for floor {floor}: {plan_file}")
            else:
                self.graph_editor.set_background_image(None)
                logger.debug(f"No plan found for floor {floor}")
        except Exception as e:
            logger.warning(f"Error loading floor plan: {e}")
            self.graph_editor.set_background_image(None)

    def _show_new_node_dialog(self, instance):
        """Показать диалог для создания нового узла"""
        dialog_layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        # Поле для имени
        name_layout = BoxLayout(size_hint_y=0.2, spacing=dp(5))
        name_layout.add_widget(Label(text='Имя узла:', size_hint_x=0.3))
        name_input = TextInput(multiline=False, size_hint_x=0.7)
        name_layout.add_widget(name_input)
        dialog_layout.add_widget(name_layout)
        
        # Выбор типа
        type_layout = BoxLayout(size_hint_y=0.2, spacing=dp(5))
        type_layout.add_widget(Label(text='Тип:', size_hint_x=0.3))
        type_spinner = Spinner(
            text='Room',
            values=('Room', 'Corridor', 'Staircase', 'Elevator'),
            size_hint_x=0.7
        )
        type_layout.add_widget(type_spinner)
        dialog_layout.add_widget(type_layout)
        
        # Координаты
        x_layout = BoxLayout(size_hint_y=0.2, spacing=dp(5))
        x_layout.add_widget(Label(text='X:', size_hint_x=0.3))
        x_input = TextInput(text='0', multiline=False, size_hint_x=0.7)
        x_layout.add_widget(x_input)
        dialog_layout.add_widget(x_layout)
        
        y_layout = BoxLayout(size_hint_y=0.2, spacing=dp(5))
        y_layout.add_widget(Label(text='Y:', size_hint_x=0.3))
        y_input = TextInput(text='0', multiline=False, size_hint_x=0.7)
        y_layout.add_widget(y_input)
        dialog_layout.add_widget(y_layout)
        
        # Кнопки
        btn_layout = BoxLayout(size_hint_y=0.2, spacing=dp(10))
        
        def on_add():
            try:
                if not name_input.text.strip():
                    logger.warning("Node name is empty")
                    return
                
                # Создаём новый узел
                new_id = f"node_{len(self.building.nodes) + 1}"
                new_node = Node(
                    id=new_id,
                    name=name_input.text,
                    x=float(x_input.text or 0),
                    y=float(y_input.text or 0),
                    floor=int(self.floor_spinner.text),
                    node_type=type_spinner.text
                )
                
                self.building.nodes.append(new_node)
                self.graph_editor.nodes.append(new_node)
                self.graph_editor._update_canvas()
                self._save_state()  # Сохраняем состояние
                
                logger.info(f"Node created: {new_node.name}")
                popup.dismiss()
            except Exception as e:
                logger.error(f"Error creating node: {e}")
        
        add_btn = Button(text='Добавить', size_hint_x=0.5)
        add_btn.bind(on_press=lambda x: on_add())
        btn_layout.add_widget(add_btn)
        
        cancel_btn = Button(text='Отмена', size_hint_x=0.5)
        cancel_btn.bind(on_press=lambda x: popup.dismiss())
        btn_layout.add_widget(cancel_btn)
        
        dialog_layout.add_widget(btn_layout)
        
        popup = Popup(
            title='Новый узел',
            content=dialog_layout,
            size_hint=(0.9, 0.9)
        )
        popup.open()

    def _show_image_chooser(self, instance):
        """Показать выбор SVG плана для текущего этажа"""
        floor = int(self.floor_spinner.text)
        
        # Получаем список доступных файлов в папке планов
        plans_folder = self.floor_plan_manager.plans_folder
        
        if not os.path.exists(plans_folder):
            os.makedirs(plans_folder, exist_ok=True)
            logger.info(f"Created plans folder: {plans_folder}")
        
        available_files = []
        try:
            for filename in os.listdir(plans_folder):
                if filename.endswith(('.svg', '.png', '.jpg', '.jpeg')):
                    available_files.append(filename)
        except Exception as e:
            logger.error(f"Error reading plans folder: {e}")
        
        # Создаём диалог выбора файла
        dialog_layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        # Список файлов
        list_layout = BoxLayout(orientation='vertical', size_hint_y=0.8)
        
        if available_files:
            scroll = ScrollView()
            
            file_grid = GridLayout(cols=1, size_hint_y=None, spacing=dp(5))
            file_grid.bind(minimum_height=file_grid.setter('height'))
            
            def select_file(filename):
                file_path = os.path.join(plans_folder, filename)
                
                # Загружаем выбранный файл как фон в редактор
                try:
                    self.graph_editor.set_background_image(file_path)
                    
                    # Регистрируем план для этажа
                    self.floor_plan_manager.register_plan(floor, file_path)
                    
                    logger.info(f"Set floor {floor} plan to: {filename}")
                    self.info_label.text = f'✓ Загруженный план: {filename}'
                    
                    popup.dismiss()
                except Exception as e:
                    logger.error(f"Error loading plan: {e}")
                    self.info_label.text = f'✗ Ошибка загрузки: {str(e)}'
            
            for filename in sorted(available_files):
                btn = Button(
                    text=filename,
                    size_hint_y=None,
                    height=dp(40),
                    background_color=(0.5, 0.7, 1.0, 1.0)
                )
                btn.bind(on_press=lambda x, f=filename: select_file(f))
                file_grid.add_widget(btn)
            
            scroll.add_widget(file_grid)
            list_layout.add_widget(scroll)
        else:
            label = Label(
                text='Нет файлов в папке:\n' + plans_folder + '\n\nПоместите SVG/PNG файлы туда',
                size_hint_y=1.0
            )
            list_layout.add_widget(label)
        
        dialog_layout.add_widget(list_layout)
        
        # Кнопки
        btn_layout = BoxLayout(size_hint_y=0.2, spacing=dp(10))
        
        cancel_btn = Button(text='Отмена')
        cancel_btn.bind(on_press=lambda x: popup.dismiss())
        btn_layout.add_widget(cancel_btn)
        
        dialog_layout.add_widget(btn_layout)
        
        popup = Popup(
            title=f'Выберите план для этажа {floor}',
            content=dialog_layout,
            size_hint=(0.9, 0.9)
        )
        popup.open()

    def _save_graph(self, instance):
        """Сохранить граф с правильной обработкой ошибок и логированием"""
        try:
            data = self.graph_editor.export_data()
            
            # Обновляем здание
            if self.building:
                floor = int(self.floor_spinner.text)
                
                # ВАЖНО: полностью заменяем узлы в здании данными из редактора
                # Воссоздаём узлы с сохранением их ID и полей
                updated_nodes = []
                for exported_node in data['nodes']:
                    # Ищем исходный узел для сохранения всех его полей
                    original_node = next((n for n in self.building.nodes if n.id == exported_node['id']), None)
                    
                    if original_node:
                        # Обновляем координаты в исходном узле
                        original_node.x = exported_node['x']
                        original_node.y = exported_node['y']
                        # Сохраняем другие поля (name, floor, type)
                        original_node.name = exported_node.get('name', original_node.name)
                        original_node.node_type = exported_node.get('type', original_node.node_type)
                        updated_nodes.append(original_node)
                    else:
                        # Если это новый узел, создаём его
                        new_node = Node(
                            id=exported_node['id'],
                            name=exported_node['name'],
                            x=exported_node['x'],
                            y=exported_node['y'],
                            floor=exported_node.get('floor', floor),
                            node_type=exported_node.get('type', 'Room')
                        )
                        updated_nodes.append(new_node)
                
                # Заменяем узлы в здании
                self.building.nodes = updated_nodes
                
                # Обновляем рёбра (сохраняем как список кортежей)
                self.building.edges = list(data['edges'])
                
                # 🔑 КРИТИЧНО: сохраняем в кэш ПЕРЕД отправкой на API
                cache_saved = self.cache_service.save_building(self.building)
                logger.info(f"Cache save result: {cache_saved}")
                
                # Также пытаемся сохранить в API если возможно (опционально)
                api_saved = False
                try:
                    api_saved = self.api_client.update_building(self.building)
                    if api_saved:
                        logger.info("Building synced to API")
                except Exception as e:
                    logger.warning(f"Could not sync to API: {e}")
                
                self._update_info()
                save_status = "✓ Сохранено" if cache_saved else "⚠ Ошибка кэша"
                self.info_label.text = f"{save_status}: {len(self.building.nodes)} узлов, {len(self.building.edges)} соединений"
                logger.info(f"Graph saved: {len(self.building.nodes)} nodes, {len(self.building.edges)} edges")
        except Exception as e:
            logger.error(f"Error saving graph: {e}")
            self.info_label.text = f"✗ Ошибка сохранения: {str(e)}"

    def _on_node_deleted(self, node):
        """Callback при удалении узла"""
        if self.building:
            self.building.nodes = [n for n in self.building.nodes if n.id != node.id]
            self._save_state()  # Сохраняем состояние
            logger.info(f"Node deleted: {node.name}")

    def _on_edge_created(self, edge):
        """Callback при создании рёбра"""
        self._save_state()  # Сохраняем состояние
        logger.info(f"Edge created: {edge}")
    
    def _on_node_moved(self, node):
        """Callback при движении узла (для undo/redo с группировкой)"""
        # Обновляем координаты в здании
        if self.building:
            building_node = next((n for n in self.building.nodes if n.id == node.id), None)
            if building_node:
                building_node.x = node.x
                building_node.y = node.y
        
        # Просто вызываем _save_state с группировкой
        self._save_state()
        logger.debug(f"Node moved: {node.name} -> ({node.x:.1f}, {node.y:.1f})")

    def _update_info(self):
        """Обновить информационную панель"""
        num_nodes = len(self.graph_editor.nodes)
        num_edges = len(self.graph_editor.edges)
        self.info_label.text = f'Узлов: {num_nodes} | Рёбер: {num_edges} | Shift+Click: выбрать | Ctrl+Drag: соединение | ✕: удалить'

    def on_enter(self):
        """Синхронизировать building при входе на экран"""
        logger.info("[GraphEditorScreen.on_enter] Starting...")
        
        # Пересчитываем размеры всех элементов через несколько ms, когда размеры экрана установлены
        def force_layout_update(dt):
            # Запускаем пересчет лейаута
            self.parent.do_layout()
            # Обновляем canvas
            self.canvas.ask_update()
            logger.info("[GraphEditorScreen] Layout updated")
        
        Clock.schedule_once(force_layout_update, 0.05)
        
        # Если building не установлен, пытаемся получить из админ или карты
        if not self.building:
            try:
                # Сначала пытаемся из админ скрина
                admin_screen = self.manager.get_screen('admin')
                if hasattr(admin_screen, 'building') and admin_screen.building:
                    self.building = admin_screen.building
                    # Отложенный вызов для полной инициализации UI
                    Clock.schedule_once(lambda dt: self._load_building_graph(), 0.15)
                    logger.info(f"GraphEditorScreen: synced building from admin_screen")
                    return
            except Exception as e:
                logger.debug(f"Failed to get building from admin_screen: {e}")
            
            try:
                # Если нет в админе, пытаемся из карты
                map_screen = self.manager.get_screen('map')
                if hasattr(map_screen, 'building') and map_screen.building:
                    self.building = map_screen.building
                    # Отложенный вызов для полной инициализации UI
                    Clock.schedule_once(lambda dt: self._load_building_graph(), 0.1)
                    logger.info(f"GraphEditorScreen: synced building from map_screen")
                    return
            except Exception as e:
                logger.warning(f"Failed to sync building: {e}")
            
            # Fallback: Пытаемся загрузить последнее здание из кэша или API
            try:
                buildings = self.api_client.get_buildings()
                if buildings:
                    self.building = buildings[0]
                    # Отложенный вызов для полной инициализации UI
                    Clock.schedule_once(lambda dt: self._load_building_graph(), 0.1)
                    logger.info(f"GraphEditorScreen: loaded default building from API: {self.building.name}")
                    return
            except Exception as e:
                logger.debug(f"Failed to load building from API: {e}")
            
            # Последний fallback: создаём пустое здание
            if not self.building:
                logger.warning("GraphEditorScreen: No building found, creating empty building")
                self.building = Building(
                    id="temp_building",
                    name="Temporary Building",
                    address="No address",
                    nodes=[],
                    floors=6,
                    edges=[]
                )
                # Отложенный вызов для полной инициализации UI
                Clock.schedule_once(lambda dt: self._load_building_graph(), 0.1)
        
        logger.info("[GraphEditorScreen.on_enter] Done")
    def on_back(self, instance):
        """Вернуться назад с финальным сохранением"""
        # Убедимся, что синхронизируем граф перед выходом
        if self.building and self.graph_editor:
            try:
                # Синхронизируем nodes и edges из graph_editor в building
                self.building.nodes = list(self.graph_editor.nodes)
                self.building.edges = list(self.graph_editor.edges)
                
                # Финальное сохранение
                self._auto_save_graph()
                logger.info(f"Final save before exit: {len(self.building.nodes)} nodes, {len(self.building.edges)} edges")
            except Exception as e:
                logger.error(f"Error during final save: {e}")
        
        # Переходим на карту
        self.manager.current = 'map'
