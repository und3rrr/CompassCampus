# CampusCompass2 - Полная документация для переноса на новые платформы

## 📋 Обзор

CampusCompass2 - это система навигации по университетскому кампусу, которая позволяет пользователям находить кратчайшие маршруты между помещениями в многоэтажных зданиях.

**Текущее состояние:** Windows Forms приложение (C#)  
**Целевые платформы:** Веб-сайт, Android, iOS (через Python)

---

## 📚 ДОКУМЕНТЫ

### 1. **PRD.md** - Product Requirements Document
📖 **[PRD.md](PRD.md)**

Полное описание продукта:
- ✅ Обзор и целевая аудитория
- ✅ Ключевые особенности
- ✅ Технические требования
- ✅ Требования к производительности
- ✅ Unit-тесты
- ✅ UI/UX требования
- ✅ Roadmap на 4 фазы

**Читайте когда:** Нужно понять что такое CampusCompass2 и какой функционал нужен

---

### 2. **TECHNICAL_ARCHITECTURE.md** - Техническая архитектура
📖 **[TECHNICAL_ARCHITECTURE.md](TECHNICAL_ARCHITECTURE.md)**

Детальная архитектура для переноса на новые платформы:
- ✅ Текущая архитектура vs Целевая архитектура
- ✅ Модульная структура Core Library
- ✅ Backend API архитектура (FastAPI)
- ✅ Frontend структура (React)
- ✅ Mobile приложение (Python/Kivy)
- ✅ Схема базы данных (PostgreSQL)
- ✅ API Endpoints спецификация
- ✅ Docker & Kubernetes
- ✅ Миграция данных из C#

**Читайте когда:** Нужно спланировать архитектуру системы на новых платформах

---

### 3. **IMPLEMENTATION_GUIDE.md** - Руководство по реализации
📖 **[IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)**

Пошаговое руководство по разработке:
- ✅ Фаза 1: Выделение Core Library
- ✅ Фаза 2: Backend API (FastAPI)
- ✅ Фаза 3: Web Frontend (React)
- ✅ Фаза 4: Mobile App (Kivy)
- ✅ Фаза 5: Интеграция и тестирование
- ✅ Фаза 6: Развёртывание
- ✅ Контрольный список
- ✅ Временные оценки (168 часов)
- ✅ Примеры кода для каждой фазы

**Читайте когда:** Готовы начать разработку и нужны пошаговые инструкции

---

### 4. **CODE_EXAMPLES.md** - Примеры кода
📖 **[CODE_EXAMPLES.md](CODE_EXAMPLES.md)**

Готовые примеры кода для всех компонентов:
- ✅ Core Library (Python)
- ✅ Backend API (FastAPI)
- ✅ Web Frontend (React/TypeScript)
- ✅ Mobile App (Kivy/Python)
- ✅ API тесты
- ✅ Быстрый старт для каждой платформы

**Читайте когда:** Нужны конкретные примеры кода для начала разработки

---

## 🗺️ СТРУКТУРА ПРОЕКТА

```
CampusCompass2/
├── PRD.md                          # Product Requirements Document
├── TECHNICAL_ARCHITECTURE.md       # Техническая архитектура
├── IMPLEMENTATION_GUIDE.md         # Пошаговое руководство
├── CODE_EXAMPLES.md               # Примеры кода
├── README.md                      # Этот файл
│
├── CampusCompass2/               # Текущее Windows Forms приложение
│   ├── NavigationForm.cs
│   ├── BuildingMap.cs
│   ├── Dijkstra.cs              # ← Ядро алгоритма
│   ├── Node.cs
│   ├── Edge.cs
│   └── ...
│
├── core_library/                 # (будет создана) Python Core Library
│   ├── core/
│   │   ├── models/
│   │   │   ├── node.py
│   │   │   ├── edge.py
│   │   │   └── building.py
│   │   ├── graph/
│   │   │   ├── dijkstra.py     # Портирована из C#
│   │   │   └── graph.py
│   │   └── cache/
│   │       └── route_cache.py
│   └── tests/
│
├── backend/                     # (будет создана) FastAPI Backend
│   ├── app/
│   │   ├── api/v1/endpoints/
│   │   ├── services/
│   │   ├── models/db/
│   │   └── main.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend-web/               # (будет создана) React Frontend
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── App.tsx
│   ├── package.json
│   └── Dockerfile
│
└── mobile-app/                # (будет создана) Kivy Mobile App
    ├── screens/
    ├── services/
    ├── main.py
    ├── buildozer.spec
    └── requirements.txt
```

---

## 🚀 БЫСТРЫЙ СТАРТ

### Для понимания проекта:
1. Прочитайте [PRD.md](PRD.md) - 15 минут
2. Посмотрите [TECHNICAL_ARCHITECTURE.md](TECHNICAL_ARCHITECTURE.md) - 30 минут

### Для разработки:
1. Начните с [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md) - Фаза 1
2. Используйте примеры из [CODE_EXAMPLES.md](CODE_EXAMPLES.md)
3. Выполните контрольный список в Фазе 1

---

## 📊 ОСНОВНЫЕ КОМПОНЕНТЫ

### Core Library (Переносимое ядро)
```python
# Используется везде: Backend, Web, Mobile
from core.graph.dijkstra import Dijkstra
from core.models.node import Node, NodeType
from core.cache.route_cache import RouteCache

path, error = Dijkstra.find_shortest_path(nodes, edges, start_id, end_id)
```

### Backend API (FastAPI)
```
GET  /api/v1/routes/shortest         # Расчёт маршрута
POST /api/v1/routes/calculate-multiple
GET  /api/v1/buildings               # Список зданий
GET  /api/v1/search                  # Поиск помещений
```

### Web Frontend (React)
- Interactive Canvas для визуализации карты
- Real-time маршрутизация
- Responsive design для мобильных браузеров

### Mobile App (Kivy)
- Native UI для Android/iOS
- Offline mode
- GPS интеграция (для будущих версий)

---

## 📈 TIMELINE

| Фаза | Компонент | Часы | Сложность |
|------|-----------|------|-----------|
| 1 | Core Library (Python) | 16 | ⭐ |
| 2 | Backend API | 40 | ⭐⭐ |
| 3 | Web Frontend | 40 | ⭐⭐ |
| 4 | Mobile App | 32 | ⭐⭐⭐ |
| 5 | Тестирование | 24 | ⭐⭐ |
| 6 | Deployment | 16 | ⭐ |
| **ИТОГО** | | **168 часов** | |

**~4-5 недель** при 8-часовом рабочем дне на одного разработчика

---

## 💾 КЛЮЧЕВЫЕ ФАЙЛЫ ДЛЯ ПОРТИРОВАНИЯ

### Из Windows Forms (C#) в Python:

| C# файл | Python файл | Что портировать |
|---------|------------|-----------------|
| Dijkstra.cs | dijkstra.py | Алгоритм поиска пути |
| Node.cs | models/node.py | Структура узла |
| Edge.cs | models/edge.py | Структура ребра |
| BuildingMap.cs | models/building.py | Модель здания |
| RouteTests.cs | tests/test_dijkstra.py | Unit-тесты |
| map.json | database | Хранение в PostgreSQL |

---

## 🔄 АРХИТЕКТУРНЫЙ ПАТТЕРН

```
┌─────────────────────────────────┐
│  Frontend Applications          │
│  ┌──────────┐  ┌─────────────┐ │
│  │   Web    │  │   Mobile    │ │
│  │ (React)  │  │   (Kivy)    │ │
│  └────┬─────┘  └──────┬──────┘ │
└───────┼────────────────┼────────┘
        │                │
        └────────┬───────┘
                 │ REST API
        ┌────────▼────────┐
        │  Backend API    │
        │   (FastAPI)     │
        └────────┬────────┘
                 │
        ┌────────▼────────┐
        │  Core Library   │
        │   (Python)      │
        │                 │
        │ • Dijkstra      │
        │ • BuildingMap   │
        │ • RouteCache    │
        └────────┬────────┘
                 │
        ┌────────▼────────┐
        │  Database       │
        │ (PostgreSQL)    │
        └─────────────────┘
```

---

## 🧪 ТЕСТИРОВАНИЕ

### Levels:
1. **Unit Tests** - Тестирование Dijkstra алгоритма
2. **Integration Tests** - Backend + Database
3. **E2E Tests** - Полный цикл: Frontend → API → Database
4. **Performance Tests** - Граф с 5000+ узлов

```bash
# Запуск тестов
pytest tests/ -v --cov=app
```

---

## 🚢 РАЗВЁРТЫВАНИЕ

### Docker Compose (локально):
```bash
docker-compose up
# http://localhost:3000 - Web
# http://localhost:8000/docs - API
```

### Production (Cloud):
```bash
# Kubernetes / AWS ECS
# Database: AWS RDS PostgreSQL
# Cache: AWS ElastiCache Redis
# Frontend: CloudFront CDN
```

---

## 📱 ПОДДЕРЖИВАЕМЫЕ ПЛАТФОРМЫ

| Платформа | Статус | Примечание |
|-----------|--------|-----------|
| Windows Desktop | ✅ Текущая | C# WinForms |
| Web (Chrome, Firefox, Safari) | 🔄 В разработке | React |
| Android | 🔄 В разработке | Python/Kivy |
| iOS | 📋 Планируется | Python/Kivy или Swift |

---

## 🤝 КОНТРИБЬЮТЕРАМ

### Подготовка к разработке:

1. **Клонируйте репозиторий**
   ```bash
   git clone <repo>
   cd CampusCompass2
   ```

2. **Прочитайте PRD.md**
   ```bash
   cat PRD.md
   ```

3. **Выберите фазу разработки**
   - Фаза 1-2: Backend разработчики
   - Фаза 3: Frontend разработчики
   - Фаза 4: Mobile разработчики
   - Фаза 5-6: DevOps инженеры

4. **Следуйте IMPLEMENTATION_GUIDE.md**

---

## ❓ ЧАСТО ЗАДАВАЕМЫЕ ВОПРОСЫ

### Q: Почему Python вместо C#?
**A:** Python имеет лучшую экосистему для кроссплатформных приложений (FastAPI, Kivy) и более простой синтаксис для мобилки.

### Q: Почему Kivy а не Flutter?
**A:** Kivy позволяет использовать один код (Python) для Android и iOS. Flutter требует Dart.

### Q: Сколько будет стоить хостинг?
**A:** $20-50/месяц для малого кампуса. Масштабируется линейно с количеством зданий.

### Q: Как обновлять карту в реальном времени?
**A:** WebSocket для live обновлений (Фаза 2 - Future).

---

## 📞 КОНТАКТЫ И ПОДДЕРЖКА

- 📧 Email: [support@campuscompass.org](mailto:support@campuscompass.org)
- 🐛 Bug Reports: GitHub Issues
- 💬 Discussions: GitHub Discussions
- 📖 Documentation: [docs.campuscompass.org](https://docs.campuscompass.org)

---

## 📄 ЛИЦЕНЗИЯ

MIT License - Свободное использование в коммерческих и личных проектах

---

## 🙏 СПАСИБО

Спасибо за использование CampusCompass2!

**Последнее обновление:** 24 декабря 2025 г.

---

## 📚 ДОПОЛНИТЕЛЬНЫЕ РЕСУРСЫ

### Документация
- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://react.dev/)
- [Kivy](https://kivy.org/)
- [SQLAlchemy](https://sqlalchemy.org/)

### Примеры
- [FastAPI Todo App](https://github.com/tiangolo/fastapi/tree/master/examples)
- [React Navigation](https://github.com/facebook/react)
- [Kivy Gallery](https://github.com/kivy/kivy/tree/master/examples)

### Инструменты
- IDE: VS Code, PyCharm
- API Testing: Postman, Insomnia
- Database: DBeaver, pgAdmin
- Monitoring: Datadog, NewRelic

---

## 🎯 NEXT STEPS

1. ✅ **Прочитайте эту документацию** (15 минут)
2. ⬜ **Начните Фазу 1** - Core Library (16 часов)
3. ⬜ **Начните Фазу 2** - Backend API (40 часов)
4. ⬜ **Начните Фазу 3** - Web Frontend (40 часов)
5. ⬜ **Начните Фазу 4** - Mobile App (32 часов)

**Удачи в разработке! 🚀**

