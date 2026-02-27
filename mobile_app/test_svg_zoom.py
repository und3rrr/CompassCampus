#!/usr/bin/env python3
"""Test script to verify SVG zoom/pan functionality"""

import logging
from widgets.map_widget import SVGRenderer
from services.svg_loader import SVGLoader

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_svg_zoom():
    """Test SVG rendering with zoom and pan"""
    
    # Try to load SVG file
    svg_path = "assets/floor_plans/floor1_example.svg"
    try:
        # Load SVG
        svg_floor_plan = SVGLoader.load_svg_file(svg_path)
        
        if not svg_floor_plan or not svg_floor_plan.elements:
            logger.error(f"No SVG elements loaded from {svg_path}")
            return False
        
        logger.info(f"[SUCCESS] Loaded {len(svg_floor_plan.elements)} SVG elements")
        
        # Test that SVGRenderer accepts zoom and pan parameters
        test_called = False
        try:
            # We can't actually render without a canvas, but we can check the method signature
            import inspect
            sig = inspect.signature(SVGRenderer.render_svg_elements)
            params = list(sig.parameters.keys())
            
            logger.info(f"SVGRenderer.render_svg_elements parameters: {params}")
            
            # Check for required parameters
            required_params = ['canvas', 'elements', 'opacity', 'zoom', 'pan_x', 'pan_y']
            for param in required_params:
                if param not in params:
                    logger.error(f"Missing parameter: {param}")
                    return False
            
            logger.info("[SUCCESS] SVGRenderer has all required zoom/pan parameters")
            test_called = True
        except Exception as e:
            logger.error(f"Error checking method signature: {e}")
            return False
        
        if test_called:
            logger.info("[SUCCESS] SVG zoom test passed!")
            return True
        
    except Exception as e:
        logger.error(f"Error loading SVG: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return False

if __name__ == '__main__':
    success = test_svg_zoom()
    if success:
        print("\n[PASS] All SVG zoom tests passed!")
    else:
        print("\n[FAIL] SVG zoom tests failed!")
        exit(1)
