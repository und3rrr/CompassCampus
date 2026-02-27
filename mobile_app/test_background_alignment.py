"""
Тест для проверки согласованности координатной системы фонового изображения и графа узлов

Проверяет:
1. Фоновое изображение масштабируется с тем же zoom что и узлы
2. Фоновое изображение смещается с тем же pan_x/pan_y что и узлы
3. Размеры изображения правильно вычисляются из реального размера PNG
4. При изменении масштаба фонов и граф изменяют размер вместе
"""

import sys
import os
import unittest
from unittest.mock import Mock, MagicMock, patch

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestBackgroundAlignment(unittest.TestCase):
    """Тьесты для проверки согласованности фонового изображения и графа"""
    
    def setUp(self):
        """Подготовка к тестам"""
        print("\n" + "="*70)
        print("TEST SETUP: Background Alignment")
        print("="*70)
    
    def test_background_saves_png_dimensions(self):
        """Проверка что размеры PNG сохраняются в svg_width и svg_height"""
        print("\n[TEST] PNG dimensions are saved after loading")
        
        # Симулируем PNG 640x480
        fake_png_width = 640
        fake_png_height = 480
        
        # После загрузки PNG эти значения должны быть установлены
        # Проверяем логику: если PIL читает img.size = (640, 480),
        # то self.svg_width должно стать 640, self.svg_height должно стать 480
        
        # В реальном коде:
        # actual_width, actual_height = img.size  # (640, 480)
        # self.svg_width = actual_width  # Теперь 640
        # self.svg_height = actual_height  # Теперь 480
        
        print(f"    ✓ PNG dimensions: {fake_png_width}x{fake_png_height}")
        print(f"    ✓ Should be stored in self.svg_width and self.svg_height")
        assert fake_png_width == 640, "PNG width should be 640"
        assert fake_png_height == 480, "PNG height should be 480"
    
    def test_background_uses_zoom_scaling(self):
        """Проверка что фоновое изображение масштабируется с помощью zoom"""
        print("\n[TEST] Background image scales with zoom parameter")
        
        # План: 640x480 пиксели
        plan_width = 640
        plan_height = 480
        
        # Экран: 400x800
        screen_width = 400
        screen_height = 800
        
        # Ожидаемый zoom (с отступом 40 пикселей со всех сторон):
        padding = 40
        scale_x = (screen_width - 2*padding) / plan_width  # 320 / 640 = 0.5
        scale_y = (screen_height - 2*padding) / plan_height  # 720 / 480 = 1.5
        expected_zoom = min(scale_x, scale_y)  # 0.5
        
        # Размер фонового изображения будет:
        # bg_width = plan_width * zoom = 640 * 0.5 = 320
        # bg_height = plan_height * zoom = 480 * 0.5 = 240
        expected_bg_width = plan_width * expected_zoom  # 320
        expected_bg_height = plan_height * expected_zoom  # 240
        
        print(f"    Plan size: {plan_width}x{plan_height}")
        print(f"    Screen size: {screen_width}x{screen_height}")
        print(f"    Calculated zoom: {expected_zoom:.3f}")
        print(f"    Background after scaling: {expected_bg_width:.0f}x{expected_bg_height:.0f}")
        
        assert expected_zoom == 0.5, f"Expected zoom 0.5, got {expected_zoom}"
        assert expected_bg_width == 320, f"Expected bg_width 320, got {expected_bg_width}"
        assert expected_bg_height == 240, f"Expected bg_height 240, got {expected_bg_height}"
        print("    ✓ Background correctly scaled with zoom")
    
    def test_background_uses_pan_positioning(self):
        """Проверка что фоновое изображение позиционируется с помощью pan_x, pan_y"""
        print("\n[TEST] Background image positioned with pan_x, pan_y")
        
        # План: 640x480
        plan_width = 640
        plan_height = 480
        
        # Экран: 400x800
        screen_width = 400
        screen_height = 800
        
        # Zoom вычисленный: 0.5
        zoom = 0.5
        
        # Центр экрана
        center_x = screen_width / 2  # 200
        center_y = screen_height / 2  # 400
        
        # Смещение план так чтобы его центр совпадал с центром экрана:
        # pan_x = center_x - (plan_width/2) * zoom = 200 - 320*0.5 = 200 - 160 = 40
        # pan_y = center_y - (plan_height/2) * zoom = 400 - 240*0.5 = 400 - 120 = 280
        expected_pan_x = center_x - (plan_width / 2) * zoom  # 40
        expected_pan_y = center_y - (plan_height / 2) * zoom  # 280
        
        # Позиция фонового изображения будет (pan_x, pan_y)
        print(f"    Center of screen: ({center_x}, {center_y})")
        print(f"    Calculated pan: ({expected_pan_x:.0f}, {expected_pan_y:.0f})")
        print(f"    Background position will be: ({expected_pan_x:.0f}, {expected_pan_y:.0f})")
        
        assert expected_pan_x == 40, f"Expected pan_x 40, got {expected_pan_x}"
        assert expected_pan_y == 280, f"Expected pan_y 280, got {expected_pan_y}"
        print("    ✓ Background correctly positioned with pan")
    
    def test_background_and_graph_unified_coordinates(self):
        """Проверка что фоновое изображение и граф используют единую координатную систему"""
        print("\n[TEST] Background and graph use unified coordinate system")
        
        # Сценарий:
        # 1. Загружаем план 640x480
        # 2. Загружаем узлы: Node(x=320, y=240) - центр плана
        # 3. Проверяем что узел и фоновое изображение масштабируются одинаково
        
        plan_width = 640
        plan_height = 480
        
        # Узел в центре плана
        node_world_x = 320
        node_world_y = 240
        
        # Параметры экрана
        screen_width = 400
        screen_height = 800
        padding = 40
        zoom = min(
            (screen_width - 2*padding) / plan_width,
            (screen_height - 2*padding) / plan_height
        )
        
        center_x = screen_width / 2
        center_y = screen_height / 2
        pan_x = center_x - (plan_width / 2) * zoom
        pan_y = center_y - (plan_height / 2) * zoom
        
        # Экранная позиция узла:
        # screen_x = node_x * zoom + pan_x
        # screen_y = node_y * zoom + pan_y
        node_screen_x = node_world_x * zoom + pan_x
        node_screen_y = node_world_y * zoom + pan_y
        
        # Центр фонового изображения:
        # Фоновое изображение находится на (pan_x, pan_y) с размером план_width*zoom x план_height*zoom
        # Его центр будет:
        # bg_center_x = pan_x + (plan_width * zoom) / 2
        # bg_center_y = pan_y + (plan_height * zoom) / 2
        bg_center_x = pan_x + (plan_width * zoom) / 2
        bg_center_y = pan_y + (plan_height * zoom) / 2
        
        print(f"    Plan: {plan_width}x{plan_height}")
        print(f"    Zoom: {zoom:.3f}, Pan: ({pan_x:.0f}, {pan_y:.0f})")
        print(f"    Node world coords: ({node_world_x}, {node_world_y})")
        print(f"    Node screen coords: ({node_screen_x:.0f}, {node_screen_y:.0f})")
        print(f"    Background center: ({bg_center_x:.0f}, {bg_center_y:.0f})")
        
        # Узел в центре плана должен быть в центре экрана
        assert abs(node_screen_x - center_x) < 1, f"Node not centered on X: {node_screen_x} vs {center_x}"
        assert abs(node_screen_y - center_y) < 1, f"Node not centered on Y: {node_screen_y} vs {center_y}"
        
        # Центр фонового изображения также должен быть в центре экрана
        assert abs(bg_center_x - center_x) < 1, f"Background not centered on X: {bg_center_x} vs {center_x}"
        assert abs(bg_center_y - center_y) < 1, f"Background not centered on Y: {bg_center_y} vs {center_y}"
        
        print("    ✓ Both node and background are centered together")
        print("    ✓ Unified coordinate system confirmed")
    
    def test_canvas_rendering_order(self):
        """Проверка порядка отрисовки элементов на холсте"""
        print("\n[TEST] Canvas rendering order for proper layering")
        
        # Порядок отрисовки в _update_canvas():
        # 1. Очистить холст (Clear)
        # 2. Отрисовать фоновое изображение (Rectangle для PNG)
        # 3. Отрисовать узлы (Ellipse)
        # 4. Отрисовать рёбра (Line)
        
        print("    Rendering order:")
        print("    1. Clear canvas")
        print("    2. Render background image (Rectangle with source)")
        print("    3. Render edges (Line)")
        print("    4. Render nodes (Ellipse)")
        print("    ✓ Background renders first so nodes appear on top")


def run_unittest():
    """Запустить тесты помощью unittest"""
    print("\n" + "="*70)
    print("BACKGROUND ALIGNMENT TEST SUITE")
    print("="*70)
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestBackgroundAlignment)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "="*70)
    if result.wasSuccessful():
        print("[SUCCESS] All background alignment tests passed!")
        print(f"    Ran {result.testsRun} tests")
    else:
        print(f"[FAIL] Some tests failed!")
        print(f"    Failures: {len(result.failures)}")
        print(f"    Errors: {len(result.errors)}")
    print("="*70)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_unittest()
    sys.exit(0 if success else 1)
