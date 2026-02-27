# Руководство по реализации CampusCompass2 на новых платформах
## Веб-сайт, Python приложение (Android/iOS)

### Версия: 1.0
### Дата: 24 декабря 2025 г.

---

## СОДЕРЖАНИЕ

1. Выделение и подготовка Core Library
2. Создание Backend API
3. Разработка веб-интерфейса
4. Разработка мобильного приложения
5. Интеграция и тестирование
6. Развёртывание

---

## ФАЗА 1: ВЫДЕЛЕНИЕ CORE LIBRARY

### Шаг 1.1: Реструктуризация текущего кода

#### 1.1.1 Создать Python версию Core компонентов

Скопировать логику из C# в Python:

```
┌─────────────────────────────────────┐
│   C# CampusCompass2 (текущее)      │
│   - Dijkstra.cs                     │
│   - BuildingMap.cs                  │
│   - Node.cs                         │
│   - Edge.cs                         │
└─────────┬───────────────────────────┘
          │ (Extract & Port)
          ▼
┌─────────────────────────────────────┐
│   Python Core Library (новое)       │
│   - dijkstra.py                     │
│   - building_map.py                 │
│   - models/node.py                  │
│   - models/edge.py                  │
│   - cache/route_cache.py            │
│   - utils/validators.py             │
└─────────────────────────────────────┘
```

#### 1.1.2 Список файлов для создания

```
core_library/
├── core/
│   ├── __init__.py
│   ├── version.py                 # "1.0.0"
│   ├── models/
│   │   ├── __init__.py
│   │   ├── node.py                # Порт Node.cs
│   │   ├── edge.py                # Порт Edge.cs
│   │   ├── building.py            # Расширение BuildingMap
│   │   └── types.py               # Enum для NodeType
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── dijkstra.py            # Порт Dijkstra.cs
│   │   ├── graph.py               # Структура графа
│   │   └── path_validator.py      # Валидация путей
│   ├── cache/
│   │   ├── __init__.py
│   │   └── route_cache.py         # Система кэширования
│   ├── serialization/
│   │   ├── __init__.py
│   │   ├── json_serializer.py     # JSON I/O
│   │   └── validators.py          # JSON валидация
│   └── utils/
│       ├── __init__.py
│       ├── geometry.py            # Расчёты расстояний
│       └── helpers.py             # Вспомогательные функции
├── tests/
│   ├── __init__.py
│   ├── test_dijkstra.py           # Из RouteTests.cs
│   ├── test_building_map.py
│   ├── test_serialization.py
│   └── conftest.py
├── pyproject.toml                 # Package configuration
├── setup.py
├── requirements.txt               # numpy, pytest, etc
└── README.md
```

#### 1.1.3 Пример портирования Dijkstra.cs -> dijkstra.py

**C# Оригинал (Dijkstra.cs)**:
```csharp
public class Dijkstra
{
    public static (List<Node> Path, string ErrorMessage) FindShortestPath(
        BuildingMap map, Node start, Node end)
    {
        // ... 70 строк кода
        var distances = new Dictionary<int, float>();
        var previous = new Dictionary<int, Node>();
        var pq = new SortedList<float, Node>();
        // ...
    }
}
```

