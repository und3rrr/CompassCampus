# Zoom Center - Quick Fix

## Проблема ✅ Чинено

Зум приближал/отдалял вбок вместо центра экрана.

## Решение

При зуме сохраняем точку в центре экрана:

```python
# 1. Что в центре?
center_x, center_y = self._screen_to_world(self.width/2, self.height/2)

# 2. Меняем zoom
self.zoom *= 1.1

# 3. Пересчитываем pan чтобы центр остался в центре
self.pan_x = self.width/2 - center_x * self.zoom
self.pan_y = self.height/2 - center_y * self.zoom
```

## Где изменено

| Файл | Методы |
|------|--------|
| `widgets/visual_graph_editor.py` | `on_scroll_down()`, `on_scroll_up()` |
| `widgets/map_widget.py` | `on_scroll_down()`, `on_scroll_up()`, `zoom_in()`, `zoom_out()` |

## До/После

| Операция | Было | Стало |
|----------|------|-------|
| Зум вверх | Смещается вбок | Центрирован ✅ |
| Зум вниз | Смещается вбок | Центрирован ✅ |

---

✅ Зум теперь работает правильно!
