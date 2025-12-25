# Техническая архитектура для миграции CampusCompass2
## На веб-сайт, Python приложение (Android/iOS)

### Версия: 1.0
### Дата: 24 декабря 2025 г.

---

## 1. АРХИТЕКТУРНЫЙ ОБЗОР

### 1.1 Текущее состояние (Windows Forms C#)
```
┌─────────────────────────────────────┐
│   NavigationForm (UI - C# WinForms) │
└─────────────┬───────────────────────┘
              │
       ┌──────┴──────┬──────────┬──────────┐
       │             │          │          │
┌──────▼──┐  ┌──────▼──┐  ┌───▼──┐  ┌───▼────┐
│BuildingMap│  │Dijkstra│  │Node │  │Edge  │
│(Map Mgmt)│  │(Router)│  │(Data)│  │(Links)│
└──────────┘  └─────────┘  └──────┘  └──────┘
       │             │          │          │
       └──────┬──────┴──────────┴──────────┘
              │
       ┌──────▼──────────┐
       │  map.json (DB)  │
       └─────────────────┘
```

### 1.2 Целевая архитектура (Микросервисы)
```
┌─────────────────────────────────────────────────────────────┐
│                       Frontend Layer                        │
│  ┌────────────┐  ┌────────────┐  ┌────────────────────┐   │
│  │   Website  │  │  Android   │  │       iOS          │   │
│  │ (React/Vue)│  │  (Kivy/Qt) │  │   (Kivy/Swift)     │   │
│  └─────┬──────┘  └─────┬──────┘  └────────┬───────────┘   │
└────────┼────────────────┼──────────────────┼────────────────┘
         │                │                  │
         └────────────────┼──────────────────┘
                          │ REST API / WebSocket
         ┌────────────────▼──────────────────┐
         │     API Gateway                   │
         │  (Load Balancer / Proxy)          │
         └────────────────┬──────────────────┘
                          │
    ┌─────────────────────┼─────────────────────┐
    │                     │                     │
┌───▼─────────┐   ┌──────▼──────┐   ┌─────────▼────┐
│ Navigation  │   │   Building  │   │   Search     │
│ Service     │   │   Service   │   │   Service    │
│ (Dijkstra)  │   │  (Map CRUD) │   │   (Index)    │
└───┬─────────┘   └──────┬──────┘   └─────────┬────┘
    │                    │                     │
    └────────────────────┼─────────────────────┘
                         │
         ┌───────────────▼────────────────┐
         │     Database Layer             │
         │  ┌───────────┐  ┌───────────┐ │
         │  │PostgreSQL │  │  Redis    │ │
         │  │(Main DB)  │  │  (Cache)  │ │
         │  └───────────┘  └───────────┘ │
         └────────────────────────────────┘
```

---

## 2. МОДУЛЬНАЯ АРХИТЕКТУРА

### 2.1 Core Library (Shared Logic)

#### Структура папок
```
core/
├── graph/
│   ├── dijkstra.py          # Алгоритм поиска пути
│   ├── graph.py             # Структура графа
│   └── __init__.py
├── models/
│   ├── node.py              # Модель узла
│   ├── edge.py              # Модель связи
│   ├── building.py          # Модель здания
│   └── __init__.py
├── cache/
│   ├── route_cache.py       # Кэш маршрутов
│   └── __init__.py
├── utils/
│   ├── validators.py        # Валидация данных
│   ├── helpers.py           # Вспомогательные функции
│   └── __init__.py
└── exceptions/
    └── custom_exceptions.py # Пользовательские исключения
```

#### Пример реализации (Python)

**core/models/node.py**
```python
from enum import Enum
from dataclasses import dataclass
from typing import Optional

class NodeType(Enum):
    ROOM = "Room"
    CORRIDOR = "Corridor"
    STAIRCASE = "Staircase"
    ELEVATOR = "Elevator"

@dataclass
class Node:
    id: int
    name: str
    floor: int
    node_type: NodeType
    position: dict  # {"x": 100, "y": 150}
    custom_size: int = 20
    rotation_angle: float = 0.0
    description: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'floor': self.floor,
            'type': self.node_type.value,
            'position': self.position,
            'customSize': self.custom_size,
            'rotationAngle': self.rotation_angle,
            'description': self.description
        }
```

