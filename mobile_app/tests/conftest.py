"""
Конфигурация для Pytest - глобальные fixtures
"""
import pytest
from unittest.mock import Mock, patch
from services.api_client import APIClient, Node, Route, Building
from services.cache_service import CacheService
import tempfile
import os


@pytest.fixture
def api_client():
    """Fixture для API клиента"""
    return APIClient(base_url="http://localhost:8000/api/v1")


@pytest.fixture
def cache_service():
    """Fixture для кэш-сервиса"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield CacheService(cache_dir=tmpdir)


@pytest.fixture
def sample_nodes():
    """Fixture с примерами узлов"""
    return [
        Node(
            id="room_101",
            name="Аудитория 101",
            x=10.0,
            y=20.0,
            floor=1,
            node_type="Room"
        ),
        Node(
            id="room_102",
            name="Аудитория 102",
            x=30.0,
            y=20.0,
            floor=1,
            node_type="Room"
        ),
        Node(
            id="corridor_1",
            name="Коридор 1",
            x=20.0,
            y=20.0,
            floor=1,
            node_type="Corridor"
        ),
    ]


@pytest.fixture
def sample_building(sample_nodes):
    """Fixture с примером здания"""
    return Building(
        id="building_1",
        name="Главный корпус",
        address="ул. Ломоносова, 27",
        nodes=sample_nodes,
        floors=3
    )


@pytest.fixture
def sample_route(sample_nodes):
    """Fixture с примером маршрута"""
    return Route(
        path=sample_nodes[:2],
        distance=25.0,
        estimated_time=2.5,
        floor_changes=0
    )


@pytest.fixture
def mock_requests():
    """Fixture для мокирования requests"""
    with patch('services.api_client.requests') as mock:
        yield mock
