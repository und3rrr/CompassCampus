"""
Кастомный виджет для отрисовки карты в Kivy с поддержкой прямой отрисовки SVG
Версия 2.0 - Поддержка отображения номеров кабинетов с масштабированием
"""
from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse, Line, Rectangle, PushMatrix, PopMatrix, Translate, Scale, ScissorPush, ScissorPop
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.core.text import Label as CoreLabel
from typing import List, Tuple, Optional
from services.api_client import Node, Route
import logging
import os
import math
import threading
from kivy.clock import Clock

logger = logging.getLogger(__name__)


class SVGRenderer:
    """Класс для отрисовки SVG элементов на холсте Kivy"""

    @staticmethod
    def _transform_point(x: float, y: float, zoom: float, pan_x: float, pan_y: float) -> Tuple[float, float]:
        """
        Преобразовать координаты с учётом масштаба и смещения

        Args:
            x, y: Координаты в мировом пространстве
            zoom: Коэффициент масштабирования
            pan_x, pan_y: Смещение по осям

        Returns:
            Преобразованные координаты (screen_x, screen_y)
        """
        screen_x = x * zoom + pan_x
        screen_y = y * zoom + pan_y
        return screen_x, screen_y

    @staticmethod
    def _is_element_visible(elem, viewport_left, viewport_top, viewport_right, viewport_bottom) -> bool:
        """
        Проверить, видим ли элемент в текущей viewport
        
        Args:
            elem: SVGElement объект
            viewport_left, viewport_top, viewport_right, viewport_bottom: Границы видимой области
            
        Returns:
            True если элемент (хотя бы частично) видим
        """
        # Элементы с точками (polygon, line, polyline, path)
        if hasattr(elem, 'points') and elem.points:
            for x, y in elem.points:
                if viewport_left <= x <= viewport_right and viewport_top <= y <= viewport_bottom:
                    return True
            # Если ни одна точка не видна, но элемент может быть очень большим, проверяем границы
            min_x = min(p[0] for p in elem.points)
            max_x = max(p[0] for p in elem.points)
            min_y = min(p[1] for p in elem.points)
            max_y = max(p[1] for p in elem.points)
            return not (max_x < viewport_left or min_x > viewport_right or 
                       max_y < viewport_top or min_y > viewport_bottom)
        
        # Прямоугольник
        if hasattr(elem, 'rect_x') and hasattr(elem, 'rect_y') and hasattr(elem, 'rect_width') and hasattr(elem, 'rect_height'):
            if elem.rect_x is not None and elem.rect_y is not None:
                x, y = elem.rect_x, elem.rect_y
                w = elem.rect_width if elem.rect_width else 0
                h = elem.rect_height if elem.rect_height else 0
                return not (x + w < viewport_left or x > viewport_right or 
                           y + h < viewport_top or y > viewport_bottom)
        
        # Круг
        if hasattr(elem, 'center') and hasattr(elem, 'radius') and elem.center and elem.radius:
            cx, cy = elem.center
            r = elem.radius
            return not (cx + r < viewport_left or cx - r > viewport_right or 
                       cy + r < viewport_top or cy - r > viewport_bottom)
        
        # По умолчанию считаем видимым
        return True

    @staticmethod
    def render_svg_elements(canvas, elements, opacity=1.0, zoom=1.0, pan_x=0.0, pan_y=0.0, viewport_width=800, viewport_height=600):
        """
        Отрисовать список SVG элементов на холсте Kivy с culling

        Args:
            canvas: Kivy Canvas объект
            elements: Список SVGElement объектов
            opacity: Общая прозрачность для всех элементов
            zoom: Коэффициент масштабирования
            pan_x: Смещение по оси X
            pan_y: Смещение по оси Y
            viewport_width: Ширина видимой области
            viewport_height: Высота видимой области
        """
        from services.svg_loader import SVGElement

        # Границы видимой области в мировых координатах
        viewport_left = -pan_x / zoom
        viewport_top = -pan_y / zoom
        viewport_right = viewport_left + viewport_width / zoom
        viewport_bottom = viewport_top + viewport_height / zoom

        rendered_count = 0
        for elem in elements:
            try:
                # Проверка видимости элемента (culling)
                if not SVGRenderer._is_element_visible(elem, viewport_left, viewport_top, viewport_right, viewport_bottom):
                    continue

                rendered_count += 1
                if elem.element_type == 'polygon':
                    SVGRenderer._render_polygon(canvas, elem, opacity, zoom, pan_x, pan_y)
                elif elem.element_type == 'line':
                    SVGRenderer._render_line(canvas, elem, opacity, zoom, pan_x, pan_y)
                elif elem.element_type == 'polyline':
                    SVGRenderer._render_polyline(canvas, elem, opacity, zoom, pan_x, pan_y)
                elif elem.element_type == 'rect':
                    SVGRenderer._render_rect(canvas, elem, opacity, zoom, pan_x, pan_y)
                elif elem.element_type == 'circle':
                    SVGRenderer._render_circle(canvas, elem, opacity, zoom, pan_x, pan_y)
                elif elem.element_type == 'ellipse':
                    SVGRenderer._render_ellipse(canvas, elem, opacity, zoom, pan_x, pan_y)
                elif elem.element_type == 'path':
                    SVGRenderer._render_path(canvas, elem, opacity, zoom, pan_x, pan_y)
            except Exception as e:
                logger.debug(f"Error rendering {elem.element_type}: {e}")
                continue
        
        if rendered_count < len(elements):
            logger.debug(f"SVG culling: rendered {rendered_count}/{len(elements)} elements")

    @staticmethod
    def _render_polygon(canvas, elem, opacity, zoom=1.0, pan_x=0.0, pan_y=0.0):
        """Отрисовать полигон"""
        from services.svg_loader import SVGElement

        if not elem.points or len(elem.points) < 3:
            return

        # Трансформируем координаты с учётом zoom и pan
        transformed_points = []
        for point in elem.points:
            tx, ty = SVGRenderer._transform_point(point[0], point[1], zoom, pan_x, pan_y)
            transformed_points.append((tx, ty))

        points_flat = []
        for point in transformed_points:
            points_flat.extend(point)

        with canvas:
            # Заливка - для Kivy используем несколько линий для визуального эффекта
            if elem.fill_color and elem.fill_color[3] > 0:
                r, g, b, a = elem.fill_color
                Color(r, g, b, a * opacity * elem.opacity * 0.3)
                # Рисуем несколько горизонтальных линий в пределах полигона (эмуляция заливки)
                # Это грубое приближение, но работает без Polygon
                if len(transformed_points) >= 3:
                    min_y = min(p[1] for p in transformed_points)
                    max_y = max(p[1] for p in transformed_points)
                    for y in range(int(min_y), int(max_y), max(1, int((max_y - min_y) / 10))):
                        # Просто рисуем замкнутый контур как заполнение
                        closed_points = points_flat + points_flat[:2]
                        Line(points=closed_points, width=0.5)

            # Обводка
            if elem.stroke_color and elem.stroke_width > 0:
                r, g, b, a = elem.stroke_color
                Color(r, g, b, a * opacity * elem.opacity)
                # Замыкаем полигон линией
                closed_points = points_flat + points_flat[:2]
                width = max(1, elem.stroke_width * zoom)  # Масштабируем толщину линии
                Line(points=closed_points, width=width)

    @staticmethod
    def _render_line(canvas, elem, opacity, zoom=1.0, pan_x=0.0, pan_y=0.0):
        """Отрисовать линию"""
        if not elem.points or len(elem.points) < 2:
            return

        # Трансформируем координаты
        transformed_points = []
        for point in elem.points:
            tx, ty = SVGRenderer._transform_point(point[0], point[1], zoom, pan_x, pan_y)
            transformed_points.append((tx, ty))

        points_flat = []
        for point in transformed_points:
            points_flat.extend(point)

        with canvas:
            if elem.stroke_color:
                r, g, b, a = elem.stroke_color
                Color(r, g, b, a * opacity * elem.opacity)
                width = max(1, elem.stroke_width * zoom)  # Масштабируем толщину линии
                Line(points=points_flat, width=width)

    @staticmethod
    def _render_polyline(canvas, elem, opacity, zoom=1.0, pan_x=0.0, pan_y=0.0):
        """Отрисовать полилинию"""
        if not elem.points or len(elem.points) < 2:
            return

        # Трансформируем координаты
        transformed_points = []
        for point in elem.points:
            tx, ty = SVGRenderer._transform_point(point[0], point[1], zoom, pan_x, pan_y)
            transformed_points.append((tx, ty))

        points_flat = []
        for point in transformed_points:
            points_flat.extend(point)

        with canvas:
            if elem.stroke_color:
                r, g, b, a = elem.stroke_color
                Color(r, g, b, a * opacity * elem.opacity)
                width = max(1, elem.stroke_width * zoom)  # Масштабируем толщину линии
                Line(points=points_flat, width=width)

    @staticmethod
    def _render_rect(canvas, elem, opacity, zoom=1.0, pan_x=0.0, pan_y=0.0):
        """Отрисовать прямоугольник"""
        # Трансформируем координаты углов прямоугольника
        x1, y1 = SVGRenderer._transform_point(elem.rect_x, elem.rect_y, zoom, pan_x, pan_y)
        x2, y2 = SVGRenderer._transform_point(
            elem.rect_x + elem.rect_width,
            elem.rect_y + elem.rect_height,
            zoom, pan_x, pan_y
        )
        
        # Вычисляем новые размеры
        new_width = abs(x2 - x1)
        new_height = abs(y2 - y1)
        new_x = min(x1, x2)
        new_y = min(y1, y2)

        with canvas:
            # Заливка
            if elem.fill_color and (elem.fill_color[3] > 0 or elem.fill_color != (0, 0, 0, 0)):
                r, g, b, a = elem.fill_color
                Color(r, g, b, a * opacity * elem.opacity)
                Rectangle(
                    pos=(new_x, new_y),
                    size=(new_width, new_height)
                )

            # Обводка
            if elem.stroke_color and elem.stroke_width > 0:
                r, g, b, a = elem.stroke_color
                Color(r, g, b, a * opacity * elem.opacity)
                # Рисуем контур прямоугольника линиями
                points = [
                    new_x, new_y,
                    new_x + new_width, new_y,
                    new_x + new_width, new_y + new_height,
                    new_x, new_y + new_height,
                    new_x, new_y
                ]
                width = max(1, elem.stroke_width * zoom)  # Масштабируем толщину линии
                Line(points=points, width=width)

    @staticmethod
    def _render_circle(canvas, elem, opacity, zoom=1.0, pan_x=0.0, pan_y=0.0):
        """Отрисовать круг"""
        if not elem.center or not elem.radius:
            return

        cx, cy = elem.center
        r = elem.radius

        # Трансформируем центр круга
        screen_cx, screen_cy = SVGRenderer._transform_point(cx, cy, zoom, pan_x, pan_y)
        # Масштабируем радиус
        screen_r = r * zoom

        with canvas:
            # Заливка
            if elem.fill_color:
                color = elem.fill_color
                Color(color[0], color[1], color[2], color[3] * opacity * elem.opacity)
                Ellipse(pos=(screen_cx - screen_r, screen_cy - screen_r), size=(screen_r * 2, screen_r * 2))

            # Обводка
            if elem.stroke_color and elem.stroke_width > 0:
                color = elem.stroke_color
                Color(color[0], color[1], color[2], color[3] * opacity * elem.opacity)
                width = max(1, elem.stroke_width * zoom)  # Масштабируем толщину линии
                # Рисуем контур как серию кружков с разными радиусами (эмуляция обводки)
                Line(circle=(screen_cx, screen_cy, screen_r), width=width)

    @staticmethod
    def _render_ellipse(canvas, elem, opacity, zoom=1.0, pan_x=0.0, pan_y=0.0):
        """Отрисовать эллипс"""
        if not elem.center or not elem.radius:
            return

        cx, cy = elem.center
        
        # Парсим радиусы из path_data если есть
        if elem.path_data:
            try:
                parts = elem.path_data.split(',')
                rx = float(parts[0])
                ry = float(parts[1]) if len(parts) > 1 else elem.radius
            except:
                rx = ry = elem.radius
        else:
            rx = ry = elem.radius

        # Трансформируем центр и масштабируем радиусы
        screen_cx, screen_cy = SVGRenderer._transform_point(cx, cy, zoom, pan_x, pan_y)
        screen_rx = rx * zoom
        screen_ry = ry * zoom

        with canvas:
            # Заливка
            if elem.fill_color:
                color = elem.fill_color
                Color(color[0], color[1], color[2], color[3] * opacity * elem.opacity)
                Ellipse(pos=(screen_cx - screen_rx, screen_cy - screen_ry), size=(screen_rx * 2, screen_ry * 2))

            # Обводка
            if elem.stroke_color and elem.stroke_width > 0:
                color = elem.stroke_color
                Color(color[0], color[1], color[2], color[3] * opacity * elem.opacity)
                width = max(1, elem.stroke_width * zoom)  # Масштабируем толщину линии
                Line(ellipse=(screen_cx - screen_rx, screen_cy - screen_ry, screen_rx * 2, screen_ry * 2), width=width)

    @staticmethod
    def _render_path(canvas, elem, opacity, zoom=1.0, pan_x=0.0, pan_y=0.0):
        """Отрисовать path элемент (сложная операция - парсим SVG path data)"""
        if not elem.path_data:
            return

        # Парсим SVG path data в координаты
        points = SVGRenderer._parse_path_data(elem.path_data)
        if not points or len(points) < 2:
            return

        # Трансформируем координаты
        transformed_points = []
        for point in points:
            tx, ty = SVGRenderer._transform_point(point[0], point[1], zoom, pan_x, pan_y)
            transformed_points.append((tx, ty))

        points_flat = []
        for point in transformed_points:
            points_flat.extend(point)

        with canvas:
            if elem.stroke_color and elem.stroke_width > 0:
                r, g, b, a = elem.stroke_color
                Color(r, g, b, a * opacity * elem.opacity)
                width = max(1, elem.stroke_width * zoom)  # Масштабируем толщину линии
                Line(points=points_flat, width=width)

            # Заливка (если указана и это замкнутый path)
            if elem.fill_color and elem.fill_color[3] > 0:
                try:
                    r, g, b, a = elem.fill_color
                    Color(r, g, b, a * opacity * elem.opacity)
                    # Рисуем замкнутую линию вместо Polygon (Kivy не имеет Polygon)
                    closed_points = points_flat + points_flat[:2]
                    Line(points=closed_points, width=0.5)
                except:
                    pass  # Не все paths можно заполнить как polygon

    @staticmethod
    def _parse_path_data(path_data: str) -> List[Tuple[float, float]]:
        """
        Парсить SVG path data строку в список координат

        Это упрощённый парсер, поддерживает основные команды:
        M/m - moveto
        L/l - lineto
        H/h - horizontal lineto
        V/v - vertical lineto
        Z/z - closepath
        """
        points = []
        current_x = 0.0
        current_y = 0.0

        # Убираем пробелы вокруг команд
        path_data = path_data.replace('\n', ' ').replace(',', ' ')

        i = 0
        while i < len(path_data):
            char = path_data[i].strip()

            if not char or char.isspace():
                i += 1
                continue

            if char in 'MmLlHhVvZz':
                # Команда движения
                command = char
                i += 1

                # Читаем числа после команды
                numbers = []
                while i < len(path_data):
                    # Пропускаем пробелы
                    while i < len(path_data) and path_data[i].isspace():
                        i += 1

                    if i >= len(path_data) or path_data[i] in 'MmLlHhVvZz':
                        break

                    # Читаем число
                    num_str = ''
                    while i < len(path_data) and (path_data[i].isdigit() or path_data[i] in '.-'):
                        num_str += path_data[i]
                        i += 1

                    if num_str:
                        try:
                            numbers.append(float(num_str))
                        except:
                            pass

                # Обрабатываем команду
                if command.upper() == 'M':  # MoveTo
                    if len(numbers) >= 2:
                        current_x, current_y = numbers[0], numbers[1]
                        points.append((current_x, current_y))

                elif command.upper() == 'L':  # LineTo
                    if len(numbers) >= 2:
                        current_x, current_y = numbers[0], numbers[1]
                        points.append((current_x, current_y))

                elif command.upper() == 'H':  # Horizontal LineTo
                    if len(numbers) >= 1:
                        current_x = numbers[0]
                        points.append((current_x, current_y))

                elif command.upper() == 'V':  # Vertical LineTo
                    if len(numbers) >= 1:
                        current_y = numbers[0]
                        points.append((current_x, current_y))

                elif command.upper() == 'Z':  # ClosePath
                    pass  # Полигон автоматически закроется

            else:
                i += 1

        return points


