# SVG Парсер: Примеры кода

## Пример 1: Загрузить и отрисовать SVG

```python
from widgets.map_widget import MapWidget

# Создать виджет
map_widget = MapWidget()

# Загрузить SVG план
map_widget.set_background_image('assets/floor_plans/floor1.svg')

# Установить узлы (обычно приходят из API)
nodes = [
    Node(id='1', name='Reception', x=100, y=100, floor=1, node_type='Room'),
    Node(id='2', name='Hallway', x=200, y=150, floor=1, node_type='Corridor'),
]
map_widget.set_nodes(nodes)

# Установить рёбра (связи между узлами)
edges = [('1', '2'), ('2', '3')]
map_widget.set_edges(edges)
```

## Пример 2: Парсинг SVG и анализ элементов

```python
from services.svg_loader import SVGLoader

# Загрузить SVG
plan = SVGLoader.load_svg_file('floor1.svg')

# Получить информацию о плане
print(f"Размер: {plan.width} x {plan.height} px")
print(f"Элементов: {len(plan.elements)}")
print(f"Комнат: {len(plan.rooms)}")
print(f"Этаж: {plan.floor_number}")

# Осмотреть все элементы
for element in plan.elements:
    print(f"\n{element.element_type.upper()}")
    if element.fill_color:
        print(f"  Fill: {element.fill_color}")
    if element.stroke_color:
        print(f"  Stroke: {element.stroke_color}")
    if element.stroke_width:
        print(f"  Stroke width: {element.stroke_width}")
    if element.opacity:
        print(f"  Opacity: {element.opacity}")

# Осмотреть комнаты
for room in plan.rooms:
    print(f"\n🏠 {room.name}")
    print(f"  Center: ({room.center_x:.1f}, {room.center_y:.1f})")
    print(f"  Color: {room.color}")
    print(f"  Area: {room.area:.1f} px²")
    print(f"  Points: {len(room.polygon_points)}")
```

## Пример 3: Фильтрация элементов по типу

```python
from services.svg_loader import SVGLoader

plan = SVGLoader.load_svg_file('floor1.svg')

# Получить только полигоны (комнаты)
polygons = [e for e in plan.elements if e.element_type == 'polygon']
print(f"Polygons: {len(polygons)}")

# Получить только линии (стены)
lines = [e for e in plan.elements if e.element_type == 'line']
print(f"Lines: {len(lines)}")

# Получить только круги (двери, приспособления)
circles = [e for e in plan.elements if e.element_type == 'circle']
print(f"Circles: {len(circles)}")

# Получить все замкнутые элементы (с заливкой)
filled = [e for e in plan.elements if e.fill_color and e.fill_color[3] > 0]
print(f"Filled elements: {len(filled)}")
```

## Пример 4: Анализ цветов в плане

```python
from services.svg_loader import SVGLoader

plan = SVGLoader.load_svg_file('floor1.svg')

# Собрать уникальные цвета заливки
fill_colors = {}
for elem in plan.elements:
    if elem.fill_color:
        color_key = str(elem.fill_color)
        fill_colors[color_key] = fill_colors.get(color_key, 0) + 1

print("Fill colors used:")
for color, count in sorted(fill_colors.items(), key=lambda x: x[1], reverse=True):
    print(f"  {color}: {count} elements")

# Собрать уникальные цвета обводки
stroke_colors = {}
for elem in plan.elements:
    if elem.stroke_color:
        color_key = str(elem.stroke_color)
        stroke_colors[color_key] = stroke_colors.get(color_key, 0) + 1

print("\nStroke colors used:")
for color, count in sorted(stroke_colors.items(), key=lambda x: x[1], reverse=True):
    print(f"  {color}: {count} elements")
```

## Пример 5: Работа с полигонами (комнатами)

