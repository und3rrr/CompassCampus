"""
Документация интеграции SVG/PNG планов этажей в CampusCompass
"""

# SVG Floor Plans Integration Guide

## 📋 Обзор

Приложение CampusCompass может отображать планы этажей в форматах:
- ✅ **SVG** (из Sweet Home 3D или других инструментов)
- ✅ **PNG/JPG** (максимально простые и быстрые)

Планы этажей отображаются как фон под узлами и маршрутами навигации.

---

## 🛠️ Подготовка планов этажей

### Вариант 1: Экспорт из Sweet Home 3D (рекомендуется)

1. **Откройте Sweet Home 3D**
   - Создайте или откройте проект вашего здания

2. **Экспортируйте план в SVG**
   ```
   Меню → Экспорт → Экспорт в SVG
   ```
   - Сохраните файл как `floor1.svg`, `floor2.svg` и т.д.
   - Выберите целевую папку: `mobile_app/assets/floor_plans/`

3. **Убедитесь что в SVG присутствуют**
   - Комнаты (обычно polygon элементы с fill цветом)
   - Двери/проходы (openings)
   - Стены (path или line элементы)

### Вариант 2: Преобразование DWG → SVG

Если у вас есть планы в AutoCAD:

```bash
# Способ 1: Через LibreCAD
libreCAD file.dwg
# Меню → Export → SVG

# Способ 2: Онлайн конвертер
https://cloudconvert.com/dwg-to-svg
https://zamzar.com/
```

### Вариант 3: Сканирование и оптимизация

Если у вас есть физические планы:

```bash
1. Отсканируйте план (300+ DPI для качества)
2. Сохраните как PNG
3. Поместите в mobile_app/assets/floor_plans/
```

---

## 📁 Структура файлов

```
mobile_app/
├── assets/
│   └── floor_plans/          ← Папка с планами этажей
│       ├── floor1.svg        ← План 1-го этажа (из Sweet Home 3D)
│       ├── floor2.svg        ← План 2-го этажа
│       ├── floor3.png        ← Альтернативно можно PNG
│       └── floor4.png
│
├── services/
│   ├── svg_loader.py         ← Парсер SVG файлов
│   ├── floor_plan_manager.py ← Менеджер планов этажей
│   └── ...
│
└── widgets/
    └── map_widget.py         ← MapWidget с поддержкой фонов
```

---

## 🚀 Использование в коде

### Автоматическая загрузка планов

Приложение автоматически:
1. Сканирует папку `assets/floor_plans/`
2. Определяет номер этажа из имени файла:
   - `floor1.svg`, `floor_1.svg` → этаж 1
   - `floor2.png`, `floor2.jpg` → этаж 2
   - `etaj3.svg`, `этаж3.svg` → этаж 3
3. При выборе этажа показывает соответствующий план

### Пример кода (MapScreen автоматически это делает)

```python
from services.floor_plan_manager import FloorPlanManager

# Инициализировать менеджер
manager = FloorPlanManager(plans_folder='assets/floor_plans')

# Получить план для этажа
plan_file = manager.get_plan_file(floor_number=1)

# Загрузить в MapWidget
map_widget.set_background_image(plan_file)
```

### Загрузка SVG файла напрямую

```python
# Способ 1: Через MapWidget
map_widget.set_background_image('assets/floor_plans/floor1.svg')

# Способ 2: Загрузить с парсингом комнат
map_widget.load_floor_plan_from_svg('assets/floor_plans/floor1.svg')
```

### Контроль фонового изображения

```python
# Установить прозрачность фона (0.0 - 1.0)
map_widget.set_background_opacity(0.7)

# Включить/выключить фон
map_widget.set_background_enabled(True)  # или False

# Очистить фон
map_widget.set_background_image(None)
```

---

## 🔄 Конверсия SVG → PNG

Для оптимальной производительности на мобилях рекомендуется конвертировать SVG в PNG:

### Способ 1: Автоматическая конверсия в коде

