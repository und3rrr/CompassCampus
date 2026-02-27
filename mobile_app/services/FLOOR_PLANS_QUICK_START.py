"""
Quick Start - Интеграция SVG планов этажей в 3 шага
"""

# ============================================================
# БЫСТРЫЙ СТАРТ: ДОБАВЬТЕ ПЛАНЫ ЭТАЖЕЙ ЗА 3 МИНУТ
# ============================================================

"""
Шаг 1: Подготовьте файлы планов
===============================
✅ Загрузите файлы плана в: mobile_app/assets/floor_plans/

Форматы:
- floor1.svg (из Sweet Home 3D)
- floor2.svg
- floor3.png (или PNG изображения)
- floor4.jpg

Файлы должны быть названы так чтобы содержали номер этажа:
- floor1.svg → этаж 1
- floor_2.svg → этаж 2  
- 3_plan.png → этаж 3
- level4.jpg → этаж 4


Шаг 2: Приложение автоматически найдет и загрузит планы
==========================================================
✅ При выборе этажа приложение:
   - Сканирует папку assets/floor_plans/
   - Находит соответствующий файл плана
   - Отображает его как фон в MapWidget
   - Показывает узлы поверх плана

Код уже готов! Находится в MapScreen._update_map_display()


Шаг 3: Оптимизируйте (опционально)
====================================
✅ Если планы медленно загружаются:
   - Конвертируйте SVG → PNG
   - Уменьшите размер изображения
   - Сожмите PNG/JPG файлы
"""

# ============================================================
# ПРИМЕРЫ КОДА
# ============================================================

# Пример 1: Проверить найденные планы
# ====================================
if __name__ == '__main__':
    from services.floor_plan_manager import FloorPlanManager
    
    manager = FloorPlanManager(plans_folder='assets/floor_plans')
    available_floors = manager.get_available_floors()
    
    print(f"✅ Найдены планы для этажей: {available_floors}")
    
    for floor_num in available_floors:
        plan_file = manager.get_plan_file(floor_num)
        print(f"   Этаж {floor_num}: {plan_file}")


# Пример 2: Загрузить план в MapWidget
# ======================================
from widgets.map_widget import MapWidget
from services.floor_plan_manager import FloorPlanManager

map_widget = MapWidget()
manager = FloorPlanManager()

# Загрузить и отобразить план floor 1
plan_file = manager.get_plan_file(floor_number=1)
if plan_file:
    map_widget.set_background_image(plan_file)
    print(f"✅ План {plan_file} загружен")


# Пример 3: Конвертировать SVG → PNG
# ====================================
from services.floor_plan_manager import FloorPlanManager

manager = FloorPlanManager()

# Конвертировать SVG в PNG для лучшей производительности
# (требует установки cairosvg)
success = manager.convert_svg_to_png(floor_number=1)

if success:
    print("✅ SVG успешно конвертирован в PNG")
else:
    print("❌ Ошибка: требуется установка cairosvg")
    print("   Установите: pip install cairosvg")


# Пример 4: Создать тестовый SVG файл
# =====================================
from services.floor_plan_manager import FloorPlanManager

# Создаст пример файла floor1.svg
FloorPlanManager.create_svg_template(
    output_path='assets/floor_plans/floor1_test.svg'
)
print("✅ Тестовый файл создан: assets/floor_plans/floor1_test.svg")


# Пример 5: Управлять прозрачностью фона
# =======================================
map_widget.set_background_opacity(0.7)  # 70% непрозрачность
map_widget.set_background_enabled(True)  # Показать фон
# или
map_widget.set_background_enabled(False)  # Скрыть фон


# ============================================================
# ФАЙЛОВАЯ СТРУКТУРА
# ============================================================

"""
mobile_app/
├── assets/
│   └── floor_plans/
│       ├── floor1.svg          ← план 1-го этажа (из Sweet Home 3D)
│       ├── floor1.png          ← или PNG версия
│       ├── floor2.svg
│       ├── floor3.png
│       └── floor1_example.svg  ← пример, включен в проект
│
├── services/
│   ├── svg_loader.py           ← парсер SVG
│   └── floor_plan_manager.py   ← управление планами
│
└── widgets/
    └── map_widget.py           ← поддерживает фоны
"""


# ============================================================
# ТРЕБОВАНИЯ
# ============================================================

"""
Основные (включены в requirements.txt):
- kivy
- requests
- python-dateutil

Опциональные (для конверсии SVG → PNG):
- cairosvg (установите если нужна конверсия)
  pip install cairosvg

Инструменты для подготовки планов:
- Sweet Home 3D (https://www.sweethome3d.com/) - для создания планов
- Inkscape (https://inkscape.org/) - для редактирования SVG
"""


# ============================================================
# TROUBLESHOOTING
# ============================================================

"""
Проблема: План не показывается
Решение: Убедитесь что файл находится в правильной папке:
        assets/floor_plans/floor1.svg или .png

Проблема: SVG загружается медленно
Решение: Конвертируйте в PNG (быстрее на мобилях)
        manager.convert_svg_to_png(1)

Проблема: Конверсия не работает
Решение: Установите cairosvg
        pip install cairosvg
        
        Если это не работает на Windows:
        - Используйте Inkscape: File→Export As→PNG
        - Или онлайн конвертер: cloudconvert.com
"""


# ============================================================
# КОД НА PYTHON ДЛЯ ТЕСТИРОВАНИЯ
# ============================================================

def test_floor_plans():
    """Полный тест загрузки планов этажей"""
    import os
    from services.floor_plan_manager import FloorPlanManager
    
    print("=" * 50)
    print("ТЕСТ: Загрузка планов этажей")
    print("=" * 50)
    
    # 1. Инициализировать менеджер
    manager = FloorPlanManager(plans_folder='assets/floor_plans')
    print("✓ Менеджер инициализирован")
    
    # 2. Сканировать доступные планы
    floors = manager.get_available_floors()
    print(f"✓ Найдены этажи: {floors}")
    
    # 3. Проверить каждый этаж
    for floor_num in floors:
        plan_file = manager.get_plan_file(floor_num)
        if os.path.exists(plan_file):
            size_kb = os.path.getsize(plan_file) / 1024
            print(f"  ✓ Floor {floor_num}: {os.path.basename(plan_file)} ({size_kb:.1f} KB)")
        else:
            print(f"  ✗ Floor {floor_num}: ФАЙЛ НЕ НАЙДЕН")
    
    # 4. Попытаться создать тестовый файл
    print("\n" + "=" * 50)
    print("Создание тестового SVG...")
    FloorPlanManager.create_svg_template('assets/floor_plans/test_floor.svg')
    if os.path.exists('assets/floor_plans/test_floor.svg'):
        print("✓ Тестовый файл создан успешно")
    
    print("=" * 50)
    print("ТЕСТ ЗАВЕРШЕН!")
    print("=" * 50)


if __name__ == '__main__':
    test_floor_plans()
