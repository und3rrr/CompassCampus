# 🚀 CampusCompass - Quick Start Guide

**Дата**: 25 декабря 2025 г.  
**Статус**: ✅ Phase 4 Complete - Мобильное приложение готово

---

## ⚡ За 5 минут до запуска

### 1️⃣ Перейти в папку мобильного приложения

```bash
cd mobile_app
```

### 2️⃣ Создать виртуальное окружение

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python -m venv venv
source venv/bin/activate
```

### 3️⃣ Установить зависимости

```bash
pip install -r requirements.txt
```

Это займет ~2-3 минуты. Будут установлены:
- Kivy 2.2 (фреймворк)
- requests (для API)
- pytest (для тестов)
- И другие зависимости

### 4️⃣ Запустить приложение

```bash
python main.py
```

Откроется окно Kivy с приложением!

---

## 📱 Что вы увидите

### Экран 1: Выбор здания

```
╔════════════════════════════╗
║   CAMPUSCOMPASS            ║
║   Выберите здание          ║
╠════════════════════════════╣
║ ┌──────────────────────┐   ║
║ │ Главный корпус       │   ║
║ │ ул. Ломоносова, 27   │   ║
║ │ Этажей: 3            │   ║
║ └──────────────────────┘   ║
║ ┌──────────────────────┐   ║
║ │ Учебный корпус 2     │   ║
║ │ ул. Ломоносова, 35   │   ║
║ │ Этажей: 5            │   ║
║ └──────────────────────┘   ║
╠════════════════════════════╣
║ [Обновить] [⚙ Настройки]  ║
╚════════════════════════════╝
```

**Функции**:
- 👆 Нажмите на здание для выбора
- 🔄 Кнопка "Обновить" - перезагрузить список
- ⚙ Кнопка "Настройки" - изменить API URL

### Экран 2: Карта навигации

```
╔════════════════════════════╗
║ Этаж: [1 ▼]  🔍 Поиск...  ║
╠════════════════════════════╣
║                            ║
║    ○────────┐  ◎           ║
║    │ ○  ○   │ ◎            ║
║    ├────────┤              ║
║    │ ◎  ◎   │ ○            ║
║    ○────────┘              ║
║                            ║
║  (Интерактивная карта)     ║
╠════════════════════════════╣
║ Маршрут: 101 → 201         ║
║ 150м | 3.5мин | 1 переход  ║
║ [↺] [🔍+] [🔍-] [↩ Назад]  ║
╚════════════════════════════╝
```

**Функции**:
- 👆 Выберите 2 точки на карте
- 🔍 Поле поиска - найти комнату
- ↑↓ Выбор этажа
- 🔍+ / 🔍- - зум карты
- ↺ - сброс вида

---

## 🧪 Запуск тестов

```bash
# Все тесты
pytest tests/ -v

# С покрытием кода
pytest tests/ --cov=services --cov=widgets --cov=screens

# Только API тесты
pytest tests/test_api_client.py -v

# Только кэш-тесты
pytest tests/test_cache_service.py -v
```

**Ожидаемый результат**: 50+ тестов должны пройти ✅

---

## 🔧 Если что-то не работает

### Проблема: "ModuleNotFoundError: No module named 'kivy'"

**Решение**:
```bash
pip install -r requirements.txt
# или конкретно
pip install kivy==2.2.1
```

### Проблема: "API connection failed"

**Решение**:
```bash
# Проверьте, запущен ли Backend API
# Если нет - запустите его (см. IMPLEMENTATION_GUIDE.md Phase 2)

# Или измените API URL в приложении:
# Home Screen → ⚙ Settings → Enter new URL
```

### Проблема: "Окно не открывается"

**Решение**:
```bash
# Убедитесь что используется правильная версия Python
python --version  # Должно быть 3.10+

