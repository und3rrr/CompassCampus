"""
Улучшенный SVG парсер для извлечения информации о помещениях, дверях и стенах
Работает без внешних зависимостей (только встроенные модули)
"""
import xml.etree.ElementTree as ET
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# XML namespace для SVG
SVG_NS = {'svg': 'http://www.w3.org/2000/svg'}


@dataclass
class SvgRoom:
    """Представление комнаты из SVG"""
    name: str
    points: Optional[List[Tuple[float, float]]] = None
    rect: Optional[Tuple[float, float, float, float]] = None  # x, y, width, height
    id: Optional[str] = None
    color: Optional[str] = None


@dataclass
class SvgDoor:
    """Представление двери из SVG"""
    id: Optional[str] = None
    rect: Optional[Tuple[float, float, float, float]] = None  # x, y, width, height
    line: Optional[Tuple[float, float, float, float]] = None  # x1, y1, x2, y2
    

@dataclass
class SvgWall:
    """Представление стены из SVG"""
    id: Optional[str] = None
    line: Tuple[float, float, float, float]  # x1, y1, x2, y2


class SvgParser:
    """
    Парсер SVG для извлечения информации о помещениях, дверях, стенах и объектах
    Использует ElementTree для разбора SVG
    """
    
    def __init__(self, svg_path: str):
        """
        Инициализировать парсер SVG файла
        
        Args:
            svg_path: Путь к SVG файлу
        """
        self.svg_path = svg_path
        self.tree = None
        self.root = None
        self.width = 1000
        self.height = 800
        
        try:
            self.tree = ET.parse(svg_path)
            self.root = self.tree.getroot()
            
            # Извлекаем размеры
            self.width = float(self.root.attrib.get('width', 1000))
            self.height = float(self.root.attrib.get('height', 800))
            
        except Exception as e:
            logger.error(f"Error parsing SVG file {svg_path}: {e}")

    def get_rooms(self) -> List[SvgRoom]:
        """
        Вернуть список комнат (по <polygon>, <rect> или <g> с data-room-name атрибутом)
        
        Returns:
            Список SvgRoom объектов
        """
        if not self.root:
            return []
            
        rooms = []
        
        # Ищем polygon элементы с data-room-name
        for elem in self.root.findall('.//svg:polygon', SVG_NS):
            name = elem.attrib.get('data-room-name')
            if name:
                points = self._parse_points(elem.attrib.get('points', ''))
                room = SvgRoom(
                    name=name,
                    points=points,
                    id=elem.attrib.get('id'),
                    color=elem.attrib.get('fill')
                )
                rooms.append(room)
        
        # Ищем rect элементы с data-room-name
        for elem in self.root.findall('.//svg:rect', SVG_NS):
            name = elem.attrib.get('data-room-name')
            if name:
                rect = (
                    float(elem.attrib.get('x', 0)),
                    float(elem.attrib.get('y', 0)),
                    float(elem.attrib.get('width', 0)),
                    float(elem.attrib.get('height', 0))
                )
                room = SvgRoom(
                    name=name,
                    rect=rect,
                    id=elem.attrib.get('id'),
                    color=elem.attrib.get('fill')
                )
                rooms.append(room)
        
        # Ищем group элементы с data-room-name
        for elem in self.root.findall('.//svg:g', SVG_NS):
            name = elem.attrib.get('data-room-name')
            if name:
                # Пытаемся извлечь информацию о комнате из дочерних элементов
                room = SvgRoom(
                    name=name,
                    id=elem.attrib.get('id')
                )
                rooms.append(room)
        
        logger.debug(f"Found {len(rooms)} rooms in SVG")
        return rooms

    def get_doors(self) -> List[SvgDoor]:
        """
        Вернуть список дверей (по <rect> или <line> с data-door атрибутом)
        
        Returns:
            Список SvgDoor объектов
        """
        if not self.root:
            return []
            
        doors = []
        
        # Ищем rect элементы с data-door
        for elem in self.root.findall('.//svg:rect', SVG_NS):
            if elem.attrib.get('data-door'):
                rect = (
                    float(elem.attrib.get('x', 0)),
                    float(elem.attrib.get('y', 0)),
                    float(elem.attrib.get('width', 0)),
                    float(elem.attrib.get('height', 0))
                )
                door = SvgDoor(
                    id=elem.attrib.get('id'),
                    rect=rect
                )
                doors.append(door)
        
        # Ищем line элементы с data-door
        for elem in self.root.findall('.//svg:line', SVG_NS):
            if elem.attrib.get('data-door'):
                line = (
                    float(elem.attrib.get('x1', 0)),
                    float(elem.attrib.get('y1', 0)),
                    float(elem.attrib.get('x2', 0)),
                    float(elem.attrib.get('y2', 0))
                )
                door = SvgDoor(
                    id=elem.attrib.get('id'),
                    line=line
                )
                doors.append(door)
        
        logger.debug(f"Found {len(doors)} doors in SVG")
        return doors

    def get_walls(self) -> List[SvgWall]:
        """
        Вернуть список стен (по <line> с data-wall атрибутом)
        
        Returns:
            Список SvgWall объектов
        """
        if not self.root:
            return []
            
        walls = []
        
        # Ищем line элементы с data-wall
        for elem in self.root.findall('.//svg:line', SVG_NS):
            if elem.attrib.get('data-wall'):
                line = (
                    float(elem.attrib.get('x1', 0)),
                    float(elem.attrib.get('y1', 0)),
                    float(elem.attrib.get('x2', 0)),
                    float(elem.attrib.get('y2', 0))
                )
                wall = SvgWall(
                    id=elem.attrib.get('id'),
                    line=line
                )
                walls.append(wall)
        
        logger.debug(f"Found {len(walls)} walls in SVG")
        return walls

    def get_dimensions(self) -> Tuple[float, float]:
        """
        Получить размеры SVG документа
        
        Returns:
            Кортеж (width, height)
        """
        return (self.width, self.height)

    @staticmethod
    def _parse_points(points_str: str) -> List[Tuple[float, float]]:
        """
        Распарсить строку points из polygon элемента
        
        Args:
            points_str: Строка с координатами, например "100,100 200,100 200,200 100,200"
            
        Returns:
            Список кортежей (x, y)
        """
        if not points_str:
            return []
        
        points = []
        try:
            # Разделяем по пробелам и запятым
            pairs = re.findall(r'([-\d.]+,[-\d.]+)', points_str)
            for pair in pairs:
                coords = pair.split(',')
                if len(coords) == 2:
                    points.append((float(coords[0]), float(coords[1])))
        except Exception as e:
            logger.warning(f"Error parsing points: {e}")
        
        return points


