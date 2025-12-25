"""
Построитель графа из данных узлов
"""
import math
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class GraphEdge:
    """Ребро графа"""
    from_id: str
    to_id: str
    weight: float  # расстояние


class GraphBuilder:
    """Построитель графа из координат узлов"""

    DISTANCE_THRESHOLD = 150  # Максимальное расстояние для автосвязи
    FLOOR_CHANGE_PENALTY = 2.0  # Штраф за смену этажа

    @staticmethod
    def calculate_distance(x1: float, y1: float, x2: float, y2: float) -> float:
        """Рассчитать евклидово расстояние между двумя точками"""
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

    @staticmethod
    def build_edges_from_nodes(nodes: List[dict]) -> List[GraphEdge]:
        """
        Построить рёбра на основе близости узлов
        
        Args:
            nodes: Список узлов с координатами
            
        Returns:
            Список рёбер графа
        """
        edges = []
        edges_set = set()  # Для избежания дубликатов

        # Группировать узлы по этажам
        nodes_by_floor = {}
        for node in nodes:
            floor = node.get('Floor', 1)
            if floor not in nodes_by_floor:
                nodes_by_floor[floor] = []
            nodes_by_floor[floor].append(node)

        # Создавать рёбра в пределах этажа (по близости)
        for floor, floor_nodes in nodes_by_floor.items():
            for i, node1 in enumerate(floor_nodes):
                for node2 in floor_nodes[i + 1:]:
                    distance = GraphBuilder.calculate_distance(
                        node1['X'], node1['Y'],
                        node2['X'], node2['Y']
                    )

                    # Если узлы близко друг к другу, создать ребро
                    if distance <= GraphBuilder.DISTANCE_THRESHOLD:
                        edge_key = tuple(sorted([
                            str(node1['Id']),
                            str(node2['Id'])
                        ]))

                        if edge_key not in edges_set:
                            edges_set.add(edge_key)
                            # Двусторонняя связь
                            edges.append(GraphEdge(
                                from_id=str(node1['Id']),
                                to_id=str(node2['Id']),
                                weight=distance
                            ))
                            edges.append(GraphEdge(
                                from_id=str(node2['Id']),
                                to_id=str(node1['Id']),
                                weight=distance
                            ))

        # Соединять лестницы и лифты между этажами
        stairs_by_location = {}
        elevators_by_location = {}

        for node in nodes:
            node_type = node.get('Type', '').lower()
            x, y = node['X'], node['Y']
            location_key = (round(x / 50) * 50, round(y / 50) * 50)  # Группировать по зонам

            if 'staircase' in node_type or 'staircase' in node.get('Name', '').lower():
                if location_key not in stairs_by_location:
                    stairs_by_location[location_key] = []
                stairs_by_location[location_key].append(node)

            if 'elevator' in node_type or 'лифт' in node.get('Name', '').lower():
                if location_key not in elevators_by_location:
                    elevators_by_location[location_key] = []
                elevators_by_location[location_key].append(node)

        # Соединять лестницы на разных этажах
        for location, stairs_list in stairs_by_location.items():
            for i, stair1 in enumerate(stairs_list):
                for stair2 in stairs_list[i + 1:]:
                    edge_key = tuple(sorted([
                        str(stair1['Id']),
                        str(stair2['Id'])
                    ]))

                    if edge_key not in edges_set:
                        edges_set.add(edge_key)
                        # Штраф за смену этажа
                        floor_distance = abs(stair1['Floor'] - stair2['Floor']) * 50
                        weight = floor_distance * GraphBuilder.FLOOR_CHANGE_PENALTY

                        edges.append(GraphEdge(
                            from_id=str(stair1['Id']),
                            to_id=str(stair2['Id']),
                            weight=weight
                        ))
                        edges.append(GraphEdge(
                            from_id=str(stair2['Id']),
                            to_id=str(stair1['Id']),
                            weight=weight
                        ))

        # Соединять лифты на разных этажах (аналогично лестницам)
        for location, elevators_list in elevators_by_location.items():
            for i, elev1 in enumerate(elevators_list):
                for elev2 in elevators_list[i + 1:]:
                    edge_key = tuple(sorted([
                        str(elev1['Id']),
                        str(elev2['Id'])
                    ]))

                    if edge_key not in edges_set:
                        edges_set.add(edge_key)
                        floor_distance = abs(elev1['Floor'] - elev2['Floor']) * 30
                        weight = floor_distance * GraphBuilder.FLOOR_CHANGE_PENALTY

                        edges.append(GraphEdge(
                            from_id=str(elev1['Id']),
                            to_id=str(elev2['Id']),
                            weight=weight
                        ))
                        edges.append(GraphEdge(
                            from_id=str(elev2['Id']),
                            to_id=str(elev1['Id']),
                            weight=weight
                        ))

        logger.info(f"Built {len(edges)} edges from {len(nodes)} nodes")
        return edges

    @staticmethod
    def edges_to_adjacency_list(edges: List[GraphEdge]) -> Dict[str, List[Tuple[str, float]]]:
        """
        Конвертировать список рёбер в список смежности
        
        Args:
            edges: Список рёбер
            
        Returns:
            Словарь {from_id: [(to_id, weight), ...]}
        """
        adjacency = {}
        for edge in edges:
            if edge.from_id not in adjacency:
                adjacency[edge.from_id] = []
            adjacency[edge.from_id].append((edge.to_id, edge.weight))

        return adjacency

    @staticmethod
    def find_shortest_path(start_id: str, end_id: str, edges: List[GraphEdge], 
                          nodes_dict: Dict[str, dict]) -> Optional[Tuple[List[str], float]]:
        """
        Найти кратчайший путь между двумя узлами используя алгоритм Dijkstra
        
        Args:
            start_id: ID стартового узла
            end_id: ID конечного узла
            edges: Список рёбер графа
            nodes_dict: Словарь узлов {id: node_dict}
            
        Returns:
            Кортеж (путь как список ID, общее расстояние) или None если пути нет
        """
        if start_id == end_id:
            return [start_id], 0.0
        
        adjacency = GraphBuilder.edges_to_adjacency_list(edges)
        
        # Инициализация расстояний
        distances = {node_id: float('inf') for node_id in nodes_dict.keys()}
        distances[start_id] = 0.0
        previous = {node_id: None for node_id in nodes_dict.keys()}
        unvisited = set(nodes_dict.keys())
        
        while unvisited:
            # Найти непосещённый узел с минимальным расстоянием
            current = min(unvisited, key=lambda x: distances[x], default=None)
            
            if current is None or distances[current] == float('inf'):
                break  # Нет пути до конца
            
            if current == end_id:
                # Восстановить путь
                path = []
                node = end_id
                while node is not None:
                    path.append(node)
                    node = previous[node]
                return list(reversed(path)), distances[end_id]
            
            unvisited.remove(current)
            
            # Обновить расстояния соседей
            if current in adjacency:
                for neighbor, weight in adjacency[current]:
                    if neighbor in unvisited:
                        new_distance = distances[current] + weight
                        if new_distance < distances[neighbor]:
                            distances[neighbor] = new_distance
                            previous[neighbor] = current
        
        return None  # Нет пути


