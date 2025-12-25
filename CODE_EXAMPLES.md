# CampusCompass2 - Примеры кода для быстрого старта
## Core, Backend, Web, Mobile

### Версия: 1.0
### Дата: 24 декабря 2025 г.

---

## 1. CORE LIBRARY - ПРИМЕРЫ

### 1.1 Инициализация графа

```python
# example_core_usage.py

from core.models.node import Node, NodeType
from core.models.building import Building
from core.graph.dijkstra import Dijkstra
from core.cache.route_cache import RouteCache

# Создать здание
building = Building(
    id="building_001",
    name="Main Campus Building",
    floors_count=3
)

# Создать узлы
nodes = [
    # Этаж 1
    Node(id=1, name="Room 101", floor=1, node_type=NodeType.ROOM, 
         position={'x': 50, 'y': 50}),
    Node(id=2, name="Room 102", floor=1, node_type=NodeType.ROOM,
         position={'x': 150, 'y': 50}),
    Node(id=3, name="Corridor 1A", floor=1, node_type=NodeType.CORRIDOR,
         position={'x': 100, 'y': 100}),
    Node(id=4, name="Stairs 1", floor=1, node_type=NodeType.STAIRCASE,
         position={'x': 200, 'y': 150}),
    
    # Этаж 2
    Node(id=5, name="Room 201", floor=2, node_type=NodeType.ROOM,
         position={'x': 50, 'y': 50}),
    Node(id=6, name="Stairs 1", floor=2, node_type=NodeType.STAIRCASE,
         position={'x': 200, 'y': 150}),
]

# Создать рёбра (граф смежности)
edges = {
    1: [(3, 25)],           # Room 101 -> Corridor 1A (25 метров)
    2: [(3, 30)],           # Room 102 -> Corridor 1A (30 метров)
    3: [(1, 25), (2, 30), (4, 40)],  # Corridor -> везде
    4: [(3, 40), (6, 15)],  # Stairs down/up
    5: [(6, 35)],           # Room 201 -> Stairs 2
    6: [(4, 15), (5, 35)],  # Stairs
}

# Найти маршрут
path, error = Dijkstra.find_shortest_path(nodes, edges, 1, 5)

if path:
    print(f"✓ Путь найден:")
    for i, node in enumerate(path):
        print(f"  {i+1}. {node.name} (этаж {node.floor})")
else:
    print(f"✗ Ошибка: {error}")

# Использование кэша
cache = RouteCache()
cache.set(1, 5, path)

# Позже...
cached_path = cache.get(1, 5)
if cached_path:
    print(f"✓ Найден в кэше: {[n.name for n in cached_path]}")
```

### 1.2 Сохранение и загрузка карты

```python
# example_serialization.py

import json
from core.serialization.json_serializer import JSONSerializer

# Сохранить карту
serializer = JSONSerializer()

building_data = {
    'nodes': [n.to_dict() for n in nodes],
    'edges': [
        {'fromId': from_id, 'toId': to_id, 'weight': weight}
        for from_id, neighbors in edges.items()
        for to_id, weight in neighbors
    ],
    'floorPlans': {
        '1': 'images/floor1.png',
        '2': 'images/floor2.png',
        '3': 'images/floor3.png'
    }
}

# Сохранить в файл
with open('map.json', 'w') as f:
    json.dump(building_data, f, indent=2)

print("✓ Карта сохранена в map.json")

# Загрузить карту
with open('map.json', 'r') as f:
    loaded_data = json.load(f)

loaded_nodes = [
    Node(
        id=n['id'],
        name=n['name'],
        floor=n['floor'],
        node_type=NodeType[n['type'].upper()],
        position=n['position'],
        custom_size=n.get('customSize', 20),
        rotation_angle=n.get('rotationAngle', 0.0)
    )
    for n in loaded_data['nodes']
]

loaded_edges = {}
for edge in loaded_data['edges']:
    from_id = edge['fromId']
    if from_id not in loaded_edges:
        loaded_edges[from_id] = []
    loaded_edges[from_id].append((edge['toId'], edge['weight']))

print(f"✓ Загружено {len(loaded_nodes)} узлов и {len(loaded_edges)} рёбер")
```

