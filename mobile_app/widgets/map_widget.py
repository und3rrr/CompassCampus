"""
Кастомный виджет для отрисовки карты в Kivy с использованием PNG
Упрощённая версия без SVG функционала
Поддержка: центрирование, граница, вращение
"""
from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse, Line, Rectangle, PushMatrix, PopMatrix, Rotate, Translate
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.metrics import dp
from typing import List, Tuple, Optional
from services.api_client import Node, Route
import logging
import os
import time
import math

logger = logging.getLogger(__name__)


class MapWidget(Widget):
    """Виджет карты с поддержкой PNG изображений"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Параметры зума и панорамирования
        self.zoom = 0.04
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.min_zoom = 0.01
        self.max_zoom = 0.5
        self.rotation = 0.0  # Угол вращения в градусах
        
        # Данные карты
        self.nodes: List[Node] = []
        self.edges: List[Tuple[int, int]] = []
        self.closed_routes: List[Route] = []
        self.route_nodes: List[int] = []
        
        # Параметры отрисовки
        self.node_color = (0.0, 0.7, 1.0, 1.0)  # Синий
        self.edge_color = (0.5, 0.5, 0.5, 1.0)  # Серый
        self.closed_color = (1.0, 0.0, 0.0, 1.0)  # Красный
        self.route_color = (0.0, 1.0, 0.0, 1.0)  # Зелёный
        self.node_radius = 8
        self.edge_width = 2
        
        # Фоновое изображение (PNG)
        self.background_image_path: Optional[str] = None
        self.background_opacity = 1.0
        self.background_enabled = True
        self.svg_width = 9757.0
        self.svg_height = 3408.0
        
        # Multi-touch для вращения
        self.active_touches = []  # Список активных touch-событий
        self.touch_start_angle = 0
        self.rotation_start = 0
        
        # Привязываем события и рисование
        self.bind(size=self._on_size)
        
        # Первоначальная отрисовка
        Clock.schedule_once(self._draw_initial, 0.1)
        
        logger.info("[MapWidget] Initialized with PNG backend (no SVG) + rotation support")

    def _draw_initial(self, dt):
        """Первоначальная отрисовка"""
        self._update_canvas()

    def _on_size(self, *args):
        """Обработчик изменения размера"""
        self._update_canvas()

    def _center_map(self):
        """Центрировать карту в окне"""
        # Вычисляем зум чтобы вся карта влезла в экран
        width_zoom = self.width / self.svg_width if self.svg_width else 0.04
        height_zoom = self.height / self.svg_height if self.svg_height else 0.04
        self.zoom = min(width_zoom, height_zoom) * 0.95  # 95% от доступного места
        
        # Вычисляем позицию для центрирования
        map_width_on_screen = self.svg_width * self.zoom
        map_height_on_screen = self.svg_height * self.zoom
        
        self.pan_x = (self.width - map_width_on_screen) / 2
        self.pan_y = (self.height - map_height_on_screen) / 2
        
        logger.debug(f"[MapWidget] Centered: zoom={self.zoom:.4f}, pan=({self.pan_x:.1f}, {self.pan_y:.1f})")

    def _clamp_pan(self):
        """Ограничить панорамирование чтобы карта не ушла полностью за пределы"""
        if not self.svg_width or not self.svg_height:
            return
        
        map_width = self.svg_width * self.zoom
        map_height = self.svg_height * self.zoom
        
        # Padding - отступ для мягких границ (позволяет карте немного выходить за пределы)
        # Это даёт возможность двигать карту даже при минимальном зуме
        padding = 50  # пиксели
        
        # Левая/правая граница: карта может выходить на padding пикселей за пределы
        self.pan_x = max(-map_width + padding, min(self.pan_x, self.width - padding))
        
        # Нижняя/верхняя граница: аналогично
        self.pan_y = max(-map_height + padding, min(self.pan_y, self.height - padding))

    def load_background_image(self, image_path: str):
        """
        Загрузить фоновое изображение (PNG)
        
        Args:
            image_path: Путь к PNG файлу
        """
        if image_path and not os.path.exists(image_path):
            logger.warning(f"Image not found: {image_path}")
            return
        
        self.background_image_path = image_path
        if image_path:
            logger.info(f"[MapWidget] Loaded background image: {image_path}")
            # Центрируем карту после загрузки
            Clock.schedule_once(lambda dt: self._center_map(), 0)
            Clock.schedule_once(lambda dt: self._update_canvas(), 0.05)

    def set_background_image(self, image_path: str):
        """Alias для load_background_image для обратной совместимости"""
        if image_path is None:
            self.background_image_path = None
        else:
            self.load_background_image(image_path)

    def set_nodes(self, nodes: List[Node], edges: List[Tuple[int, int]] = None, 
                  closed_routes: List[Route] = None):
        """
        Установить узлы и рёбра графа
        
        Args:
            nodes: Список узлов
            edges: Список рёбер (пары индексов узлов)
            closed_routes: Список закрытых маршрутов
        """
        self.nodes = nodes or []
        self.edges = edges or []
        self.closed_routes = closed_routes or []
        
        logger.debug(f"[MapWidget] Set {len(self.nodes)} nodes, {len(self.edges)} edges")
        Clock.schedule_once(lambda dt: self._update_canvas(), 0)

    def set_edges(self, edges: List[Tuple[int, int]]):
        """
        Установить рёбра графа
        
        Args:
            edges: Список рёбер (пары индексов узлов)
        """
        self.edges = edges or []
        logger.debug(f"[MapWidget] Set {len(self.edges)} edges")
        Clock.schedule_once(lambda dt: self._update_canvas(), 0)

    def set_closed_routes(self, closed_edges: List[Tuple[int, int]], closed_nodes: List[int]):
        """
        Установить закрытые маршруты
        
        Args:
            closed_edges: Список закрытых рёбер (пары ID узлов)
            closed_nodes: Список ID узлов на закрытых маршрутах
        """
        # Конвертируем в список Route (структура compat)
        if closed_nodes:
            self.closed_routes = [type('Route', (), {'nodes': closed_nodes})()]
        logger.debug(f"[MapWidget] Set closed routes: {len(closed_nodes)} nodes")
        Clock.schedule_once(lambda dt: self._update_canvas(), 0)

    def set_route(self, node_ids: List[int]):
        """
        Установить маршрут для отрисовки
        
        Args:
            node_ids: Список ID узлов маршрута
        """
        self.route_nodes = node_ids
        Clock.schedule_once(lambda dt: self._update_canvas(), 0)

    def clear_selection(self):
        """Очистить выделение маршрута"""
        self.route_nodes = []
        Clock.schedule_once(lambda dt: self._update_canvas(), 0)

    def on_touch_down(self, touch):
        """Обработка нажатия мыши"""
        if self.collide_point(*touch.pos):
            touch.grab(self)
            touch.ud['zoom_start'] = self.zoom
            touch.ud['pan_start'] = (self.pan_x, self.pan_y)
            touch.ud['mouse_pos'] = touch.pos
            
            # Добавляем в активные touches
            self.active_touches.append(touch)
            
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        """Обработка движения мыши/пальца"""
        if touch.grab_current is self:
            # Multi-touch вращение (два пальца)
            if len(self.active_touches) >= 2:
                # Вычисляем угол между двумя точками
                touch1, touch2 = self.active_touches[0], self.active_touches[1]
                
                # Текущий угол
                dx = touch2.pos[0] - touch1.pos[0]
                dy = touch2.pos[1] - touch1.pos[1]
                current_angle = math.degrees(math.atan2(dy, dx))
                
                # Начальный угол
                if 'start_angle' not in touch.ud:
                    start_dx = touch2.ud.get('mouse_pos', touch2.pos)[0] - touch1.ud.get('mouse_pos', touch1.pos)[0]
                    start_dy = touch2.ud.get('mouse_pos', touch2.pos)[1] - touch1.ud.get('mouse_pos', touch1.pos)[1]
                    touch.ud['start_angle'] = math.degrees(math.atan2(start_dy, start_dx))
                    touch.ud['rotation_start'] = self.rotation
                
                # Вычисляем дельту вращения
                angle_delta = current_angle - touch.ud['start_angle']
                self.rotation = touch.ud['rotation_start'] + angle_delta
                
                # Ограничиваем вращение 0-360
                self.rotation = self.rotation % 360
                
                self._update_canvas()
            else:
                # Single-touch панорамирование
                dx = touch.pos[0] - touch.ud.get('mouse_pos', touch.pos)[0]
                dy = touch.pos[1] - touch.ud.get('mouse_pos', touch.pos)[1]
                
                self.pan_x += dx
                self.pan_y += dy
                
                # Применяем границы
                self._clamp_pan()
                
                touch.ud['mouse_pos'] = touch.pos
                self._update_canvas()
            
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        """Обработка отпускания мыши"""
        if touch.grab_current is self:
            # Удаляем из активных touches
            if touch in self.active_touches:
                self.active_touches.remove(touch)
            touch.ungrab(self)
            return True
        return super().on_touch_up(touch)

    def on_mouse_scroll(self, window, scroll_type, me):
        """Обработка прокрутки колеса мыши для зума"""
        if not self.collide_point(me.x, me.y):
            return
        
        zoom_factor = 1.1
        if me.z > 0:  # Zoom in
            new_zoom = self.zoom * zoom_factor
        else:  # Zoom out
            new_zoom = self.zoom / zoom_factor
        
        new_zoom = max(self.min_zoom, min(self.max_zoom, new_zoom))
        
        # Приближаем к точке курсора
        mx, my = me.x - self.x, me.y - self.y
        self.pan_x -= mx * (new_zoom - self.zoom)
        self.pan_y -= my * (new_zoom - self.zoom)
        
        self.zoom = new_zoom
        self._clamp_pan()
        self._update_canvas()

    def zoom_in(self):
        """Увеличить зум"""
        new_zoom = self.zoom * 1.2
        new_zoom = min(new_zoom, self.max_zoom)
        self.zoom = new_zoom
        self._clamp_pan()
        self._update_canvas()

    def zoom_out(self):
        """Уменьшить зум"""
        new_zoom = self.zoom / 1.2
        new_zoom = max(new_zoom, self.min_zoom)
        self.zoom = new_zoom
        self._clamp_pan()
        self._update_canvas()

    def fit_to_screen(self):
        """Вместить всю карту в экран"""
        self._center_map()
        self.rotation = 0.0
        self._update_canvas()

    def _update_canvas(self):
        """Обновить отрисовку карты"""
        self.canvas.clear()
        
        with self.canvas:
            # Белый фон
            Color(1, 1, 1, 1)
            Rectangle(pos=(0, 0), size=self.size)
            
            # Вычисляем центр карты для вращения
            map_width_on_screen = self.svg_width * self.zoom
            map_height_on_screen = self.svg_height * self.zoom
            center_x = self.pan_x + map_width_on_screen / 2
            center_y = self.pan_y + map_height_on_screen / 2
            
            # Применяем ротацию если она не нулевая
            if abs(self.rotation) > 0.1:
                PushMatrix()
                Translate(center_x, center_y)
                Rotate(angle=self.rotation, origin=(0, 0))
                Translate(-center_x, -center_y)
            
            # PNG фоновое изображение
            t_bg = time.perf_counter()
            if self.background_enabled and self.background_image_path:
                Color(1, 1, 1, self.background_opacity)
                try:
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
                except Exception as e:
                    logger.warning(f"Error rendering background: {e}")
            t_bg_end = time.perf_counter()
            
            # Закрытые маршруты (красные линии)
            t_closed = time.perf_counter()
            if self.closed_routes:
                Color(*self.closed_color)
                for route in self.closed_routes:
                    if route.nodes and len(route.nodes) > 1:
                        points = []
                        for node_id in route.nodes:
                            node = next((n for n in self.nodes if n.id == node_id), None)
                            if node:
                                x = node.x * self.zoom + self.pan_x
                                y = node.y * self.zoom + self.pan_y
                                points.extend([x, y])
                        if points:
                            Line(points=points, width=self.edge_width * 2)
            t_closed_end = time.perf_counter()
            
            # Маршрут (зелёные линии)
            t_route = time.perf_counter()
            if self.route_nodes and len(self.route_nodes) > 1:
                Color(*self.route_color)
                points = []
                for node_id in self.route_nodes:
                    node = next((n for n in self.nodes if n.id == node_id), None)
                    if node:
                        x = node.x * self.zoom + self.pan_x
                        y = node.y * self.zoom + self.pan_y
                        points.extend([x, y])
                if points:
                    Line(points=points, width=self.edge_width * 3)
            t_route_end = time.perf_counter()
            
            # Рёбра графа (серые линии)
            t_edges = time.perf_counter()
            if self.edges and self.nodes:
                Color(*self.edge_color)
                for node_id1, node_id2 in self.edges:
                    node1 = next((n for n in self.nodes if n.id == node_id1), None)
                    node2 = next((n for n in self.nodes if n.id == node_id2), None)
                    if node1 and node2:
                        x1 = node1.x * self.zoom + self.pan_x
                        y1 = node1.y * self.zoom + self.pan_y
                        x2 = node2.x * self.zoom + self.pan_x
                        y2 = node2.y * self.zoom + self.pan_y
                        Line(points=[x1, y1, x2, y2], width=self.edge_width)
            t_edges_end = time.perf_counter()
            
            # Узлы (синие круги)
            t_nodes = time.perf_counter()
            if self.nodes:
                Color(*self.node_color)
                for node in self.nodes:
                    x = node.x * self.zoom + self.pan_x
                    y = node.y * self.zoom + self.pan_y
                    Ellipse(pos=(x - self.node_radius, y - self.node_radius),
                            size=(self.node_radius * 2, self.node_radius * 2))
            t_nodes_end = time.perf_counter()
            
            # Отключаем ротацию после отрисовки
            if abs(self.rotation) > 0.1:
                PopMatrix()
            
            # Логирование производительности
            t_total = (t_bg_end - t_bg) + (t_closed_end - t_closed) + (t_route_end - t_route) + \
                      (t_edges_end - t_edges) + (t_nodes_end - t_nodes)
            if t_total > 0.01:  # Логируем только если > 10ms
                logger.debug(f"[[PROFILE] PNG] BG: {(t_bg_end - t_bg)*1000:.1f}ms | " +
                            f"Edges: {(t_edges_end - t_edges)*1000:.1f}ms | " +
                            f"Closed: {(t_closed_end - t_closed)*1000:.1f}ms | " +
                            f"Route: {(t_route_end - t_route)*1000:.1f}ms | " +
                            f"Nodes: {(t_nodes_end - t_nodes)*1000:.1f}ms | " +
                            f"TOTAL: {t_total*1000:.1f}ms")
