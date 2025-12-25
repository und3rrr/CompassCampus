#!/usr/bin/env python3
"""
Скрипт тестирования основного функционала Phase 5
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.auth_service import AuthenticationService, UserRole, UserPermission
from services.qr_service import QRCodeService
from services.route_closure_service import RouteClosureService, ClosureType
from services.graph_builder import GraphBuilder, DEMO_NODES_CSV
from services.api_client import init_api_client, get_api_client
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_csv_loading():
    """Тест загрузки CSV данных"""
    print("\n📋 Тест CSV данных:")
    print(f"✓ Загружено {len(DEMO_NODES_CSV)} узлов из cds.csv")
    
    # Проверить типы узлов
    node_types = set(n['Type'] for n in DEMO_NODES_CSV)
    print(f"✓ Типы узлов: {node_types}")
    
    # Проверить этажи
    floors = set(int(n['Floor']) for n in DEMO_NODES_CSV)
    print(f"✓ Этажи: {sorted(floors)}")
    
    # Проверить координаты
    sample = DEMO_NODES_CSV[0]
    print(f"✓ Пример узла: {sample['Name']} (этаж {sample['Floor']}, координаты X={sample['X']}, Y={sample['Y']})")

def test_authentication():
    """Тест системы аутентификации"""
    print("\n🔐 Тест аутентификации:")
    
    auth = AuthenticationService()
    
    # Тест входа гостя
    guest = auth.login_as_guest()
    print(f"✓ Вход как гость: {guest.username} (роль: {guest.role.name})")
    
    # Проверить права гостя
    can_view_map = guest.has_permission(UserPermission.VIEW_MAP)
    can_manage_routes = guest.has_permission(UserPermission.MANAGE_ROUTES)
    print(f"  - Может просматривать карту: {can_view_map}")
    print(f"  - Может управлять маршрутами: {can_manage_routes}")
    
    # Тест входа студента
    student = auth.login_student("Иван", "ivan@example.com", "12345")
    print(f"✓ Вход студента: {student.username} (роль: {student.role.name})")
    
    # Проверить права студента
    can_analytics = student.has_permission(UserPermission.VIEW_ANALYTICS)
    print(f"  - Может просматривать аналитику: {can_analytics}")
    
    # Тест входа администратора
    admin = auth.login_admin("Администратор", "admin@example.com", "admin123", "secret")
    print(f"✓ Вход администратора: {admin.username} (роль: {admin.role.name})")
    
    # Проверить права администратора
    can_admin = admin.has_permission(UserPermission.ADMIN_PANEL)
    print(f"  - Имеет доступ к админ-панели: {can_admin}")
    
    auth.logout()
    print(f"✓ Выход выполнен")

def test_qr_system():
    """Тест QR системы"""
    print("\n📱 Тест QR кодов:")
    
    qr = QRCodeService()
    
    # Создать QR код
    qr_code = qr.create_qr_mapping("room_101", "Кабинет 101", 1)
    print(f"✓ Создан QR код: {qr_code}")
    
    # Получить местоположение по QR коду
    location = qr.get_location_by_qr(qr_code)
    print(f"✓ По QR коду найдено место: {location['node_name']} (этаж {location['floor']})")
    
    # Парсинг разных форматов
    parsed = qr.parse_qr_code(f"CC-room_101-abc12345")
    print(f"✓ Спарсен QR код, node_id: {parsed}")

def test_route_closures():
    """Тест системы закрытых маршрутов"""
    print("\n🚧 Тест закрытых маршрутов:")
    
    closure = RouteClosureService()
    
    # Закрыть маршрут
    closure_id = closure.close_route(
        "room_101", "corridor_1",
        "Техническое обслуживание",
        ClosureType.MAINTENANCE,
        2  # на 2 часа
    )
    print(f"✓ Маршрут закрыт: {closure_id}")
    
    # Проверить если маршрут закрыт
    is_closed = closure.is_route_closed("room_101", "corridor_1")
    print(f"✓ Маршрут закрыт: {is_closed}")
    
    # Получить причину
    reason = closure.get_closure_reason("room_101", "corridor_1")
    print(f"✓ Причина закрытия: {reason}")
    
    # Закрыть узел
    closure_id = closure.close_node(
        "room_201",
        "Санитарная уборка",
        ClosureType.CLEANING,
        1  # на 1 час
    )
    print(f"✓ Узел закрыт: {closure_id}")
    
    # Получить списки закрытых маршрутов
    closed_edges = closure.get_closed_edges()
    closed_nodes = closure.get_closed_nodes()
    print(f"✓ Всего закрытых маршрутов: {len(closed_edges)}")
    print(f"✓ Всего закрытых узлов: {len(closed_nodes)}")

def test_api_building_data():
    """Тест загрузки данных здания из API"""
    print("\n🏢 Тест данных здания:")
    
    init_api_client()
    api = get_api_client()
    
    # Получить здания
    buildings = api.get_buildings()
    print(f"✓ Загружено зданий: {len(buildings)}")
    
    building = buildings[0]
    print(f"✓ Здание: {building.name}")
    print(f"  - Адрес: {building.address}")
    print(f"  - Этажей: {building.floors}")
    print(f"  - Узлов: {len(building.nodes)}")
    
    # Проверить узлы по этажам
    for floor in range(1, building.floors + 1):
        floor_nodes = [n for n in building.nodes if n.floor == floor]
        print(f"  - Этаж {floor}: {len(floor_nodes)} узлов")

def test_graph_building():
    """Тест построения графа"""
    print("\n📊 Тест построения графа:")
    
    builder = GraphBuilder()
    edges = builder.build_edges_from_nodes(DEMO_NODES_CSV)
    print(f"✓ Построено {len(edges)} рёбер графа")
    
    # Проверить связи между этажами
    floor1_edges = [e for e in edges if e.floor_change == 1]
    floor_change_edges = [e for e in edges if e.floor_change > 1]
    
    print(f"✓ Рёбра на одном этаже: {len(floor1_edges)}")
    print(f"✓ Рёбра между этажами (со штрафом): {len(floor_change_edges)}")

def main():
    """Основная функция тестирования"""
    print("=" * 60)
    print("🧪 ТЕСТИРОВАНИЕ PHASE 5 EXTENDED")
    print("=" * 60)
    
    try:
        test_csv_loading()
        test_authentication()
        test_qr_system()
        test_route_closures()
        test_api_building_data()
        test_graph_building()
        
        print("\n" + "=" * 60)
        print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