---

## 2. BACKEND API - ПРИМЕРЫ

### 2.1 Быстрый старт с FastAPI

```python
# backend/example_quick_start.py

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="CampusCompass API", version="1.0.0")

# Модели
class Node(BaseModel):
    id: int
    name: str
    floor: int
    node_type: str
    position: dict

class RouteResponse(BaseModel):
    path: List[Node]
    totalDistance: float
    estimatedTime: str
    instructions: List[str]

# Примеры данных (в реальности из БД)
SAMPLE_NODES = {
    1: Node(id=1, name="Room 101", floor=1, node_type="Room", position={'x': 50, 'y': 50}),
    2: Node(id=2, name="Corridor", floor=1, node_type="Corridor", position={'x': 100, 'y': 100}),
    3: Node(id=3, name="Room 201", floor=2, node_type="Room", position={'x': 50, 'y': 50}),
}

SAMPLE_EDGES = {
    1: [(2, 30)],
    2: [(1, 30), (3, 50)],
    3: [(2, 50)],
}

@app.get("/")
async def root():
    return {"message": "CampusCompass API v1.0.0"}

@app.get("/api/v1/health")
async def health():
    return {"status": "healthy", "service": "CampusCompass"}

@app.get("/api/v1/nodes")
async def get_nodes(building_id: Optional[str] = None, floor: Optional[int] = None):
    """Получить список всех узлов"""
    nodes = list(SAMPLE_NODES.values())
    
    if floor:
        nodes = [n for n in nodes if n.floor == floor]
    
    return {"count": len(nodes), "nodes": nodes}

@app.get("/api/v1/nodes/{node_id}")
async def get_node(node_id: int):
    """Получить информацию об узле"""
    node = SAMPLE_NODES.get(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node

@app.get("/api/v1/routes/shortest", response_model=RouteResponse)
async def get_shortest_route(start_id: int, end_id: int):
    """Получить кратчайший маршрут между двумя узлами"""
    
    # Валидация
    if start_id not in SAMPLE_NODES:
        raise HTTPException(status_code=400, detail=f"Start node {start_id} not found")
    if end_id not in SAMPLE_NODES:
        raise HTTPException(status_code=400, detail=f"End node {end_id} not found")
    
    # Простая имитация маршрута
    if start_id == 1 and end_id == 3:
        path = [SAMPLE_NODES[1], SAMPLE_NODES[2], SAMPLE_NODES[3]]
        instructions = [
            "Start at Room 101",
            "Move to Corridor",
            "Go up to Floor 2",
            "Arrive at Room 201"
        ]
    elif start_id == 3 and end_id == 1:
        path = [SAMPLE_NODES[3], SAMPLE_NODES[2], SAMPLE_NODES[1]]
        instructions = [
            "Start at Room 201",
            "Move to Corridor",
            "Go down to Floor 1",
            "Arrive at Room 101"
        ]
    else:
        path = [SAMPLE_NODES[start_id], SAMPLE_NODES[end_id]]
        instructions = [
            f"Start at {SAMPLE_NODES[start_id].name}",
            f"Go to {SAMPLE_NODES[end_id].name}"
        ]
    
    return RouteResponse(
        path=path,
        totalDistance=80.0,
        estimatedTime="1 minute",
        instructions=instructions
    )

@app.post("/api/v1/routes/calculate-multiple")
async def calculate_multiple_routes(routes: List[dict]):
    """Рассчитать несколько маршрутов (batch)"""
    results = []
    for route in routes:
        # Обработать каждый маршрут
        pass
    return {"count": len(results), "routes": results}

@app.get("/api/v1/search")
async def search_nodes(q: str, building_id: Optional[str] = None):
    """Поиск узлов по названию"""
    query = q.lower()
    results = [
        n for n in SAMPLE_NODES.values()
        if query in n.name.lower()
    ]
    return {
        "query": q,
        "count": len(results),
        "results": results
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Запуск: python example_quick_start.py
# Документация API: http://localhost:8000/docs
```

