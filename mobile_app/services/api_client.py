"""
API Client Service для взаимодействия с Backend API
"""
import requests
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class Node:
    """Модель узла графа"""
    id: str
    name: str
    x: float
    y: float
    floor: int
    node_type: str  # Room, Corridor, Staircase, Elevator

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if isinstance(other, Node):
            return self.id == other.id
        return False


@dataclass
class Route:
    """Модель маршрута"""
    path: List[Node]
    distance: float
    estimated_time: float  # в минутах
    floor_changes: int


@dataclass
class Building:
    """Модель здания"""
    id: str
    name: str
    address: str
    nodes: List[Node]
    floors: int


class APIClient:
    """Клиент для работы с REST API"""

    def __init__(self, base_url: str = "http://localhost:8000/api/v1", timeout: int = 10):
        """
        Инициализация API клиента

        Args:
            base_url: URL базового сервера API
            timeout: Timeout для запросов в секундах
        """
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "CampusCompass-Mobile/1.0"
        })

    def _handle_response(self, response: requests.Response) -> Dict:
        """
        Обработка ответа от API

        Args:
            response: Ответ от requests

        Returns:
            Распарсенный JSON или ошибка

        Raises:
            requests.HTTPError: Если статус код != 2xx
        """
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"API Error: {e.response.status_code} - {e.response.text}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request Error: {e}")
            raise

    # ============== NAVIGATION ENDPOINTS ==============

    def get_route(
        self,
        building_id: str,
        start_node_id: str,
        end_node_id: str,
        avoid_stairs: bool = False
    ) -> Route:
        """
        Получить маршрут между двумя точками

        Args:
            building_id: ID здания
            start_node_id: ID стартового узла
            end_node_id: ID конечного узла
            avoid_stairs: Избегать лестниц (для инвалидов)

        Returns:
            Объект Route с маршрутом
        """
        endpoint = f"{self.base_url}/navigation/routes/shortest"
        params = {
            "building_id": building_id,
            "start_node_id": start_node_id,
            "end_node_id": end_node_id,
            "avoid_stairs": avoid_stairs
        }

        try:
            response = self.session.get(
                endpoint,
                params=params,
                timeout=self.timeout
            )
            data = self._handle_response(response)

            # Парсим ответ в объект Route
            path_nodes = [
                Node(
                    id=node["id"],
                    name=node["name"],
                    x=node["x"],
                    y=node["y"],
                    floor=node["floor"],
                    node_type=node["type"]
                )
                for node in data["path"]
            ]

            return Route(
                path=path_nodes,
                distance=data["distance"],
                estimated_time=data["estimated_time"],
                floor_changes=data["floor_changes"]
            )
        except Exception as e:
            logger.error(f"Failed to get route: {e}")
            raise

    def get_multiple_routes(
        self,
        building_id: str,
        start_node_id: str,
        end_node_ids: List[str]
    ) -> List[Route]:
        """
        Получить маршруты до нескольких целей

        Args:
            building_id: ID здания
            start_node_id: ID стартового узла
            end_node_ids: Список ID целевых узлов

        Returns:
            Список маршрутов
        """
        endpoint = f"{self.base_url}/navigation/routes/calculate-multiple"
        payload = {
            "building_id": building_id,
            "start_node_id": start_node_id,
            "end_node_ids": end_node_ids
        }

        try:
            response = self.session.post(
                endpoint,
                json=payload,
                timeout=self.timeout
            )
            data = self._handle_response(response)

            routes = []
            for route_data in data["routes"]:
                path_nodes = [
                    Node(
                        id=node["id"],
                        name=node["name"],
                        x=node["x"],
                        y=node["y"],
                        floor=node["floor"],
                        node_type=node["type"]
                    )
                    for node in route_data["path"]
                ]
                routes.append(Route(
                    path=path_nodes,
                    distance=route_data["distance"],
                    estimated_time=route_data["estimated_time"],
                    floor_changes=route_data["floor_changes"]
                ))

            return routes
        except Exception as e:
            logger.error(f"Failed to get multiple routes: {e}")
            raise

    # ============== BUILDING ENDPOINTS ==============

    def get_buildings(self) -> List[Building]:
        """
        Получить список всех зданий

        Returns:
            Список зданий
        """
        endpoint = f"{self.base_url}/buildings"

        try:
            response = self.session.get(endpoint, timeout=self.timeout)
            data = self._handle_response(response)

            buildings = []
            for building_data in data["buildings"]:
                nodes = [
                    Node(
                        id=node["id"],
                        name=node["name"],
                        x=node["x"],
                        y=node["y"],
                        floor=node["floor"],
                        node_type=node["type"]
                    )
                    for node in building_data.get("nodes", [])
                ]
                buildings.append(Building(
                    id=building_data["id"],
                    name=building_data["name"],
                    address=building_data["address"],
                    nodes=nodes,
                    floors=building_data["floors"]
                ))

            return buildings
        except Exception as e:
            logger.error(f"Failed to get buildings: {e}")
            # Возвращаем демо-данные если API недоступен
            logger.info("Using demo data for buildings")
            return self._get_demo_buildings()

    def _get_demo_buildings(self) -> List[Building]:
        """Получить реальные данные зданий из CSV (cds.csv)"""
        from .graph_builder import DEMO_NODES_CSV, GraphBuilder
        
        # Используем реальные данные из CSV
        nodes_data = DEMO_NODES_CSV
        
        # Преобразуем в объекты Node
        nodes_dict = {}
        for node_data in nodes_data:
            node = Node(
                id=str(node_data['Id']),
                name=node_data['Name'],
                x=float(node_data['X']),
                y=float(node_data['Y']),
                floor=int(node_data['Floor']),
                node_type=node_data['Type']
            )
            nodes_dict[node.id] = node
        
        # Получаем все уникальные узлы
        all_nodes = list(nodes_dict.values())
        
        # Определяем количество этажей
        floors = max([node.floor for node in all_nodes], default=1)
        
        # Возвращаем одно здание со всеми узлами
        building = Building(
            id="building_main",
            name="Главный корпус",
            address="ул. Ломоносова, 27",
            floors=floors,
            nodes=all_nodes
        )
        
        logger.info(f"Loaded {len(all_nodes)} nodes from CSV data for {floors} floors")
        return [building]

    def get_building(self, building_id: str) -> Building:
        """
        Получить информацию о конкретном здании

        Args:
            building_id: ID здания

        Returns:
            Объект Building
        """
        endpoint = f"{self.base_url}/buildings/{building_id}"

        try:
            response = self.session.get(endpoint, timeout=self.timeout)
            data = self._handle_response(response)

            nodes = [
                Node(
                    id=node["id"],
                    name=node["name"],
                    x=node["x"],
                    y=node["y"],
                    floor=node["floor"],
                    node_type=node["type"]
                )
                for node in data.get("nodes", [])
            ]

            return Building(
                id=data["id"],
                name=data["name"],
                address=data["address"],
                nodes=nodes,
                floors=data["floors"]
            )
        except Exception as e:
            logger.error(f"Failed to get building {building_id}: {e}")
            raise

    # ============== SEARCH ENDPOINTS ==============

    def search_nodes(self, building_id: str, query: str) -> List[Node]:
        """
        Поиск узлов по названию

        Args:
            building_id: ID здания
            query: Поисковый запрос

        Returns:
            Список найденных узлов
        """
        endpoint = f"{self.base_url}/search"
        params = {
            "building_id": building_id,
            "query": query
        }

        try:
            response = self.session.get(
                endpoint,
                params=params,
                timeout=self.timeout
            )
            data = self._handle_response(response)

            nodes = [
                Node(
                    id=node["id"],
                    name=node["name"],
                    x=node["x"],
                    y=node["y"],
                    floor=node["floor"],
                    node_type=node["type"]
                )
                for node in data.get("results", [])
            ]

            return nodes
        except Exception as e:
            logger.error(f"Search failed for query '{query}': {e}")
            raise

    # ============== HEALTH CHECK ==============

    def health_check(self) -> bool:
        """
        Проверка доступности API

        Returns:
            True если API доступен, False иначе
        """
        try:
            endpoint = f"{self.base_url}/health"
            response = self.session.get(endpoint, timeout=3)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def set_base_url(self, base_url: str):
        """
        Изменить базовый URL API

        Args:
            base_url: Новый URL базового сервера
        """
        self.base_url = base_url


# Глобальный экземпляр клиента
_api_client: Optional[APIClient] = None


def get_api_client() -> APIClient:
    """Получить или создать глобальный экземпляр API клиента"""
    global _api_client
    if _api_client is None:
        _api_client = APIClient()
    return _api_client


def init_api_client(base_url: str = "http://localhost:8000/api/v1"):
    """Инициализировать глобальный API клиент"""
    global _api_client
    _api_client = APIClient(base_url=base_url)