**core/models/edge.py**
```python
from dataclasses import dataclass

@dataclass
class Edge:
    from_id: int
    to_id: int
    weight: float  # расстояние
    
    def to_dict(self) -> dict:
        return {
            'fromId': self.from_id,
            'toId': self.to_id,
            'weight': self.weight
        }
```

**core/graph/dijkstra.py**
```python
from typing import List, Tuple, Optional, Dict
from ..models.node import Node, NodeType
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
        Поиск кратчайшего пути алгоритмом Дейкстры
        
        Args:
            nodes: Список всех узлов
            edges: Словарь смежности {from_id: [(to_id, weight), ...]}
            start_id: ID стартового узла
            end_id: ID конечного узла
            
        Returns:
            Tuple[List[Node], Optional[str]]: (путь, сообщение об ошибке)
        """
        
        node_map = {node.id: node for node in nodes}
        
        if start_id not in node_map or end_id not in node_map:
            return None, "Start or end node not found"
        
        # Инициализация
        distances = {node.id: float('inf') for node in nodes}
        distances[start_id] = 0
        previous = {node.id: None for node in nodes}
        pq = [(0, start_id)]
        visited = set()
        
        while pq:
            current_dist, current_id = heapq.heappop(pq)
            
            if current_id in visited:
                continue
            
            visited.add(current_id)
            
            if current_id == end_id:
                # Восстановление пути
                path = []
                node_id = end_id
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
        
        return None, "Path not found"
```

**core/cache/route_cache.py**
```python
from typing import List, Tuple, Optional
from ..models.node import Node

class RouteCache:
    def __init__(self, max_size: int = 1000):
        self.cache: Dict[Tuple[int, int], List[Node]] = {}
        self.max_size = max_size
    
    def get(self, from_id: int, to_id: int) -> Optional[List[Node]]:
        """Получить путь из кэша"""
        key = (from_id, to_id)
        return self.cache.get(key)
    
    def set(self, from_id: int, to_id: int, path: List[Node]):
        """Сохранить путь в кэш"""
        if len(self.cache) >= self.max_size:
            # Удалить наиболее старый элемент (простая FIFO стратегия)
            self.cache.pop(next(iter(self.cache)))
        
        key = (from_id, to_id)
        self.cache[key] = path
    
    def clear(self):
        """Очистить кэш"""
        self.cache.clear()
```

### 2.2 Backend Service (REST API)

#### Структура проекта
```
backend/
├── app/
│   ├── main.py              # FastAPI/Flask app
│   ├── config.py            # Конфигурация
│   ├── database.py          # Подключение к БД
│   ├── dependencies.py      # Зависимости
│   ├── api/
│   │   ├── routes.py        # Маршруты API
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── navigation.py  # Маршруты навигации
│   │   │   │   ├── buildings.py   # Информация о зданиях
│   │   │   │   ├── nodes.py       # CRUD для узлов
│   │   │   │   └── search.py      # Поиск
│   │   │   └── schemas.py   # Pydantic схемы
│   ├── services/
│   │   ├── navigation_service.py
│   │   ├── building_service.py
│   │   └── search_service.py
│   ├── models/
│   │   ├── db/
│   │   │   ├── building.py
│   │   │   ├── node.py
│   │   │   └── edge.py
│   │   └── dto/              # Data Transfer Objects
│   └── utils/
├── tests/
│   ├── test_navigation.py
│   ├── test_buildings.py
│   └── conftest.py
├── requirements.txt
└── Dockerfile
```

#### Пример API (FastAPI)