### 2.2 Интеграция с БД (SQLAlchemy)

```python
# backend/app/models/db/node.py

from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.database import Base
import enum

class NodeTypeEnum(enum.Enum):
    ROOM = "Room"
    CORRIDOR = "Corridor"
    STAIRCASE = "Staircase"
    ELEVATOR = "Elevator"

class Node(Base):
    __tablename__ = "nodes"
    
    id = Column(Integer, primary_key=True, index=True)
    building_id = Column(String, ForeignKey("buildings.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(String(500))
    floor = Column(Integer, nullable=False)
    node_type = Column(Enum(NodeTypeEnum), nullable=False, index=True)
    position_x = Column(Float, nullable=False)
    position_y = Column(Float, nullable=False)
    custom_size = Column(Integer, default=20)
    rotation_angle = Column(Float, default=0.0)
    
    building = relationship("Building", back_populates="nodes")
    edges_from = relationship("Edge", foreign_keys="Edge.from_id", back_populates="from_node")
    edges_to = relationship("Edge", foreign_keys="Edge.to_id", back_populates="to_node")
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'floor': self.floor,
            'type': self.node_type.value,
            'position': {'x': self.position_x, 'y': self.position_y},
            'description': self.description
        }

class Edge(Base):
    __tablename__ = "edges"
    
    id = Column(Integer, primary_key=True, index=True)
    from_id = Column(Integer, ForeignKey("nodes.id"), nullable=False, index=True)
    to_id = Column(Integer, ForeignKey("nodes.id"), nullable=False, index=True)
    weight = Column(Float, nullable=False)  # расстояние
    is_bidirectional = Column(Boolean, default=True)
    
    from_node = relationship("Node", foreign_keys=[from_id], back_populates="edges_from")
    to_node = relationship("Node", foreign_keys=[to_id], back_populates="edges_to")

class Building(Base):
    __tablename__ = "buildings"
    
    id = Column(String, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(String(1000))
    address = Column(String(500))
    floors_count = Column(Integer, default=1)
    
    nodes = relationship("Node", back_populates="building")
```

### 2.3 Тестирование API

```python
# backend/tests/test_routes.py

import pytest
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import get_db, Base
from app.models.db.node import Node, NodeTypeEnum, Building, Edge

# Временная БД для тестов
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
async def setup_test_data():
    """Подготовить тестовые данные"""
    db = TestingSessionLocal()
    
    # Создать здание
    building = Building(id="test_building", name="Test Building")
    db.add(building)
    
    # Создать узлы
    node1 = Node(
        building_id="test_building",
        name="Room 101",
        floor=1,
        node_type=NodeTypeEnum.ROOM,
        position_x=50,
        position_y=50
    )
    node2 = Node(
        building_id="test_building",
        name="Room 102",
        floor=1,
        node_type=NodeTypeEnum.ROOM,
        position_x=150,
        position_y=50
    )
    
    db.add_all([node1, node2])
    db.commit()
    db.refresh(node1)
    db.refresh(node2)
    
    # Создать рёбра
    edge = Edge(from_id=node1.id, to_id=node2.id, weight=30.0)
    db.add(edge)
    db.commit()
    
    yield db
    
    db.close()
    Base.metadata.drop_all(bind=engine)

@pytest.mark.asyncio
async def test_get_shortest_route(setup_test_data):
    """Тест получения кратчайшего маршрута"""
    db = setup_test_data
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/routes/shortest",
            params={"start_id": 1, "end_id": 2}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "path" in data
        assert len(data["path"]) >= 2
        assert data["path"][0]["id"] == 1
        assert data["path"][-1]["id"] == 2
        assert "totalDistance" in data
        assert "instructions" in data
```

