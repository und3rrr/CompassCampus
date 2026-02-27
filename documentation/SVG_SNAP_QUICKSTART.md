# Quick Start: SVG & Snap-to-Grid Features

## 🎯 What's New

Your app now supports:
1. **SVG Floor Plans** - Display architectural plans under the graph
2. **Snap-to-Grid** - Nodes align to a 20px grid for organized layout
3. **Snap-to-SVG** - Nodes automatically align to room centers and elements
4. **Per-Floor Management** - Different SVG file per floor in editor

## 📱 Using in Map View

### Automatic Loading
- Just select a floor from the dropdown
- Floor plan SVG loads automatically
- Nodes display over the plan
- Routes show connections

**That's it!** No configuration needed.

## ✏️ Using in Editor View

### View/Change Floor Plan

1. Select floor from spinner
2. Click **"📷 Фон"** button (background/image in Russian)
3. Browse and select SVG or PNG file
4. Plan loads behind the nodes

### Edit Nodes with Snapping

**Drag to move nodes:**
- Nodes snap to 20px grid (automatic)
- When close to a room, nodes snap to room center
- Release to finalize position

**Grid is visible as light gray lines when you drag**

### Toggle Grid Snapping

In editor code, you can toggle:
```python
# In VisualGraphEditor
editor.toggle_snap_to_grid()  # Toggle on/off
editor.toggle_snap_to_grid(enabled=True)  # Force on
```

## 📂 Adding Your Own Floor Plans

1. Create SVG files of your building floors
2. Save to: `assets/floor_plans/`
3. Name pattern (one of these):
   - `floor1.svg`, `floor2.svg` ✅
   - `floor_1.svg`, `etaj_2.svg` ✅
   - `level1.svg`, `floor1_classroom.svg` ✅
   - `1floor.svg`, `1этаж.svg` ✅

4. App auto-detects and maps files to floor numbers

### Example SVG (SimpleBox Format)

```xml
<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="800">
  <!-- Rooms as polygons -->
  <polygon points="100,100 300,100 300,300 100,300"
           fill="#cce5ff" stroke="black" stroke-width="2"/>
  
  <!-- Can also use circles or rectangles -->
  <circle cx="450" cy="400" r="50" fill="#ccffcc" stroke="black"/>
  <rect x="600" y="100" width="200" height="150" 
        fill="#ffffcc" stroke="black" stroke-width="2"/>
</svg>
```

## ⚙️ Configuration

### Change Grid Size

In [widgets/visual_graph_editor.py](widgets/visual_graph_editor.py):

```python
self.grid_size = dp(20)  # Change 20 to desired grid size
```

### Change Snap Radius

In [widgets/visual_graph_editor.py](widgets/visual_graph_editor.py):

```python
# In snap_node_to_svg_elements() method
if dist < 50 and dist < min_distance:  # Change 50 to snap distance
```

### Disable Snapping

```python
# Default is enabled
snap_to_grid_enabled = False  # In VisualGraphEditor.__init__
```

## 🧪 Testing Features

Run quick test:
```bash
python test_svg_integration.py
```

This verifies:
- ✅ Floor plans auto-detected
- ✅ SVG loaded without errors
- ✅ Snap-to-grid works
- ✅ All components integrated

## 🎨 Visual Behavior

### Grid Overlay
- Light gray grid lines visible when dragging node
- Helps visualize snap positions
- Disappears when not dragging

### SVG Display
- Semi-transparent (30% opacity) behind nodes
- Rooms visible as colored shapes
- Text labels visible if defined in SVG

### Snap Feedback
- Nodes move smoothly to snap position
- No animation (instant snap)
- Success is silent (node stationary)

## 🐛 Troubleshooting

**SVG not showing in editor?**
- Check if file exists in `assets/floor_plans/`
- Verify SVG is valid XML
- Check browser console for errors

**Nodes not snapping to grid?**
- `snap_to_grid_enabled` should be `True`
- Check `grid_size` is not 0
- Verify node is being dragged (not just clicked)

**Nodes not snapping to SVG elements?**
- Ensure SVG has polygons/circles with defined positions
- Check snap radius (default 50 units)
- Verify elements are within the canvas bounds

## 📚 Related Files

- [SVG_SNAP_IMPLEMENTATION.md](SVG_SNAP_IMPLEMENTATION.md) - Technical details
- [services/floor_plan_manager.py](services/floor_plan_manager.py) - Floor plan management
- [widgets/visual_graph_editor.py](widgets/visual_graph_editor.py) - Snap implementation
- [services/svg_loader.py](services/svg_loader.py) - SVG parsing

## ✅ What's Included

```
✅ Layout fix (no more button overlap)
✅ Automatic SVG detection
✅ Per-floor SVG management
✅ Snap-to-grid (20px default)
✅ Snap-to-SVG-elements (50px radius)
✅ Grid visualization
✅ Full integration testing
```

**You're ready to use! 🚀**