**backend/app/api/v1/endpoints/navigation.py**
```python
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from ....services.navigation_service import NavigationService
from ....models.dto import RouteResponse, NodeResponse

router = APIRouter(prefix="/routes", tags=["navigation"])

@router.get("/shortest")
async def get_shortest_route(
    start_id: int,
    end_id: int,
    building_id: str = None,
    service: NavigationService = Depends()
) -> RouteResponse:
    """
    Получить кратчайший маршрут между двумя узлами
    
    Query Parameters:
    - start_id: ID стартового узла
    - end_id: ID конечного узла
    - building_id: ID здания (опционально)
    
    Returns:
    {
        "path": [{"id": 1, "name": "Room 101", "floor": 1, ...}, ...],
        "totalDistance": 45.5,
        "estimatedTime": "2 minutes",
        "floorTransitions": [1, 2],
        "instructions": ["Exit Room 101", "Walk to corridor", "Take elevator"]
    }
    """
    
    try:
        route = service.calculate_route(start_id, end_id, building_id)
        if not route:
            raise HTTPException(status_code=404, detail="Route not found")
        return route
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/bulk-calculate")
async def calculate_multiple_routes(
    routes: List[dict],
    service: NavigationService = Depends()
):
    """Рассчитать несколько маршрутов (batch operation)"""
    results = []
    for route_req in routes:
        route = service.calculate_route(
            route_req['start_id'],
            route_req['end_id']
        )
        results.append(route)
    return {"routes": results}
```

**backend/app/services/navigation_service.py**
```python
from typing import List, Optional
from ..models.dto import RouteResponse
from core.graph.dijkstra import Dijkstra
from core.cache.route_cache import RouteCache
from core.models.node import Node

class NavigationService:
    def __init__(self, db_session, cache: RouteCache):
        self.db = db_session
        self.cache = cache
    
    def calculate_route(
        self,
        start_id: int,
        end_id: int,
        building_id: Optional[str] = None
    ) -> Optional[RouteResponse]:
        """Расчёт маршрута с кэшированием"""
        
        # Проверка кэша
        cached = self.cache.get(start_id, end_id)
        if cached:
            return self._build_response(cached)
        
        # Получение узлов из БД
        nodes = self.db.query(Node).filter(
            Node.building_id == building_id
        ).all()
        
        edges = self._build_edges_dict(nodes)
        
        # Расчёт пути
        path, error = Dijkstra.find_shortest_path(
            nodes, edges, start_id, end_id
        )
        
        if path:
            self.cache.set(start_id, end_id, path)
            return self._build_response(path)
        
        return None
    
    def _build_response(self, path: List[Node]) -> RouteResponse:
        """Построить ответ для API"""
        total_distance = self._calculate_distance(path)
        instructions = self._generate_instructions(path)
        floor_transitions = self._extract_floor_transitions(path)
        
        return RouteResponse(
            path=[node.to_dto() for node in path],
            totalDistance=total_distance,
            estimatedTime=self._estimate_time(total_distance),
            floorTransitions=floor_transitions,
            instructions=instructions
        )
```

### 2.3 Frontend - Web (React)

#### Структура проекта
```
frontend-web/
├── public/
├── src/
│   ├── components/
│   │   ├── Map.tsx          # Главная карта
│   │   ├── NavBar.tsx       # Навигационная панель
│   │   ├── RoutePanel.tsx   # Панель маршрута
│   │   ├── FloorSelector.tsx# Выбор этажа
│   │   └── Search.tsx       # Поиск помещений
│   ├── pages/
│   │   ├── HomePage.tsx
│   │   ├── BuildingPage.tsx
│   │   └── AdminPage.tsx
│   ├── services/
│   │   └── api.ts           # API клиент
│   ├── types/
│   │   └── index.ts         # TypeScript типы
│   ├── utils/
│   │   └── mapUtils.ts
│   ├── App.tsx
│   └── index.tsx
├── package.json
└── Dockerfile
```

#### Пример компонента (React/TypeScript)