**Python версия (dijkstra.py)**:
```python
# core/graph/dijkstra.py

from typing import List, Tuple, Optional, Dict, Set
from ..models.node import Node
from ..models.edge import Edge
import heapq

class Dijkstra:
    @staticmethod
    def find_shortest_path(
        nodes: List[Node],
        edges: Dict[int, List[Tuple[int, float]]],
        start_id: int,
        end_id: int
    ) -> Tuple[Optional[List[Node]], Optional[str]]:
        """
        Найти кратчайший путь между двумя узлами
        
        Args:
            nodes: Список всех узлов
            edges: Словарь смежности {from_id: [(to_id, weight), ...]}
            start_id: ID стартового узла
            end_id: ID конечного узла
        
        Returns:
            (path, error_message): путь или None + сообщение об ошибке
        """
        
        # Валидация входных данных
        node_map = {node.id: node for node in nodes}
        
        if start_id not in node_map or end_id not in node_map:
            return None, "Start or end node not found"
        
        if start_id == end_id:
            return [node_map[start_id]], None
        
        # Инициализация структур данных
        distances: Dict[int, float] = {node.id: float('inf') for node in nodes}
        distances[start_id] = 0
        
        previous: Dict[int, Optional[int]] = {node.id: None for node in nodes}
        
        # Priority queue: (distance, node_id)
        pq: List[Tuple[float, int]] = [(0, start_id)]
        
        visited: Set[int] = set()
        
        # Основной цикл Дейкстры
        while pq:
            current_dist, current_id = heapq.heappop(pq)
            
            # Пропустить, если уже посещали
            if current_id in visited:
                continue
            
            visited.add(current_id)
            
            # Достигли цели
            if current_id == end_id:
                # Восстановить путь
                path = []
                node_id: Optional[int] = end_id
                
                while node_id is not None:
                    path.append(node_map[node_id])
                    node_id = previous[node_id]
                
                path.reverse()
                return path, None
            
            # Обход соседей
            if current_id in edges:
                for neighbor_id, weight in edges[current_id]:
                    if neighbor_id not in visited:
                        new_distance = distances[current_id] + weight
                        
                        if new_distance < distances[neighbor_id]:
                            distances[neighbor_id] = new_distance
                            previous[neighbor_id] = current_id
                            heapq.heappush(pq, (new_distance, neighbor_id))
        
        # Путь не найден
        return None, "Path not found"
```

### Шаг 1.2: Создание тестов для Core Library

Перенести все тесты из RouteTests.cs:

```python
# tests/test_dijkstra.py

import pytest
from core.models.node import Node, NodeType
from core.graph.dijkstra import Dijkstra

class TestDijkstra:
    
    @pytest.fixture
    def setup_simple_graph(self):
        """Создать простой граф для тестирования"""
        nodes = [
            Node(id=1, name="A", position={'x': 0, 'y': 0}, 
                 floor=1, node_type=NodeType.ROOM),
            Node(id=2, name="B", position={'x': 100, 'y': 100}, 
                 floor=1, node_type=NodeType.ROOM),
            Node(id=3, name="C", position={'x': 200, 'y': 200}, 
                 floor=1, node_type=NodeType.ROOM),
        ]
        
        edges = {
            1: [(2, 10)],
            2: [(1, 10), (3, 10)],
            3: [(2, 10)]
        }
        
        return nodes, edges
    
    def test_route_calculation_simple_path(self, setup_simple_graph):
        """Тест: простой путь A -> C"""
        nodes, edges = setup_simple_graph
        
        path, error = Dijkstra.find_shortest_path(nodes, edges, 1, 3)
        
        assert error is None
        assert path is not None
        assert len(path) == 3
        assert path[0].id == 1
        assert path[1].id == 2
        assert path[2].id == 3
    
    def test_route_calculation_same_start_and_end(self, setup_simple_graph):
        """Тест: начало и конец - один узел"""
        nodes, edges = setup_simple_graph
        
        path, error = Dijkstra.find_shortest_path(nodes, edges, 1, 1)
        
        assert error is None
        assert path is not None
        assert len(path) == 1
        assert path[0].id == 1
    
    def test_route_calculation_no_path_exists(self):
        """Тест: пути не существует"""
        nodes = [
            Node(id=1, name="A", position={'x': 0, 'y': 0}, 
                 floor=1, node_type=NodeType.ROOM),
            Node(id=2, name="B", position={'x': 100, 'y': 100}, 
                 floor=1, node_type=NodeType.ROOM),
        ]
        edges = {}  # Нет связей
        
        path, error = Dijkstra.find_shortest_path(nodes, edges, 1, 2)
        
        assert path is None
        assert error == "Path not found"
    
    def test_route_with_multiple_floors(self):
        """Тест: маршрут между этажами"""
        nodes = [
            Node(id=1, name="Room A", position={'x': 0, 'y': 0}, 
                 floor=1, node_type=NodeType.ROOM),
            Node(id=2, name="Stairs", position={'x': 50, 'y': 50}, 
                 floor=1, node_type=NodeType.STAIRCASE),
            Node(id=3, name="Stairs", position={'x': 50, 'y': 50}, 
                 floor=2, node_type=NodeType.STAIRCASE),
            Node(id=4, name="Room B", position={'x': 100, 'y': 100}, 
                 floor=2, node_type=NodeType.ROOM),
        ]
        
        edges = {
            1: [(2, 10)],
            2: [(1, 10), (3, 10)],  # Переход между этажами
            3: [(2, 10), (4, 15)],
            4: [(3, 15)]
        }
        
        path, error = Dijkstra.find_shortest_path(nodes, edges, 1, 4)
        
        assert error is None
        assert path is not None
        assert len(path) == 4
        assert path[2].floor == 2
```