---

## 3. ВЕunderlying-ПРИЛОЖЕНИЕ - ПРИМЕРЫ (React/TypeScript)

### 3.1 Компонент Map с Canvas

```typescript
// src/components/Map/Map.tsx

import React, { useRef, useEffect, useState } from 'react';
import styles from './Map.module.css';

interface MapProps {
  nodes: Node[];
  edges: Edge[];
  route?: Node[];
  startNode?: Node;
  endNode?: Node;
  floorPlan?: string;
  onNodeClick: (node: Node) => void;
}

export const Map: React.FC<MapProps> = ({
  nodes,
  edges,
  route,
  startNode,
  endNode,
  floorPlan,
  onNodeClick,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [scale, setScale] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });

  // Основной цикл отрисовки
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d')!;
    const width = canvas.width;
    const height = canvas.height;

    // Очистить холст
    ctx.fillStyle = '#f5f5f5';
    ctx.fillRect(0, 0, width, height);

    // Нарисовать рёбра
    ctx.strokeStyle = '#cccccc';
    ctx.lineWidth = 2;
    edges.forEach((edge) => {
      const fromNode = nodes.find((n) => n.id === edge.fromId);
      const toNode = nodes.find((n) => n.id === edge.toId);

      if (fromNode && toNode) {
        ctx.beginPath();
        ctx.moveTo(fromNode.position.x * scale + offset.x, fromNode.position.y * scale + offset.y);
        ctx.lineTo(toNode.position.x * scale + offset.x, toNode.position.y * scale + offset.y);
        ctx.stroke();
      }
    });

    // Нарисовать маршрут
    if (route && route.length > 1) {
      ctx.strokeStyle = '#ff3333';
      ctx.lineWidth = 5;
      ctx.beginPath();
      ctx.moveTo(route[0].position.x * scale + offset.x, route[0].position.y * scale + offset.y);
      for (let i = 1; i < route.length; i++) {
        ctx.lineTo(route[i].position.x * scale + offset.x, route[i].position.y * scale + offset.y);
      }
      ctx.stroke();
    }

    // Нарисовать узлы
    nodes.forEach((node) => {
      const x = node.position.x * scale + offset.x;
      const y = node.position.y * scale + offset.y;
      const size = 15;

      // Выбрать цвет по типу
      const colors: { [key: string]: string } = {
        Room: '#3366cc',
        Corridor: '#33cc33',
        Staircase: '#ffaa00',
        Elevator: '#ff3333',
      };
      ctx.fillStyle = colors[node.type] || '#999999';

      // Нарисовать квадрат
      ctx.fillRect(x - size / 2, y - size / 2, size, size);

      // Выделить стартовую и конечную точку
      if (node === startNode) {
        ctx.strokeStyle = '#00cc00';
        ctx.lineWidth = 3;
        ctx.strokeRect(x - size / 2 - 3, y - size / 2 - 3, size + 6, size + 6);
      }
      if (node === endNode) {
        ctx.strokeStyle = '#ff0000';
        ctx.lineWidth = 3;
        ctx.strokeRect(x - size / 2 - 3, y - size / 2 - 3, size + 6, size + 6);
      }

      // Нарисовать название
      ctx.fillStyle = '#000000';
      ctx.font = '12px Arial';
      ctx.fillText(node.name, x + size / 2 + 5, y);
    });
  }, [nodes, edges, route, startNode, endNode, scale, offset]);

  // Обработка клика на карту
  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const clickX = (e.clientX - rect.left - offset.x) / scale;
    const clickY = (e.clientY - rect.top - offset.y) / scale;

    // Проверить попадание на узел
    for (const node of nodes) {
      const dx = node.position.x - clickX;
      const dy = node.position.y - clickY;
      const distance = Math.sqrt(dx * dx + dy * dy);

      if (distance < 20) {
        onNodeClick(node);
        return;
      }
    }
  };

  // Обработка скролла
  const handleWheel = (e: React.WheelEvent<HTMLCanvasElement>) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    setScale((prev) => Math.min(Math.max(prev * delta, 0.5), 3));
  };

  // Обработка перетаскивания
  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const startX = e.clientX;
    const startY = e.clientY;
    const startOffsetX = offset.x;
    const startOffsetY = offset.y;

    const handleMouseMove = (moveEvent: MouseEvent) => {
      const dx = moveEvent.clientX - startX;
      const dy = moveEvent.clientY - startY;
      setOffset({
        x: startOffsetX + dx,
        y: startOffsetY + dy,
      });
    };

    const handleMouseUp = () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  };

  return (
    <canvas
      ref={canvasRef}
      width={800}
      height={600}
      onClick={handleCanvasClick}
      onWheel={handleWheel}
      onMouseDown={handleMouseDown}
      className={styles.canvas}
    />
  );
};
```