class MapWidget(Widget):
    """Виджет для отрисовки карты здания с поддержкой SVG элементов"""

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

        # SVG элементы для отрисовки
        self.svg_elements: List = []  # Список SVGElement объектов
        self.svg_width: Optional[float] = None
        self.svg_height: Optional[float] = None

        # Свойства для фонового изображения (PNG/JPG для совместимости)
        self.background_image_path: Optional[str] = None
        self.background_enabled = True
        self.background_opacity = 1.0  # 0.0 - 1.0
        self.use_svg_coordinates = False  # Если True, используем координаты из SVG файла

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

    def _find_floor_plan_file(self, image_path: str) -> Tuple[Optional[str], str]:
        """
        Найти план этажа с приоритетом PNG > SVG
        
        Если передан путь без расширения или с .svg, ищет PNG в первую очередь
        
        Args:
            image_path: Путь к файлу (может быть с расширением или без)
            
        Returns:
            Кортеж (path_to_file, file_type) где file_type = 'png' или 'svg' или 'unknown'
        """
        # Если явно указана полная папка "floor_1" - ищем файлы
        candidates = []
        
        # Случай 1: Передан путь с расширением
        if '.' in os.path.basename(image_path):
            base_path = image_path.rsplit('.', 1)[0]
            folder = os.path.dirname(image_path)
        else:
            # Случай 2: Передан путь без расширения
            base_path = image_path
            folder = os.path.dirname(image_path)
        
        # Ищем PNG в первую очередь (основной формат)
        png_path = f"{base_path}.png"
        if os.path.exists(png_path):
            logger.info(f"Found floor plan (PNG): {png_path}")
            return png_path, 'png'
        
        # Если PNG не найден, ищем SVG (опциональный формат)
        svg_path = f"{base_path}.svg"
        if os.path.exists(svg_path):
            logger.info(f"Found floor plan (SVG): {svg_path}")
            return svg_path, 'svg'
        
        # Если оригинальный путь существует - используем его
        if os.path.exists(image_path):
            ext = os.path.splitext(image_path)[1].lower()
            return image_path, 'png' if ext == '.png' else 'svg' if ext == '.svg' else 'unknown'
        
        logger.warning(f"Floor plan file not found: {image_path} (tried: {png_path}, {svg_path})")
        return None, 'unknown'

    def _fit_to_screen(self, plan_width: Optional[float] = None, plan_height: Optional[float] = None):
        """
        Масштабировать карту так, чтобы она оптимально отображалась на экране
        
        Найдёт оптимальный zoom уровень чтобы:
        - План целиком видился на экране
        - Был баланс между видимостью и размером
        - Карта была центрирована
        
        Args:
            plan_width: Ширина плана этажа (если None, используется svg_width)
            plan_height: Высота плана этажа (если None, используется svg_height)
        """
        if not self.width or not self.height:
            return  # Окно ещё не инициализировано
        
        # Используем переданные размеры или размеры SVG
        width = plan_width or self.svg_width
        height = plan_height or self.svg_height
        
        if not width or not height:
            return  # Размеры не известны
        
        # Оставляем небольшой отступ от краёв экрана
        padding = 40  # Фиксированный отступ в пикселях
        available_width = self.width - 2 * padding
        available_height = self.height - 2 * padding
        
        # Вычисляем масштаб на основе обоих измерений
        scale_x = available_width / width if width > 0 else 1.0
        scale_y = available_height / height if height > 0 else 1.0
        
        # Берём минимум чтобы весь план влез на экран
        self.zoom = min(scale_x, scale_y)
        
        # Центрируем план на экране
        center_x = self.width / 2
        center_y = self.height / 2
        
        # Смещение так, чтобы центр плана совпал с центром экрана
        self.pan_x = center_x - (width / 2) * self.zoom
        self.pan_y = center_y - (height / 2) * self.zoom
        
        logger.info(f"Fitted to screen: zoom={self.zoom:.2f}, pan=({self.pan_x:.0f}, {self.pan_y:.0f})")

    def set_background_image(self, image_path: str, svg_width: Optional[float] = None, 
                            svg_height: Optional[float] = None, use_svg_coordinates: bool = False):
        """
        Установить фоновое изображение - PNG как основной формат, SVG как опция
        
        Приоритет: PNG > SVG > Nothing
        Для PNG: загружается как растровое изображение (быстро)
        Для SVG: загружается как векторные элементы (если PNG не доступен)
        
        При загрузке автоматически центрирует и масштабирует план на экран.

        Args:
            image_path: Путь к файлу плана этажа (PNG или SVG)
            svg_width: Ширина SVG (если используется SVG координаты)
            svg_height: Высота SVG (если используется SVG координаты)
            use_svg_coordinates: Если True, узлы отображаются в координатах SVG
        """
        if image_path is None:
            self.background_image_path = None
            self.svg_elements = []
            self._update_canvas()
            return

        # Ищем файл с приоритетом PNG > SVG
        file_path, file_type = self._find_floor_plan_file(image_path)
        
        if file_path is None:
            logger.warning(f"Could not find floor plan: {image_path}")
            self.background_image_path = None
            self.svg_elements = []
            self._update_canvas()
            return

        # ОСНОВНОЙ СПОСОБ: Загружаем PNG как растровое изображение
        if file_type == 'png':
            self.background_image_path = file_path
            self.svg_elements = []  # Очищаем SVG элементы
            self.svg_width = svg_width
            self.svg_height = svg_height
            self.use_svg_coordinates = use_svg_coordinates
            
            # Для PNG пытаемся получить размеры изображения
            try:
                from PIL import Image as PILImage
                img = PILImage.open(file_path)
                if img.size:
                    actual_width, actual_height = img.size
                    logger.info(f"PNG size: {actual_width}x{actual_height}")
                    
                    # Сохраняем размеры PNG
                    self.svg_width = actual_width
                    self.svg_height = actual_height
                    
                    # Масштабируем на основе размеров PNG
                    self._fit_to_screen(actual_width, actual_height)
                else:
                    logger.warning("Could not get PNG dimensions")
            except ImportError:
                logger.debug("PIL not available, skipping PNG dimension extraction")
            except Exception as e:
                logger.debug(f"Could not get PNG dimensions: {e}")
            
            logger.info(f"Background image set (PNG): {file_path}")
            self._update_canvas()
            return

        # ОПЦИОНАЛЬНЫЙ СПОСОБ: Загружаем SVG если PNG не доступен
        if file_type == 'svg':
            # Загружаем SVG в фоновом потоке чтобы не блокировать UI
            def _load_svg_in_background(path, use_svg_coords):
                try:
                    from services.svg_loader import SVGLoader
                    floor_plan = SVGLoader.load_svg_file(path)

                    # Обновление UI должно происходить в основном потоке
                    Clock.schedule_once(lambda dt: self._on_svg_loaded(floor_plan, path, use_svg_coords), 0)
                except ImportError:
                    logger.error("SVGLoader not available. Could not parse SVG file.")
                    Clock.schedule_once(lambda dt: self._on_svg_failed(path, "SVGLoader not available"), 0)
                except Exception as e:
                    logger.error(f"Error loading SVG file in background: {e}")
                    Clock.schedule_once(lambda dt: self._on_svg_failed(path, str(e)), 0)

            thread = threading.Thread(target=_load_svg_in_background, args=(file_path, use_svg_coordinates), daemon=True)
            thread.start()
            # Возвращаемся сразу — визуализация произойдёт после завершения парсинга
            logger.info("[MapWidget] Starting async SVG parse...")
            return

        # Неизвестный формат
        logger.warning(f"Unsupported floor plan format: {file_type}")
        self.background_image_path = None
        self.svg_elements = []
        self._update_canvas()

    def set_background_opacity(self, opacity: float):
        """
        Установить прозрачность фонового изображения (0.0 - 1.0)

        Args:
            opacity: Значение прозрачности
        """
        self.background_opacity = max(0.0, min(1.0, opacity))
        self._update_canvas()

    def set_background_enabled(self, enabled: bool):
        """
        Включить/выключить отрисовку фонового изображения

        Args:
            enabled: True для показа фона, False для скрытия
        """
        self.background_enabled = enabled
        self._update_canvas()

    def load_floor_plan_from_svg(self, svg_path: str):
        """
        Загрузить план этажа из SVG файла
        
        Парсит SVG и отрисовывает векторные элементы напрямую в Kivy
        Без конвертирования в PNG, что сохраняет качество векторной графики

        Args:
            svg_path: Путь к SVG файлу из Sweet Home 3D
        """
        if not os.path.exists(svg_path):
            logger.error(f"SVG file not found: {svg_path}")
            return

        # Просто загружаем SVG напрямую (set_background_image сделает парсинг)
        self.set_background_image(
            image_path=svg_path,
            use_svg_coordinates=False
        )

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

    def on_mouse_pos(self, *args):
        """Обработка движения мыши"""
        pass

    def on_scroll_down(self, *args):
        """Зум по колесику мыши (вверх - приближение)"""
        # Сохраняем центр экрана перед зумом
        center_screen_x = self.width / 2
        center_screen_y = self.height / 2
        center_world_x, center_world_y = self._screen_to_world(center_screen_x, center_screen_y)
        
        # Приближаем
        self.zoom *= 1.1
        
        # Пересчитываем pan чтобы центр остался в центре
        self.pan_x = center_screen_x - center_world_x * self.zoom
        self.pan_y = center_screen_y - center_world_y * self.zoom
        
        self._update_canvas()
        return True

    def on_scroll_up(self, *args):
        """Зум по колесику мыши (вниз - отдаление)"""
        # Сохраняем центр экрана перед зумом
        center_screen_x = self.width / 2
        center_screen_y = self.height / 2
        center_world_x, center_world_y = self._screen_to_world(center_screen_x, center_screen_y)
        
        # Отдаляем
        self.zoom /= 1.1
        
        # Пересчитываем pan чтобы центр остался в центре
        self.pan_x = center_screen_x - center_world_x * self.zoom
        self.pan_y = center_screen_y - center_world_y * self.zoom
        
        self._update_canvas()
        return True

    def zoom_in(self):
        """Увеличить масштаб карты"""
        # Сохраняем центр экрана перед зумом
        center_screen_x = self.width / 2
        center_screen_y = self.height / 2
        center_world_x, center_world_y = self._screen_to_world(center_screen_x, center_screen_y)
        
        # Приближаем (максимум 5x зум)
        self.zoom = min(self.zoom * 1.2, 5.0)
        
        # Пересчитываем pan чтобы центр остался в центре
        self.pan_x = center_screen_x - center_world_x * self.zoom
        self.pan_y = center_screen_y - center_world_y * self.zoom
        
        self._update_canvas()

    def zoom_out(self):
        """Уменьшить масштаб карты"""
        # Сохраняем центр экрана перед зумом
        center_screen_x = self.width / 2
        center_screen_y = self.height / 2
        center_world_x, center_world_y = self._screen_to_world(center_screen_x, center_screen_y)
        
        # Отдаляем (минимум 0.3x зум)
        self.zoom = max(self.zoom / 1.2, 0.3)
        
        # Пересчитываем pan чтобы центр остался в центре
        self.pan_x = center_screen_x - center_world_x * self.zoom
        self.pan_y = center_screen_y - center_world_y * self.zoom
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
        """Обновить отрисовку карты с профилированием"""
        import time
        self.canvas.clear()

        if not self.nodes:
            return

        # Вычисляем границы графа
        if self.nodes:
            min_x = min(n.x for n in self.nodes)
            max_x = max(n.x for n in self.nodes)
            min_y = min(n.y for n in self.nodes)
            max_y = max(n.y for n in self.nodes)
            graph_width = max_x - min_x or 100
            graph_height = max_y - min_y or 100
            padding = 50
            available_width = self.width - 2 * padding
            available_height = self.height - 2 * padding
            scale_x = available_width / graph_width if graph_width > 0 else 1.0
            scale_y = available_height / graph_height if graph_height > 0 else 1.0
            auto_zoom = min(scale_x, scale_y, 2.0)
            center_x = self.width / 2
            center_y = self.height / 2
            graph_center_x = (min_x + max_x) / 2
            graph_center_y = (min_y + max_y) / 2
            self.auto_pan_x = center_x - (graph_center_x * auto_zoom)
            self.auto_pan_y = center_y - (graph_center_y * auto_zoom)

        t0 = time.perf_counter()
        with self.canvas:
            ScissorPush(x=int(self.x), y=int(self.y), width=int(self.width), height=int(self.height))
            Color(1, 1, 1, 1)
            Rectangle(pos=self.pos, size=self.size)

            # SVG elements - DISABLED (too slow, use raster background instead)
            t_svg = time.perf_counter()
            # if self.background_enabled and self.svg_elements:
            #     try:
            #         SVGRenderer.render_svg_elements(...)
            #     except Exception as e:
            #         logger.warning(f"Error rendering SVG elements: {e}")
            t_svg_end = time.perf_counter()

            # Background image
            t_bg = time.perf_counter()
            if self.background_enabled and self.background_image_path:
                Color(1, 1, 1, self.background_opacity)
                try:
                    if self.background_image_path.endswith(('.png', '.jpg', '.jpeg')):
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
                            Rectangle(
                                source=self.background_image_path,
                                pos=self.pos,
                                size=self.size
                            )
                except Exception as e:
                    logger.warning(f"Error rendering background image: {e}")
            t_bg_end = time.perf_counter()

            # Edges
            t_edges = time.perf_counter()
            Color(0.7, 0.7, 0.7, 0.5)
            for from_id, to_id in self.edges:
                if (from_id, to_id) in self.closed_edges or (to_id, from_id) in self.closed_edges:
                    continue
                from_node = next((n for n in self.nodes if n.id == from_id), None)
                to_node = next((n for n in self.nodes if n.id == to_id), None)
                if from_node and to_node:
                    screen_x1, screen_y1 = self._world_to_screen(from_node.x, from_node.y)
                    screen_x2, screen_y2 = self._world_to_screen(to_node.x, to_node.y)
                    Line(points=[screen_x1, screen_y1, screen_x2, screen_y2], width=self.line_width)
            t_edges_end = time.perf_counter()

            # Closed edges
            t_closed = time.perf_counter()
            Color(1.0, 0.0, 0.0, 0.7)
            for from_id, to_id in self.closed_edges:
                from_node = next((n for n in self.nodes if n.id == from_id), None)
                to_node = next((n for n in self.nodes if n.id == to_id), None)
                if from_node and to_node:
                    screen_x1, screen_y1 = self._world_to_screen(from_node.x, from_node.y)
                    screen_x2, screen_y2 = self._world_to_screen(to_node.x, to_node.y)
                    Line(points=[screen_x1, screen_y1, screen_x2, screen_y2], width=dp(4))
            t_closed_end = time.perf_counter()

            # Route
            t_route = time.perf_counter()
            if self.route:
                Color(0.2, 0.8, 0.2, 0.7)
                route_points = []
                for node in self.route.path:
                    screen_x, screen_y = self._world_to_screen(node.x, node.y)
                    route_points.extend([screen_x, screen_y])
                if route_points:
                    Line(points=route_points, width=dp(4))
            t_route_end = time.perf_counter()

            # Nodes
            t_nodes = time.perf_counter()
            for node in self.nodes:
                screen_x, screen_y = self._world_to_screen(node.x, node.y)
                color = self.node_colors.get(node.node_type, (0.5, 0.5, 0.5, 1.0))
                if node.id in self.closed_nodes:
                    Color(1.0, 0.0, 0.0, 1.0)
                elif node == self.start_node:
                    Color(0.2, 1.0, 0.2, 1.0)
                elif node == self.end_node:
                    Color(0.2, 0.8, 1.0, 1.0)
                elif node == self.selected_node:
                    Color(1.0, 1.0, 0.0, 1.0)
                else:
                    Color(*color)
                Ellipse(
                    pos=(screen_x - self.node_radius, screen_y - self.node_radius),
                    size=(self.node_radius * 2, self.node_radius * 2)
                )
            t_nodes_end = time.perf_counter()

            # Labels
            t_labels = time.perf_counter()
            if self.zoom >= 0.5:
                font_size = max(10, int(16 * self.zoom))
                for node in self.nodes:
                    display_text = node.name if node.node_type != 'Corridor' else '🚶'
                    if display_text:
                        try:
                            label = CoreLabel(
                                text=display_text[:15],
                                font_size=font_size,
                                color=(0.1, 0.1, 0.1, 1.0)
                            )
                            label.refresh()
                            if label.texture:
                                screen_x, screen_y = self._world_to_screen(node.x, node.y)
                                text_width, text_height = label.texture.size
                                text_x = screen_x - text_width / 2
                                text_y = screen_y + self.node_radius + 5
                                Color(0.1, 0.1, 0.1, 1.0)
                                Rectangle(
                                    texture=label.texture,
                                    pos=(text_x, text_y),
                                    size=(text_width, text_height)
                                )
                        except Exception as e:
                            logger.debug(f"Could not render node label for {node.name}: {e}")
            t_labels_end = time.perf_counter()

            ScissorPop()

        t1 = time.perf_counter()
        logger.info(f"[PROFILE] SVG: {(t_svg_end-t_svg)*1000:.1f}ms | BG: {(t_bg_end-t_bg)*1000:.1f}ms | Edges: {(t_edges_end-t_edges)*1000:.1f}ms | Closed: {(t_closed_end-t_closed)*1000:.1f}ms | Route: {(t_route_end-t_route)*1000:.1f}ms | Nodes: {(t_nodes_end-t_nodes)*1000:.1f}ms | Labels: {(t_labels_end-t_labels)*1000:.1f}ms | TOTAL: {(t1-t0)*1000:.1f}ms")

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

    def _on_svg_loaded(self, floor_plan, file_path: str, use_svg_coordinates: bool):
        """Вызов из главного потока после успешной фоновой загрузки SVG"""
        logger.info("[MapWidget._on_svg_loaded] Starting...")
        try:
            logger.info("[MapWidget._on_svg_loaded] Setting SVG elements...")
            self.svg_elements = floor_plan.elements
            self.svg_width = floor_plan.width
            self.svg_height = floor_plan.height
            self.background_image_path = None
            self.use_svg_coordinates = use_svg_coordinates

            # Масштабируем и обновляем
            logger.info("[MapWidget._on_svg_loaded] Fitting to screen...")
            self._fit_to_screen(floor_plan.width, floor_plan.height)
            logger.info(f"Background image set (SVG fallback): {file_path} ({floor_plan.width}x{floor_plan.height}, {len(floor_plan.elements)} elements)")
            logger.info("[MapWidget._on_svg_loaded] Scheduling canvas update...")
            # Отложим обновление canvas на несколько фреймов чтобы не блокировать UI
            Clock.schedule_once(lambda dt: self._update_canvas(), 0.016)  # ~60 FPS
            logger.info("[MapWidget._on_svg_loaded] Done!")
        except Exception as e:
            logger.error(f"Error applying loaded SVG to UI: {e}")
            self.svg_elements = []
            Clock.schedule_once(lambda dt: self._update_canvas(), 0.016)

    def _on_svg_failed(self, file_path: str, error_msg: str):
        """Вызов из главного потока при ошибке фоновой загрузки SVG"""
        logger.error(f"Failed to load SVG {file_path}: {error_msg}")
        self.svg_elements = []
        self._update_canvas()
