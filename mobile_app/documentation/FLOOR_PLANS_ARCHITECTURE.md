"""
Архитектура интеграции SVG/PNG планов этажей в CampusCompass
Как все компоненты работают вместе
"""

# =============================================================================
# ДИАГРАММА ПОТОКА ДАННЫХ
# =============================================================================

"""
┌─────────────────────────────────────────────────────────────────────────┐
│                    CAMPUSCOMPASS FLOOR PLANS INTEGRATION                 │
└─────────────────────────────────────────────────────────────────────────┘

     ┌──────────────────────────────────────────┐
     │     Sweet Home 3D / CAD Tools            │
     │                                          │
     │  Экспортирует план в SVG                │
     └──────────────┬───────────────────────────┘
                    │
                    ▼
     ┌──────────────────────────────────────┐
     │  assets/floor_plans/                  │
     │  ├── floor1.svg                      │
     │  ├── floor2.svg                      │
     │  └── floor3.png                      │
     └──────────────┬───────────────────────┘
                    │
                    ▼
     ┌──────────────────────────────────────┐
     │  FloorPlanManager                    │
     │                                      │
     │  1. Сканирует folder               │
     │  2. Определяет номер этажа          │
     │  3. Кэширует пути                   │
     │  4. Преобразует SVG → PNG           │
     └──────────────┬───────────────────────┘
                    │
                    ▼
     ┌──────────────────────────────────────┐
     │  SVGLoader                           │
     │                                      │
     │  1. Парсит SVG файлы                │
     │  2. Извлекает комнаты (polygon)     │
     │  3. Вычисляет координаты комнат     │
     │  4. Сохраняет как PNG (опционально) │
     └──────────────┬───────────────────────┘
                    │
         ┌──────────┴──────────┐
         ▼                     ▼
    ┌─────────────┐  ┌───────────────┐
    │  PNG/JPG    │  │ SVG (парсед)  │
    │  файлы      │  │ в памяти      │
    └──────┬──────┘  └────────┬──────┘
           │                  │
           └──────────┬───────┘
                      ▼
     ┌──────────────────────────────────────┐
     │  MapScreen._update_map_display()     │
     │                                      │
     │  При изменении этажа:               │
     │  1. Получить файл плана              │
     │  2. Передать в MapWidget             │
     └──────────────┬───────────────────────┘
                    │
                    ▼
     ┌──────────────────────────────────────┐
     │  MapWidget.set_background_image()    │
     │                                      │
     │  Сохранить путь к изображению       │
     └──────────────┬───────────────────────┘
                    │
                    ▼
     ┌──────────────────────────────────────┐
     │  MapWidget._update_canvas()          │
     │                                      │
     │  Отрисовка в порядке:               │
     │  1. Белый фон                        │
     │  2. PNG/SVG план (Rectangle)        │
     │  3. Рёбра графа (Line)              │
     │  4. Маршруты (Line)                 │
     │  5. Узлы (Circle)                   │
     └──────────────┬───────────────────────┘
                    │
                    ▼
     ┌──────────────────────────────────────┐
     │         ЭКРАН ПОЛЬЗОВАТЕЛЯ           │
     │                                      │
     │  [План этажа с узлами сверху]       │
     │  [Маршруты между узлами]            │
     │  [Интерактивные элементы]           │
     └──────────────────────────────────────┘
"""

# =============================================================================
# КОМПОНЕНТЫ СИСТЕМЫ
# =============================================================================

"""
1. FLOOR PLANS (файлы на диске)
   └── assets/floor_plans/
       ├── floor1.svg (вектор)
       ├── floor2.png (растр)
       └── floor3.jpg (сжатый растр)

2. SVGLOADER (сервис парсинга)
   ├── Читает SVG файл (XML)
   ├── Извлекает элементы:
   │   ├── Polygons (комнаты)
   │   ├── Lines (стены)
   │   └── Text (подписи)
   ├── Вычисляет координаты центров комнат
   └── Экспортирует в PNG если нужно

3. FLOORPLANMANAGER (менеджер коллекции)
   ├── Сканирует assets/floor_plans/
   ├── Определяет номера этажей из имён файлов
   ├── Кэширует пути в памяти
   ├── Возвращает нужный файл по номеру этажа
   └── Конвертирует SVG → PNG при необходимости

4. MAPSCREEN (UI контроллер)
   ├── Инициализирует FloorPlanManager
   ├── При выборе этажа (spinener изменение):
   │   ├── Получает файл плана от менеджера
   │   ├── Устанавливает фон в MapWidget
   │   ├── Фильтрует узлы по этажу
   │   └── Обновляет дисплей
   └── Обновляет при изменении зданий/этажей

5. MAPWIDGET (рендерер карты)
   ├── Хранит справку на фоновое изображение
   ├── При _update_canvas():
   │   ├── Рисует белый фон
   │   ├── Если background_image_path установлен:
   │   │   └── Рисует Rectangle(source=image)
   │   ├── Рисует рёбра графа (Line)
   │   ├── Рисует маршруты (Line)
   │   └── Рисует узлы (Circle)
   ├── Поддерживает масштабирование (zoom)
   ├── Поддерживает панорамирование (pan)
   └── Прозрачность регулируется (opacity)
"""

