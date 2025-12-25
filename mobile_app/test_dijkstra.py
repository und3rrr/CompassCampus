#!/usr/bin/env python3
"""
Тест алгоритма Dijkstra для поиска кратчайшего пути
"""
import logging
from services.graph_builder import GraphBuilder, DEMO_NODES_CSV

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_dijkstra():
    """Тестируем поиск пути между двумя узлами"""
    
    # Создаём граф из демо-узлов
    edges = GraphBuilder.build_edges_from_nodes(DEMO_NODES_CSV)
    logger.info(f"Built {len(edges)} edges")
    
    # Создаём словарь узлов
    nodes_dict = {str(node['Id']): node for node in DEMO_NODES_CSV}
    
    # Тест 1: Поиск пути от узла 1 к узлу 5
    start_id = "29"
    end_id = "54"
    
    if start_id in nodes_dict and end_id in nodes_dict:
        result = GraphBuilder.find_shortest_path(start_id, end_id, edges, nodes_dict)
        if result:
            path, distance = result
            logger.info(f"Path from {start_id} to {end_id}:")
            logger.info(f"  Distance: {distance:.2f}")
            logger.info(f"  Path length: {len(path)} nodes")
            logger.info(f"  Path: {' -> '.join(path)}")
        else:
            logger.error(f"No path found between {start_id} and {end_id}")
    else:
        logger.error(f"Node {start_id} or {end_id} not found")
    
    # Тест 2: Путь к самому себе
    result = GraphBuilder.find_shortest_path("1", "1", edges, nodes_dict)
    if result:
        path, distance = result
        logger.info(f"Path to itself: {path}, distance: {distance}")
    
    logger.info("Test completed!")

if __name__ == '__main__':
    test_dijkstra()
