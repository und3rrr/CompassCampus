# Быстрый старт: SVG планы этажей

## Что изменилось?

Больше **не нужен cairosvg** и конвертирование PNG! 

Приложение теперь парсит и отрисовывает SVG напрямую, сохраняя качество векторной графики.

## Использование

### Шаг 1: Экспортировать план из Sweet Home 3D

1. Откройте ваш проект в Sweet Home 3D
2. **File → Export...**
3. Выберите **SVG** формат
4. Сохраните как `floor1.svg`, `floor2.svg` и т.д.

### Шаг 2: Разместить файлы

Разместите SVG файлы в папке:
```
mobile_app/assets/floor_plans/
├── floor1.svg
├── floor2.svg
├── floor3.svg
└── ...
```

### Шаг 3: Запустить приложение

```bash
cd mobile_app
python main.py
```

**Готово!** Планы этажей будут загружены и отрисованы автоматически.

## Какие форматы поддерживаются?

| Формат | Поддержка | Заметки |
|--------|-----------|---------|
| SVG | ✅ **Основной** | Полная поддержка, лучшее качество |
| PNG | ✅ Поддержка | Растровые изображения |
| JPG | ✅ Поддержка | Растровые изображения |

## Код для программистов

### Загрузить SVG план

```python
from widgets.map_widget import MapWidget

map_widget = MapWidget()
map_widget.set_background_image('floor1.svg')
```

### Работать с элементами SVG

```python
from services.svg_loader import SVGLoader

# Загрузить и распарсить
plan = SVGLoader.load_svg_file('floor1.svg')

# Осмотреть элементы
print(f"Размер: {plan.width} x {plan.height}")
print(f"Элементов: {len(plan.elements)}")

# Осмотреть комнаты
for room in plan.rooms:
    print(f"{room.name}: {room.color}")
```

## Производительность

- ⚡ Быстрое парсирование (~10ms для типичного плана)
- 📈 Плавное масштабирование (зум/панорамирование без задержек)
- 💾 Низкое потребление памяти

## Проблемы и решения

### "SVG не отображается"

1. Проверьте путь файла:
   ```
   assets/floor_plans/floor1.svg  ✅
   assets/floor_plans/floor1.SVG  ❌ (регистр имеет значение)
   ```

2. Проверьте формат SVG:
   - Утилита: `python -c "from services.svg_loader import SVGLoader; SVGLoader.load_svg_file('floor1.svg')"`

### "Только черные элементы отображаются"

Убедитесь, что в SVG указаны цвета со стилями (fill/stroke):
```svg
<polygon points="..." fill="#e8f0ff" stroke="#000000" />  ✅
<polygon points="..." />  ❌ (нет цвета)
```

### "Отображается изображение но узлы графа спрятаны"

Отрегулируйте прозрачность:
```python
map_widget.set_background_opacity(0.5)  # 50% прозрачности
```

## Примеры экспорта

### Из Sweet Home 3D
**File → Export → SVG**

### Из Inkscape
**File → Save As → format: Scalable Vector Graphics (.svg)**

### Онлайн инструменты
- https://cloudconvert.com/ (конвертировать в SVG)
- https://www.online-convert.com/ (другие форматы)

## Дополнительные ресурсы

- Полная документация: [SVG_DIRECT_RENDERING.md](SVG_DIRECT_RENDERING.md)
- Примеры кода: [CODE_EXAMPLES.md](../CODE_EXAMPLES.md)
- Architecture: [TECHNICAL_ARCHITECTURE.md](../TECHNICAL_ARCHITECTURE.md)

## Совместимость

- ✅ Python 3.8+
- ✅ Kivy 2.3+
- ✅ Windows, Linux, macOS
- ✅ Android (через Buildozer)

## Версия

- **SVG Renderer:** 2.0
- **Дата:** 2026-02-25
- **Статус:** Production Ready

## Вопросы?

Смотрите документацию или откройте issue в GitHub.