# =============================================================================
# ПОТОК ВЫПОЛНЕНИЯ ПРИ ОТКРЫТИИ ЭКРАНА КАРТЫ
# =============================================================================

"""
1. MapScreen.__init__()
   ↓
   ├─→ Инициализировать FloorPlanManager
   ├─→ Создать MapWidget
   └─→ Установить callback на floor_spinner.bind(text=self.on_floor_changed)

2. on_building_selected(building)
   ↓
   ├─→ Установить self.building = building
   ├─→ Обновить spinner values (список этажей здания)
   └─→ Вызвать _update_map_display()

3. on_floor_changed(spinner, text) → вызывает _update_map_display()
   ↓
   ├─→ Получить current_floor из spinner
   ├─→ Отфильтровать узлы по этажу
   │
   ├─→ ✨ NEW STUFF ✨
   ├─→ FloorPlanManager.get_plan_file(current_floor)
   │   └─→ Возвращает путь к файлу плана или None
   │
   ├─→ if plan_file:
   │   └─→ MapWidget.set_background_image(plan_file)
   │       └─→ Сохраняет путь в self.background_image_path
   │
   ├─→ Иначе: MapWidget.set_background_image(None)
   │   └─→ Очищает fон (остаётся только белый)
   │
   ├─→ GraphBuilder.build_edges_from_nodes()
   ├─→ MapWidget.set_edges(floor_edges)
   │
   └─→ MapWidget._update_canvas()
       (автоматически вызывается из set_edges)
"""

# =============================================================================
# ОТРИСОВКА CANVAS
# =============================================================================

"""
MapWidget._update_canvas():

    with self.canvas:
        # 1. Белый фон
        Color(1, 1, 1, 1)
        Rectangle(pos=self.pos, size=self.size)
        
        # 2. ✨ NEW: Фоновое изображение план этажа ✨
        if self.background_enabled and self.background_image_path:
            Color(1, 1, 1, self.background_opacity)  # Прозрачность
            
            if self.background_image_path.endswith(('.png', '.jpg')):
                Rectangle(source=self.background_image_path,
                         pos=self.pos, size=self.size)
            
            elif self.background_image_path.endswith('.svg'):
                # SVG требует преобразования в PNG для Kivy
                png_path = self.background_image_path.replace('.svg', '.png')
                if os.path.exists(png_path):
                    Rectangle(source=png_path, ...)
        
        # 3. Рёбра (серые линии)
        Color(0.7, 0.7, 0.7, 0.5)
        for edge in edges:
            Line(points=[...], width=2)
        
        # 4. Закрытые маршруты (красные линии)
        Color(1.0, 0.0, 0.0, 0.7)
        for closed_edge in closed_edges:
            Line(points=[...], width=4)
        
        # 5. Маршрут (зелёная линия)
        if route:
            Color(0.2, 0.8, 0.2, 0.7)
            Line(points=[...], width=4)
        
        # 6. Узлы (círculos)
        for node in nodes:
            if node.id in closed_nodes:
                Color(1.0, 0.0, 0.0, 1.0)  # Красный
            elif node == start_node:
                Color(0.2, 1.0, 0.2, 1.0)  # Зелёный
            elif node == end_node:
                Color(0.2, 0.8, 1.0, 1.0)  # Голубой
            elif node == selected_node:
                Color(1.0, 1.0, 0.0, 1.0)  # Жёлтый
            else:
                Color(*node_color)  # По типу
            
            Ellipse(pos=..., size=...)
"""

# =============================================================================
# КООРДИНАТНЫЕ СИСТЕМЫ
# =============================================================================

"""
Есть несколько координатных систем:

1. WORLD COORDINATES (граф узлов)
   ├─ Origine в левом нижнем углу
   ├─ Определены в данных узлов (node.x, node.y)
   ├─ Независимы от размера экрана
   └─ Используются для расчёта маршрутов

2. SCREEN COORDINATES (экран)
   ├─ Origine в левом нижнем углу Kivy widget
   ├─ (0, 0) = левый нижний угол
   ├─ (width, height) = правый верхний угол
   └─ Используются для отрисовки canvas

3. SVG COORDINATES (если используется use_svg_coordinates=True)
   ├─ Из файла SVG
   ├─ Обычно origen в верхнем левом углу
   └─ Опциональное преобразование координат

Преобразование:
    
    World → Screen:
    screen_x = (world_x * zoom) + pan_x
    screen_y = (world_y * zoom) + pan_y
    
    Screen → World:
    world_x = (screen_x - pan_x) / zoom
    world_y = (screen_y - pan_y) / zoom

План этажа (PNG/SVG):
    ├─ Масштабируется под размер widget
    ├─ Rectangle(source=..., pos=self.pos, size=self.size)
    └─ Автоматически заполняет весь widget
"""