**src/components/Map.tsx**
```typescript
import React, { useEffect, useState, useRef } from 'react';
import { Canvas } from './Canvas';
import { RoutePanel } from './RoutePanel';
import { apiService } from '../services/api';
import { Node as NodeType, Edge as EdgeType } from '../types';

interface MapProps {
  buildingId: string;
  floor: number;
}

export const Map: React.FC<MapProps> = ({ buildingId, floor }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [nodes, setNodes] = useState<NodeType[]>([]);
  const [edges, setEdges] = useState<EdgeType[]>([]);
  const [startNode, setStartNode] = useState<NodeType | null>(null);
  const [endNode, setEndNode] = useState<NodeType | null>(null);
  const [route, setRoute] = useState<NodeType[] | null>(null);
  const [loading, setLoading] = useState(false);

  // Загрузка узлов и рёбер
  useEffect(() => {
    const loadBuilding = async () => {
      try {
        const building = await apiService.getBuilding(buildingId);
        const floorNodes = building.nodes.filter((n: NodeType) => n.floor === floor);
        setNodes(floorNodes);
        
        // Фильтруем рёбра для текущего этажа
        const floorEdges = building.edges.filter((e: EdgeType) => {
          const fromNode = building.nodes.find((n: NodeType) => n.id === e.fromId);
          const toNode = building.nodes.find((n: NodeType) => n.id === e.toId);
          return fromNode?.floor === floor && toNode?.floor === floor;
        });
        setEdges(floorEdges);
      } catch (error) {
        console.error('Failed to load building:', error);
      }
    };

    loadBuilding();
  }, [buildingId, floor]);

  // Расчёт маршрута
  useEffect(() => {
    if (startNode && endNode) {
      calculateRoute();
    }
  }, [startNode, endNode]);

  const calculateRoute = async () => {
    if (!startNode || !endNode) return;
    
    setLoading(true);
    try {
      const routeData = await apiService.getRoute(startNode.id, endNode.id, buildingId);
      setRoute(routeData.path);
    } catch (error) {
      console.error('Failed to calculate route:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleNodeClick = (node: NodeType) => {
    if (!startNode) {
      setStartNode(node);
    } else if (!endNode && node.id !== startNode.id) {
      setEndNode(node);
    } else {
      setStartNode(node);
      setEndNode(null);
    }
  };

  return (
    <div className="map-container">
      <Canvas
        ref={canvasRef}
        nodes={nodes}
        edges={edges}
        route={route}
        startNode={startNode}
        endNode={endNode}
        onNodeClick={handleNodeClick}
        floorPlan={`/images/floor-${floor}.png`}
      />
      <RoutePanel
        startNode={startNode}
        endNode={endNode}
        route={route}
        loading={loading}
        onReset={() => {
          setStartNode(null);
          setEndNode(null);
          setRoute(null);
        }}
      />
    </div>
  );
};
```

### 2.4 Frontend - Mobile (Python/Kivy)

#### Структура проекта (Android/iOS)
```
mobile-app/
├── main.py
├── buildozer.spec           # Конфиг для Kivy->APK
├── screens/
│   ├── home_screen.py
│   ├── map_screen.py
│   ├── search_screen.py
│   └── settings_screen.py
├── services/
│   ├── api_client.py
│   ├── location_service.py
│   └── cache_service.py
├── widgets/
│   ├── map_widget.py
│   ├── route_panel.py
│   └── floor_selector.py
├── assets/
│   ├── images/
│   └── icons/
├── requirements.txt
└── icon.png
```

#### Пример экрана (Kivy/Python)

**mobile-app/screens/map_screen.py**
```python
from kivy.uix.screen import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.garden.mapview import MapView, MapMarker
from kivy.clock import Clock

from ..services.api_client import APIClient
from ..widgets.map_widget import MapWidget
from ..widgets.route_panel import RoutePanel


class MapScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.api_client = APIClient()
        self.building_id = None
        self.floor = 1
        self.start_node = None
        self.end_node = None
        self.route = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """Инициализировать UI"""
        layout = BoxLayout(orientation='vertical')
        
        # Верхняя панель с выбором этажа
        top_panel = BoxLayout(size_hint_y=0.1)
        top_panel.add_widget(Label(text='Floor:', size_hint_x=0.2))
        self.floor_spinner = Spinner(
            text=str(self.floor),
            values=('1', '2', '3', '4', '5'),
            size_hint_x=0.2
        )
        self.floor_spinner.bind(text=self.on_floor_change)
        top_panel.add_widget(self.floor_spinner)
        top_panel.add_widget(Label(text='', size_hint_x=0.6))
        
        layout.add_widget(top_panel)
        
        # Главная карта
        self.map_widget = MapWidget(
            size_hint=(1, 0.7),
            building_id=self.building_id
        )
        self.map_widget.bind(on_node_select=self.on_node_select)
        layout.add_widget(self.map_widget)
        
        # Панель маршрута
        self.route_panel = RoutePanel(size_hint_y=0.3)
        layout.add_widget(self.route_panel)
        
        self.add_widget(layout)
    
    def on_floor_change(self, spinner, text):
        """Обработка изменения этажа"""
        self.floor = int(text)
        self.map_widget.load_floor(self.floor)
    
    def on_node_select(self, widget, node):
        """Обработка выбора узла"""
        if not self.start_node:
            self.start_node = node
            self.route_panel.set_start_node(node)
        elif not self.end_node and node['id'] != self.start_node['id']:
            self.end_node = node
            self.route_panel.set_end_node(node)
            self.calculate_route()
        else:
            self.start_node = node
            self.end_node = None
            self.route_panel.set_start_node(node)
            self.route_panel.clear_end_node()
    
    def calculate_route(self):
        """Расчёт маршрута"""
        if not self.start_node or not self.end_node:
            return
        
        Clock.schedule_once(
            lambda dt: self._do_calculate_route(),
            0
        )
    
    def _do_calculate_route(self):
        """Асинхронный расчёт маршрута"""
        try:
            route_data = self.api_client.get_route(
                self.start_node['id'],
                self.end_node['id'],
                self.building_id
            )
            self.route = route_data['path']
            self.map_widget.set_route(self.route)
            self.route_panel.set_route(route_data)
        except Exception as e:
            print(f"Error calculating route: {e}")
            self.route_panel.show_error(f"Failed to calculate route: {e}")
```