### Шаг 1.3: Документирование Core Library

```python
# core/__init__.py

"""
CampusCompass2 Core Library

Переносимая библиотека для навигации по зданиям/кампусам.
Может использоваться в веб, мобильных приложениях и на рабочих столах.

Основные компоненты:
- models: Структуры данных (Node, Edge, Building)
- graph: Алгоритмы поиска пути (Dijkstra)
- cache: Система кэширования маршрутов
- serialization: I/O операции с JSON

Пример использования:

    from core.models.node import Node, NodeType
    from core.graph.dijkstra import Dijkstra
    
    # Создать узлы
    nodes = [
        Node(id=1, name="Room 101", floor=1, node_type=NodeType.ROOM, ...),
        Node(id=2, name="Corridor", floor=1, node_type=NodeType.CORRIDOR, ...),
    ]
    
    # Построить граф
    edges = {
        1: [(2, 15.5)],
        2: [(1, 15.5)]
    }
    
    # Найти путь
    path, error = Dijkstra.find_shortest_path(nodes, edges, 1, 2)
    if path:
        print(f"Путь найден: {[n.name for n in path]}")
"""

__version__ = "1.0.0"

from .models import Node, Edge, Building, NodeType
from .graph import Dijkstra, Graph
from .cache import RouteCache
from .serialization import JSONSerializer

__all__ = [
    'Node',
    'Edge',
    'Building',
    'NodeType',
    'Dijkstra',
    'Graph',
    'RouteCache',
    'JSONSerializer',
]
```

---

## ФАЗА 2: BACKEND API (FastAPI)

### Шаг 2.1: Инициализация проекта

```bash
# Создать директорию
mkdir campuscompass-backend
cd campuscompass-backend

# Инициализировать venv
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Создать requirements.txt
cat > requirements.txt << EOF
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
pydantic==2.5.0
pydantic-settings==2.1.0
redis==5.0.1
python-multipart==0.0.6
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
python-json-logger==2.0.7
aiofiles==23.2.1
EOF

pip install -r requirements.txt
```

### Шаг 2.2: Структура проекта

```bash
mkdir -p app/{api/v1/endpoints,services,models/{db,dto},core,utils}
mkdir -p tests
touch app/__init__.py app/main.py app/config.py app/database.py
```

### Шаг 2.3: Основные файлы

**app/config.py**
```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost/campuscompass"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "CampusCompass2"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = ".env"

@lru_cache
def get_settings():
    return Settings()
```