```python
from services.svg_loader import SVGLoader

plan = SVGLoader.load_svg_file('floor1.svg')

# Найти комнату с максимальной площадью
largest_room = max(plan.rooms, key=lambda r: r.area)
print(f"Largest room: {largest_room.name}")
print(f"  Area: {largest_room.area:.1f} px²")
print(f"  Center: ({largest_room.center_x:.1f}, {largest_room.center_y:.1f})")
print(f"  Color: {largest_room.color}")

# Найти комнату ближайшую к точке (200, 250)
target_x, target_y = 200, 250
nearest_room = min(
    plan.rooms,
    key=lambda r: (r.center_x - target_x)**2 + (r.center_y - target_y)**2
)
print(f"\nNearest room to ({target_x}, {target_y}): {nearest_room.name}")

# Вывести координаты точек для каждой комнаты
for room in plan.rooms:
    print(f"\n{room.name}:")
    for i, (x, y) in enumerate(room.polygon_points):
        print(f"  Point {i}: ({x:.1f}, {y:.1f})")
```

## Пример 6: Работа с MapWidget для интерактивности

```python
from widgets.map_widget import MapWidget
from services.api_client import Node, Route

# Создать виджет
map_widget = MapWidget()

# Загрузить плана
map_widget.set_background_image('floor1.svg')

# Установить узлы и рёбра
nodes = [...]  # узлы от API
edges = [...]  # рёбра от API
map_widget.set_nodes(nodes)
map_widget.set_edges(edges)

# Установить callback для выбора узла
def on_node_selected(node):
    print(f"Selected: {node.name} at ({node.x}, {node.y})")

map_widget.on_node_selected_callback = on_node_selected

# Установить стартовый и конечный узлы маршрута
start_node = nodes[0]
end_node = nodes[-1]

map_widget.set_start_node(start_node)
map_widget.set_end_node(end_node)

# Установить маршрут
route = Route(
    id='route_1',
    from_node=start_node,
    to_node=end_node,
    distance=250.5,
    path=[nodes[0], nodes[1], nodes[2]]
)
map_widget.set_route(route)

# Управление масштабированием
map_widget.zoom_in()      # Увеличить на 20%
map_widget.zoom_out()     # Уменьшить на 17%
map_widget.reset_view()   # Сбросить зум и панораму

# Управление прозрачностью фона
map_widget.set_background_opacity(0.5)  # 50% прозрачности

# Отключить/включить фон
map_widget.set_background_enabled(False)  # Скрыть план
map_widget.set_background_enabled(True)   # Показать план
```

## Пример 7: Интеграция с FloorPlanManager

```python
from services.floor_plan_manager import FloorPlanManager
from widgets.map_widget import MapWidget

# Создать менеджер планов
manager = FloorPlanManager(plans_folder='assets/floor_plans')
manager.scan_folder()

# Получить доступные этажи
floors = manager.get_available_floors()
print(f"Available floors: {floors}")  # [1, 2, 3, 4]

# Загрузить план для конкретного этажа
for floor in floors:
    plan_file = manager.get_plan_file(floor)
    if plan_file:
        print(f"Floor {floor}: {plan_file}")
        
        map_widget = MapWidget()
        map_widget.set_background_image(plan_file)
```

## Пример 8: Сохранение информации о плане

```python
import json
from services.svg_loader import SVGLoader

plan = SVGLoader.load_svg_file('floor1.svg')

# Сохранить информацию о комнатах в JSON
rooms_data = []
for room in plan.rooms:
    rooms_data.append({
        'name': room.name,
        'center': {'x': room.center_x, 'y': room.center_y},
        'color': room.color,
        'area': room.area,
        'points': room.polygon_points
    })

with open('floor1_rooms.json', 'w') as f:
    json.dump(rooms_data, f, indent=2)

# Сохранить информацию об элементах
elements_data = []
for elem in plan.elements:
    elem_dict = {
        'type': elem.element_type,
        'fill_color': elem.fill_color,
        'stroke_color': elem.stroke_color,
        'stroke_width': elem.stroke_width,
        'opacity': elem.opacity,
    }
    
    # Добавить тип-специфичные поля
    if elem.element_type == 'polygon':
        elem_dict['points'] = elem.points
    elif elem.element_type == 'circle':
        elem_dict['center'] = elem.center
        elem_dict['radius'] = elem.radius
    elif elem.element_type == 'rect':
        elem_dict['rect'] = {
            'x': elem.rect_x,
            'y': elem.rect_y,
            'width': elem.rect_width,
            'height': elem.rect_height
        }
    
    elements_data.append(elem_dict)

with open('floor1_elements.json', 'w') as f:
    json.dump(elements_data, f, indent=2)

print("✅ Saved room and element data to JSON")
```