**mobile-app/widgets/map_widget.py**
```python
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line, Ellipse
from kivy.core.window import Window
from kivy.properties import ListProperty, NumericProperty
from kivy.uix.image import Image as KivyImage

class MapWidget(Widget):
    nodes = ListProperty([])
    edges = ListProperty([])
    route = ListProperty([])
    scale = NumericProperty(1.0)
    
    def __init__(self, building_id, **kwargs):
        super().__init__(**kwargs)
        self.building_id = building_id
        self.start_node = None
        self.end_node = None
        self.floor_plan = None
        
        self.bind(size=self.on_size)
        self.bind(pos=self.on_pos)
    
    def load_floor(self, floor):
        """Загрузить этаж"""
        # Загрузить изображение плана этажа
        self.floor_plan = KivyImage(
            source=f'assets/images/floor-{floor}.png',
            size=self.size,
            pos=self.pos
        )
        # Загрузить узлы и рёбра для этажа
        self.load_nodes_and_edges(floor)
    
    def load_nodes_and_edges(self, floor):
        """Загрузить узлы и рёбра с сервера"""
        # API call to get nodes and edges
        pass
    
    def on_touch_down(self, touch):
        """Обработка нажатия на экран"""
        if self.collide_point(*touch.pos):
            # Проверить, нажали ли на какой-то узел
            for node in self.nodes:
                if self.is_point_in_node(touch.pos, node):
                    self.dispatch('on_node_select', node)
                    return True
        return super().on_touch_down(touch)
    
    def is_point_in_node(self, touch_pos, node):
        """Проверить, находится ли точка в узле"""
        node_x = node['position']['x'] * self.scale + self.x
        node_y = node['position']['y'] * self.scale + self.y
        distance = ((touch_pos[0] - node_x)**2 + (touch_pos[1] - node_y)**2)**0.5
        return distance <= 20
    
    def set_route(self, route):
        """Установить маршрут для визуализации"""
        self.route = route
        self.canvas.ask_update()
    
    def on_size(self, *args):
        """Обновить размер при изменении окна"""
        self.canvas.ask_update()
    
    def on_draw(self):
        """Рисование карты"""
        with self.canvas:
            # Очистить холст
            self.canvas.clear()
            
            # Нарисовать план этажа (если есть)
            # ... код рисования плана ...
            
            # Нарисовать рёбра
            Color(0.7, 0.7, 0.7)
            for edge in self.edges:
                from_node = next((n for n in self.nodes if n['id'] == edge['fromId']), None)
                to_node = next((n for n in self.nodes if n['id'] == edge['toId']), None)
                if from_node and to_node:
                    Line(points=[
                        from_node['position']['x'] * self.scale + self.x,
                        from_node['position']['y'] * self.scale + self.y,
                        to_node['position']['x'] * self.scale + self.x,
                        to_node['position']['y'] * self.scale + self.y
                    ])
            
            # Нарисовать узлы
            for node in self.nodes:
                Color(*self.get_node_color(node['type']))
                Ellipse(
                    pos=(
                        node['position']['x'] * self.scale + self.x - 10,
                        node['position']['y'] * self.scale + self.y - 10
                    ),
                    size=(20, 20)
                )
            
            # Нарисовать маршрут
            if self.route:
                Color(1, 0, 0, 0.7)  # Красный полупрозрачный
                for i in range(len(self.route) - 1):
                    from_node = self.route[i]
                    to_node = self.route[i + 1]
                    Line(points=[
                        from_node['position']['x'] * self.scale + self.x,
                        from_node['position']['y'] * self.scale + self.y,
                        to_node['position']['x'] * self.scale + self.x,
                        to_node['position']['y'] * self.scale + self.y
                    ], width=3)
    
    def get_node_color(self, node_type):
        """Получить цвет узла по типу"""
        colors = {
            'Room': (0, 0, 1),      # Синий
            'Corridor': (0, 1, 0),  # Зелёный
            'Staircase': (1, 0.5, 0),  # Оранжевый
            'Elevator': (1, 0, 0)   # Красный
        }
        return colors.get(node_type, (0.5, 0.5, 0.5))
```