**app/database.py**
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**app/main.py**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
from app.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.PROJECT_NAME)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {"message": "CampusCompass2 API", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Шаг 2.4: API Endpoints

**app/api/v1/endpoints/navigation.py**
```python
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.navigation_service import NavigationService
from app.models.dto.route import RouteResponse, RouteRequest

router = APIRouter(prefix="/routes", tags=["navigation"])

@router.get("/shortest", response_model=RouteResponse)
async def get_shortest_route(
    start_id: int,
    end_id: int,
    building_id: str = None,
    db: Session = Depends(get_db)
):
    """Получить кратчайший маршрут"""
    service = NavigationService(db)
    route = service.calculate_route(start_id, end_id, building_id)
    
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    
    return route

@router.post("/calculate-multiple", response_model=List[RouteResponse])
async def calculate_multiple_routes(
    routes: List[RouteRequest],
    db: Session = Depends(get_db)
):
    """Рассчитать несколько маршрутов (batch)"""
    service = NavigationService(db)
    results = []
    
    for route_req in routes:
        result = service.calculate_route(
            route_req.start_id,
            route_req.end_id,
            route_req.building_id
        )
        if result:
            results.append(result)
    
    return results
```

**app/services/navigation_service.py**
```python
from typing import Optional, List, Dict, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_

from core.graph.dijkstra import Dijkstra
from core.models.node import Node as CoreNode
from core.cache.route_cache import RouteCache

from app.models.db.node import Node
from app.models.db.edge import Edge
from app.models.dto.route import RouteResponse
from app.utils.geometry import calculate_distance

class NavigationService:
    def __init__(self, db: Session, cache: Optional[RouteCache] = None):
        self.db = db
        self.cache = cache or RouteCache(max_size=1000)
    
    def calculate_route(
        self,
        start_id: int,
        end_id: int,
        building_id: Optional[str] = None
    ) -> Optional[RouteResponse]:
        """Расчёт кратчайшего маршрута"""
        
        # Проверка кэша
        cached = self.cache.get(start_id, end_id)
        if cached:
            return self._build_response(cached)
        
        # Получить узлы и рёбра
        nodes_data = self.db.query(Node).filter(
            Node.building_id == building_id if building_id else True
        ).all()
        
        edges_data = self.db.query(Edge).all()
        
        if not nodes_data:
            return None
        
        # Преобразовать в модели Core
        nodes = [self._db_node_to_core(n) for n in nodes_data]
        edges_dict = self._build_edges_dict(edges_data)
        
        # Найти путь
        path, error = Dijkstra.find_shortest_path(
            nodes, edges_dict, start_id, end_id
        )
        
        if path:
            self.cache.set(start_id, end_id, path)
            return self._build_response(path)
        
        return None
    
    def _db_node_to_core(self, db_node: Node) -> CoreNode:
        """Конвертировать DB node в Core node"""
        from core.models.node import NodeType
        
        return CoreNode(
            id=db_node.id,
            name=db_node.name,
            floor=db_node.floor,
            position={'x': db_node.position_x, 'y': db_node.position_y},
            node_type=NodeType[db_node.node_type.upper()],
            custom_size=db_node.custom_size,
            rotation_angle=db_node.rotation_angle
        )
    
    def _build_edges_dict(self, edges_data: List[Edge]) -> Dict:
        """Построить словарь смежности из рёбер"""
        edges_dict = {}
        for edge in edges_data:
            if edge.from_id not in edges_dict:
                edges_dict[edge.from_id] = []
            edges_dict[edge.from_id].append((edge.to_id, edge.weight))
            
            if edge.is_bidirectional:
                if edge.to_id not in edges_dict:
                    edges_dict[edge.to_id] = []
                edges_dict[edge.to_id].append((edge.from_id, edge.weight))
        
        return edges_dict
    
    def _build_response(self, path: List[CoreNode]) -> RouteResponse:
        """Построить ответ API"""
        total_distance = self._calculate_distance(path)
        instructions = self._generate_instructions(path)
        floors = list(set(n.floor for n in path))
        
        return RouteResponse(
            path=[{
                'id': n.id,
                'name': n.name,
                'floor': n.floor,
                'type': n.node_type.value,
                'position': n.position
            } for n in path],
            totalDistance=round(total_distance, 2),
            estimatedTime=self._estimate_time(total_distance),
            floorTransitions=sorted(floors),
            instructions=instructions
        )
    
    def _calculate_distance(self, path: List[CoreNode]) -> float:
        """Расчёт общей длины пути"""
        if len(path) < 2:
            return 0
        
        total = 0
        for i in range(len(path) - 1):
            from_node = path[i]
            to_node = path[i + 1]
            
            # Если переход между этажами
            if from_node.floor != to_node.floor:
                total += 10.0  # Фиксированное расстояние
            else:
                # Расстояние между точками
                dist = calculate_distance(
                    from_node.position['x'], from_node.position['y'],
                    to_node.position['x'], to_node.position['y']
                )
                total += dist
        
        return total
    
    def _estimate_time(self, distance: float) -> str:
        """Оценить время в пути (средняя скорость 1.5 м/сек)"""
        seconds = int(distance / 1.5)
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        
        if minutes == 0:
            return f"{remaining_seconds}s"
        elif remaining_seconds == 0:
            return f"{minutes}m"
        else:
            return f"{minutes}m {remaining_seconds}s"
    
    def _generate_instructions(self, path: List[CoreNode]) -> List[str]:
        """Генерировать пошаговые инструкции"""
        instructions = []
        
        current_floor = path[0].floor
        instructions.append(f"Start at {path[0].name}")
        
        for i in range(1, len(path)):
            current = path[i - 1]
            next_node = path[i]
            
            if next_node.floor != current_floor:
                if next_node.node_type.value in ['Staircase', 'Elevator']:
                    instr = f"Use {next_node.node_type.value.lower()} to floor {next_node.floor}"
                    instructions.append(instr)
                    current_floor = next_node.floor
            else:
                instructions.append(f"Move to {next_node.name}")
        
        return instructions
```

---

## ФАЗА 3: FRONTEND - ВЕБ (React)

### Шаг 3.1: Инициализация

```bash
npx create-react-app campuscompass-web --template typescript
cd campuscompass-web

# Дополнительные зависимости
npm install axios react-router-dom zustand tailwindcss
npm install -D @types/react-router-dom
```

### Шаг 3.2: Структура проекта

```
src/
├── components/
│   ├── Map.tsx
│   ├── RoutePanel.tsx
│   ├── FloorSelector.tsx
│   ├── SearchBar.tsx
│   └── NavBar.tsx
├── pages/
│   ├── Home.tsx
│   ├── Building.tsx
│   └── AdminPanel.tsx
├── services/
│   └── api.ts
├── store/
│   └── navigationStore.ts
├── types/
│   └── index.ts
├── utils/
│   └── mapRenderer.ts
├── App.tsx
└── index.tsx
```

### Шаг 3.3: API Service

**src/services/api.ts**
```typescript
import axios, { AxiosInstance } from 'axios';

interface RouteRequest {
  startId: number;
  endId: number;
  buildingId?: string;
}

interface Node {
  id: number;
  name: string;
  floor: number;
  type: 'Room' | 'Corridor' | 'Staircase' | 'Elevator';
  position: { x: number; y: number };
}

interface RouteResponse {
  path: Node[];
  totalDistance: number;
  estimatedTime: string;
  floorTransitions: number[];
  instructions: string[];
}

class APIService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1',
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  async getBuilding(buildingId: string) {
    return (await this.api.get(`/buildings/${buildingId}`)).data;
  }

  async getRoute(startId: number, endId: number, buildingId?: string): Promise<RouteResponse> {
    return (await this.api.get('/routes/shortest', {
      params: { start_id: startId, end_id: endId, building_id: buildingId },
    })).data;
  }

  async searchNodes(query: string, buildingId: string) {
    return (await this.api.get('/search', {
      params: { q: query, building_id: buildingId },
    })).data;
  }

  async getFloorPlan(buildingId: string, floor: number) {
    return (await this.api.get(`/buildings/${buildingId}/floor-plan/${floor}`)).data;
  }
}

export default new APIService();
```

### Шаг 3.4: Главный компонент Map

**src/components/Map.tsx**
```typescript
import React, { useEffect, useRef, useState } from 'react';
import { useNavigationStore } from '../store/navigationStore';
import { renderMap } from '../utils/mapRenderer';
import { Node } from '../types';

interface MapProps {
  buildingId: string;
  floor: number;
  onNodeSelect: (node: Node) => void;
}

export const Map: React.FC<MapProps> = ({ buildingId, floor, onNodeSelect }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [nodes, setNodes] = useState<Node[]>([]);
  const [route, setRoute] = useState<Node[]>([]);
  
  const { startNode, endNode, path } = useNavigationStore();

  useEffect(() => {
    // Загрузить узлы для этажа
    const loadFloor = async () => {
      // Fetch nodes from API
      // setNodes(data)
    };

    loadFloor();
  }, [floor, buildingId]);

  useEffect(() => {
    // Перерисовать карту
    if (canvasRef.current) {
      renderMap(canvasRef.current, {
        nodes,
        edges: [],
        route: path || [],
        startNode,
        endNode,
        floorPlan: null,
      });
    }
  }, [nodes, startNode, endNode, path]);

  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    // Проверить, нажали ли на узел
    for (const node of nodes) {
      const dx = node.position.x - x;
      const dy = node.position.y - y;
      const distance = Math.sqrt(dx * dx + dy * dy);

      if (distance < 15) {
        onNodeSelect(node);
        break;
      }
    }
  };

  return (
    <canvas
      ref={canvasRef}
      width={800}
      height={600}
      onClick={handleCanvasClick}
      style={{ border: '1px solid #ccc', cursor: 'pointer' }}
    />
  );
};
```

---

## ФАЗА 4: МОБИЛЬНОЕ ПРИЛОЖЕНИЕ (Python/Kivy)

### Шаг 4.1: Инициализация

```bash
# Установка Kivy
pip install kivy

# Структура проекта
mkdir -p mobile-app/{screens,services,widgets,assets/images}
touch mobile-app/main.py mobile-app/requirements.txt
```

### Шаг 4.2: Структура приложения

**mobile-app/main.py**
```python
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout

from screens.home_screen import HomeScreen
from screens.map_screen import MapScreen
from screens.search_screen import SearchScreen


class CampusCompassApp(App):
    def build(self):
        self.screen_manager = ScreenManager()
        
        # Add screens
        self.screen_manager.add_widget(HomeScreen(name='home'))
        self.screen_manager.add_widget(MapScreen(name='map'))
        self.screen_manager.add_widget(SearchScreen(name='search'))
        
        self.screen_manager.current = 'home'
        
        return self.screen_manager


if __name__ == '__main__':
    CampusCompassApp().run()
```

### Шаг 4.3: Конвертация в APK/IPA

**buildozer.spec**
```ini
[app]
title = CampusCompass
package.name = campuscompass
package.domain = org.campuscompass

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 1.0

requirements = python3,kivy,requests,pillow

orientation = portrait
fullscreen = 0

[buildozer]
log_level = 2
warn_on_root = 1
```

```bash
# Инсталлировать buildozer
pip install buildozer cython

# Построить APK
buildozer android debug

# Результат будет в bin/campuscompass-1.0-debug.apk
```

---

## ФАЗА 5: ИНТЕГРАЦИЯ И ТЕСТИРОВАНИЕ

### Шаг 5.1: End-to-End тесты

```python
# tests/e2e/test_navigation_flow.py

import pytest
from httpx import AsyncClient
from backend.app.main import app

@pytest.mark.asyncio
async def test_complete_navigation_flow():
    """E2E тест: полный цикл навигации"""
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 1. Получить информацию о здании
        building_response = await client.get("/buildings/building_001")
        assert building_response.status_code == 200
        
        building_data = building_response.json()
        nodes = building_data["nodes"]
        
        # 2. Выбрать два узла
        start_node = nodes[0]
        end_node = nodes[-1]
        
        # 3. Рассчитать маршрут
        route_response = await client.get(
            "/routes/shortest",
            params={
                "start_id": start_node["id"],
                "end_id": end_node["id"],
            }
        )
        assert route_response.status_code == 200
        
        route_data = route_response.json()
        assert "path" in route_data
        assert len(route_data["path"]) >= 2
        assert route_data["path"][0]["id"] == start_node["id"]
        assert route_data["path"][-1]["id"] == end_node["id"]
        
        # 4. Проверить инструкции
        assert len(route_data["instructions"]) > 0
        
        # 5. Проверить расстояние
        assert route_data["totalDistance"] > 0
```

### Шаг 5.2: Performance тесты

```python
# tests/performance/test_performance.py

import time
import pytest
from core.graph.dijkstra import Dijkstra
from core.models.node import Node, NodeType


def test_dijkstra_performance_large_graph():
    """Тест производительности на большом графе"""
    
    # Создать граф с 5000 узлами
    nodes = [
        Node(
            id=i,
            name=f"Node {i}",
            floor=i // 1000,
            position={'x': i % 100, 'y': (i // 100) % 100},
            node_type=NodeType.ROOM
        )
        for i in range(5000)
    ]
    
    # Создать рёбра (каждый узел связан с соседями)
    edges = {}
    for i in range(5000):
        edges[i] = []
        if i > 0:
            edges[i].append((i - 1, 10))
        if i < 4999:
            edges[i].append((i + 1, 10))
    
    # Измерить время
    start_time = time.time()
    path, error = Dijkstra.find_shortest_path(nodes, edges, 0, 4999)
    elapsed_time = time.time() - start_time
    
    # Должно выполниться за < 500ms
    assert elapsed_time < 0.5
    assert path is not None
    assert len(path) == 5000
```

---

## ФАЗА 6: РАЗВЁРТЫВАНИЕ

### Шаг 6.1: Docker & Docker Compose

**docker-compose.yml**
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: campuscompass
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://user:password@postgres:5432/campuscompass
      REDIS_URL: redis://redis:6379
    depends_on:
      - postgres
      - redis
    volumes:
      - ./backend:/app

  web:
    build:
      context: ./frontend-web
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    depends_on:
      - backend

volumes:
  postgres_data:
```

**backend/Dockerfile**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Шаг 6.2: CI/CD Pipeline (GitHub Actions)

**.github/workflows/ci.yml**
```yaml
name: CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: campuscompass_test
          POSTGRES_USER: user
          POSTGRES_PASSWORD: password
      
      redis:
        image: redis:7

    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      
      - name: Run tests
        run: pytest --cov=app tests/
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  build:
    needs: test
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Build Docker images
        run: |
          docker-compose build
      
      - name: Push to registry
        run: |
          # Пушить в DockerHub/ECR
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker-compose push
```

---

## КОНТРОЛЬНЫЙ СПИСОК РЕАЛИЗАЦИИ

### Phase 1: Core Library
- [ ] Портирование Dijkstra.cs в Python
- [ ] Портирование Node.cs и Edge.cs
- [ ] Создание модели Building
- [ ] Реализация RouteCache
- [ ] Перенос всех unit-тестов
- [ ] Документирование API Core

### Phase 2: Backend API
- [ ] Инициализация FastAPI проекта
- [ ] Создание моделей БД (SQLAlchemy)
- [ ] Реализация endpoints для маршрутов
- [ ] Реализация endpoints для зданий
- [ ] Реализация поиска
- [ ] Интеграция с Redis cache
- [ ] Документирование API (Swagger)

### Phase 3: Web Frontend
- [ ] Инициализация React проекта
- [ ] Создание компонента Map
- [ ] Создание компонента RoutePanel
- [ ] Реализация FloorSelector
- [ ] Реализация Search
- [ ] Интеграция с API
- [ ] Адаптивный дизайн (responsive)

### Phase 4: Mobile App
- [ ] Инициализация Kivy проекта
- [ ] Создание MapWidget
- [ ] Создание RoutePanel
- [ ] Интеграция с API
- [ ] Тестирование на Android
- [ ] Тестирование на iOS (опционально)

### Phase 5: Integration & Testing
- [ ] E2E тесты
- [ ] Performance тесты
- [ ] Security тесты
- [ ] Load тесты

### Phase 6: Deployment
- [ ] Настройка Docker
- [ ] Настройка CI/CD
- [ ] Развёртывание на staging
- [ ] Развёртывание на production

---

## ВРЕМЕННЫЕ ОЦЕНКИ

| Фаза | Задача | Часы |
|------|--------|------|
| 1 | Core Library | 16 |
| 2 | Backend API | 40 |
| 3 | Web Frontend | 40 |
| 4 | Mobile App | 32 |
| 5 | Тестирование | 24 |
| 6 | Deployment | 16 |
| **ИТОГО** | | **168 часов** |

---

## ДОПОЛНИТЕЛЬНЫЕ РЕСУРСЫ

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [React Docs](https://react.dev/)
- [Kivy Docs](https://kivy.org/doc/stable/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)

