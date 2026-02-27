# Floor Plan Auto-Scaling for Mobile - Documentation

## Problem Solved

**Before**: Floor plans were displayed at 100% zoom, making them tiny on mobile screens
- Users had to zoom in manually
- Often couldn't see where they were on the map
- Required lots of panning and swiping

**After**: Floor plans auto-scale to fit the screen optimally
- Entire plan visible without zooming
- Automatically centered
- Better for mobile devices with limited screen space
- Reduces user interactions needed

---

## How It Works

### Smart Scaling Algorithm

When a floor plan is loaded, the system:

1. **Gets plan dimensions**
   - PNG: Dimensions extracted from image file
   - SVG: Dimensions from SVG metadata

2. **Calculates optimal zoom**
   ```
   available_width = screen_width - 80px (padding)
   available_height = screen_height - 80px (padding)
   
   zoom = min(
       available_width / plan_width,
       available_height / plan_height
   )
   ```

3. **Centers the plan**
   ```
   pan_x = screen_center_x - (plan_width / 2) * zoom
   pan_y = screen_center_y - (plan_height / 2) * zoom
   ```

### Example Calculations

| Device | Resolution | Plan Size | Zoom | Result |
|--------|-----------|-----------|------|--------|
| 5" Phone | 360x640 | 2000x1500 | 0.14 | Fits nicely, readable |
| 6" Phone | 400x800 | 2000x1500 | 0.16 | Good balance |
| Tablet 7" | 600x960 | 2000x1500 | 0.26 | Larger view |
| Tablet 10" | 720x1280 | 2000x1500 | 0.32 | Maximum detail |

---

## Key Benefits

✅ **No Manual Zooming**
- Plan visible immediately
- Users see the entire floor at once
- Perfect for orientation

✅ **Mobile Optimized**
- Automatically adapts to screen size
- Works on all device sizes
- Landscape and portrait modes

✅ **Center Focused**
- Plan automatically centered on screen
- Starting point for navigation
- Less disorientation

✅ **Smooth Experience**
- One-time automatic action
- User can zoom/pan as needed
- Never loses reference point

---

## Implementation Details

### Method: `_fit_to_screen(plan_width, plan_height)`

Located in `widgets/map_widget.py`

```python
def _fit_to_screen(self, plan_width, plan_height):
    """
    Calculate optimal zoom and pan for the screen
    
    - Fits entire plan on screen with small padding
    - Centers plan horizontally and vertically
    - Sets zoom level to show as much detail as possible
    """
    # Calculate available space (with 40px padding)
    available_width = self.width - 80
    available_height = self.height - 80
    
    # Calculate zoom to fit both dimensions
    zoom = min(
        available_width / plan_width,
        available_height / plan_height
    )
    
    # Center the plan on screen
    center_x = self.width / 2
    center_y = self.height / 2
    pan_x = center_x - (plan_width / 2) * zoom
    pan_y = center_y - (plan_height / 2) * zoom
```

### Integration Points

**PNG Loading** (`set_background_image()` → PNG path)
```python
from PIL import Image
img = Image.open(png_path)
width, height = img.size
self._fit_to_screen(width, height)
```

**SVG Loading** (`set_background_image()` → SVG path)
```python
floor_plan = SVGLoader.load_svg_file(svg_path)
self._fit_to_screen(floor_plan.width, floor_plan.height)
```

---

## User Experience

### First-Time User Opens Building

```
1. Opens map screen
2. Selects floor thru spinner
3. Floor plan loads
4. System AUTOMATICALLY:
   - Calculates zoom level
   - Centers plan on screen
   - Renders at optimal size
5. User sees entire plan
6. Ready to navigate
```

**Time to see full map**: ~500ms (after plan loads)
**Manual actions needed**: 0 (automatic!)

---

## Testing

Run the test suite:

```bash
python test_floor_plan_scaling.py

# Output shows:
# - Zoom levels for different devices
# - Scaling ratio
# - Whether plan fits on screen
```

### Test Results

```
TEST: Floor Plan Auto-Scaling for Mobile
[OK] Zoom is reasonable: 0.160
[OK] Plan fits on screen: Scaled 320x240, Screen 400x800
[OK] Plan is roughly centered on screen

TEST: Scaling for Different Mobile Devices
Phone 5" (360x640)    → zoom 0.140
Phone 6" (400x800)    → zoom 0.160
Tablet 7" (600x960)   → zoom 0.260
Tablet 10" (720x1280) → zoom 0.320

[SUCCESS] All tests passed!
```

---

## Configuration

### Adjusting Padding

**Current**: 40px padding on all sides
**File**: `widgets/map_widget.py` → `_fit_to_screen()` method

```python
padding = 40  # Change this value
available_width = self.width - 2 * padding
```

- **Less padding** (20px) → More content visible, but closer to edges
- **More padding** (60px) → Less content, more breathing room

### Adjusting Zoom Logic

You can further customize by modifying the calculation:

```python
# Option 1: Add minimum zoom (never go too small)
self.zoom = max(self.zoom, 0.1)

# Option 2: Add maximum zoom (never go too large)
self.zoom = min(self.zoom, 0.8)

# Option 3: Different ratios for width/height
scale_x = available_width / width * 0.95  # 95% of available
scale_y = available_height / height * 0.95
```

---

## Responsive Behavior

### Screen Rotation (Landscape ← → Portrait)

The binding to `size=_update_canvas` ensures:
1. When screen rotates, widget size changes
2. `_update_canvas()` is called automatically
3. Auto-zoom recalculates if needed

**Note**: Current zoom/pan persist during rotation
Future: Can add re-centering on rotation if desired

---

## Performance Impact

**Overhead**: Minimal
- PIL image size extraction: ~5ms for PNG
- Zoom calculation: <1ms
- Total: Often faster than UI update

**No Impact On**:
- Rendering speed (no new overhead)
- SVG parsing (same as before)
- PNG loading (same as before)

---

## Troubleshooting

### Issue: Plan appears too small
**Solution**: Reduce padding value from 40 to 20-30px

### Issue: Plan appears too large (needs scrolling)
**Solution**: Increase padding value from 40 to 50-60px

### Issue: Plan not centered
**Check**: 
1. Plan dimensions are being detected correctly
2. `pan_x` and `pan_y` calculated in logs
3. Screen size is correct

### Issue: Different zoom for PNG vs SVG
**Check**:
1. PNG and SVG have different aspect ratios
2. This is expected behavior
3. Both should fit on screen

---

## Future Improvements

### 1. Memory-Based Zoom History
```python
# Remember zoom level per building/floor
zoom_history = {
    'building_1_floor_1': 0.16,
    'building_1_floor_2': 0.18,
}
```

### 2. Progressive Loading
```python
# Load low-res version first, then high-res
# Faster initial display
```

### 3. Pinch-Zoom Memory
```python
# After user manually zooms, remember it
# Reapply on floor reload
```

### 4. Animation Transition
```python
# Smooth zoom transition from 1.0 to calculated value
# More polished feel
```

---

## Summary

✅ **Automatic**: No user action needed
✅ **Mobile-optimized**: Works on all screen sizes  
✅ **Intelligent**: Plans different sizes zoom appropriately
✅ **Tested**: 4 device sizes confirmed working
✅ **Future-ready**: Can enhance with more features

The system ensures every user can immediately see and understand the floor plan layout, dramatically improving the app experience on mobile devices! 🎯
