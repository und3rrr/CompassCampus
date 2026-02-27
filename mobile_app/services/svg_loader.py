"""
Загрузчик и парсер SVG файлов из Sweet Home 3D
Поддерживает прямую отрисовку векторных элементов в Kivy без конвертирования
"""
import xml.etree.ElementTree as ET
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass, field
import logging
import os
from pathlib import Path
import re
import math

logger = logging.getLogger(__name__)


@dataclass
class SVGRoom:
    """Комната из SVG"""
    name: str
    polygon_points: List[Tuple[float, float]]
    center_x: float
    center_y: float
    color: str
    area: float  # Приблизительная площадь


@dataclass
class SVGElement:
    """Базовый элемент SVG для векторной отрисовки"""
    element_type: str  # 'line', 'polygon', 'circle', 'rect', 'path', 'polyline'
    fill_color: Optional[Tuple[float, float, float, float]] = None  # RGBA (0-1)
    stroke_color: Optional[Tuple[float, float, float, float]] = None  # RGBA (0-1)
    stroke_width: float = 1.0
    opacity: float = 1.0
    points: List[Tuple[float, float]] = field(default_factory=list)  # Для линий, полигонов
    center: Optional[Tuple[float, float]] = None  # Для кругов
    radius: Optional[float] = None  # Для кругов
    rect_x: Optional[float] = None  # Для прямоугольников
    rect_y: Optional[float] = None
    rect_width: Optional[float] = None
    rect_height: Optional[float] = None
    path_data: Optional[str] = None  # Для path элементов


@dataclass
class SVGFloorPlan:
    """План этажа из SVG"""
    floor_number: int
    svg_path: str
    width: float
    height: float
    rooms: List[SVGRoom]
    elements: List[SVGElement] = field(default_factory=list)  # Все векторные элементы
    raw_svg_content: str = ""  # Исходный SVG код