```python
from services.floor_plan_manager import FloorPlanManager

manager = FloorPlanManager()

# Конвертировать SVG в PNG (требует cairosvg)
success = manager.convert_svg_to_png(floor_number=1, output_dpi=96)

if success:
    print("Конверсия успешна! Файл сохранен как floor1.png")
```

### Способ 2: Используя Inkscape

```bash
# Linux/Mac
inkscape floor1.svg --export-png floor1.png --export-dpi=96

# Или используйте GUI
inkscape floor1.svg
# File → Export As → PNG
```

### Способ 3: Используя онлайн инструменты

- https://convertio.co/svg-png/
- https://online-convert.com/svg-to-png
- https://cloudconvert.com/

---

## 🔧 Требования для установки

### Для работы с SVG парсингом

```bash
pip install xmltodict  # Уже включен в requirements.txt
```

### Для конверсии SVG → PNG (опционально)

```bash
pip install cairosvg

# На Windows может потребоваться:
pip install cairocffi cffi
```

Если cairosvg не установлен, библиотека будет работать, но конверсия не будет доступна.

---

## 🧪 Тестирование

### Создать SVG шаблон для тестирования

```python
from services.floor_plan_manager import FloorPlanManager

# Создаст тестовый файл floor1.svg
FloorPlanManager.create_svg_template(
    output_path='assets/floor_plans/floor1.svg'
)
```

### Запустить тесты

```bash
cd mobile_app
pytest tests/ -v

# Или создать простой тест
python -c "
from services.floor_plan_manager import FloorPlanManager
manager = FloorPlanManager()
plans = manager.scan_folder()
print(f'Found {len(plans)} floor plans')
for floor, path in plans.items():
    print(f'  Floor {floor}: {path}')
"
```

---

## 📊 Формат SVG из Sweet Home 3D

Sweet Home 3D экспортирует SVG со следующей структурой:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="800">
  <!-- Стены -->
  <line x1="100" y1="100" x2="900" y2="100" stroke="black" stroke-width="2"/>
  
  <!-- Комнаты (полигоны с fill цветом) -->
  <polygon points="150,150 500,150 500,450 150,450" 
           fill="#cce5ff" stroke="black" stroke-width="1"/>
  
  <!-- Окна и двери -->
  <circle cx="300" cy="150" r="10" fill="white"/>
  
  <!-- Текст подписей -->
  <text x="325" y="300" text-anchor="middle">Room Name</text>
</svg>
```

---

## 🎨 Оптимизация планов

### Размер файла

```
Оптимальный размер для мобилей:
- SVG: 50-300 KB на файл
- PNG: 100-500 KB на файл
- JPG: 50-200 KB на файл
```

### Оптимизация SVG

```bash
# Используя scourSVG
pip install scour
scour -i floor1.svg -o floor1-optimized.svg

# Или онлайн: https://scour.etree.org/
```

### Оптимизация PNG

```bash
# Windows/Linux
pngquant floor1.png --output floor1-opt.png

# Или используйте ImageMagick
magick convert floor1.png -strip -quality 85 floor1-opt.png
```

---

## 🐛 Решение проблем

### Проблема: План не загружается

```python
# 1. Проверить путь к файлу
import os
print(os.path.exists('assets/floor_plans/floor1.svg'))

# 2. Проверить имя файла
# Файл должен быть: floor1.svg, floor_1.svg, или содержать число

# 3. Проверить логи
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Проблема: SVG отображается медленно

```python
# Решение: Конвертировать в PNG
manager = FloorPlanManager()
manager.convert_svg_to_png(floor_number=1)  # Требует cairosvg
```

### Проблема: Требует cairosvg но он не установлен

```bash
# Вариант 1: Установить (может быть сложно на Windows)
pip install cairosvg

# Вариант 2: Предварительно конвертировать SVG → PNG
# Используйте: Inkscape, Photoshop, или онлайн конвертер
# Потом просто используйте PNG файлы
```

---

## 📐 Координаты узлов

⚠️ **Важно**: Координаты узлов должны соответствовать координатам на плане этажа!

Есть два подхода:

### Подход 1: Независимые координаты (просто) ✅ Используется сейчас

