#!/usr/bin/env python3
"""
Test PNG > SVG priority when loading floor plans
"""

import os
import tempfile
from PIL import Image

def test_png_svg_priority():
    """Test PNG > SVG priority"""
    
    print("\n" + "="*70)
    print("TEST: PNG > SVG Priority for Floor Plan Loading")
    print("="*70)
    
    from widgets.map_widget import MapWidget
    
    widget = MapWidget()
    
    # Create temp directory
    temp_dir = tempfile.mkdtemp(prefix="test_priority_")
    print(f"\n[1/4] Temp directory: {temp_dir}")
    
    # Create test files
    png_path = os.path.join(temp_dir, "floor_1.png")
    svg_path = os.path.join(temp_dir, "floor_1.svg")
    
    # PNG
    img = Image.new('RGB', (100, 100), color=(100, 100, 100))
    img.save(png_path)
    print(f"[2/4] Created PNG: {os.path.basename(png_path)}")
    
    # SVG
    with open(svg_path, 'w') as f:
        f.write('<?xml version="1.0"?>\n')
        f.write('<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">\n')
        f.write('  <circle cx="50" cy="50" r="40" fill="red"/>\n')
        f.write('</svg>\n')
    print(f"[3/4] Created SVG: {os.path.basename(svg_path)}")
    
    # TEST 1: Both files exist - PNG should be loaded
    print(f"\n[4/4] Test 1: Both files exist")
    print(f"      Input: floor_1 (no extension)")
    
    widget.set_background_image(os.path.join(temp_dir, "floor_1"))
    
    if widget.background_image_path == png_path and len(widget.svg_elements) == 0:
        print(f"      [PASS] PNG loaded with priority")
        result1 = True
    else:
        print(f"      [FAIL] PNG not loaded")
        print(f"         PNG: {widget.background_image_path}")
        print(f"         SVG elements: {len(widget.svg_elements)}")
        result1 = False
    
    # TEST 2: Remove PNG - SVG should load (fallback)
    print(f"\n[5/4] Test 2: Only SVG exists (PNG removed)")
    os.remove(png_path)
    
    widget.background_image_path = None
    widget.svg_elements = []
    widget.set_background_image(os.path.join(temp_dir, "floor_1"))
    
    if len(widget.svg_elements) > 0 and widget.background_image_path is None:
        print(f"      [PASS] SVG loaded as fallback ({len(widget.svg_elements)} elements)")
        result2 = True
    else:
        print(f"      [FAIL] SVG not loaded")
        result2 = False
    
    # TEST 3: Explicit .svg path
    print(f"\n[6/4] Test 3: Explicit .svg path")
    
    widget.background_image_path = None
    widget.svg_elements = []
    widget.set_background_image(svg_path)
    
    if len(widget.svg_elements) > 0 and widget.background_image_path is None:
        print(f"      [PASS] SVG loaded ({len(widget.svg_elements)} elements)")
        result3 = True
    else:
        print(f"      [FAIL] SVG not loaded")
        result3 = False
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)
    
    print("\n" + "="*70)
    if result1 and result2 and result3:
        print("[RESULT] ALL TESTS PASSED")
        print("\nPriority system works correctly:")
        print("  [OK] Both available: PNG loaded")
        print("  [OK] PNG missing: SVG loads as fallback")
        print("  [OK] Explicit paths work")
        return True
    else:
        print("[RESULT] SOME TESTS FAILED")
        return False


if __name__ == '__main__':
    try:
        success = test_png_svg_priority()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        exit(1)
