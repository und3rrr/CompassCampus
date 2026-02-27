"""
Визуальный редактор графов для редактирования узлов и рёбер
"""
from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse, Line, Rectangle, ScissorPush, ScissorPop
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.clock import Clock
from typing import List, Tuple, Optional, Dict, Set
from services.api_client import Node
import logging
import uuid

logger = logging.getLogger(__name__)


class VisualGraphEditor(Widget):
    """Визуальный редактор для графов с поддержкой режимов"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.nodes: List[Node] = []
        self.edges: List[Tuple[str, str]] = []
        self.selected_nodes: Set[str] = set()
        self.dragging_node: Optional[Node] = None
        self.connection_start: Optional[Node] = None
        self.corridor_nodes: List[Node] = []  # Для режима коридора
        self.editing_mode = False
        self.corridor_node_counter = 0  # Счетчик для уникальных ID коридорных узлов
        
        # 🎯 РЕЖИМЫ РЕДАКТИРОВАНИЯ
        self.editor_mode = 'select'  # select, link, delete, corridor
        
        # Параметры отрисовки (БОЛЬШИЕ узлы для удобства)
        self.zoom = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.node_radius = dp(30)  # 🔑 УВЕЛИЧЕНО: размер половины стороны квадрата узла
        self.node_radius_selected = dp(35)  # Для выбранных узлов
        self.line_width = dp(2)
        
        # Видимость рёбер и маршрута
        self.show_edges = True  # 🔑 Рёбра видны всегда в редакторе
        self.route = None
        self.on_node_moved_callback = None
        
        # Фоновое изображение (план этажа)
        self.background_image_path: Optional[str] = None
        self.svg_elements: List = []
        self.svg_width: Optional[float] = None
        self.svg_height: Optional[float] = None
        
        # Snap-to-grid параметры
        self.snap_to_grid_enabled = True
        self.grid_size = dp(20)
        
        # Цвета узлов
        self.node_colors = {
            'Room': (0.3, 0.6, 1.0, 1.0),
            'Corridor': (0.8, 0.8, 0.8, 1.0),
            'Staircase': (1.0, 0.6, 0.2, 1.0),
            'Elevator': (1.0, 0.2, 0.2, 1.0),
        }
        
        # Callback'и
        self.on_node_created_callback = None  # При создании нового узла
        self.on_node_deleted_callback = None
        self.on_edge_created_callback = None
        self.on_edge_deleted_callback = None
        self.on_node_moved_callback = None  # При движении узла
        
        # Привязка событий
        self.bind(size=self._update_canvas)

    def set_nodes(self, nodes: List[Node]):
        """Установить список узлов"""
        self.nodes = nodes
        self._update_canvas()

    def set_edges(self, edges: List[Tuple[str, str]]):
        """Установить список рёбер"""
        self.edges = edges
        self._update_canvas()

    def _screen_to_world(self, screen_x: float, screen_y: float) -> Tuple[float, float]:
        """Преобразовать координаты экрана в мир"""
        world_x = (screen_x - self.pan_x) / self.zoom
        world_y = (screen_y - self.pan_y) / self.zoom
        return world_x, world_y

    def _world_to_screen(self, world_x: float, world_y: float) -> Tuple[float, float]:
        """Преобразовать координаты мира в экран"""
        screen_x = world_x * self.zoom + self.pan_x
        screen_y = world_y * self.zoom + self.pan_y
        return screen_x, screen_y

    def on_touch_down(self, touch):
        """🎯 Обработка нажатия с поддержкой режимов"""
        if not self.collide_point(*touch.pos):
            return False

        # Проверяем двойной клик (для создания коридора)
        if touch.is_double_tap and self.editor_mode == 'corridor':
            world_x, world_y = self._screen_to_world(touch.x, touch.y)
            self._create_corridor_node(world_x, world_y)
            return True

        world_x, world_y = self._screen_to_world(touch.x, touch.y)
        has_shift = 'shift' in touch.modifiers if hasattr(touch, 'modifiers') else False

        # Находим БЛИЖАЙШИЙ узел под курсором (не просто первый)
        clicked_node = None
        closest_distance = float('inf')
        for node in self.nodes:
            dx = node.x - world_x
            dy = node.y - world_y
            distance = (dx**2 + dy**2) ** 0.5
            if distance <= self.node_radius / self.zoom and distance < closest_distance:
                clicked_node = node
                closest_distance = distance

        # ===== РЕЖИМ ВЫБОРА (SELECT) =====
        if self.editor_mode == 'select':
            if clicked_node:
                if has_shift:
                    # Мультивыбор
                    if clicked_node.id in self.selected_nodes:
                        self.selected_nodes.remove(clicked_node.id)
                    else:
                        self.selected_nodes.add(clicked_node.id)
                else:
                    # Одиночный выбор
                    self.selected_nodes = {clicked_node.id}
                
                # Начинаем перетаскивание
                self.dragging_node = clicked_node
                touch.ud['drag_start'] = (touch.x, touch.y)
                self._update_canvas()
                return True
            else:
                # Клик в пустоту - очищаем выделение
                if not has_shift:
                    self.selected_nodes.clear()
                    self._update_canvas()
                return False

        # ===== РЕЖИМ СВЯЗИ (LINK) =====
        elif self.editor_mode == 'link':
            if clicked_node:
                if self.connection_start is None:
                    # Выбиваем первую точку
                    self.connection_start = clicked_node
                    self.selected_nodes = {clicked_node.id}
                    self._update_canvas()
                    logger.info(f"Link mode: selected start node {clicked_node.name}")
                else:
                    # Связываем две точки
                    if self.connection_start.id != clicked_node.id:
                        edge = (self.connection_start.id, clicked_node.id)
                        if edge not in self.edges:
                            self.edges.append(edge)
                            logger.info(f"Link created: {self.connection_start.name} → {clicked_node.name}")
                            
                            # Вызываем callback
                            if hasattr(self, 'on_edge_created_callback') and self.on_edge_created_callback:
                                self.on_edge_created_callback(edge)
                    
                    # Сбрасываем режим связи
                    self.connection_start = None
                    self.selected_nodes.clear()
                    self._update_canvas()
                return True
            return False

        # ===== РЕЖИМ УДАЛЕНИЯ (DELETE) =====
        elif self.editor_mode == 'delete':
            if clicked_node:
                self._delete_node(clicked_node)
                logger.info(f"Delete mode: deleted node {clicked_node.name}")
                return True
            return False

        # ===== РЕЖИМ КОРИДОРА (CORRIDOR) =====
        elif self.editor_mode == 'corridor':
            if clicked_node:
                # Если это сам коридор - двойной клик создаёт точки
                # (обрабатывается в on_touch_down в начале)
                
                # Если это обычный узел (кабинет) - соединяем его с ребром коридора
                if clicked_node.node_type != 'Corridor':
                    logger.info(f"Corridor connection attempt: {clicked_node.name}")
                    
                    # Находим ближайшее ребро коридора
                    corridor_edge_info = self._find_closest_corridor_edge(clicked_node.x, clicked_node.y)
                    
                    if corridor_edge_info:
                        start_node, end_node, closest_x, closest_y = corridor_edge_info
                        
                        logger.info(f"Found corridor edge: {start_node.name} → {end_node.name} at ({closest_x:.1f}, {closest_y:.1f})")
                        
                        # Создаём новый узел коридора в ближайшей точке на ребре
                        # Используем счетчик для уникального ID
                        self.corridor_node_counter += 1
                        new_corridor_node = Node(
                            id=f"corridor_point_{self.corridor_node_counter}_{uuid.uuid4().hex[:8]}",
                            name=f"Точка коридора",
                            x=closest_x,
                            y=closest_y,
                            floor=clicked_node.floor,  # Новый узел на том же этаже
                            node_type='Corridor'
                        )
                        
                        # Добавляем новый узел в список
                        self.nodes.append(new_corridor_node)
                        logger.info(f"✓ Created new corridor node: {new_corridor_node.id} at ({closest_x:.1f}, {closest_y:.1f})")
                        
                        # Разбиваем старое ребро на два (через новый узел)
                        # Удаляем старое ребро
                        old_edge = (start_node.id, end_node.id)
                        reverse_edge = (end_node.id, start_node.id)
                        
                        if old_edge in self.edges:
                            self.edges.remove(old_edge)
                        elif reverse_edge in self.edges:
                            self.edges.remove(reverse_edge)
                        
                        # Добавляем два новых ребра через новый узел
                        edge1 = (start_node.id, new_corridor_node.id)
                        edge2 = (new_corridor_node.id, end_node.id)
                        self.edges.append(edge1)
                        self.edges.append(edge2)
                        logger.info(f"✓ Split corridor edge: {start_node.name} → {new_corridor_node.name} → {end_node.name}")
                        
                        # Соединяем кабинет с новым узлом коридора
                        cabin_edge = (clicked_node.id, new_corridor_node.id)
                        if cabin_edge not in self.edges and (new_corridor_node.id, clicked_node.id) not in self.edges:
                            self.edges.append(cabin_edge)
                            logger.info(f"✓ Cabin connected: {clicked_node.name} → {new_corridor_node.name}")
                            
                            # Вызываем callback для создания нового узла коридора
                            if hasattr(self, 'on_node_created_callback') and self.on_node_created_callback:
                                self.on_node_created_callback(new_corridor_node)
                            
                            # Вызываем callback для синхронизации ВСЕХ изменений
                            # (разбитое ребро + новый узел + новое ребро кабинета)
                            if hasattr(self, 'on_edge_created_callback') and self.on_edge_created_callback:
                                self.on_edge_created_callback(cabin_edge)

                    else:
                        logger.warning(f"✗ Corridor: NO corridor edges found! Create corridor first with double-click")
                    
                    self._update_canvas()
                    return True
            return False

        return False

    def on_touch_move(self, touch):
        """Обработка перемещения"""
        if not self.collide_point(*touch.pos):
            return False

        if self.dragging_node:
            # Перетаскиваем узел
            world_x, world_y = self._screen_to_world(touch.x, touch.y)
            
            # Применяем snap-to-grid
            world_x, world_y = self.snap_to_grid(world_x, world_y)
            
            # Обновляем позицию для всех выбранных узлов
            if self.dragging_node.id in self.selected_nodes:
                # Вычисляем смещение
                if 'last_world' in touch.ud:
                    dx = world_x - touch.ud['last_world'][0]
                    dy = world_y - touch.ud['last_world'][1]
                    
                    # Перемещаем все выбранные узлы
                    for node in self.nodes:
                        if node.id in self.selected_nodes:
                            node.x += dx
                            node.y += dy
            else:
                # Просто перемещаем этот узел
                self.dragging_node.x = world_x
                self.dragging_node.y = world_y
            
            touch.ud['last_world'] = (world_x, world_y)
            self._update_canvas()
            
            # Вызываем callback при движении узла (для undo/redo)
            if self.on_node_moved_callback:
                self.on_node_moved_callback(self.dragging_node)
            
            return True

        if self.connection_start:
            # Рисуем временную линию для соединения
            self._update_canvas()
            return True

        # Панорамирование
        if hasattr(touch, 'ud') and 'previous' in touch.ud:
            self.pan_x += touch.x - touch.ud['previous'][0]
            self.pan_y += touch.y - touch.ud['previous'][1]
            self._update_canvas()

        touch.ud['previous'] = (touch.x, touch.y)
        return True

    def on_touch_up(self, touch):
        """Обработка отпускания"""
        if self.dragging_node:
            # Пытаемся привязать узел к ближайшему элементу SVG
            self.snap_node_to_svg_elements(self.dragging_node)
            self.dragging_node = None
            touch.ud.pop('drag_start', None)
            touch.ud.pop('last_world', None)
            self._update_canvas()
            return True

        if self.connection_start:
            # Проверяем, на какой узел указываем
            world_x, world_y = self._screen_to_world(touch.x, touch.y)
            
            for node in self.nodes:
                dx = node.x - world_x
                dy = node.y - world_y
                distance = (dx**2 + dy**2) ** 0.5

                if distance <= self.node_radius / self.zoom and node != self.connection_start:
                    # Создаём соединение
                    self._create_edge(self.connection_start, node)
                    break
            
            self.connection_start = None
            self._update_canvas()
            return True

        if 'previous' in touch.ud:
            del touch.ud['previous']
        return False

    def on_scroll_down(self, *args):
        """Зум вверх (приближение)"""
        # Сохраняем центр экрана перед зумом
        center_screen_x = self.width / 2
        center_screen_y = self.height / 2
        center_world_x, center_world_y = self._screen_to_world(center_screen_x, center_screen_y)
        
        # Приближаем (максимум 5x)
        old_zoom = self.zoom
        self.zoom = min(self.zoom * 1.1, 5.0)
        
        # Пересчитываем pan чтобы центр остался в центре
        self.pan_x = center_screen_x - center_world_x * self.zoom
        self.pan_y = center_screen_y - center_world_y * self.zoom
        
        logger.info(f"Zoom: {old_zoom:.2f}x → {self.zoom:.2f}x (in)")
        self._update_canvas()
        return True

    def on_scroll_up(self, *args):
        """Зум вниз (отдаление)"""
        # Сохраняем центр экрана перед зумом
        center_screen_x = self.width / 2
        center_screen_y = self.height / 2
        center_world_x, center_world_y = self._screen_to_world(center_screen_x, center_screen_y)
        
        # Отдаляем (минимум 0.2x)
        old_zoom = self.zoom
        self.zoom = max(self.zoom / 1.1, 0.2)
        
        # Пересчитываем pan чтобы центр остался в центре
        self.pan_x = center_screen_x - center_world_x * self.zoom
        self.pan_y = center_screen_y - center_world_y * self.zoom
        
        logger.info(f"Zoom: {old_zoom:.2f}x → {self.zoom:.2f}x (out)")
        self._update_canvas()
        return True
    
    def zoom_in(self, factor: float = 1.1):
        """Приближение (для кнопок)"""
        self.on_scroll_down()
    
    def zoom_out(self, factor: float = 1.1):
        """Отдаление (для кнопок)"""
        self.on_scroll_up()
    
    def reset_zoom(self):
        """Сбросить зум на 1.0x и центрировать"""
        self.zoom = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        logger.info("Zoom reset to 1.0x")
        self._update_canvas()

    def _distance_point_to_line(self, px: float, py: float, x1: float, y1: float, x2: float, y2: float) -> float:
        """Вычислить расстояние от точки (px, py) до линии [(x1, y1), (x2, y2)]"""
        # Используем формулу расстояния от точки до линии
        numerator = abs((y2 - y1) * px - (x2 - x1) * py + x2 * y1 - y2 * x1)
        denominator = ((y2 - y1)**2 + (x2 - x1)**2) ** 0.5
        if denominator == 0:
            # Линия - это точка
            return ((px - x1)**2 + (py - y1)**2) ** 0.5
        return numerator / denominator

    def _closest_point_on_segment(self, px: float, py: float, x1: float, y1: float, x2: float, y2: float) -> Tuple[float, float]:
        """Найти ближайшую точку на отрезке [(x1, y1), (x2, y2)] к точке (px, py)"""
        # Вектор от (x1, y1) к (x2, y2)
        dx = x2 - x1
        dy = y2 - y1
        
        if dx == 0 and dy == 0:
            return x1, y1
        
        # Параметр t ближайшей точки на линии
        t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
        
        # Ближайшая точка
        closest_x = x1 + t * dx
        closest_y = y1 + t * dy
        
        return closest_x, closest_y

    def _find_closest_corridor_edge(self, node_x: float, node_y: float) -> Optional[Tuple[Node, Node, float, float]]:
        """
        Найти ближайшее ребро коридора к узлу (кабинету).
        
        Returns:
            Tuple[start_node, end_node, closest_point_x, closest_point_y] или None если коридорных рёбер нет
        """
        # Найти все узлы коридора
        corridor_nodes = {n.id: n for n in self.nodes if n.node_type == 'Corridor'}
        
        if not corridor_nodes:
            return None
        
        min_distance = float('inf')
        closest_edge_info = None
        
        # Для каждого ребра коридора найти расстояние до кабинета
        for edge in self.edges:
            from_id, to_id = edge
            
            # Проверяем, что оба конца - коридоры
            if from_id not in corridor_nodes or to_id not in corridor_nodes:
                continue
            
            start_node = corridor_nodes[from_id]
            end_node = corridor_nodes[to_id]
            
            # Вычисляем расстояние от кабинета до этого ребра
            distance = self._distance_point_to_line(node_x, node_y, start_node.x, start_node.y, end_node.x, end_node.y)
            
            if distance < min_distance:
                min_distance = distance
                # Найти ближайшую точку на ребре
                closest_x, closest_y = self._closest_point_on_segment(node_x, node_y, start_node.x, start_node.y, end_node.x, end_node.y)
                closest_edge_info = (start_node, end_node, closest_x, closest_y)
        
        return closest_edge_info

    def _create_corridor_node(self, world_x: float, world_y: float):
        """Создать коридор с двумя конечными точками и ребром между ними"""
        # Привязываем к сетке
        world_x, world_y = self.snap_to_grid(world_x, world_y)
        
        # Проверяем есть ли уже начальная точка коридора
        if not self.corridor_nodes:
            # Это начало коридора - создаём первую точку
            corridor_start_id = f"corridor_start_{len(self.nodes)}_{int(world_x)}_{int(world_y)}"
            
            corridor_start = Node(
                id=corridor_start_id,
                name=f"Коридор {len([n for n in self.nodes if n.node_type == 'Corridor']) // 2 + 1} (начало)",
                x=world_x,
                y=world_y,
                node_type='Corridor',
                floor=1
            )
            
            self.nodes.append(corridor_start)
            self.corridor_nodes = [corridor_start]
            self.selected_nodes = {corridor_start.id}
            logger.info(f"Corridor START created: {corridor_start.name} at ({world_x:.0f}, {world_y:.0f})")
            
        else:
            # Это конец коридора - создаём вторую точку и ребро
            corridor_start = self.corridor_nodes[0]
            corridor_end_id = f"corridor_end_{len(self.nodes)}_{int(world_x)}_{int(world_y)}"
            
            corridor_end = Node(
                id=corridor_end_id,
                name=f"Коридор {len([n for n in self.nodes if n.node_type == 'Corridor']) // 2 + 1} (конец)",
                x=world_x,
                y=world_y,
                node_type='Corridor',
                floor=1
            )
            
            self.nodes.append(corridor_end)
            
            # ВАЖНО: создаём ребро между начальной и конечной точкой коридора
            edge = (corridor_start.id, corridor_end.id)
            self.edges.append(edge)
            logger.info(f"Corridor EDGE created: {corridor_start.name} ↔ {corridor_end.name}")
            
            # Вызываем callback для создания ребра
            if hasattr(self, 'on_edge_created_callback') and self.on_edge_created_callback:
                self.on_edge_created_callback(edge)
            
            # Сбрасываем режим коридора - готов к следующему коридору
            self.corridor_nodes = []
            self.selected_nodes = set()
            logger.info(f"Corridor COMPLETE: {corridor_start.name} ↔ {corridor_end.name}")
        
        self._update_canvas()
    
    def _delete_node(self, node: Node):
        """Удалить узел"""
        # Удаляем все рёбра, связанные с узлом
        self.edges = [
            (f, t) for f, t in self.edges 
            if f != node.id and t != node.id
        ]
        
        # Удаляем сам узел
        self.nodes = [n for n in self.nodes if n.id != node.id]
        self.selected_nodes.discard(node.id)
        
        if self.on_node_deleted_callback:
            self.on_node_deleted_callback(node)
        
        logger.info(f"Node deleted: {node.name}")
        self._update_canvas()

    def _create_edge(self, from_node: Node, to_node: Node):
        """Создать рёбро между узлами"""
        edge = (from_node.id, to_node.id)
        reverse_edge = (to_node.id, from_node.id)
        
        # Проверяем что такого края нет
        if edge not in self.edges and reverse_edge not in self.edges:
            self.edges.append(edge)
            if self.on_edge_created_callback:
                self.on_edge_created_callback(edge)
            logger.info(f"Edge created: {from_node.name} -> {to_node.name}")
        
        self._update_canvas()

    def _update_canvas(self, *args):
        """Обновить отрисовку"""
        self.canvas.clear()

        with self.canvas:
            # ========== ОБРЕЗКА СОДЕРЖИМОГО ПО ГРАНИЦАМ РЕДАКТОРА ==========
            ScissorPush(x=int(self.x), y=int(self.y), width=int(self.width), height=int(self.height))
            
            # Фон
            Color(0.95, 0.95, 0.95, 1)
            Rectangle(pos=self.pos, size=self.size)
            
            # Отрисовка SVG элементов (стены, двери, комнаты)
            # SVG elements - DISABLED (too slow for interactive editor)
            # if self.svg_elements:
            #     try:
            #         from widgets.map_widget import SVGRenderer
            #         SVGRenderer.render_svg_elements(...)
            #     except Exception as e:
            #         logger.debug(f"Error rendering SVG elements: {e}")
            
            # Отрисовка растрового фона изображения если загружено
            if self.background_image_path and not self.background_image_path.endswith('.svg'):
                try:
                    Color(1, 1, 1, 0.5)
                    # Применяем масштабирование и смещение к фоновому изображению
                    if self.svg_width and self.svg_height:
                        bg_width = self.svg_width * self.zoom
                        bg_height = self.svg_height * self.zoom
                        bg_pos_x = self.pan_x
                        bg_pos_y = self.pan_y
                        Rectangle(
                            source=self.background_image_path,
                            pos=(bg_pos_x, bg_pos_y),
                            size=(bg_width, bg_height)
                        )
                    else:
                        # Fallback если размеры не известны
                        Rectangle(
                            source=self.background_image_path,
                            pos=self.pos,
                            size=self.size
                        )
                except Exception as e:
                    logger.debug(f"Error rendering background image: {e}")

            if not self.nodes:
                return

            # Отрисовка сетки если включена привязка к сетке
            if self.snap_to_grid_enabled:
                Color(0.8, 0.8, 0.8, 0.2)
                # Вертикальные линии сетки
                x = 0
                while x <= self.size[0]:
                    Line(points=[x, 0, x, self.size[1]], width=0.5)
                    x += self.grid_size
                # Горизонтальные линии сетки
                y = 0
                while y <= self.size[1]:
                    Line(points=[0, y, self.size[0], y], width=0.5)
                    y += self.grid_size

            # Масштабируемая толщина линий - чем ближе zoom, тем тоньше линия
            # Формула: 4 / zoom (при zoom=1 линия 4px, при zoom=2 линия 2px, и т.д.)
            scaled_line_width = max(1.0, 4.0 / max(0.5, self.zoom))  # Минимум 1px
            
            # Отрисовка рёбер только если show_edges=True
            if self.show_edges:
                Color(0.5, 0.5, 0.5, 0.6)
                for from_id, to_id in self.edges:
                    from_node = next((n for n in self.nodes if n.id == from_id), None)
                    to_node = next((n for n in self.nodes if n.id == to_id), None)

                    if from_node and to_node:
                        screen_x1, screen_y1 = self._world_to_screen(from_node.x, from_node.y)
                        screen_x2, screen_y2 = self._world_to_screen(to_node.x, to_node.y)
                        Line(points=[screen_x1, screen_y1, screen_x2, screen_y2], width=scaled_line_width)

            # Отрисовка маршрута если он выбран (видно всегда)
            if self.route and self.route.path:
                Color(0.2, 0.8, 0.2, 0.8)  # Зелёный цвет для маршрута
                route_points = []
                for node in self.route.path:
                    screen_x, screen_y = self._world_to_screen(node.x, node.y)
                    route_points.extend([screen_x, screen_y])
                
                if route_points:
                    # Маршрут рисуется с увеличенной толщиной
                    route_line_width = max(2.0, 6.0 / max(0.5, self.zoom))
                    Line(points=route_points, width=route_line_width)

            # Отрисовка временной линии для соединения
            if self.connection_start and hasattr(self, 'last_touch_pos'):
                Color(0.2, 0.7, 0.2, 0.5)
                screen_x1, screen_y1 = self._world_to_screen(self.connection_start.x, self.connection_start.y)
                Line(points=[screen_x1, screen_y1, self.last_touch_pos[0], self.last_touch_pos[1]], width=scaled_line_width)

            # Отрисовка узлов
            for node in self.nodes:
                screen_x, screen_y = self._world_to_screen(node.x, node.y)
                
                # Выбираем цвет
                if node.id in self.selected_nodes:
                    Color(1.0, 1.0, 0.0, 1.0)  # Жёлтый для выбранных
                else:
                    color = self.node_colors.get(node.node_type, (0.5, 0.5, 0.5, 1.0))
                    Color(*color)

                # 🔑 Отрисовка КВАДРАТА вместо круга для лучшей визуализации
                Rectangle(
                    pos=(screen_x - self.node_radius, screen_y - self.node_radius),
                    size=(self.node_radius * 2, self.node_radius * 2)
                )
                
                # Границы для визуализации выделения
                if node.id in self.selected_nodes:
                    Color(1.0, 1.0, 0.0, 1.0)
                    Line(
                        rectangle=(screen_x - self.node_radius - dp(2), screen_y - self.node_radius - dp(2), 
                                  self.node_radius * 2 + dp(4), self.node_radius * 2 + dp(4)),
                        width=dp(3)
                    )
            
            # ========== КОНЕЦ ОБРЕЗКИ ==========
            ScissorPop()

    def export_data(self) -> Dict:
        """Экспортировать данные"""
        return {
            'nodes': [
                {'id': n.id, 'name': n.name, 'x': n.x, 'y': n.y, 'type': n.node_type}
                for n in self.nodes
            ],
            'edges': self.edges
        }
    def set_background_image(self, image_path: Optional[str]):
        """Установить фоновое изображение (SVG/PNG)"""
        import os
        import threading
        from kivy.clock import Clock

        if image_path is None:
            self.background_image_path = None
            self.svg_elements = []
            self.svg_width = None
            self.svg_height = None
            self._update_canvas()
            return

        if not os.path.exists(image_path):
            logger.warning(f"Background image not found: {image_path}")
            return

        # Если это SVG, загружаем элементы в фоне
        if image_path.endswith('.svg'):
            def _load_svg(path):
                try:
                    from services.svg_loader import SVGLoader
                    floor_plan = SVGLoader.load_svg_file(path)
                    Clock.schedule_once(lambda dt: self._apply_svg_floor_plan(floor_plan, path), 0)
                except Exception as e:
                    logger.error(f"Error loading SVG in background: {e}")
                    Clock.schedule_once(lambda dt: self._apply_svg_failed(path, str(e)), 0)

            thread = threading.Thread(target=_load_svg, args=(image_path,), daemon=True)
            thread.start()
            return

        # Для PNG: синхронно извлекаем размеры (быстрая операция)
        self.svg_elements = []
        try:
            from PIL import Image as PILImage
            img = PILImage.open(image_path)
            if img.size:
                actual_width, actual_height = img.size
                logger.info(f"PNG size: {actual_width}x{actual_height}")
                self.svg_width = actual_width
                self.svg_height = actual_height
            else:
                logger.warning("Could not get PNG dimensions")
                self.svg_width = None
                self.svg_height = None
        except ImportError:
            logger.debug("PIL not available, skipping PNG dimension extraction")
            self.svg_width = None
            self.svg_height = None
        except Exception as e:
            logger.debug(f"Could not get PNG dimensions: {e}")
            self.svg_width = None
            self.svg_height = None

        self.background_image_path = image_path
        self._update_canvas()

    def _apply_svg_floor_plan(self, floor_plan, path: str):
        try:
            logger.info("[VisualGraphEditor._apply_svg_floor_plan] Applying SVG floor plan...")
            self.svg_elements = floor_plan.elements
            self.svg_width = floor_plan.width
            self.svg_height = floor_plan.height
            self.background_image_path = path
            logger.info(f"Loaded SVG background with {len(floor_plan.elements)} elements ({floor_plan.width}x{floor_plan.height})")
            # Отложим обновление canvas на несколько фреймов
            Clock.schedule_once(lambda dt: self._update_canvas(), 0.016)  # ~60 FPS
            logger.info("[VisualGraphEditor._apply_svg_floor_plan] Done!")
        except Exception as e:
            logger.error(f"Error applying SVG floor plan: {e}")
            self.svg_elements = []
            self.svg_width = None
            self.svg_height = None
            Clock.schedule_once(lambda dt: self._update_canvas(), 0.016)

    def _apply_svg_failed(self, path: str, error_msg: str):
        logger.error(f"Failed to load SVG {path}: {error_msg}")
        self.svg_elements = []
        self.svg_width = None
        self.svg_height = None
        self._update_canvas()

    def snap_to_grid(self, x: float, y: float) -> Tuple[float, float]:
        """Привязать координаты к сетке (snap-to-grid)"""
        if not self.snap_to_grid_enabled:
            return x, y
        
        grid = self.grid_size
        snapped_x = round(x / grid) * grid
        snapped_y = round(y / grid) * grid
        return snapped_x, snapped_y

    def snap_node_to_svg_elements(self, node: Node) -> bool:
        """
        Привязать узел к ближайшему элементу SVG
        Возвращает True если узел был привязан
        """
        if not self.svg_elements or node is None:
            return False
        
        min_distance = float('inf')
        snap_x, snap_y = node.x, node.y
        
        # Ищем ближайший элемент SVG
        for elem in self.svg_elements:
            if elem.element_type == 'polygon' and elem.points:
                # Для полигонов - привязываем к центру
                center_x = sum(p[0] for p in elem.points) / len(elem.points)
                center_y = sum(p[1] for p in elem.points) / len(elem.points)
                
                dist = ((node.x - center_x)**2 + (node.y - center_y)**2) ** 0.5
                
                # Если достаточно близко (в пределах 50 единиц)
                if dist < 50 and dist < min_distance:
                    min_distance = dist
                    snap_x, snap_y = center_x, center_y
            
            elif elem.element_type in ('circle', 'rect'):
                # Для кругов и прямоугольников - привязываем к центру
                if elem.center:
                    cx, cy = elem.center
                    dist = ((node.x - cx)**2 + (node.y - cy)**2) ** 0.5
                    if dist < 50 and dist < min_distance:
                        min_distance = dist
                        snap_x, snap_y = cx, cy
        
        # Если нашли что-то близко, привязываем
        if min_distance < 50:
            node.x = snap_x
            node.y = snap_y
            return True
        
        return False

    def toggle_snap_to_grid(self, enabled: bool = None):
        """Включить/выключить snap-to-grid"""
        if enabled is not None:
            self.snap_to_grid_enabled = enabled
        else:
            self.snap_to_grid_enabled = not self.snap_to_grid_enabled
        
        logger.info(f"Snap to grid: {'ON' if self.snap_to_grid_enabled else 'OFF'}")
    
    def set_show_edges(self, show: bool):
        """Показать/скрыть рёбра графа"""
        self.show_edges = show
        self._update_canvas()
        logger.info(f"Edges visibility: {'ON' if show else 'OFF'}")
    
    def set_route(self, route):
        """Установить маршрут для отображения"""
        self.route = route
        # Когда маршрут выбран, рёбра становятся видимыми
        if route:
            self.show_edges = True
        self._update_canvas()
        logger.info(f"Route set: {route.id if route else 'None'}")
    
    def _update_edge_visibility(self):
        """Обновить видимость рёбер на основе выделения узлов"""
        # Рёбра видны если:
        # 1. Есть выделённые узлы
        # 2. Выбран маршрут
        if self.selected_nodes or self.route:
            self.show_edges = True
        else:
            self.show_edges = False
        
        self._update_canvas()
        logger.debug(f"Edge visibility updated: {self.show_edges} (selected: {len(self.selected_nodes)}, route: {bool(self.route)})")