- Узлы имеют свои координаты в графе (X, Y)
- План этажа масштабируется под размер виджета
- Узлы отображаются поверх плана в своих координатах

### Подход 2: SVG координаты (сложный)

- Координаты узлов совпадают с координатами в SVG файле
- Требует точного согласования между планом и узлами
- `use_svg_coordinates=True` в `set_background_image()`

```python
map_widget.set_background_image(
    image_path='floor1.svg',
    svg_width=1000,  # Ширина из SVG
    svg_height=800,   # Высота из SVG
    use_svg_coordinates=True  # Использовать координаты SVG
)
```

---

## 🚀 Performance Tips

### Оптимальные параметры для мобилей

```python
# 1. Использовать PNG вместо SVG
# PNG загружается быстрее на мобилях

# 2. Оптимальный размер плана
# Ширина: 800-1200px
# Высота: 600-1000px
# Формат: PNG/JPG

# 3. Уменьшить количество узлов на плане
# Максимум 100-150 узлов на этаж для плавного скролла

# 4. Использовать прозрачность опционально
map_widget.set_background_opacity(0.8)  # Не полностью непрозрачный
```

### Производительность по формату

```
SVG:
- Загрузка: 200-500ms (требует парсинга)
- FPS: 45-60
- Размер: 50-300 KB

PNG:
- Загрузка: 50-150ms (прямая загрузка)
- FPS: 58-60 ✅ Лучше
- Размер: 100-500 KB

JPG:
- Загрузка: 30-100ms ✅ Самый быстрый
- FPS: 58-60 ✅ Лучше
- Размер: 50-200 KB ✅ Меньше
- Качество: легкое сжатие артефактов
```

**Рекомендация**: Используйте **PNG** как оптимальный баланс.

---

## 📝 Пример реальной интеграции

```python
# main.py или где инициализируется приложение

from services.floor_plan_manager import FloorPlanManager

# Создать менеджер
manager = FloorPlanManager(plans_folder='assets/floor_plans')

# Сканировать доступные планы
available_floors = manager.get_available_floors()
print(f"Available floors: {available_floors}")

# При загрузке в MapScreen:
# (это делается автоматически в _update_map_display)

def load_building_data(building_id):
    """Загрузить данные здания и его планы"""
    # Получить узлы здания
    building = api_client.get_building(building_id)
    
    # Сканировать и загрузить планы этажей
    self.floor_plan_manager.scan_folder()
    
    # При выборе этажа MapScreen автоматически:
    # 1. Фильтрует узлы по этажу
    # 2. Загружает план этажа как фон
    # 3. Отрисовывает узлы поверх плана
    
    map_widget.set_nodes(floor_nodes)
    plan_file = self.floor_plan_manager.get_plan_file(floor_number)
    if plan_file:
        map_widget.set_background_image(plan_file)
```

---

## ✅ Чек-лист подготовки

- [ ] Экспортировать планы из Sweet Home 3D (или подготовить PNG)
- [ ] Создать папку `mobile_app/assets/floor_plans/`
- [ ] Сохранить файлы как `floor1.svg`, `floor2.svg` и т.д.
- [ ] Установить зависимости: `pip install -r requirements.txt`
- [ ] (Опционально) Установить cairosvg: `pip install cairosvg`
- [ ] Запустить приложение и проверить загрузку планов
- [ ] Если медленно → конвертировать в PNG
- [ ] Оптимизировать размер изображений при необходимости

---

## 🔗 Ссылки

- **Sweet Home 3D**: https://www.sweethome3d.com/
- **Inkscape (редактор SVG)**: https://inkscape.org/
- **SVG to PNG конвертеры**:
  - https://cloudconvert.com/svg-to-png
  - https://convertio.co/svg-png/
  - https://online-convert.com/svg-to-png
- **Оптимизация SVG**: https://scour.etree.org/
- **Оптимизация PNG**: https://tinypng.com/

---

**Теперь ваше приложение готово отображать красивые планы этажей из Sweet Home 3D!** 🎉
