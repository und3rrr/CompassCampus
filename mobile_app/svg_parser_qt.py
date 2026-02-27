from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QGraphicsView, QGraphicsScene, QComboBox, QVBoxLayout, QWidget, QLabel
from PyQt5.QtSvg import QGraphicsSvgItem, QSvgRenderer
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QColor, QPainter
import sys
import xml.etree.ElementTree as ET
import os
from pathlib import Path

class SvgParser:
    """
    SVG-парсер для извлечения информации о помещениях, стенах, объектах и т.д.
    Использует ElementTree для разбора SVG и QSvgRenderer для визуализации.
    """
    def __init__(self, svg_path):
        self.svg_path = svg_path
        self.tree = ET.parse(svg_path)
        self.root = self.tree.getroot()
        self.ns = {'svg': 'http://www.w3.org/2000/svg'}

    def get_rooms(self):
        """Вернуть список комнат (по <polygon> или <rect> с data-room-name)"""
        rooms = []
        for elem in self.root.findall('.//svg:polygon', self.ns):
            name = elem.attrib.get('data-room-name')
            if name:
                points = elem.attrib.get('points')
                rooms.append({'name': name, 'points': points})
        for elem in self.root.findall('.//svg:rect', self.ns):
            name = elem.attrib.get('data-room-name')
            if name:
                x = float(elem.attrib.get('x', 0))
                y = float(elem.attrib.get('y', 0))
                w = float(elem.attrib.get('width', 0))
                h = float(elem.attrib.get('height', 0))
                rooms.append({'name': name, 'rect': (x, y, w, h)})
        return rooms

    def get_doors(self):
        """Вернуть список дверей (по <rect> или <line> с data-door)"""
        doors = []
        for elem in self.root.findall('.//svg:rect', self.ns):
            if elem.attrib.get('data-door'):
                x = float(elem.attrib.get('x', 0))
                y = float(elem.attrib.get('y', 0))
                w = float(elem.attrib.get('width', 0))
                h = float(elem.attrib.get('height', 0))
                doors.append({'rect': (x, y, w, h)})
        for elem in self.root.findall('.//svg:line', self.ns):
            if elem.attrib.get('data-door'):
                x1 = float(elem.attrib.get('x1', 0))
                y1 = float(elem.attrib.get('y1', 0))
                x2 = float(elem.attrib.get('x2', 0))
                y2 = float(elem.attrib.get('y2', 0))
                doors.append({'line': (x1, y1, x2, y2)})
        return doors

    def get_walls(self):
        """Вернуть список стен (по <line> с data-wall)"""
        walls = []
        for elem in self.root.findall('.//svg:line', self.ns):
            if elem.attrib.get('data-wall'):
                x1 = float(elem.attrib.get('x1', 0))
                y1 = float(elem.attrib.get('y1', 0))
                x2 = float(elem.attrib.get('x2', 0))
                y2 = float(elem.attrib.get('y2', 0))
                walls.append({'line': (x1, y1, x2, y2)})
        return walls

class SvgViewer(QMainWindow):
    """
    Приложение для просмотра SVG планов этажей из assets/floor_plans.
    Автоматически сканирует папку и предоставляет выбор доступных планов.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SVG Парсер + QSvgRenderer")
        self.setGeometry(100, 100, 1200, 800)
        
        # Папка с планами
        self.plans_folder = Path(__file__).parent / "assets" / "floor_plans"
        self.current_svg = None
        self.parser = None
        
        # Основной виджет
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Выбор плана
        plan_label = QLabel("Выберите план этажа:")
        self.plan_combo = QComboBox()
        self.plan_combo.currentTextChanged.connect(self.on_plan_selected)
        layout.addWidget(plan_label)
        layout.addWidget(self.plan_combo)
        
        # Граф сцена
        self.view = QGraphicsView()
        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)
        self.view.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        layout.addWidget(self.view)
        
        # Загружаем доступные планы
        self.load_available_plans()

    def load_available_plans(self):
        """Сканировать assets/floor_plans и загрузить доступные SVG файлы"""
        if not self.plans_folder.exists():
            print(f"Папка планов не найдена: {self.plans_folder}")
            return
        
        svg_files = list(self.plans_folder.glob("*.svg"))
        if not svg_files:
            print(f"SVG файлы не найдены в {self.plans_folder}")
            return
        
        for svg_file in sorted(svg_files):
            self.plan_combo.addItem(svg_file.stem, str(svg_file))
        
        print(f"Загружено {len(svg_files)} планов: {[f.stem for f in svg_files]}")

    def on_plan_selected(self, plan_name):
        """Загрузить выбранный план"""
        if not plan_name:
            return
        
        svg_path = self.plan_combo.currentData()
        if not svg_path:
            return
        
        self.load_svg(svg_path)

    def load_svg(self, svg_path):
        """Загрузить и визуализировать SVG"""
        try:
            self.scene.clear()
            self.current_svg = svg_path
            self.parser = SvgParser(svg_path)
            
            # Парсим содержимое
            rooms = self.parser.get_rooms()
            doors = self.parser.get_doors()
            walls = self.parser.get_walls()
            
            print(f"\n=== План: {Path(svg_path).stem} ===")
            print(f"Комнаты ({len(rooms)}): {[r.get('name', 'N/A') for r in rooms]}")
            print(f"Двери: {len(doors)}")
            print(f"Стены: {len(walls)}")
            
            # Визуализируем SVG
            svg_item = QGraphicsSvgItem(svg_path)
            self.scene.addItem(svg_item)
            
            # Выделяем найденные комнаты
            for room in rooms:
                if 'rect' in room:
                    x, y, w, h = room['rect']
                    rect_item = self.scene.addRect(x, y, w, h, brush=QBrush(QColor(0,255,0,80)))
                    rect_item.setZValue(1)
                    
                    # Добавляем подпись комнаты
                    label = self.scene.addText(room.get('name', 'Room'))
                    label.setPos(x + w/2, y + h/2)
                    label.setZValue(2)
            
            # Показываем границы сцены
            rect = svg_item.boundingRect()
            self.scene.setSceneRect(rect)
            self.view.fitInView(rect, Qt.KeepAspectRatio)
            
        except Exception as e:
            print(f"Ошибка загрузки {svg_path}: {e}")

# Пример использования
if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = SvgViewer()
    viewer.show()
    sys.exit(app.exec_())