class SVGLoader:
    """Загрузчик SVG файлов из Sweet Home 3D с поддержкой векторной отрисовки"""

    # Пространства имён XML
    SVG_NS = {'svg': 'http://www.w3.org/2000/svg'}

    @staticmethod
    def load_svg_file(file_path: str) -> SVGFloorPlan:
        """
        Загрузить SVG файл плана этажа с парсингом всех элементов

        Args:
            file_path: Путь к SVG файлу

        Returns:
            Объект SVGFloorPlan с распарсеными данными и элементами
        """
        if not os.path.exists(file_path):
            logger.error(f"SVG file not found: {file_path}")
            raise FileNotFoundError(f"SVG file not found: {file_path}")

        try:
            # Читаем SVG
            with open(file_path, 'r', encoding='utf-8') as f:
                svg_content = f.read()

            # Парсим XML
            root = ET.fromstring(svg_content)

            # Получаем размеры
            width = float(root.get('width', '1000').replace('px', ''))
            height = float(root.get('height', '1000').replace('px', ''))

            # Извлекаем все элементы SVG
            elements = SVGLoader._extract_all_elements(root, width, height)

            # Извлекаем комнаты (как часть элементов)
            rooms = SVGLoader._extract_rooms(root)

            # Получаем номер этажа из имени файла
            floor_number = SVGLoader._extract_floor_number(file_path)

            logger.info(f"Loaded SVG: {file_path} ({width}x{height}, {len(elements)} elements, {len(rooms)} rooms)")

            return SVGFloorPlan(
                floor_number=floor_number,
                svg_path=file_path,
                width=width,
                height=height,
                rooms=rooms,
                elements=elements,
                raw_svg_content=svg_content
            )

        except Exception as e:
            logger.error(f"Error loading SVG file: {e}")
            raise

    @staticmethod
    def _extract_all_elements(root: ET.Element, svg_width: float, svg_height: float) -> List[SVGElement]:
        """
        Извлечь все векторные элементы из SVG для отрисовки

        Args:
            root: Корневой элемент SVG
            svg_width: Ширина SVG
            svg_height: Высота SVG

        Returns:
            Список SVGElement для отрисовки на холсте Kivy
        """
        elements = []

        # Ищем все графические элементы (в порядке отрисовки важна глубина)
        for elem in root.iter():
            # Получаем локальный тег (без namespace)
            tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag

            try:
                if tag == 'line':
                    svg_elem = SVGLoader._parse_line(elem)
                    if svg_elem:
                        elements.append(svg_elem)

                elif tag == 'polygon':
                    svg_elem = SVGLoader._parse_polygon(elem)
                    if svg_elem:
                        elements.append(svg_elem)

                elif tag == 'polyline':
                    svg_elem = SVGLoader._parse_polyline(elem)
                    if svg_elem:
                        elements.append(svg_elem)

                elif tag == 'rect':
                    svg_elem = SVGLoader._parse_rect(elem)
                    if svg_elem:
                        elements.append(svg_elem)

                elif tag == 'circle':
                    svg_elem = SVGLoader._parse_circle(elem)
                    if svg_elem:
                        elements.append(svg_elem)

                elif tag == 'ellipse':
                    svg_elem = SVGLoader._parse_ellipse(elem)
                    if svg_elem:
                        elements.append(svg_elem)

                elif tag == 'path':
                    svg_elem = SVGLoader._parse_path(elem)
                    if svg_elem:
                        elements.append(svg_elem)

            except Exception as e:
                logger.debug(f"Error parsing {tag} element: {e}")
                continue

        logger.debug(f"Extracted {len(elements)} elements from SVG")
        return elements

    @staticmethod
    def _parse_line(elem: ET.Element) -> Optional[SVGElement]:
        """Парсить <line> элемент"""
        try:
            x1 = float(elem.get('x1', 0))
            y1 = float(elem.get('y1', 0))
            x2 = float(elem.get('x2', 0))
            y2 = float(elem.get('y2', 0))

            stroke_color = SVGLoader._parse_color(elem.get('stroke', '#000000'), 1.0)
            stroke_width = float(elem.get('stroke-width', '1'))
            opacity = float(elem.get('opacity', '1.0'))

            return SVGElement(
                element_type='line',
                stroke_color=stroke_color,
                stroke_width=stroke_width,
                opacity=opacity,
                points=[(x1, y1), (x2, y2)]
            )
        except Exception as e:
            logger.debug(f"Error parsing line: {e}")
            return None

    @staticmethod
    def _parse_polygon(elem: ET.Element) -> Optional[SVGElement]:
        """Парсить <polygon> элемент"""
        try:
            points_str = elem.get('points', '')
            if not points_str:
                return None

            points = SVGLoader._parse_points(points_str)
            if len(points) < 3:
                return None

            fill_color = SVGLoader._parse_color(elem.get('fill', '#cccccc'), 0.5)
            stroke_color = SVGLoader._parse_color(elem.get('stroke', '#000000'), 1.0)
            stroke_width = float(elem.get('stroke-width', '1'))
            opacity = float(elem.get('opacity', '1.0'))

            return SVGElement(
                element_type='polygon',
                fill_color=fill_color,
                stroke_color=stroke_color,
                stroke_width=stroke_width,
                opacity=opacity,
                points=points
            )
        except Exception as e:
            logger.debug(f"Error parsing polygon: {e}")
            return None

    @staticmethod
    def _parse_polyline(elem: ET.Element) -> Optional[SVGElement]:
        """Парсить <polyline> элемент"""
        try:
            points_str = elem.get('points', '')
            if not points_str:
                return None

            points = SVGLoader._parse_points(points_str)
            if len(points) < 2:
                return None

            stroke_color = SVGLoader._parse_color(elem.get('stroke', '#000000'), 1.0)
            stroke_width = float(elem.get('stroke-width', '1'))
            opacity = float(elem.get('opacity', '1.0'))

            return SVGElement(
                element_type='polyline',
                stroke_color=stroke_color,
                stroke_width=stroke_width,
                opacity=opacity,
                points=points
            )
        except Exception as e:
            logger.debug(f"Error parsing polyline: {e}")
            return None

    @staticmethod
    def _parse_rect(elem: ET.Element) -> Optional[SVGElement]:
        """Парсить <rect> элемент"""
        try:
            x = float(elem.get('x', '0'))
            y = float(elem.get('y', '0'))
            width = float(elem.get('width', '100'))
            height = float(elem.get('height', '100'))

            fill_color = SVGLoader._parse_color(elem.get('fill', '#cccccc'), 0.5)
            stroke_color = SVGLoader._parse_color(elem.get('stroke', '#000000'), 1.0)
            stroke_width = float(elem.get('stroke-width', '1'))
            opacity = float(elem.get('opacity', '1.0'))

            return SVGElement(
                element_type='rect',
                fill_color=fill_color,
                stroke_color=stroke_color,
                stroke_width=stroke_width,
                opacity=opacity,
                rect_x=x,
                rect_y=y,
                rect_width=width,
                rect_height=height
            )
        except Exception as e:
            logger.debug(f"Error parsing rect: {e}")
            return None

    @staticmethod
    def _parse_circle(elem: ET.Element) -> Optional[SVGElement]:
        """Парсить <circle> элемент"""
        try:
            cx = float(elem.get('cx', '0'))
            cy = float(elem.get('cy', '0'))
            r = float(elem.get('r', '10'))

            fill_color = SVGLoader._parse_color(elem.get('fill', '#cccccc'), 0.5)
            stroke_color = SVGLoader._parse_color(elem.get('stroke', '#000000'), 1.0)
            stroke_width = float(elem.get('stroke-width', '1'))
            opacity = float(elem.get('opacity', '1.0'))

            return SVGElement(
                element_type='circle',
                fill_color=fill_color,
                stroke_color=stroke_color,
                stroke_width=stroke_width,
                opacity=opacity,
                center=(cx, cy),
                radius=r
            )
        except Exception as e:
            logger.debug(f"Error parsing circle: {e}")
            return None

    @staticmethod
    def _parse_ellipse(elem: ET.Element) -> Optional[SVGElement]:
        """Парсить <ellipse> элемент"""
        try:
            cx = float(elem.get('cx', '0'))
            cy = float(elem.get('cy', '0'))
            rx = float(elem.get('rx', '10'))
            ry = float(elem.get('ry', '5'))

            fill_color = SVGLoader._parse_color(elem.get('fill', '#cccccc'), 0.5)
            stroke_color = SVGLoader._parse_color(elem.get('stroke', '#000000'), 1.0)
            stroke_width = float(elem.get('stroke-width', '1'))
            opacity = float(elem.get('opacity', '1.0'))

            # Используем radius для хранения оххх... просто сохраним как точку и радиусы в path_data
            return SVGElement(
                element_type='ellipse',
                fill_color=fill_color,
                stroke_color=stroke_color,
                stroke_width=stroke_width,
                opacity=opacity,
                center=(cx, cy),
                radius=max(rx, ry),
                path_data=f"{rx},{ry}"  # Сохраняем оба радиуса
            )
        except Exception as e:
            logger.debug(f"Error parsing ellipse: {e}")
            return None

    @staticmethod
    def _parse_path(elem: ET.Element) -> Optional[SVGElement]:
        """Парсить <path> элемент"""
        try:
            path_data = elem.get('d', '')
            if not path_data:
                return None

            fill_color = SVGLoader._parse_color(elem.get('fill', 'none'), 0.5)
            stroke_color = SVGLoader._parse_color(elem.get('stroke', '#000000'), 1.0)
            stroke_width = float(elem.get('stroke-width', '1'))
            opacity = float(elem.get('opacity', '1.0'))

            return SVGElement(
                element_type='path',
                fill_color=fill_color,
                stroke_color=stroke_color,
                stroke_width=stroke_width,
                opacity=opacity,
                path_data=path_data
            )
        except Exception as e:
            logger.debug(f"Error parsing path: {e}")
            return None

    @staticmethod
    def _parse_color(color_str: str, default_alpha: float = 1.0) -> Tuple[float, float, float, float]:
        """
        Парсить цвет из SVG в формат Kivy (RGBA 0-1)

        Args:
            color_str: Цвет в формате #RRGGBB или rgb(r,g,b) или название цвета
            default_alpha: Альфа канал по умолчанию

        Returns:
            Кортеж (r, g, b, a) где каждое значение 0-1
        """
        # По умолчанию прозрачный черный
        default = (0.0, 0.0, 0.0, default_alpha)

        if not color_str or color_str.lower() == 'none':
            return (0, 0, 0, 0)

        # HEX формат
        if color_str.startswith('#'):
            try:
                hex_color = color_str.lstrip('#')
                if len(hex_color) == 6:
                    r = int(hex_color[0:2], 16) / 255.0
                    g = int(hex_color[2:4], 16) / 255.0
                    b = int(hex_color[4:6], 16) / 255.0
                    return (r, g, b, default_alpha)
                elif len(hex_color) == 8:
                    r = int(hex_color[0:2], 16) / 255.0
                    g = int(hex_color[2:4], 16) / 255.0
                    b = int(hex_color[4:6], 16) / 255.0
                    a = int(hex_color[6:8], 16) / 255.0
                    return (r, g, b, a)
            except:
                return default

        # RGB формат: rgb(255,128,0)
        if color_str.startswith('rgb'):
            try:
                match = re.match(r'rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)', color_str)
                if match:
                    r = int(match.group(1)) / 255.0
                    g = int(match.group(2)) / 255.0
                    b = int(match.group(3)) / 255.0
                    a = float(match.group(4)) if match.group(4) else default_alpha
                    return (r, g, b, a)
            except:
                return default

        # Названия цветов CSS
        color_names = {
            'black': (0, 0, 0, 1),
            'white': (1, 1, 1, 1),
            'red': (1, 0, 0, 1),
            'green': (0, 1, 0, 1),
            'blue': (0, 0, 1, 1),
            'gray': (0.5, 0.5, 0.5, 1),
            'grey': (0.5, 0.5, 0.5, 1),
            'lightgray': (0.8, 0.8, 0.8, 1),
            'lightgrey': (0.8, 0.8, 0.8, 1),
            'darkgray': (0.3, 0.3, 0.3, 1),
            'darkgrey': (0.3, 0.3, 0.3, 1),
            'yellow': (1, 1, 0, 1),
            'cyan': (0, 1, 1, 1),
            'magenta': (1, 0, 1, 1),
        }
        
        if color_str.lower() in color_names:
            color = color_names[color_str.lower()]
            return (color[0], color[1], color[2], default_alpha) if len(color) == 3 else color

        return default

    @staticmethod
    def _extract_floor_number(file_path: str) -> int:
        """Получить номер этажа из имени файла"""
        try:
            # Ищем паттерны: floor1, floor_1, etaj1, этаж1 и т.д.
            filename = Path(file_path).stem.lower()
            
            for pattern in ['floor', 'этаж', 'etaj', 'level']:
                if pattern in filename:
                    # Ищем число после паттерна
                    idx = filename.find(pattern)
                    after = filename[idx + len(pattern):]
                    for i, char in enumerate(after):
                        if char.isdigit():
                            number = int(after[i])
                            return number
            
            # По умолчанию этаж 1
            return 1

        except Exception as e:
            logger.warning(f"Could not extract floor number: {e}")
            return 1

    @staticmethod
    def _extract_rooms(root: ET.Element) -> List[SVGRoom]:
        """
        Извлечь комнаты из SVG

        Sweet Home 3D обычно использует:
        - <polygon> для комнат с fill цветом
        - <path> для стен
        - <text> для подписей комнат
        """
        rooms = []

        # Ищем все polygon элементы (обычно это комнаты в Sweet Home 3D)
        for polygon in root.findall('.//svg:polygon', SVGLoader.SVG_NS):
            try:
                points_str = polygon.get('points', '')
                if not points_str:
                    continue

                # Парсим координаты
                polygon_points = SVGLoader._parse_points(points_str)
                if len(polygon_points) < 3:
                    continue

                # Получаем цвет заливки
                fill = polygon.get('fill', '#cccccc')

                # Вычисляем центр полигона
                center_x = sum(p[0] for p in polygon_points) / len(polygon_points)
                center_y = sum(p[1] for p in polygon_points) / len(polygon_points)

                # Вычисляем приблизительную площадь (для справки)
                area = SVGLoader._calculate_polygon_area(polygon_points)

                # Пробуем получить имя из data-room-name или других атрибутов
                room_name = (
                    polygon.get('data-room-name') or
                    polygon.get('id') or
                    f"Room_{len(rooms) + 1}"
                )

                room = SVGRoom(
                    name=room_name,
                    polygon_points=polygon_points,
                    center_x=center_x,
                    center_y=center_y,
                    color=fill,
                    area=area
                )

                rooms.append(room)
                logger.debug(f"Extracted room: {room_name} at ({center_x:.1f}, {center_y:.1f})")

            except Exception as e:
                logger.warning(f"Error extracting polygon: {e}")
                continue

        # Альтернативно: ищем rectangles (некоторые экспортеры используют их)
        for rect in root.findall('.//svg:rect', SVGLoader.SVG_NS):
            try:
                x = float(rect.get('x', '0'))
                y = float(rect.get('y', '0'))
                width = float(rect.get('width', '100'))
                height = float(rect.get('height', '100'))

                # Исключаем маленькие элементы (вероятно стены)
                if width < 20 or height < 20:
                    continue

                polygon_points = [
                    (x, y),
                    (x + width, y),
                    (x + width, y + height),
                    (x, y + height)
                ]

                fill = rect.get('fill', '#cccccc')
                room_name = rect.get('id') or f"Room_{len(rooms) + 1}"

                room = SVGRoom(
                    name=room_name,
                    polygon_points=polygon_points,
                    center_x=x + width / 2,
                    center_y=y + height / 2,
                    color=fill,
                    area=width * height
                )

                rooms.append(room)

            except Exception as e:
                logger.warning(f"Error extracting rectangle: {e}")
                continue

        logger.info(f"Extracted {len(rooms)} rooms from SVG")
        return rooms

    @staticmethod
    def _parse_points(points_str: str) -> List[Tuple[float, float]]:
        """Парсить строку координат из SVG polygon points"""
        try:
            # Заменяем запятые на пробелы для единообразной обработки
            points_str = points_str.replace(',', ' ')

            # Разбиваем на части и конвертируем в float
            parts = [float(x) for x in points_str.split() if x.strip()]

            # Собираем в пары (x, y)
            points = [(parts[i], parts[i + 1]) for i in range(0, len(parts) - 1, 2)]

            return points

        except Exception as e:
            logger.error(f"Error parsing points: {e}")
            return []

    @staticmethod
    def _calculate_polygon_area(points: List[Tuple[float, float]]) -> float:
        """Вычислить площадь полигона используя формулу Шоелейса"""
        if len(points) < 3:
            return 0.0

        area = 0.0
        for i in range(len(points)):
            x1, y1 = points[i]
            x2, y2 = points[(i + 1) % len(points)]
            area += x1 * y2 - x2 * y1

        return abs(area) / 2.0

    @staticmethod
    def save_as_png(floor_plan: SVGFloorPlan, output_path: str, dpi: int = 96):
        """
        Сохранить SVG как PNG (требует cairosvg)

        Args:
            floor_plan: SVGFloorPlan объект
            output_path: Путь для сохранения PNG
            dpi: DPI для конверсии (96 - стандартный экран)
        """
        try:
            import cairosvg
        except ImportError:
            logger.error("cairosvg not installed. Install with: pip install cairosvg")
            logger.info("Alternatively, use an online SVG to PNG converter or Inkscape")
            return False

        try:
            cairosvg.svg2png(
                url=floor_plan.svg_path,
                write_to=output_path,
                dpi=dpi
            )
            logger.info(f"Saved PNG: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error converting SVG to PNG: {e}")
            return False

    @staticmethod
    def svg_to_canvas_instructions(floor_plan: SVGFloorPlan) -> str:
        """
        Получить инструкции Kivy Canvas для отрисовки SVG элементов

        Это попытка конвертировать SVG в Kivy Canvas инструкции
        """
        instructions = []

        # Фоновый цвет
        instructions.append(f"Color(1, 1, 1, 1)")
        instructions.append(f"Rectangle(size=({floor_plan.width}, {floor_plan.height}))")

        # Отрисовка комнат
        for room in floor_plan.rooms:
            # Парсим цвет
            rgb = SVGLoader._hex_to_rgb(room.color)
            instructions.append(f"Color({rgb[0]:.2f}, {rgb[1]:.2f}, {rgb[2]:.2f}, 0.3)")

            # Рисуем полигон (как набор треугольников)
            if len(room.polygon_points) >= 3:
                points = room.polygon_points
                # Простой способ: рисуем линию по периметру
                point_list = []
                for p in points:
                    point_list.extend(list(p))
                # Замыкаем полигон
                point_list.extend(list(points[0]))

                instructions.append(f"Line(points={point_list}, width=1)")

        return "\n".join(instructions)

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> Tuple[float, float, float]:
        """Конвертировать HEX цвет в RGB (0-1 диапазон)"""
        try:
            hex_color = hex_color.lstrip('#')
            if len(hex_color) == 6:
                r, g, b = [int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4)]
                return (r, g, b)
        except:
            pass

        # По умолчанию серый
        return (0.8, 0.8, 0.8)