---

## 3. БАЗА ДАННЫХ

### 3.1 Схема PostgreSQL

```sql
-- Здания
CREATE TABLE buildings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    address VARCHAR(500),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    floors_count INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Этажи и планы
CREATE TABLE floor_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    building_id UUID NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,
    floor INT NOT NULL,
    image_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Узлы (помещения)
CREATE TABLE nodes (
    id SERIAL PRIMARY KEY,
    building_id UUID NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    floor INT NOT NULL,
    node_type VARCHAR(50) NOT NULL CHECK(node_type IN ('Room', 'Corridor', 'Staircase', 'Elevator')),
    position_x DECIMAL(10, 2),
    position_y DECIMAL(10, 2),
    custom_size INT DEFAULT 20,
    rotation_angle DECIMAL(5, 2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(building_id, floor, name)
);

-- Рёбра (связи между узлами)
CREATE TABLE edges (
    id SERIAL PRIMARY KEY,
    from_id INT NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    to_id INT NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    weight DECIMAL(10, 2) NOT NULL,
    is_bidirectional BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(from_id, to_id)
);

-- Пользователи (для аутентификации в будущем)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    role VARCHAR(50) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- История маршрутов (для аналитики)
CREATE TABLE route_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    start_node_id INT REFERENCES nodes(id),
    end_node_id INT REFERENCES nodes(id),
    distance DECIMAL(10, 2),
    calculation_time_ms INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для оптимизации
CREATE INDEX idx_nodes_building_floor ON nodes(building_id, floor);
CREATE INDEX idx_nodes_type ON nodes(node_type);
CREATE INDEX idx_edges_from_id ON edges(from_id);
CREATE INDEX idx_edges_to_id ON edges(to_id);
CREATE INDEX idx_route_history_user_id ON route_history(user_id);
CREATE INDEX idx_route_history_created_at ON route_history(created_at);
```

### 3.2 Redis Cache

```python
# Кэширование маршрутов
cache_key = f"route:{building_id}:{start_id}:{end_id}"
cached_route = redis_client.get(cache_key)

if not cached_route:
    route = calculate_route(start_id, end_id)
    # Сохранить на 1 час
    redis_client.setex(cache_key, 3600, json.dumps(route))
else:
    route = json.loads(cached_route)
```

---

## 4. API СПЕЦИФИКАЦИЯ

### 4.1 REST Endpoints

```
GET  /api/v1/buildings                          # Список зданий
GET  /api/v1/buildings/{id}                     # Информация о здании
GET  /api/v1/buildings/{id}/floors              # Список этажей
GET  /api/v1/buildings/{id}/nodes               # Список узлов
GET  /api/v1/buildings/{id}/floor-plan/{floor}  # План этажа

GET  /api/v1/routes/shortest                    # Кратчайший маршрут
POST /api/v1/routes/bulk-calculate              # Массовый расчёт
GET  /api/v1/routes/{id}/instructions           # Инструкции маршрута

GET  /api/v1/search                             # Поиск помещений
GET  /api/v1/nodes/{id}                         # Информация о узле
```

### 4.2 WebSocket (для real-time)

```
WS /ws/building/{buildingId}/floor/{floor}

# Сообщения
- user_location_update
- route_recalculation
- building_map_update
```