# =============================================================================
# ИНТЕГРАЦИЯ С СУЩЕСТВУЮЩИМ КОДОМ
# =============================================================================

"""
✅ MapWidget:
   ├─ Работает как раньше (100% backward compatible)
   ├─ Добавлены новые методы:
   │  ├─ set_background_image()
   │  ├─ set_background_opacity()
   │  ├─ set_background_enabled()
   │  ├─ load_floor_plan_from_svg()
   │  └─ convert_svg_to_png()
   └─ При set_nodes() и set_edges() работает как раньше

✅ MapScreen:
   ├─ Инициализирует FloorPlanManager
   ├─ В _update_map_display() добавлена загрузка плана
   └─ Остальной код не изменился

✅ APIClient:
   └─ Используется как раньше (no changes)

✅ GraphBuilder:
   └─ Используется как раньше (no changes)

✅ Сервисы:
   ├─ SVGLoader - новый
   └─ FloorPlanManager - новый
   
   Оба опциональны! Если и не используются, код работает без них.
"""

# =============================================================================
# КОНВЕРСИЯ SVG → PNG
# =============================================================================

"""
Если установлен cairosvg:

    FloorPlanManager.convert_svg_to_png(floor_number=1)
    
    ↓
    
    SVGLoader.load_svg_file('floor1.svg')
    ↓
    SVGLoader.save_as_png(floor_plan, 'floor1.png', dpi=96)
    ↓
    cairosvg.svg2png(url='floor1.svg', write_to='floor1.png')
    ↓
    Результат: floor1.png (растровое изображение)
    
При следующей загрузке:
    FloorPlanManager.get_plan_file(1)
    ↓
    Сначала будет возвращен floor1.svg
    Но если нужен PNG - MapWidget проверит exists('floor1.png')
    ↓
    MapWidget.set_background_image() → использует PNG если есть
"""

# =============================================================================
# ПРОИЗВОДИТЕЛЬНОСТЬ
# =============================================================================

"""
Timeline (примерно времени):

1. Инициализация приложения:
   ├─ FloorPlanManager.__init__() - 1ms
   └─ FloorPlanManager.scan_folder() - 10-50ms (в зависимости от числа файлов)

2. При выборе здания:
   └─ FloorPlanManager.get_available_floors() - <1ms (из кэша)

3. При выборе этажа:
   ├─ FloorPlanManager.get_plan_file(floor) - <1ms (из кэша)
   ├─ MapWidget.set_background_image() - <1ms (сохранить в памяти)
   ├─ Фильтр узлов K... - 10-50ms (зависит от количества узлов)
   ├─ Построение edges - 50-200ms (для 100+ узлов)
   └─ Отрисовка canvas - 16-33ms (60 FPS)

4. При перемещении/масштабировании:
   └─ _update_canvas() - 16-33ms (60 FPS)

Загрузка изображений:
   ├─ PNG из памяти - <1ms (Kivy кэширует)
   ├─ SVG парсинг - 100-300ms в зависимости от сложности
   └─ PNG парсинг - <10ms

Итого первый раз при выборе этажа: ~250-500ms
Итого последующие разы: ~50-100ms (из кэша)
"""

# =============================================================================
# ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ API
# =============================================================================

# Пример 1: Простой способ
# ========================
from services.floor_plan_manager import FloorPlanManager

manager = FloorPlanManager()
plan_file = manager.get_plan_file(floor_number=1)
if plan_file:
    mapwidget.set_background_image(plan_file)


# Пример 2: С обработкой ошибок
# ===============================
try:
    if manager.has_plan(floor_number):
        plan_file = manager.get_plan_file(floor_number)
        mapwidget.set_background_image(plan_file)
        mapwidget.set_background_opacity(0.8)
    else:
        mapwidget.set_background_image(None)  # Без фона
except Exception as e:
    logger.error(f"Error loading floor plan: {e}")
    mapwidget.set_background_image(None)


# Пример 3: С конверсией SVG → PNG
# ==================================
plan_file = manager.get_plan_file(floor_number)
if plan_file.endswith('.svg'):
    # Конвертировать при первой загрузке
    manager.convert_svg_to_png(floor_number)
    # Потом будет использован PNG


# Пример 4: Управление видимостью
# =================================
# Показать фон
mapwidget.set_background_enabled(True)
mapwidget.set_background_opacity(1.0)

# Скрыть фон (только узлы)
mapwidget.set_background_enabled(False)

# Полупрозрачный фон
mapwidget.set_background_enabled(True)
mapwidget.set_background_opacity(0.5)
"""