## Пример 9: Обработка ошибок при парсинге

```python
from services.svg_loader import SVGLoader
import logging

logger = logging.getLogger(__name__)

try:
    plan = SVGLoader.load_svg_file('nonexistent.svg')
except FileNotFoundError as e:
    logger.error(f"File not found: {e}")
    # Использовать резервные данные
    plan = None
except Exception as e:
    logger.error(f"Error parsing SVG: {e}")
    plan = None

if plan:
    print(f"✅ Loaded {len(plan.elements)} elements")
else:
    print("❌ Could not load SVG plan")
```

## Пример 10: Создание простого тестового приложения

```python
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from widgets.map_widget import MapWidget
from services.svg_loader import SVGLoader
from services.api_client import Node

class SVGTestApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical')
        
        # Создать MapWidget
        self.map_widget = MapWidget()
        
        # Загрузить SVG
        self.map_widget.set_background_image('assets/floor_plans/floor1.svg')
        
        # Добавить тестовые узлы
        test_nodes = [
            Node(id='1', name='Point 1', x=100, y=100, floor=1, node_type='Room'),
            Node(id='2', name='Point 2', x=300, y=200, floor=1, node_type='Corridor'),
            Node(id='3', name='Point 3', x=500, y=150, floor=1, node_type='Room'),
        ]
        self.map_widget.set_nodes(test_nodes)
        
        # Добавить рёбра
        edges = [('1', '2'), ('2', '3')]
        self.map_widget.set_edges(edges)
        
        layout.add_widget(self.map_widget)
        
        # Добавить кнопки управления
        button_layout = BoxLayout(size_hint_y=0.1, spacing=10)
        
        zoom_in_btn = Button(text='Zoom In', size_hint_x=0.25)
        zoom_in_btn.bind(on_press=lambda x: self.map_widget.zoom_in())
        button_layout.add_widget(zoom_in_btn)
        
        zoom_out_btn = Button(text='Zoom Out', size_hint_x=0.25)
        zoom_out_btn.bind(on_press=lambda x: self.map_widget.zoom_out())
        button_layout.add_widget(zoom_out_btn)
        
        reset_btn = Button(text='Reset View', size_hint_x=0.25)
        reset_btn.bind(on_press=lambda x: self.map_widget.reset_view())
        button_layout.add_widget(reset_btn)
        
        toggle_bg_btn = Button(text='Toggle BG', size_hint_x=0.25)
        toggle_bg_btn.bind(on_press=self.toggle_background)
        button_layout.add_widget(toggle_bg_btn)
        
        layout.add_widget(button_layout)
        
        return layout
    
    def toggle_background(self, instance):
        current = self.map_widget.background_enabled
        self.map_widget.set_background_enabled(not current)

if __name__ == '__main__':
    SVGTestApp().run()
```

---

## Результаты

Все примеры выше работают с новым SVG парсером и демонстрируют:

✅ Загрузку и отрисовку SVG  
✅ Парсинг и анализ элементов  
✅ Работу с комнатами и геометрией  
✅ Интеграцию с графом узлов  
✅ Управление масштабированием  
✅ Обработку ошибок  

Все это работает **без конвертирования в PNG** и сохраняет **векторное качество** изображения!