---

## 5. РАЗВЁРТЫВАНИЕ

### 5.1 Docker Compose (локально)

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@postgres:5432/campuscompass
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
    volumes:
      - ./backend:/app

  web:
    build: ./frontend-web
    ports:
      - "3000:3000"
    depends_on:
      - backend

  postgres:
    image: postgres:14
    environment:
      - POSTGRES_DB=campuscompass
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

### 5.2 Production (Cloud)

```bash
# AWS ECS / Kubernetes
- Backend service (Auto-scaled)
- Web app (CloudFront CDN)
- RDS PostgreSQL
- ElastiCache Redis
- S3 для изображений
```

---

## 6. МИГРАЦИЯ ДАННЫХ

### 6.1 Конвертация из C# в Python/JSON

```python
import json
from core.models.node import Node, NodeType
from core.models.edge import Edge

def migrate_from_csharp_json(csharp_json_path: str) -> dict:
    """Конвертировать map.json из C# в Python формат"""
    
    with open(csharp_json_path, 'r') as f:
        data = json.load(f)
    
    # Преобразование узлов
    nodes = []
    for node_data in data.get('Nodes', []):
        node = {
            'id': node_data['Id'],
            'name': node_data['Name'],
            'floor': node_data['Floor'],
            'type': node_data['Type'],
            'position': {
                'x': node_data['Position']['X'],
                'y': node_data['Position']['Y']
            },
            'custom_size': node_data.get('CustomSize', 20),
            'rotation_angle': node_data.get('RotationAngle', 0.0)
        }
        nodes.append(node)
    
    # Преобразование рёбер
    edges = []
    for edge_data in data.get('Edges', []):
        edge = {
            'from_id': edge_data['FromId'],
            'to_id': edge_data['ToId'],
            'weight': edge_data['Weight']
        }
        edges.append(edge)
    
    return {
        'nodes': nodes,
        'edges': edges,
        'floor_plans': data.get('FloorPlans', {})
    }
```

---

## 7. ТЕСТИРОВАНИЕ

### 7.1 Unit тесты (Python)

```python
# tests/test_dijkstra.py
import pytest
from core.graph.dijkstra import Dijkstra
from core.models.node import Node, NodeType

class TestDijkstra:
    @pytest.fixture
    def sample_graph(self):
        nodes = [
            Node(id=1, name="A", floor=1, node_type=NodeType.ROOM, position={'x': 0, 'y': 0}),
            Node(id=2, name="B", floor=1, node_type=NodeType.ROOM, position={'x': 100, 'y': 0}),
            Node(id=3, name="C", floor=1, node_type=NodeType.ROOM, position={'x': 200, 'y': 0}),
        ]
        edges = {
            1: [(2, 10)],
            2: [(1, 10), (3, 15)],
            3: [(2, 15)]
        }
        return nodes, edges
    
    def test_simple_path(self, sample_graph):
        nodes, edges = sample_graph
        path, error = Dijkstra.find_shortest_path(nodes, edges, 1, 3)
        
        assert error is None
        assert len(path) == 3
        assert path[0].id == 1
        assert path[-1].id == 3
```

### 7.2 Integration тесты

```python
# tests/test_api_integration.py
import pytest
from httpx import AsyncClient
from backend.app.main import app

@pytest.mark.asyncio
async def test_get_route():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/routes/shortest",
            params={"start_id": 1, "end_id": 3}
        )
        assert response.status_code == 200
        assert "path" in response.json()
```

---

## 8. MONITORING И LOGGING

```python
# Использовать ELK Stack или CloudWatch
import logging
from pythonjsonlogger import jsonlogger

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
handler.setFormatter(formatter)
logger.addHandler(handler)

logger.info("Route calculated", extra={
    "start_id": 1,
    "end_id": 3,
    "distance": 45.5,
    "time_ms": 23
})
```

---

## ЗАКЛЮЧЕНИЕ

Эта архитектура обеспечивает:
- ✅ Переносимость кода между платформами
- ✅ Масштабируемость (микросервисы)
- ✅ Высокую производительность (кэширование)
- ✅ Легкость тестирования (модульная структура)
- ✅ Поддержку multiple frontend приложений
- ✅ Простоту развёртывания (Docker, Kubernetes)

