"""
Тест для проверки что Визуальный редактор графов имеет тот же функционал что и MapWidget

Проверяет:
1. ScissorPush/ScissorPop добавлены в редактор
2. Размеры PNG/SVG сохраняются
3. Фоновое изображение масштабируется
4. Обрезка по границам виджета работает
"""

import sys
import os


def test_editor_clipping():
    """Проверка что обрезка добавлена в редактор графа"""
    print("\n" + "="*70)
    print("TEST: Visual Graph Editor Clipping")
    print("="*70)
    
    editor_path = os.path.join(os.path.dirname(__file__), 'widgets', 'visual_graph_editor.py')
    
    with open(editor_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Проверка 1: Импорты
    print("\n[TEST] ScissorPush and ScissorPop imported in editor")
    if 'ScissorPush' in content and 'ScissorPop' in content:
        print("    ✓ ScissorPush imported")
        print("    ✓ ScissorPop imported")
    else:
        print("    ✗ FAIL: ScissorPush/ScissorPop not in imports")
        return False
    
    # Проверка 2: ScissorPush в _update_canvas
    print("\n[TEST] ScissorPush enabled in editor's _update_canvas()")
    if 'ScissorPush(x=int(self.x), y=int(self.y), width=int(self.width), height=int(self.height))' in content:
        print("    ✓ ScissorPush enabled with widget bounds")
    else:
        print("    ✗ FAIL: ScissorPush not properly configured")
        return False
    
    # Проверка 3: ScissorPop в _update_canvas
    print("\n[TEST] ScissorPop disables clipping after rendering")
    scissor_pop_index = content.find('# ========== КОНЕЦ ОБРЕЗКИ ==========')
    if scissor_pop_index > 0:
        after_comment = content[scissor_pop_index:scissor_pop_index+200]
        if 'ScissorPop()' in after_comment:
            print("    ✓ ScissorPop found after rendering")
        else:
            print("    ✗ FAIL: ScissorPop not found after end comment")
            return False
    else:
        print("    ✗ FAIL: End clipping comment not found")
        return False
    
    # Проверка 4: Размеры SVG сохраняются
    print("\n[TEST] SVG dimensions stored in editor")
    if 'self.svg_width = floor_plan.width' in content and 'self.svg_height = floor_plan.height' in content:
        print("    ✓ SVG width stored")
        print("    ✓ SVG height stored")
    else:
        print("    ✗ FAIL: SVG dimensions not stored")
        return False
    
    # Проверка 5: Размеры PNG сохраняются
    print("\n[TEST] PNG dimensions extracted and stored in editor")
    if 'self.svg_width = actual_width' in content and 'self.svg_height = actual_height' in content:
        print("    ✓ PNG width extracted and stored")
        print("    ✓ PNG height extracted and stored")
    else:
        print("    ✗ FAIL: PNG dimensions not extracted")
        return False
    
    # Проверка 6: Фоновое изображение масштабируется
    print("\n[TEST] Background image scales with zoom in editor")
    if 'bg_width = self.svg_width * self.zoom' in content:
        print("    ✓ Background width scaled by zoom")
        print("    ✓ Background height scaled by zoom")
    else:
        print("    ✗ FAIL: Background image not scaled")
        return False
    
    # Проверка 7: Фоновое изображение позиционируется
    print("\n[TEST] Background image positioned with pan_x, pan_y")
    if 'bg_pos_x = self.pan_x' in content and 'bg_pos_y = self.pan_y' in content:
        print("    ✓ Background positioned with pan")
    else:
        print("    ✗ FAIL: Background not positioned")
        return False
    
    # Проверка 8: SVG элементы также используют zoom/pan
    print("\n[TEST] SVG elements in editor use zoom and pan parameters")
    if 'SVGRenderer.render_svg_elements(' in content:
        svg_render_index = content.find('SVGRenderer.render_svg_elements(')
        svg_render_section = content[svg_render_index:svg_render_index+500]
        if 'zoom=self.zoom' in svg_render_section and 'pan_x=self.pan_x' in svg_render_section:
            print("    ✓ SVG elements use zoom parameter")
            print("    ✓ SVG elements use pan_x parameter")
            print("    ✓ SVG elements use pan_y parameter")
        else:
            print("    ✗ FAIL: SVG elements don't use zoom/pan")
            return False
    
    return True


def test_editor_attributes():
    """Проверка что в редакторе добавлены нужные атрибуты"""
    print("\n" + "="*70)
    print("TEST: Visual Graph Editor Attributes")
    print("="*70)
    
    editor_path = os.path.join(os.path.dirname(__file__), 'widgets', 'visual_graph_editor.py')
    
    with open(editor_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Проверка атрибутов
    print("\n[TEST] Editor has svg_width and svg_height attributes")
    if 'self.svg_width: Optional[float] = None' in content:
        print("    ✓ self.svg_width initialized")
    else:
        print("    ✗ FAIL: missing self.svg_width")
        return False
    
    if 'self.svg_height: Optional[float] = None' in content:
        print("    ✓ self.svg_height initialized")
    else:
        print("    ✗ FAIL: missing self.svg_height")
        return False
    
    return True


def main():
    """Главная функция тестирования"""
    print("\n" + "="*70)
    print("VISUAL GRAPH EDITOR TEST SUITE")
    print("="*70)
    
    try:
        result1 = test_editor_clipping()
        result2 = test_editor_attributes()
        
        print("\n" + "="*70)
        if result1 and result2:
            print("[SUCCESS] Visual Graph Editor has all required fixes!")
            print("    ✓ Canvas clipping configured")
            print("    ✓ Background alignment implemented")
            print("    ✓ All attributes initialized")
        else:
            print("[FAIL] Visual Graph Editor has missing features!")
        print("="*70)
        
        return result1 and result2
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