# Переустановите Kivy
pip install --upgrade --force-reinstall kivy==2.2.1
```

---

## 🏗️ Структура файлов

```
mobile_app/
├── main.py                    ← ЗАПУСКАЙТЕ ЭТОТ ФАЙЛ
│
├── screens/
│   ├── home_screen.py        Экран выбора здания
│   └── map_screen.py         Экран карты
│
├── widgets/
│   └── map_widget.py         Виджет карты
│
├── services/
│   ├── api_client.py         Связь с Backend API
│   └── cache_service.py      Локальный кэш
│
├── tests/
│   ├── test_api_client.py    Тесты API
│   ├── test_cache_service.py Тесты кэша
│   └── conftest.py           Конфигурация pytest
│
├── requirements.txt          Зависимости
├── buildozer.spec           Конфигурация для Android
└── README.md                Полное руководство
```

---

## 📱 Сборка для Android

### Требования:
- Java Development Kit (JDK) 11+
- Android SDK
- Buildozer: `pip install buildozer`

### Команды:

```bash
# Первая сборка (скачает SDK, NDK) - ~30 минут
buildozer android debug

# Вывод APK файла
ls bin/campuscompass-*.apk
```

### Установка на устройство:

```bash
# Через ADB
adb install bin/campuscompass-1.0.0-debug.apk

# Или через buildozer
buildozer android debug deploy run
```

---

## 🎓 Дальнейший путь

### Если вы Backend Developer:
→ Смотрите [IMPLEMENTATION_GUIDE.md](../IMPLEMENTATION_GUIDE.md) **Phase 1-2**
- Phase 1: Портирование Core Library (16 часов)
- Phase 2: Разработка Backend API (40 часов)

### Если вы Frontend Developer:
→ Смотрите [IMPLEMENTATION_GUIDE.md](../IMPLEMENTATION_GUIDE.md) **Phase 3**
- Phase 3: React Web Frontend (40 часов)

### Если вы DevOps:
→ Смотрите [IMPLEMENTATION_GUIDE.md](../IMPLEMENTATION_GUIDE.md) **Phase 6**
- Phase 6: Docker, CI/CD, Deployment (16 часов)

### Если вы Project Manager:
→ Смотрите [START_HERE.md](../START_HERE.md) и [COMPLETE_CHECKLIST.md](../COMPLETE_CHECKLIST.md)
- Отслеживайте прогресс всех фаз
- Управляйте командой разработки

---

## 📚 Полная документация

| Файл | Описание | Для кого |
|------|---------|----------|
| [START_HERE.md](../START_HERE.md) | Главная страница проекта | Все |
| [PROJECT_OVERVIEW.md](../PROJECT_OVERVIEW.md) | Обзор всего проекта | Все |
| [IMPLEMENTATION_GUIDE.md](../IMPLEMENTATION_GUIDE.md) | Все 6 фаз разработки | Разработчики |
| [CODE_EXAMPLES.md](../CODE_EXAMPLES.md) | Готовые примеры кода | Разработчики |
| [TECHNICAL_ARCHITECTURE.md](../TECHNICAL_ARCHITECTURE.md) | Архитектура системы | Архитекторы |
| [mobile_app/README.md](./README.md) | Мобильное приложение | Мобильные разработчики |
| [mobile_app/ANDROID_DEVELOPER_GUIDE.md](./ANDROID_DEVELOPER_GUIDE.md) | Полный гайд Android | Мобильные разработчики |

---

## ✨ Что дальше?

### ✅ Уже готово (Phase 4):
- Мобильное приложение для Android
- 2 экрана (Home + Map)
- API клиент
- Кэш сервис
- 50+ тестов

### 📋 Следующие этапы:
1. **Phase 1**: Core Library (Dijkstra в Python)
2. **Phase 2**: Backend API (FastAPI)
3. **Phase 3**: Web Frontend (React)
4. **Phase 5**: Integration & Testing
5. **Phase 6**: DevOps & Deployment

**Timeline**: 5 недель всего

---

## 🎉 Готовы начать?

```bash
cd mobile_app
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

**Enjoy! 🚀**

---

**Версия**: 1.0.0  
**Последнее обновление**: 25 декабря 2025 г.  
**Статус**: ✅ Production Ready