### 3.2 Hook для управления состоянием

```typescript
// src/store/navigationStore.ts

import { create } from 'zustand';
import { Node, RouteResponse } from '../types';

interface NavigationStore {
  // Состояние
  startNode: Node | null;
  endNode: Node | null;
  path: Node[] | null;
  loading: boolean;
  error: string | null;
  
  // Действия
  setStartNode: (node: Node) => void;
  setEndNode: (node: Node) => void;
  setPath: (path: Node[]) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  resetRoute: () => void;
}

export const useNavigationStore = create<NavigationStore>((set) => ({
  startNode: null,
  endNode: null,
  path: null,
  loading: false,
  error: null,
  
  setStartNode: (node) => set({ startNode: node }),
  setEndNode: (node) => set({ endNode: node }),
  setPath: (path) => set({ path }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  resetRoute: () => set({
    startNode: null,
    endNode: null,
    path: null,
    error: null,
  }),
}));
```

### 3.3 Интеграция с API

```typescript
// src/services/api.ts

import axios from 'axios';
import { Node, RouteResponse } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiService = {
  // Здания
  getBuildings: async () => {
    const response = await api.get('/buildings');
    return response.data;
  },
  
  getBuilding: async (buildingId: string) => {
    const response = await api.get(`/buildings/${buildingId}`);
    return response.data;
  },
  
  // Маршруты
  getRoute: async (startId: number, endId: number, buildingId?: string): Promise<RouteResponse> => {
    const response = await api.get('/routes/shortest', {
      params: {
        start_id: startId,
        end_id: endId,
        building_id: buildingId,
      },
    });
    return response.data;
  },
  
  // Поиск
  searchNodes: async (query: string, buildingId?: string) => {
    const response = await api.get('/search', {
      params: {
        q: query,
        building_id: buildingId,
      },
    });
    return response.data.results;
  },
  
  // Планы этажей
  getFloorPlan: async (buildingId: string, floor: number) => {
    const response = await api.get(`/buildings/${buildingId}/floor-plan/${floor}`);
    return response.data;
  },
};
```

---

## 4. МОБИЛЬНОЕ ПРИЛОЖЕНИЕ - ПРИМЕРЫ (Python/Kivy)

### 4.1 Main App

```python
# mobile-app/main.py

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivy.core.window import Window

from screens.home_screen import HomeScreen
from screens.map_screen import MapScreen

Window.size = (400, 800)

class CampusCompassApp(App):
    def build(self):
        self.screen_manager = ScreenManager()
        
        # Инициализировать экраны
        home_screen = HomeScreen(name='home')
        map_screen = MapScreen(name='map')
        
        self.screen_manager.add_widget(home_screen)
        self.screen_manager.add_widget(map_screen)
        
        return self.screen_manager

if __name__ == '__main__':
    app = CampusCompassApp()
    app.run()
```

### 4.2 Home Screen