class SVGFloorPlanManager:
    """Менеджер для управления коллекцией планов этажей"""

    def __init__(self, svg_folder: str):
        """
        Инициализировать менеджер

        Args:
            svg_folder: Папка с SVG файлами
        """
        self.svg_folder = svg_folder
        self.floor_plans: Dict[int, SVGFloorPlan] = {}

    def load_all_floor_plans(self):
        """Загрузить все SVG файлы из папки"""
        if not os.path.exists(self.svg_folder):
            logger.warning(f"SVG folder not found: {self.svg_folder}")
            return

        try:
            for filename in os.listdir(self.svg_folder):
                if filename.endswith('.svg'):
                    file_path = os.path.join(self.svg_folder, filename)
                    try:
                        floor_plan = SVGLoader.load_svg_file(file_path)
                        self.floor_plans[floor_plan.floor_number] = floor_plan
                    except Exception as e:
                        logger.error(f"Error loading {filename}: {e}")

            logger.info(f"Loaded {len(self.floor_plans)} floor plans")

        except Exception as e:
            logger.error(f"Error loading floor plans: {e}")

    def get_floor_plan(self, floor_number: int) -> Optional[SVGFloorPlan]:
        """Получить план определённого этажа"""
        return self.floor_plans.get(floor_number)

    def get_available_floors(self) -> List[int]:
        """Получить список доступных этажей"""
        return sorted(self.floor_plans.keys())
