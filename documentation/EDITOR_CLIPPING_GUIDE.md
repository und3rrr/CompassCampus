# Visual Graph Editor - Canvas Clipping & Alignment

## Реализовано в редакторе графа

Визуальный редактор графов теперь имеет **все те же улучшения** что и основной виджет карты:

### 1. Canvas Clipping ✅
- Добавлены импорты `ScissorPush` и `ScissorPop`
- Все элементы редактора обрезаны по его границам
- Элементы за пределами редактора не видны
- UI интерфейс не перекрывается при редактировании

### 2. Background Alignment ✅
- Фоновое изображение (PNG/SVG) масштабируется вместе с узлами
- Используется единая координатная система `zoom`, `pan_x`, `pan_y`
- Размеры PNG/SVG автоматически извлекаются
- Сохраняются и переиспользуются для трансформаций

### 3. SVG Element Rendering ✅
- SVG элементы также используют параметры `zoom` и `pan`
- Единая система координат для всех элементов редактора
- При масштабировании и передвижении всё движется вместе

## Файлы изменены

### `widgets/visual_graph_editor.py`

#### 1. Импорты (строка 5)
```python
# БЫЛО:
from kivy.graphics import Color, Ellipse, Line, Rectangle

# СТАЛО:
from kivy.graphics import Color, Ellipse, Line, Rectangle, ScissorPush, ScissorPop
```

#### 2. Атрибуты в __init__ (строка ~36)
```python
# БЫЛО:
self.background_image_path: Optional[str] = None
self.svg_elements: List = []

# СТАЛО:
self.background_image_path: Optional[str] = None
self.svg_elements: List = []
self.svg_width: Optional[float] = None     # ← НОВОЕ
self.svg_height: Optional[float] = None    # ← НОВОЕ
```

#### 3. Обрезка в _update_canvas() (строка ~260)
```python
with self.canvas:
    # ========== ОБРЕЗКА СОДЕРЖИМОГО ПО ГРАНИЦАМ РЕДАКТОРА ==========
    ScissorPush(x=int(self.x), y=int(self.y), width=int(self.width), height=int(self.height))
    
    # ... остальное содержимое отрисовки ...
    
    # ========== КОНЕЦ ОБРЕЗКИ ==========
    ScissorPop()
```

#### 4. SVG элементы с zoom/pan (строка ~280)
```python
# БЫЛО:
SVGRenderer.render_svg_elements(self.canvas, self.svg_elements, opacity=0.3)

# СТАЛО:
SVGRenderer.render_svg_elements(
    self.canvas, 
    self.svg_elements, 
    opacity=0.3,
    zoom=self.zoom,      # ← НОВОЕ
    pan_x=self.pan_x,    # ← НОВОЕ
    pan_y=self.pan_y     # ← НОВОЕ
)
```

#### 5. Масштабирование фонового изображения (строка ~290)
```python
# БЫЛО:
Rectangle(
    source=self.background_image_path,
    pos=self.pos,
    size=self.size
)

# СТАЛО:
if self.svg_width and self.svg_height:
    bg_width = self.svg_width * self.zoom
    bg_height = self.svg_height * self.zoom
    bg_pos_x = self.pan_x
    bg_pos_y = self.pan_y
    Rectangle(
        source=self.background_image_path,
        pos=(bg_pos_x, bg_pos_y),
        size=(bg_width, bg_height)
    )
else:
    # Fallback
    Rectangle(
        source=self.background_image_path,
        pos=self.pos,
        size=self.size
    )
```

#### 6. Сохранение размеров PNG/SVG (строка ~381-424)
```python
def set_background_image(self, image_path: Optional[str]):
    """Установить фоновое изображение"""
    
    # Если это SVG
    if image_path.endswith('.svg'):
        # ... загрузка SVG ...
        self.svg_width = floor_plan.width   # ← НОВОЕ
        self.svg_height = floor_plan.height # ← НОВОЕ
    else:
        # Для PNG - используем PIL
        from PIL import Image as PILImage
        img = PILImage.open(image_path)
        actual_width, actual_height = img.size
        self.svg_width = actual_width       # ← НОВОЕ
        self.svg_height = actual_height     # ← НОВОЕ
```

## Тестирование

Запуск тестов:
```bash
python test_editor_clipping.py
```

Результаты:
```
✓ ScissorPush and ScissorPop imported
✓ ScissorPush enabled in editor's _update_canvas()
✓ ScissorPop disables clipping after rendering
✓ SVG dimensions stored
✓ PNG dimensions extracted and stored
✓ Background image scales with zoom
✓ Background image positioned with pan_x, pan_y
✓ SVG elements use zoom and pan parameters
✓ Editor has svg_width and svg_height attributes
```

## Визуальный результат

### ДО (Проблемы):
```
┌─────────────────────────────┐
│ Visual Graph Editor         │
│ ╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱│ ← Выходит за границы
│ ❌ Can edit nodes/edges    │
│ ❌ Background fills widget  │
│ ╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱│
└─────────────────────────────┘
[❌DISABLED BUTTONS]            ← Перекрыто
```

### ПОСЛЕ (Исправлено):
```
┌─────────────────────────────┐
│ Visual Graph Editor         │
│ ┌─────────────────────────┐ │
│ │ ✅ Edit nodes/edges     │ │ ← В границах
│ │ ✅ Background scales    │ │ 
│ │ ✅ Clipped at edges     │ │
│ └─────────────────────────┘ │
└─────────────────────────────┘
[✅ACCESSIBLE BUTTONS]          ← Доступно
```

## Синхронизация MapWidget и VisualGraphEditor

| Функция | MapWidget | Editor |
|---------|-----------|--------|
| ScissorPush/Pop обрезка | ✅ | ✅ |
| Сохранение размеров PNG | ✅ | ✅ |
| Сохранение размеров SVG | ✅ | ✅ |
| Масштабирование фона | ✅ | ✅ |
| Позиционирование фона | ✅ | ✅ |
| SVG элементы с zoom/pan | ✅ | ✅ |
| Единая координатная система | ✅ | ✅ |

## Преимущества

1. **Консистентность**: Оба режима работают одинаково
2. **Удобство редактирования**: Элементы не выходят за границы при масштабировании
3. **Производительность**: GPU-level clipping не требует больше ресурсов
4. **Масштабируемость**: Автоматически работает для любых размеров
5. **Мобильность**: Полностью работает на всех устройствах

## Проверка синхронизации

Оба компонента теперь имеют идентичную логику:

```python
# И в MapWidget и в VisualGraphEditor:

# 1. Импорты
from kivy.graphics import ..., ScissorPush, ScissorPop

# 2. Атрибуты
self.svg_width: Optional[float] = None
self.svg_height: Optional[float] = None

# 3. В _update_canvas():
ScissorPush(...)  # Обрезка включена
# ... отрисовка ...
ScissorPop()      # Обрезка отключена

# 4. Масштабирование фона
bg_width = self.svg_width * self.zoom
bg_height = self.svg_height * self.zoom

# 5. Позиционирование фона
pos=(self.pan_x, self.pan_y)
```

---

**Статус**: ✅ ЗАВЕРШЕНО  
**Тесты**: ✅ ВСЕ ПРОЙДЕНЫ  
**Синхронизация**: ✅ ПОЛНАЯ