```python
# mobile-app/screens/home_screen.py

from kivy.uix.screen import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner

class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Заголовок
        title = Label(
            text='CampusCompass',
            size_hint_y=0.2,
            font_size='32sp',
            bold=True
        )
        layout.add_widget(title)
        
        # Выбор здания
        building_layout = BoxLayout(size_hint_y=0.1)
        building_layout.add_widget(Label(text='Building:', size_hint_x=0.3))
        
        buildings = Spinner(
            text='Select Building',
            values=('Main Building', 'Lab Building', 'Library'),
            size_hint_x=0.7
        )
        building_layout.add_widget(buildings)
        layout.add_widget(building_layout)
        
        # Кнопки
        button_layout = GridLayout(cols=1, spacing=10, size_hint_y=0.5)
        
        navigate_btn = Button(text='Navigate', size_hint_y=0.25)
        navigate_btn.bind(on_press=self.go_to_map)
        button_layout.add_widget(navigate_btn)
        
        search_btn = Button(text='Search Room', size_hint_y=0.25)
        button_layout.add_widget(search_btn)
        
        saved_btn = Button(text='Saved Routes', size_hint_y=0.25)
        button_layout.add_widget(saved_btn)
        
        settings_btn = Button(text='Settings', size_hint_y=0.25)
        button_layout.add_widget(settings_btn)
        
        layout.add_widget(button_layout)
        
        self.add_widget(layout)
        self.selected_building = buildings
    
    def go_to_map(self, instance):
        self.manager.current = 'map'
```

### 4.3 Map Screen

```python
# mobile-app/screens/map_screen.py

from kivy.uix.screen import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.garden.mapview import MapView

from widgets.map_widget import MapWidget
from services.api_client import APIClient

class MapScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.api_client = APIClient()
        self.start_node = None
        self.end_node = None
        self.floor = 1
        
        layout = BoxLayout(orientation='vertical', padding=5, spacing=5)
        
        # Верхняя панель
        top_panel = BoxLayout(size_hint_y=0.08)
        back_btn = Button(text='← Back', size_hint_x=0.2)
        back_btn.bind(on_press=self.go_back)
        top_panel.add_widget(back_btn)
        
        floor_label = Label(text=f'Floor: {self.floor}', size_hint_x=0.3)
        top_panel.add_widget(floor_label)
        
        floor_spinner = Spinner(
            text=str(self.floor),
            values=('1', '2', '3', '4', '5'),
            size_hint_x=0.3
        )
        floor_spinner.bind(text=self.on_floor_change)
        top_panel.add_widget(floor_spinner)
        
        self.floor_label = floor_label
        layout.add_widget(top_panel)
        
        # Карта
        self.map_widget = MapWidget(size_hint_y=0.6)
        self.map_widget.bind(on_node_select=self.on_node_select)
        layout.add_widget(self.map_widget)
        
        # Панель поиска
        search_layout = BoxLayout(size_hint_y=0.08)
        search_input = TextInput(
            hint_text='Search room...',
            multiline=False,
            size_hint_x=0.8
        )
        search_btn = Button(text='Search', size_hint_x=0.2)
        search_btn.bind(on_press=lambda x: self.search_room(search_input.text))
        search_layout.add_widget(search_input)
        search_layout.add_widget(search_btn)
        layout.add_widget(search_layout)
        
        # Панель маршрута
        route_layout = BoxLayout(orientation='vertical', size_hint_y=0.24)
        
        info_label = Label(text='Select start and end point', size_hint_y=0.3)
        route_layout.add_widget(info_label)
        self.info_label = info_label
        
        instructions_label = Label(text='', size_hint_y=0.7)
        route_layout.add_widget(instructions_label)
        self.instructions_label = instructions_label
        
        button_layout = BoxLayout(size_hint_y=0.1, spacing=5)
        reset_btn = Button(text='Reset')
        reset_btn.bind(on_press=self.reset_route)
        button_layout.add_widget(reset_btn)
        
        route_layout.add_widget(button_layout)
        layout.add_widget(route_layout)
        
        self.add_widget(layout)
    
    def on_floor_change(self, spinner, text):
        self.floor = int(text)
        self.floor_label.text = f'Floor: {self.floor}'
        self.map_widget.load_floor(self.floor)
    
    def on_node_select(self, widget, node):
        if not self.start_node:
            self.start_node = node
            self.info_label.text = f'Start: {node["name"]}'
        elif not self.end_node and node['id'] != self.start_node['id']:
            self.end_node = node
            self.info_label.text = f'{self.start_node["name"]} → {node["name"]}'
            self.calculate_route()
        else:
            self.start_node = node
            self.end_node = None
            self.info_label.text = f'Start: {node["name"]}'
    
    def calculate_route(self):
        if not self.start_node or not self.end_node:
            return
        
        try:
            route_data = self.api_client.get_route(
                self.start_node['id'],
                self.end_node['id']
            )
            
            self.map_widget.set_route(route_data['path'])
            
            instructions_text = '\n'.join(route_data['instructions'])
            self.instructions_label.text = instructions_text
            
        except Exception as e:
            self.info_label.text = f'Error: {str(e)}'
    
    def reset_route(self, instance):
        self.start_node = None
        self.end_node = None
        self.map_widget.set_route([])
        self.info_label.text = 'Select start and end point'
        self.instructions_label.text = ''
    
    def search_room(self, query):
        if not query:
            return
        
        try:
            results = self.api_client.search_nodes(query)
            if results:
                room = results[0]
                self.start_node = room
                self.info_label.text = f'Start: {room["name"]} (Floor {room["floor"]})'
                self.floor = room["floor"]
        except Exception as e:
            self.info_label.text = f'Error: {str(e)}'
    
    def go_back(self, instance):
        self.manager.current = 'home'
```

