#!/usr/bin/env python3
"""
Тест интеграции SVG и snap-to-grid функционала
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.floor_plan_manager import FloorPlanManager
from services.svg_loader import SVGLoader
from services.api_client import Node
from kivy.metrics import dp
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_floor_plan_manager():
    """Тест менеджера планов этажей"""
    print("\n📋 Тест FloorPlanManager:")
    
    plans_folder = os.path.join(os.path.dirname(__file__), 'assets/floor_plans')
    manager = FloorPlanManager(plans_folder=plans_folder)
    
    print(f"✓ Папка с планами: {plans_folder}")
    print(f"✓ Обнаружено планов: {len(manager.auto_detected_plans)}")
    
    for floor, path in manager.auto_detected_plans.items():
        print(f"  - Этаж {floor}: {os.path.basename(path)}")
    
    # Тест get_plan_file
    for floor in [1, 2, 3]:
        plan = manager.get_plan_file(floor)
        if plan:
            print(f"✓ План для этажа {floor}: {os.path.basename(plan)}")
        else:
            print(f"  - План для этажа {floor}: не найден")

def test_svg_loader():
    """Тест загрузчика SVG"""
    print("\n📝 Тест SVGLoader:")
    
    svg_path = os.path.join(os.path.dirname(__file__), 'assets/floor_plans/floor1_example.svg')
    
    if not os.path.exists(svg_path):
        print(f"✗ SVG файл не найден: {svg_path}")
        return
    
    try:
        floor_plan = SVGLoader.load_svg_file(svg_path)
        print(f"✓ Загружено SVG: {svg_path}")
        print(f"✓ Элементов в плане: {len(floor_plan.elements)}")
        
        # Показываем типы элементов
        element_types = {}
        for elem in floor_plan.elements:
            elem_type = elem.element_type
            element_types[elem_type] = element_types.get(elem_type, 0) + 1
        
        print(f"✓ Типы элементов:")
        for elem_type, count in sorted(element_types.items()):
            print(f"  - {elem_type}: {count}")
        
    except Exception as e:
        print(f"✗ Ошибка загрузки SVG: {e}")
        import traceback
        traceback.print_exc()

def test_snap_to_grid():
    """Тест функции snap-to-grid"""
    print("\n🎯 Тест snap-to-grid:")
    
    grid_size = dp(20)
    print(f"✓ Размер ячейки: {grid_size}")
    
    def snap_to_grid(x, y, grid=grid_size):
        """Простая функция привязки к сетке"""
        snapped_x = round(x / grid) * grid
        snapped_y = round(y / grid) * grid
        return snapped_x, snapped_y
    
    # Тестовые координаты
    test_coords = [(10, 15), (25, 20), (45, 55), (100.5, 200.3)]
    
    for x, y in test_coords:
        snapped_x, snapped_y = snap_to_grid(x, y)
        print(f"  ({x}, {y}) → ({snapped_x}, {snapped_y})")

def test_svg_elements_properties():
    """Тест свойств элементов SVG"""
    print("\n📐 Тест свойств SVG элементов:")
    
    svg_path = os.path.join(os.path.dirname(__file__), 'assets/floor_plans/floor1_example.svg')
    
    if not os.path.exists(svg_path):
        print(f"✗ SVG файл не найден: {svg_path}")
        return
    
    try:
        floor_plan = SVGLoader.load_svg_file(svg_path)
        
        print(f"✓ Проверка элементов:")
        for i, elem in enumerate(floor_plan.elements[:5]):  # Первые 5 элементов
            print(f"\n  Элемент {i}:")
            print(f"    - Тип: {elem.element_type}")
            print(f"    - ID: {elem.element_id}")
            
            if elem.element_type == 'polygon' and elem.points:
                center_x = sum(p[0] for p in elem.points) / len(elem.points)
                center_y = sum(p[1] for p in elem.points) / len(elem.points)
                print(f"    - Центр полигона: ({center_x}, {center_y})")
            
            if hasattr(elem, 'center') and elem.center:
                print(f"    - Центр (свойство): {elem.center}")
    
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Главная функция тестирования"""
    print("=" * 60)
    print("🧪 ТЕСТ ИНТЕГРАЦИИ SVG И SNAP-TO-GRID")
    print("=" * 60)
    
    test_floor_plan_manager()
    test_svg_loader()
    test_snap_to_grid()
    test_svg_elements_properties()
    
    print("\n" + "=" * 60)
    print("✅ ТЕСТЫ ЗАВЕРШЕНЫ")
    print("=" * 60)

if __name__ == '__main__':
    main()
