#!/usr/bin/env python3
"""Integration test to verify SVG zoom/pan synchronization with graph nodes"""

import logging
from widgets.map_widget import MapWidget, SVGRenderer
from services.svg_loader import SVGLoader
from services.api_client import Node

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_svg_zoom_integration():
    """Test SVG zoom/pan integration with MapWidget"""
    
    try:
        # Load SVG file
        svg_path = "assets/floor_plans/floor1_example.svg"
        svg_floor_plan = SVGLoader.load_svg_file(svg_path)
        
        if not svg_floor_plan or not svg_floor_plan.elements:
            logger.error(f"No SVG elements loaded from {svg_path}")
            return False
        
        logger.info(f"[1/4] Loaded {len(svg_floor_plan.elements)} SVG elements - OK")
        
        # Create a MapWidget instance
        map_widget = MapWidget()
        
        # Verify initial state
        if map_widget.zoom != 1.0:
            logger.error(f"Initial zoom should be 1.0, got {map_widget.zoom}")
            return False
        
        if map_widget.pan_x != 0.0 or map_widget.pan_y != 0.0:
            logger.error(f"Initial pan should be (0, 0), got ({map_widget.pan_x}, {map_widget.pan_y})")
            return False
        
        logger.info(f"[2/4] MapWidget initial state verified - OK")
        
        # Set SVG elements
        map_widget.svg_elements = svg_floor_plan.elements
        
        logger.info(f"[3/4] SVG elements assigned to MapWidget - OK")
        
        # Add some test nodes
        nodes = [
            Node(id='Room_1', name='Room 1', x=200, y=200, node_type='Room', floor=1),
            Node(id='Room_2', name='Room 2', x=450, y=200, node_type='Room', floor=1),
        ]
        map_widget.set_nodes(nodes)
        
        # Test zoom functionality
        logger.info("Testing zoom functionality...")
        
        # Zoom in
        initial_zoom = map_widget.zoom
        map_widget.zoom_in()
        zoomed_in = map_widget.zoom
        
        if zoomed_in <= initial_zoom:
            logger.error(f"Zoom in failed: {initial_zoom} -> {zoomed_in}")
            return False
        
        logger.info(f"  Zoom in: {initial_zoom} -> {zoomed_in} - OK")
        
        # Zoom out
        map_widget.zoom_out()
        zoomed_out = map_widget.zoom
        
        if zoomed_out >= zoomed_in or zoomed_out < initial_zoom:
            logger.error(f"Zoom out failed: {zoomed_in} -> {zoomed_out}")
            return False
        
        logger.info(f"  Zoom out: {zoomed_in} -> {zoomed_out} - OK")
        
        # Verify _world_to_screen transformation works with zoom
        world_x, world_y = 100, 100
        screen_x, screen_y = map_widget._world_to_screen(world_x, world_y)
        
        # At zoom 1.0, screen coords should equal world coords + pan
        if screen_x != world_x + map_widget.pan_x or screen_y != world_y + map_widget.pan_y:
            logger.error(f"World to screen transformation failed")
            return False
        
        logger.info(f"  World-to-screen transformation verified - OK")
        
        # Verify SVGRenderer._transform_point works
        tx, ty = SVGRenderer._transform_point(100, 100, map_widget.zoom, map_widget.pan_x, map_widget.pan_y)
        if tx != screen_x or ty != screen_y:
            logger.error(f"SVGRenderer._transform_point doesn't match _world_to_screen")
            return False
        
        logger.info(f"  SVGRenderer._transform_point verified - OK")
        
        logger.info(f"[4/4] SVG zoom integration test completed - OK")
        
        return True
        
    except Exception as e:
        logger.error(f"Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_svg_zoom_integration()
    if success:
        print("\n[PASS] SVG zoom integration test PASSED!")
        print("\nSummary:")
        print("  - SVG elements loaded correctly")
        print("  - MapWidget initialized with proper state")
        print("  - Zoom in/out functions work")
        print("  - World-to-screen transformation is correct")
        print("  - SVG zoom/pan parameters are properly implemented")
        exit(0)
    else:
        print("\n[FAIL] SVG zoom integration test FAILED!")
        exit(1)