### 4.4 API Client для мобилки

```python
# mobile-app/services/api_client.py

import requests
from typing import Optional, List, Dict

class APIClient:
    def __init__(self, base_url: str = 'http://localhost:8000/api/v1'):
        self.base_url = base_url
        self.session = requests.Session()
    
    def get_building(self, building_id: str) -> Dict:
        """Получить информацию о здании"""
        response = self.session.get(f'{self.base_url}/buildings/{building_id}')
        response.raise_for_status()
        return response.json()
    
    def get_route(self, start_id: int, end_id: int, building_id: Optional[str] = None) -> Dict:
        """Получить маршрут"""
        params = {
            'start_id': start_id,
            'end_id': end_id,
        }
        if building_id:
            params['building_id'] = building_id
        
        response = self.session.get(f'{self.base_url}/routes/shortest', params=params)
        response.raise_for_status()
        return response.json()
    
    def search_nodes(self, query: str) -> List[Dict]:
        """Поиск узлов"""
        response = self.session.get(
            f'{self.base_url}/search',
            params={'q': query}
        )
        response.raise_for_status()
        return response.json().get('results', [])
    
    def get_nodes_for_floor(self, building_id: str, floor: int) -> List[Dict]:
        """Получить узлы для этажа"""
        response = self.session.get(
            f'{self.base_url}/buildings/{building_id}/nodes',
            params={'floor': floor}
        )
        response.raise_for_status()
        return response.json().get('nodes', [])
```

---

## ЗАПУСК ПРИМЕРОВ

### Core Library
```bash
cd core_library
python example_core_usage.py
python example_serialization.py
pytest tests/ -v
```

### Backend API
```bash
cd backend
pip install -r requirements.txt
python example_quick_start.py
# Откройте http://localhost:8000/docs для Swagger UI
```

### Web Frontend
```bash
cd frontend-web
npm install
npm start
# Откройте http://localhost:3000
```

### Mobile App
```bash
cd mobile-app
pip install -r requirements.txt
python main.py
```

---

## ЗАКЛЮЧЕНИЕ

Эти примеры охватывают основные компоненты CampusCompass2 на всех платформах. 
Используйте их как стартовые точки для разработки.

