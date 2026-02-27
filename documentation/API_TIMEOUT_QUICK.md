# Quick Fix: API Timeout

## Проблема
API запрос ждал 10 секунд перед fallback на локальный поиск.

## Решение
- Таймаут API: 10 сек → **5 сек** (глобально)
- Таймаут маршрутов: 10 сек → **2 сек** (специально)

## Результат
- До: 10 сек ожидания если API недоступна
- После: **2 сек ожидания** затем локальный поиск
- **Улучшение: 5x быстрее!** ✨

## Где изменено
1. `services/api_client.py` - `timeout=10` → `timeout=5`
2. `screens/map_screen.py` - добавлен таймаут 2 сек в `_fetch_route()`

## Логирование
```
Route from API: 150ms                 (если API работает)
Failed to get route from API (2000ms) (если таймаут)
Falling back to local pathfinding     (затем локальный поиск)
```

## Status
✅ Implemented  
✅ Tested  
✅ Documented  
✅ Ready
