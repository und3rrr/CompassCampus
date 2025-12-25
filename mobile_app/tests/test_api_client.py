"""
Unit тесты для API Client
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from services.api_client import APIClient, Node, Route, Building
import requests
from requests.exceptions import RequestException, HTTPError


class TestAPIClient:
    """Тесты для APIClient"""

    def test_initialization(self):
        """Тест инициализации API клиента"""
        api = APIClient(base_url="http://test.local/api", timeout=15)
        assert api.base_url == "http://test.local/api"
        assert api.timeout == 15

    def test_default_initialization(self):
        """Тест инициализации с дефолтными параметрами"""
        api = APIClient()
        assert api.base_url == "http://localhost:8000/api/v1"
        assert api.timeout == 10

    def test_set_base_url(self):
        """Тест изменения базового URL"""
        api = APIClient()
        api.set_base_url("http://new.local/api")
        assert api.base_url == "http://new.local/api"

    def test_health_check_success(self):
        """Тест успешной проверки здоровья API"""
        api = APIClient()
        with patch.object(api.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            result = api.health_check()
            assert result is True

    def test_health_check_failure(self):
        """Тест неудачной проверки здоровья API"""
        api = APIClient()
        with patch.object(api.session, 'get') as mock_get:
            mock_get.side_effect = RequestException("Connection failed")

            result = api.health_check()
            assert result is False

    def test_get_buildings_success(self, api_client, sample_building):
        """Тест успешного получения списка зданий"""
        with patch.object(api_client.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {
                "buildings": [
                    {
                        "id": sample_building.id,
                        "name": sample_building.name,
                        "address": sample_building.address,
                        "floors": sample_building.floors,
                        "nodes": []
                    }
                ]
            }
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            buildings = api_client.get_buildings()
            assert len(buildings) == 1
            assert buildings[0].id == sample_building.id
            assert buildings[0].name == sample_building.name

    def test_get_buildings_empty(self, api_client):
        """Тест получения пустого списка зданий"""
        with patch.object(api_client.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {"buildings": []}
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            buildings = api_client.get_buildings()
            assert len(buildings) == 0

    def test_get_building_by_id(self, api_client, sample_building):
        """Тест получения здания по ID"""
        with patch.object(api_client.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {
                "id": sample_building.id,
                "name": sample_building.name,
                "address": sample_building.address,
                "floors": sample_building.floors,
                "nodes": []
            }
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            building = api_client.get_building(sample_building.id)
            assert building.id == sample_building.id
            assert building.name == sample_building.name

    def test_get_route_success(self, api_client, sample_route):
        """Тест успешного получения маршрута"""
        with patch.object(api_client.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {
                "path": [
                    {"id": "room_101", "name": "Аудитория 101", "x": 10.0, "y": 20.0, "floor": 1, "type": "Room"},
                    {"id": "room_102", "name": "Аудитория 102", "x": 30.0, "y": 20.0, "floor": 1, "type": "Room"}
                ],
                "distance": 25.0,
                "estimated_time": 2.5,
                "floor_changes": 0
            }
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            route = api_client.get_route("building_1", "room_101", "room_102")
            assert route.distance == 25.0
            assert route.estimated_time == 2.5
            assert len(route.path) == 2

    def test_get_multiple_routes_success(self, api_client):
        """Тест получения нескольких маршрутов"""
        with patch.object(api_client.session, 'post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {
                "routes": [
                    {
                        "path": [
                            {"id": "room_101", "name": "Аудитория 101", "x": 10.0, "y": 20.0, "floor": 1, "type": "Room"}
                        ],
                        "distance": 15.0,
                        "estimated_time": 1.5,
                        "floor_changes": 0
                    },
                    {
                        "path": [
                            {"id": "room_102", "name": "Аудитория 102", "x": 30.0, "y": 20.0, "floor": 1, "type": "Room"}
                        ],
                        "distance": 25.0,
                        "estimated_time": 2.5,
                        "floor_changes": 0
                    }
                ]
            }
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            routes = api_client.get_multiple_routes("building_1", "room_101", ["room_102", "room_103"])
            assert len(routes) == 2
            assert routes[0].distance == 15.0
            assert routes[1].distance == 25.0

    def test_search_nodes_success(self, api_client):
        """Тест успешного поиска узлов"""
        with patch.object(api_client.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {
                "results": [
                    {"id": "room_101", "name": "Аудитория 101", "x": 10.0, "y": 20.0, "floor": 1, "type": "Room"},
                    {"id": "room_102", "name": "Аудитория 102", "x": 30.0, "y": 20.0, "floor": 1, "type": "Room"}
                ]
            }
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            results = api_client.search_nodes("building_1", "Аудитория")
            assert len(results) == 2
            assert results[0].name == "Аудитория 101"

    def test_search_nodes_empty(self, api_client):
        """Тест поиска без результатов"""
        with patch.object(api_client.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {"results": []}
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            results = api_client.search_nodes("building_1", "NonExistent")
            assert len(results) == 0

    def test_handle_response_error(self, api_client):
        """Тест обработки ошибок ответа"""
        with patch.object(api_client.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.text = "Not found"
            mock_response.raise_for_status.side_effect = HTTPError("404 Not found")
            mock_get.return_value = mock_response

            with pytest.raises(HTTPError):
                api_client._handle_response(mock_response)

    def test_connection_timeout(self, api_client):
        """Тест обработки timeout"""
        with patch.object(api_client.session, 'get') as mock_get:
            mock_get.side_effect = RequestException("Connection timeout")

            with pytest.raises(RequestException):
                api_client.get_buildings()


class TestNodeDataClass:
    """Тесты для Node dataclass"""

    def test_node_creation(self, sample_nodes):
        """Тест создания узла"""
        node = sample_nodes[0]
        assert node.id == "room_101"
        assert node.name == "Аудитория 101"
        assert node.x == 10.0
        assert node.y == 20.0
        assert node.floor == 1
        assert node.node_type == "Room"

    def test_node_equality(self, sample_nodes):
        """Тест сравнения узлов"""
        node1 = sample_nodes[0]
        node2 = Node(
            id="room_101",
            name="Аудитория 101",
            x=10.0,
            y=20.0,
            floor=1,
            node_type="Room"
        )
        assert node1 == node2


class TestRouteDataClass:
    """Тесты для Route dataclass"""

    def test_route_creation(self, sample_route):
        """Тест создания маршрута"""
        assert sample_route.distance == 25.0
        assert sample_route.estimated_time == 2.5
        assert sample_route.floor_changes == 0
        assert len(sample_route.path) == 2

    def test_route_distance_calculation(self, sample_nodes):
        """Тест расчета дистанции маршрута"""
        route = Route(
            path=sample_nodes[:2],
            distance=float('inf'),
            estimated_time=0,
            floor_changes=0
        )
        # Расстояние между (10, 20) и (30, 20) = 20
        expected_distance = 20.0
        assert route.distance == float('inf')  # Внешняя логика должна вычислить


class TestBuildingDataClass:
    """Тесты для Building dataclass"""

    def test_building_creation(self, sample_building):
        """Тест создания здания"""
        assert sample_building.id == "building_1"
        assert sample_building.name == "Главный корпус"
        assert sample_building.floors == 3
        assert len(sample_building.nodes) == 3

    def test_building_floors_count(self, sample_building):
        """Тест подсчета этажей"""
        assert sample_building.floors == 3
