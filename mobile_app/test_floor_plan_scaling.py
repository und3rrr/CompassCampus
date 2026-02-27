#!/usr/bin/env python3
"""
Test auto-scaling of floor plans to fit screen
"""

import os
import tempfile
from PIL import Image

def test_floor_plan_scaling():
    """Test that floor plans scale to fit screen properly"""
    
    print("\n" + "="*70)
    print("TEST: Floor Plan Auto-Scaling for Mobile")
    print("="*70)
    
    from widgets.map_widget import MapWidget
    from services.api_client import Node
    
    # Create widget (simulating mobile screen size ~400x800)
    widget = MapWidget()
    widget.width = 400
    widget.height = 800
    print(f"\n[1/4] Widget size: {widget.width}x{widget.height} (mobile screen)")
    
    # Create temp directory
    temp_dir = tempfile.mkdtemp(prefix="test_scaling_")
    
    # Create test PNG (large, like a real floor plan)
    png_path = os.path.join(temp_dir, "floor_1.png")
    plan_width = 2000  # Large floor plan
    plan_height = 1500
    img = Image.new('RGB', (plan_width, plan_height), color=(200, 200, 200))
    
    # Add some visual markers to simulate rooms
    pixels = img.load()
    for x in range(100, 500):
        for y in range(100, 400):
            pixels[x, y] = (100, 100, 200)  # Blue room
    
    img.save(png_path)
    print(f"[2/4] Created large PNG: {plan_width}x{plan_height}px")
    print(f"      Saved to: {png_path}")
    
    # Add some test nodes
    widget.nodes = [
        Node(id='1', name='Room 1', x=100, y=100, node_type='Room', floor=1),
        Node(id='2', name='Room 2', x=500, y=100, node_type='Room', floor=1),
        Node(id='3', name='Room 3', x=100, y=500, node_type='Room', floor=1),
    ]
    print(f"[3/4] Added {len(widget.nodes)} test nodes")
    
    # Load floor plan
    print(f"\n[4/4] Loading floor plan with auto-scaling...")
    widget.set_background_image(os.path.join(temp_dir, "floor_1"))
    
    # Check results
    print(f"\nResults:")
    print(f"  Zoom level: {widget.zoom:.3f}")
    print(f"  Pan X: {widget.pan_x:.1f}")
    print(f"  Pan Y: {widget.pan_y:.1f}")
    print(f"  PNG loaded: {widget.background_image_path is not None}")
    
    # Validate
    success = True
    
    # Check 1: Zoom should be reasonable (not too small or too large)
    if 0.15 < widget.zoom < 0.5:
        print(f"\n[OK] Zoom is reasonable: {widget.zoom:.3f}")
    else:
        print(f"\n[FAIL] Zoom out of range: {widget.zoom:.3f} (expected 0.15-0.5)")
        success = False
    
    # Check 2: Plan should fit on screen
    scaled_width = plan_width * widget.zoom
    scaled_height = plan_height * widget.zoom
    
    if scaled_width <= widget.width * 1.1 and scaled_height <= widget.height * 1.1:
        print(f"[OK] Plan fits on screen:")
        print(f"     Scaled size: {scaled_width:.0f}x{scaled_height:.0f}")
        print(f"     Screen size: {widget.width}x{widget.height}")
    else:
        print(f"[FAIL] Plan doesn't fit")
        success = False
    
    # Check 3: Pan should center plan
    center_x = widget.width / 2
    center_y = widget.height / 2
    plan_center_x = center_x - widget.pan_x
    plan_center_y = center_y - widget.pan_y
    
    tolerance = widget.width * 0.2  # 20% tolerance
    if abs(plan_center_x - center_x) < tolerance and abs(plan_center_y - center_y) < tolerance:
        print(f"[OK] Plan is roughly centered on screen")
    else:
        print(f"[WARN] Plan centering may be off")
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)
    
    print("\n" + "="*70)
    if success:
        print("[RESULT] Auto-scaling works correctly!")
        print("\nBenefits:")
        print("  - Floor plan visible without zooming")
        print("  - Reasonable zoom level for mobile")
        print("  - Less swiping needed")
        print("  - Better user experience")
    else:
        print("[RESULT] Issues found in auto-scaling")
    
    return success


def test_different_screen_sizes():
    """Test scaling works for different device screen sizes"""
    
    print("\n" + "="*70)
    print("TEST: Scaling for Different Mobile Devices")
    print("="*70)
    
    from widgets.map_widget import MapWidget
    from PIL import Image
    import tempfile
    
    # Test different screen sizes
    devices = [
        ("Phone 5\" (normal)", 360, 640),
        ("Phone 6\" (large)", 400, 800),
        ("Tablet 7\"", 600, 960),
        ("Tablet 10\"", 720, 1280),
    ]
    
    # Create test image once
    temp_dir = tempfile.mkdtemp()
    png_path = os.path.join(temp_dir, "floor.png")
    plan_width = 2000
    plan_height = 1500
    img = Image.new('RGB', (plan_width, plan_height), color=(200, 200, 200))
    img.save(png_path)
    
    print(f"\nFloor plan size: {plan_width}x{plan_height}")
    print(f"\nDevice comparison:\n")
    print(f"{'Device':<25} {'Size':<20} {'Zoom':<10} {'Ft/Px':<10}")
    print("-" * 65)
    
    all_ok = True
    for device_name, width, height in devices:
        widget = MapWidget()
        widget.width = width
        widget.height = height
        widget.set_background_image(png_path)
        
        # Calculate "feet per pixel" at this zoom
        # (higher = more map visible per pixel, better for overview)
        zoom_quality = 1.0 / widget.zoom if widget.zoom else 0
        
        device_info = f"{width}x{height}"
        print(f"{device_name:<25} {device_info:<20} {widget.zoom:.3f}    {zoom_quality:.1f}")
        
        # Check if zoom is reasonable (0.1 to 1.0)
        if not (0.1 < widget.zoom < 1.0):
            all_ok = False
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)
    
    print("\n" + "="*70)
    if all_ok:
        print("[RESULT] All devices scale correctly!")
    else:
        print("[RESULT] Some devices may have scaling issues")
    
    return all_ok


if __name__ == '__main__':
    try:
        test1 = test_floor_plan_scaling()
        test2 = test_different_screen_sizes()
        
        print("\n" + "="*70)
        if test1 and test2:
            print("[SUCCESS] All tests passed!")
            exit(0)
        else:
            print("[FAILURE] Some tests failed")
            exit(1)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        exit(1)