# Статические данные из cds.csv для демонстрации
DEMO_NODES_CSV = [
    {'Id': 15, 'Name': 'Лестница', 'Floor': 1, 'Type': 'Staircase', 'X': 1135, 'Y': 553},
    {'Id': 19, 'Name': 'Лестница', 'Floor': 1, 'Type': 'Staircase', 'X': 1656, 'Y': 833},
    {'Id': 20, 'Name': 'Лифт', 'Floor': 1, 'Type': 'Elevator', 'X': 1640, 'Y': 906},
    {'Id': 22, 'Name': 'Спортзал', 'Floor': 1, 'Type': 'Room', 'X': 809, 'Y': 112},
    {'Id': 24, 'Name': 'холл', 'Floor': 1, 'Type': 'Room', 'X': 985, 'Y': 698},
    {'Id': 26, 'Name': 'Столовая', 'Floor': 1, 'Type': 'Room', 'X': 248, 'Y': 610},
    {'Id': 28, 'Name': 'гардероб', 'Floor': 1, 'Type': 'Room', 'X': 771, 'Y': 841},
    {'Id': 29, 'Name': 'гардероб', 'Floor': 1, 'Type': 'Room', 'X': 1165, 'Y': 840},
    {'Id': 30, 'Name': 'коридор', 'Floor': 1, 'Type': 'Room', 'X': 385, 'Y': 837},
    {'Id': 31, 'Name': '156', 'Floor': 1, 'Type': 'Room', 'X': 1246, 'Y': 749},
    {'Id': 32, 'Name': '153', 'Floor': 1, 'Type': 'Room', 'X': 1289, 'Y': 764},
    {'Id': 33, 'Name': '150', 'Floor': 1, 'Type': 'Room', 'X': 1345, 'Y': 790},
    {'Id': 35, 'Name': '101', 'Floor': 1, 'Type': 'Room', 'X': 1369, 'Y': 689},
    {'Id': 36, 'Name': '102', 'Floor': 1, 'Type': 'Room', 'X': 1451, 'Y': 733},
    {'Id': 37, 'Name': '103', 'Floor': 1, 'Type': 'Room', 'X': 1512, 'Y': 756},
    {'Id': 38, 'Name': '106', 'Floor': 1, 'Type': 'Room', 'X': 1604, 'Y': 721},
    {'Id': 39, 'Name': '107', 'Floor': 1, 'Type': 'Room', 'X': 1628, 'Y': 645},
    {'Id': 41, 'Name': '109', 'Floor': 1, 'Type': 'Room', 'X': 1706, 'Y': 489},
    {'Id': 42, 'Name': '110', 'Floor': 1, 'Type': 'Room', 'X': 1724, 'Y': 445},
    {'Id': 45, 'Name': '124', 'Floor': 1, 'Type': 'Room', 'X': 1827, 'Y': 469},
    {'Id': 48, 'Name': '129', 'Floor': 1, 'Type': 'Room', 'X': 1734, 'Y': 692},
    {'Id': 50, 'Name': '133', 'Floor': 1, 'Type': 'Room', 'X': 1688, 'Y': 793},
    {'Id': 51, 'Name': 'коридор', 'Floor': 1, 'Type': 'Room', 'X': 1273, 'Y': 695},
    {'Id': 52, 'Name': 'коридор', 'Floor': 1, 'Type': 'Room', 'X': 1384, 'Y': 743},
    {'Id': 54, 'Name': 'коридор', 'Floor': 1, 'Type': 'Room', 'X': 1671, 'Y': 675},
    {'Id': 55, 'Name': 'коридор', 'Floor': 1, 'Type': 'Room', 'X': 1735, 'Y': 539},
    {'Id': 56, 'Name': 'коридор', 'Floor': 1, 'Type': 'Room', 'X': 1815, 'Y': 294},
    {'Id': 57, 'Name': 'B5', 'Floor': 1, 'Type': 'Room', 'X': 640, 'Y': 1010},
    {'Id': 58, 'Name': 'B4', 'Floor': 1, 'Type': 'Room', 'X': 491, 'Y': 1076},
    {'Id': 59, 'Name': 'B3', 'Floor': 1, 'Type': 'Room', 'X': 353, 'Y': 1107},
    {'Id': 60, 'Name': 'B2', 'Floor': 1, 'Type': 'Room', 'X': 511, 'Y': 1269},
    {'Id': 61, 'Name': 'B1', 'Floor': 1, 'Type': 'Room', 'X': 698, 'Y': 1206},
    {'Id': 62, 'Name': 'Д1', 'Floor': 1, 'Type': 'Room', 'X': 1333, 'Y': 1038},
    {'Id': 63, 'Name': 'Д5', 'Floor': 1, 'Type': 'Room', 'X': 1253, 'Y': 1203},
    {'Id': 65, 'Name': 'Д4', 'Floor': 1, 'Type': 'Room', 'X': 1427, 'Y': 1278},
    {'Id': 66, 'Name': 'Д3', 'Floor': 1, 'Type': 'Room', 'X': 1589, 'Y': 1127},
    {'Id': 67, 'Name': 'Вход', 'Floor': 1, 'Type': 'Room', 'X': 989, 'Y': 1080},
    {'Id': 68, 'Name': 'холл', 'Floor': 1, 'Type': 'Room', 'X': 1203, 'Y': 1012},
    {'Id': 69, 'Name': 'холл', 'Floor': 1, 'Type': 'Room', 'X': 772, 'Y': 1011},
    {'Id': 70, 'Name': 'лобби', 'Floor': 1, 'Type': 'Room', 'X': 585, 'Y': 1145},
    {'Id': 71, 'Name': 'лобби', 'Floor': 1, 'Type': 'Room', 'X': 405, 'Y': 1194},
    {'Id': 72, 'Name': 'лобби', 'Floor': 1, 'Type': 'Room', 'X': 1359, 'Y': 1128},
    {'Id': 73, 'Name': 'лобби', 'Floor': 1, 'Type': 'Room', 'X': 1555, 'Y': 1217},
    {'Id': 17, 'Name': 'Лифт', 'Floor': 1, 'Type': 'Elevator', 'X': 1022, 'Y': 556},
    {'Id': 16, 'Name': 'Лифт', 'Floor': 1, 'Type': 'Elevator', 'X': 941, 'Y': 549},
    {'Id': 23, 'Name': 'Библиотека', 'Floor': 1, 'Type': 'Room', 'X': 939, 'Y': 426},
    {'Id': 53, 'Name': 'коридор', 'Floor': 1, 'Type': 'Room', 'X': 1593, 'Y': 854},
    {'Id': 49, 'Name': '132', 'Floor': 1, 'Type': 'Room', 'X': 1697, 'Y': 747},
    {'Id': 64, 'Name': 'Д2', 'Floor': 1, 'Type': 'Room', 'X': 1467, 'Y': 1091},
    {'Id': 18, 'Name': 'Лестница', 'Floor': 1, 'Type': 'Staircase', 'X': 292, 'Y': 843},
    {'Id': 21, 'Name': 'Лифт', 'Floor': 1, 'Type': 'Elevator', 'X': 317, 'Y': 913},
    {'Id': 74, 'Name': 'коридор', 'Floor': 1, 'Type': 'Room', 'X': 688, 'Y': 699},
    {'Id': 27, 'Name': 'корридор', 'Floor': 1, 'Type': 'Room', 'X': 562, 'Y': 750},
    {'Id': 34, 'Name': '147', 'Floor': 1, 'Type': 'Room', 'X': 1426, 'Y': 828},
    {'Id': 43, 'Name': '120', 'Floor': 1, 'Type': 'Room', 'X': 1895, 'Y': 310},
    {'Id': 40, 'Name': '108', 'Floor': 1, 'Type': 'Room', 'X': 1658, 'Y': 586},
    {'Id': 46, 'Name': '126', 'Floor': 1, 'Type': 'Room', 'X': 1797, 'Y': 532},
    {'Id': 44, 'Name': '123', 'Floor': 1, 'Type': 'Room', 'X': 1836, 'Y': 384},
    {'Id': 47, 'Name': '128', 'Floor': 1, 'Type': 'Room', 'X': 1745, 'Y': 606},
    {'Id': 75, 'Name': 'ксерокс', 'Floor': 1, 'Type': 'Room', 'X': 773, 'Y': 325},
    {'Id': 14, 'Name': 'Лестница', 'Floor': 1, 'Type': 'Staircase', 'X': 822, 'Y': 547},
    {'Id': 76, 'Name': 'Медпункт', 'Floor': 1, 'Type': 'Room', 'X': 582, 'Y': 812},
    {'Id': 77, 'Name': 'Диспетчер', 'Floor': 1, 'Type': 'Room', 'X': 676, 'Y': 775},
    # Этаж 2
    {'Id': 79, 'Name': '401', 'Floor': 2, 'Type': 'Room', 'X': 1209, 'Y': 1215},
    {'Id': 80, 'Name': '402', 'Floor': 2, 'Type': 'Room', 'X': 2136, 'Y': 1215},
    {'Id': 82, 'Name': '434', 'Floor': 2, 'Type': 'Room', 'X': 109, 'Y': 256},
    {'Id': 83, 'Name': '429', 'Floor': 2, 'Type': 'Room', 'X': 140, 'Y': 328},
    {'Id': 84, 'Name': '428', 'Floor': 2, 'Type': 'Room', 'X': 166, 'Y': 390},
    {'Id': 85, 'Name': '427', 'Floor': 2, 'Type': 'Room', 'X': 181, 'Y': 422},
    {'Id': 86, 'Name': 'коридор', 'Floor': 2, 'Type': 'Room', 'X': 226, 'Y': 389},
    {'Id': 87, 'Name': 'коридор', 'Floor': 2, 'Type': 'Room', 'X': 268, 'Y': 490},
    {'Id': 88, 'Name': 'коридор', 'Floor': 2, 'Type': 'Room', 'X': 365, 'Y': 706},
    {'Id': 89, 'Name': '423', 'Floor': 2, 'Type': 'Room', 'X': 216, 'Y': 502},
    {'Id': 90, 'Name': '421', 'Floor': 2, 'Type': 'Room', 'X': 241, 'Y': 568},
    {'Id': 91, 'Name': '420', 'Floor': 2, 'Type': 'Room', 'X': 278, 'Y': 619},
    {'Id': 92, 'Name': '425', 'Floor': 2, 'Type': 'Room', 'X': 196, 'Y': 453},
    {'Id': 93, 'Name': 'кордиор', 'Floor': 2, 'Type': 'Room', 'X': 182, 'Y': 243},
    {'Id': 81, 'Name': 'столовая', 'Floor': 2, 'Type': 'Room', 'X': 311, 'Y': 174},
    {'Id': 139, 'Name': 'Лестница', 'Floor': 2, 'Type': 'Staircase', 'X': 741, 'Y': 454},
    {'Id': 140, 'Name': 'Лестница', 'Floor': 2, 'Type': 'Staircase', 'X': 996, 'Y': 466},
    {'Id': 141, 'Name': 'Лифт', 'Floor': 2, 'Type': 'Elevator', 'X': 882, 'Y': 460},
    {'Id': 146, 'Name': 'Лестница', 'Floor': 2, 'Type': 'Staircase', 'X': 300, 'Y': 694},
    {'Id': 147, 'Name': 'Лифт', 'Floor': 2, 'Type': 'Elevator', 'X': 335, 'Y': 753},
    {'Id': 148, 'Name': 'Лестница', 'Floor': 2, 'Type': 'Staircase', 'X': 1453, 'Y': 686},
    {'Id': 149, 'Name': 'Лифт', 'Floor': 2, 'Type': 'Elevator', 'X': 1441, 'Y': 758},
]
