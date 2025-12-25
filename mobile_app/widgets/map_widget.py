"""
Кастомный виджет для отрисовки карты в Kivy
"""
from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.core.window import Window
from kivy.metrics import dp
from typing import List, Tuple, Optional
from services.api_client import Node, Route
import logging

logger = logging.getLogger(__name__)


class MapWidget(Widget):
    """Виджет для отрисовки карты здания"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.nodes: List[Node] = []
        self.edges: List[Tuple[str, str]] = []
        self.route: Optional[Route] = None
        self.selected_node: Optional[Node] = None
        self.start_node: Optional[Node] = None
        self.end_node: Optional[Node] = None
        self.closed_edges: List[Tuple[str, str]] = []
        self.closed_nodes: List[str] = []
        
        # Callback для выбора узла
        self.on_node_selected_callback = None

        # Параметры отрисовки
        self.zoom = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.node_radius = dp(8)
        self.line_width = dp(2)

        # Цвета для различных типов узлов
        self.node_colors = {
            'Room': (0.3, 0.6, 1.0, 1.0),  # Синий
            'Corridor': (0.8, 0.8, 0.8, 1.0),  # Серый
            'Staircase': (1.0, 0.6, 0.2, 1.0),  # Оранжевый
            'Elevator': (1.0, 0.2, 0.2, 1.0),  # Красный
        }

        # Привязка событий
        self.bind(size=self._update_canvas)

    def set_nodes(self, nodes: List[Node]):
        """
        Установить список узлов для отрисовки

        Args:
            nodes: Список объектов Node
        """
        self.nodes = nodes
        self._update_canvas()

    def set_edges(self, edges: List[Tuple[str, str]]):
        """
        Установить список ребер графа

        Args:
            edges: Список кортежей (from_id, to_id)
        """
        self.edges = edges
        self._update_canvas()

    def set_route(self, route: Optional[Route]):
        """
        Установить маршрут для отрисовки

        Args:
            route: Объект Route или None
        """
        self.route = route
        self._update_canvas()

    def set_start_node(self, node: Optional[Node]):
        """Установить стартовый узел"""
        self.start_node = node
        self._update_canvas()

    def set_end_node(self, node: Optional[Node]):
        """Установить конечный узел"""
        self.end_node = node
        self._update_canvas()

    def set_closed_routes(self, closed_edges: List[Tuple[str, str]], closed_nodes: List[str]):
        """
        Установить закрытые маршруты и узлы для визуализации

        Args:
            closed_edges: Список кортежей (from_id, to_id) закрытых маршрутов
            closed_nodes: Список ID закрытых узлов
        """
        self.closed_edges = closed_edges
        self.closed_nodes = closed_nodes
        self._update_canvas()

    def _screen_to_world(self, screen_x: float, screen_y: float) -> Tuple[float, float]:
        """
        Преобразовать координаты экрана в координаты мира

        Args:
            screen_x: X координата на экране
            screen_y: Y координата на экране

        Returns:
            Кортеж (world_x, world_y)
        """
        world_x = (screen_x - self.pan_x) / self.zoom
        world_y = (screen_y - self.pan_y) / self.zoom
        return world_x, world_y

    def _world_to_screen(self, world_x: float, world_y: float) -> Tuple[float, float]:
        """
        Преобразовать координаты мира в координаты экрана

        Args:
            world_x: X координата в мире
            world_y: Y координата в мире

        Returns:
            Кортеж (screen_x, screen_y)
        """
        screen_x = world_x * self.zoom + self.pan_x
        screen_y = world_y * self.zoom + self.pan_y
        return screen_x, screen_y

    def on_touch_down(self, touch):
        """Обработка касания по карте"""
        if not self.collide_point(*touch.pos):
            return False

        # Преобразуем координаты
        world_x, world_y = self._screen_to_world(touch.x, touch.y)

        # Проверяем, какой узел был нажат
        for node in self.nodes:
            dx = node.x - world_x
            dy = node.y - world_y
            distance = (dx**2 + dy**2) ** 0.5

            if distance <= self.node_radius / self.zoom:
                self.selected_node = node
                logger.info(f"Selected node: {node.name}")
                
                # Вызываем callback если он установлен
                if self.on_node_selected_callback:
                    self.on_node_selected_callback(node)
                
                self._update_canvas()
                return True

        return False

    def on_touch_move(self, touch):
        """Обработка перемещения по карте (pan)"""
        if not self.collide_point(*touch.pos):
            return False

        if hasattr(touch, 'ud') and 'previous' in touch.ud:
            # Панорамирование карты
            self.pan_x += touch.x - touch.ud['previous'][0]
            self.pan_y += touch.y - touch.ud['previous'][1]
            self._update_canvas()

        touch.ud['previous'] = (touch.x, touch.y)
        return True

    def on_touch_up(self, touch):
        """Обработка отпускания касания"""
        if 'previous' in touch.ud:
            del touch.ud['previous']
        return False

    def zoom_in(self):
        """Увеличить масштаб карты"""
        self.zoom *= 1.2
        self._update_canvas()

    def zoom_out(self):
        """Уменьшить масштаб карты"""
        self.zoom /= 1.2
        self._update_canvas()

    def reset_view(self):
        """Сбросить панораму и масштаб"""
        self.zoom = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self._update_canvas()

    def clear_selection(self):
        """Очистить выбранные начальную и конечную точки"""
        self.start_node = None
        self.end_node = None
        self.route = None
        self._update_canvas()

    def _update_canvas(self, *args):
        """Обновить отрисовку карты"""
        self.canvas.clear()

        if not self.nodes:
            return

        with self.canvas:
            # Фон
            Color(1, 1, 1, 1)
            Rectangle(pos=self.pos, size=self.size)

            # Отрисовка ребер (линии связи) - обычные связи серым цветом
            Color(0.7, 0.7, 0.7, 0.5)
            for from_id, to_id in self.edges:
                # Пропускаем закрытые маршруты
                if (from_id, to_id) in self.closed_edges or (to_id, from_id) in self.closed_edges:
                    continue
                    
                from_node = next((n for n in self.nodes if n.id == from_id), None)
                to_node = next((n for n in self.nodes if n.id == to_id), None)

                if from_node and to_node:
                    screen_x1, screen_y1 = self._world_to_screen(from_node.x, from_node.y)
                    screen_x2, screen_y2 = self._world_to_screen(to_node.x, to_node.y)
                    Line(points=[screen_x1, screen_y1, screen_x2, screen_y2], width=self.line_width)

            # Отрисовка закрытых маршрутов красным цветом
            Color(1.0, 0.0, 0.0, 0.7)
            for from_id, to_id in self.closed_edges:
                from_node = next((n for n in self.nodes if n.id == from_id), None)
                to_node = next((n for n in self.nodes if n.id == to_id), None)

                if from_node and to_node:
                    screen_x1, screen_y1 = self._world_to_screen(from_node.x, from_node.y)
                    screen_x2, screen_y2 = self._world_to_screen(to_node.x, to_node.y)
                    Line(points=[screen_x1, screen_y1, screen_x2, screen_y2], width=dp(4))

            # Отрисовка маршрута если есть
            if self.route:
                Color(0.2, 0.8, 0.2, 0.7)
                route_points = []
                for node in self.route.path:
                    screen_x, screen_y = self._world_to_screen(node.x, node.y)
                    route_points.extend([screen_x, screen_y])

                if route_points:
                    Line(points=route_points, width=dp(4))

            # Отрисовка узлов
            for node in self.nodes:
                screen_x, screen_y = self._world_to_screen(node.x, node.y)

                # Выбираем цвет в зависимости от типа узла
                color = self.node_colors.get(node.node_type, (0.5, 0.5, 0.5, 1.0))

                # Если узел закрыт, показываем его красным
                if node.id in self.closed_nodes:
                    Color(1.0, 0.0, 0.0, 1.0)  # Красный для закрытых узлов
                # Выделяем стартовый и конечный узлы
                elif node == self.start_node:
                    Color(0.2, 1.0, 0.2, 1.0)  # Зелёный
                elif node == self.end_node:
                    Color(0.2, 0.8, 1.0, 1.0)  # Голубой
                elif node == self.selected_node:
                    Color(1.0, 1.0, 0.0, 1.0)  # Жёлтый
                else:
                    Color(*color)

                # Отрисовка круга узла
                Ellipse(
                    pos=(screen_x - self.node_radius, screen_y - self.node_radius),
                    size=(self.node_radius * 2, self.node_radius * 2)
                )

    def get_selected_node(self) -> Optional[Node]:
        """Получить выбранный узел"""
        return self.selected_node

    def clear(self):
        """Очистить карту"""
        self.nodes = []
        self.edges = []
        self.route = None
        self.selected_node = None
        self._update_canvas()