class SvgParserFactory:
    """Фабрика для создания парсеров и управления ими"""
    
    @staticmethod
    def create_parser(svg_path: str) -> Optional[SvgParser]:
        """
        Создать парсер для SVG файла
        
        Args:
            svg_path: Путь к SVG файлу
            
        Returns:
            SvgParser объект или None если файл не найден
        """
        if not Path(svg_path).exists():
            logger.error(f"SVG file not found: {svg_path}")
            return None
        
        try:
            return SvgParser(svg_path)
        except Exception as e:
            logger.error(f"Error creating SVG parser: {e}")
            return None

    @staticmethod
    def parse_floor_plan(svg_path: str) -> Optional[Dict]:
        """
        Распарсить план этажа из SVG файла и вернуть словарь с информацией
        
        Args:
            svg_path: Путь к SVG файлу
            
        Returns:
            Словарь с информацией о плане этажа или None
        """
        parser = SvgParserFactory.create_parser(svg_path)
        if not parser:
            return None
        
        width, height = parser.get_dimensions()
        
        return {
            'path': str(svg_path),
            'width': width,
            'height': height,
            'rooms': [
                {
                    'name': room.name,
                    'id': room.id,
                    'color': room.color,
                    'points': room.points,
                    'rect': room.rect
                }
                for room in parser.get_rooms()
            ],
            'doors': [
                {
                    'id': door.id,
                    'rect': door.rect,
                    'line': door.line
                }
                for door in parser.get_doors()
            ],
            'walls': [
                {
                    'id': wall.id,
                    'line': wall.line
                }
                for wall in parser.get_walls()
            ]
        }
