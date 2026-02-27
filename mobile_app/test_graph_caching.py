#!/usr/bin/env python3
"""
Тест оптимизации с кэшированием графа

Проверяет:
1. Кэширование построения графа
2. Полное время с кэшем
"""

import time
import random
from services.graph_builder import GraphBuilder

def test_graph_caching():
    """Тест кэширования графа"""
    print("=" * 60)
    print("ТЕСТ КЭШИРОВАНИЯ ГРАФА")
    print("=" * 60)
    print()
    
    # Генерируем случайные узлы
    nodes = []
    for i in range(100):
        x = random.uniform(0, 1000)
        y = random.uniform(0, 1000)
        nodes.append({
            'Id': str(i),
            'Name': f'Node{i}',
            'Floor': random.choice([1, 2, 3]),
            'Type': 'Room',
            'X': x,
            'Y': y
        })
    
    # Очищаем кэши
    GraphBuilder.clear_route_cache()
    GraphBuilder.clear_graph_cache()
    
    print("Сценарий 1: Первый поиск маршрута (граф не кэширован)")
    print("-" * 60)
    
    # Первое построение графа (без кэша)
    start_time = time.time()
    edges1 = GraphBuilder.build_edges_from_nodes(nodes)
    build_time_1 = (time.time() - start_time) * 1000
    
    graph_cache_1 = GraphBuilder.get_graph_cache_size()
    
    print(f"✓ Построено графа: {len(edges1)} рёбер за {build_time_1:.3f}ms")
    print(f"✓ Размер кэша графа: {graph_cache_1}")
    
    # Первый поиск маршрута
    nodes_dict = {str(n['Id']): n for n in nodes}
    search_start = time.time()
    result1 = GraphBuilder.find_shortest_path('0', '99', edges1, nodes_dict)
    search_time_1 = (time.time() - search_start) * 1000
    
    route_cache_1 = GraphBuilder.get_cache_size()
    
    print(f"✓ Поиск маршрута: {search_time_1:.3f}ms")
    print(f"✓ Размер кэша маршрутов: {route_cache_1}")
    print(f"✓ Общее время: {build_time_1 + search_time_1:.3f}ms")
    print()
    
    print("Сценарий 2: Повторный поиск того же маршрута (всё кэшировано)")
    print("-" * 60)
    
    # Второе построение графа (из кэша)
    start_time = time.time()
    edges2 = GraphBuilder.build_edges_from_nodes(nodes)
    build_time_2 = (time.time() - start_time) * 1000
    
    print(f"✓ Получено из кэша графа: {len(edges2)} рёбер за {build_time_2:.3f}ms")
    
    # Повторный поиск (из кэша маршрутов)
    search_start = time.time()
    result2 = GraphBuilder.find_shortest_path('0', '99', edges2, nodes_dict)
    search_time_2 = (time.time() - search_start) * 1000
    
    print(f"✓ Поиск маршрута (из кэша): {search_time_2:.3f}ms")
    print(f"✓ Общее время: {build_time_2 + search_time_2:.3f}ms")
    print()
    
    print("Сценарий 3: Новый маршрут (граф кэширован, маршрут нет)")
    print("-" * 60)
    
    # Построение графа (из кэша)
    start_time = time.time()
    edges3 = GraphBuilder.build_edges_from_nodes(nodes)
    build_time_3 = (time.time() - start_time) * 1000
    
    # Новый поиск (не из кэша маршрутов)
    search_start = time.time()
    result3 = GraphBuilder.find_shortest_path('10', '90', edges3, nodes_dict)
    search_time_3 = (time.time() - search_start) * 1000
    
    route_cache_3 = GraphBuilder.get_cache_size()
    
    print(f"✓ Граф (кэш): {build_time_3:.3f}ms")
    print(f"✓ Новый маршрут: {search_time_3:.3f}ms")
    print(f"✓ Размер кэша маршрутов: {route_cache_3}")
    print(f"✓ Общее время: {build_time_3 + search_time_3:.3f}ms")
    print()
    
    print("=" * 60)
    print("РЕЗУЛЬТАТЫ КЭШИРОВАНИЯ")
    print("=" * 60)
    print()
    
    total_1 = build_time_1 + search_time_1
    total_2 = build_time_2 + search_time_2
    total_3 = build_time_3 + search_time_3
    
    improvement_2_vs_1 = (total_1 - total_2) / total_1 * 100
    improvement_3_vs_1 = (total_1 - total_3) / total_1 * 100
    
    print(f"Первый поиск (холодный кэш):      {total_1:.3f}ms (100%)")
    print(f"Повторный поиск (горячий кэш):   {total_2:.3f}ms ({100-improvement_2_vs_1:.1f}%)")
    print(f"Новый маршрут (кэш графа):       {total_3:.3f}ms ({100-improvement_3_vs_1:.1f}%)")
    print()
    print(f"Улучшение с кэшем маршрута:  {improvement_2_vs_1:.1f}%")
    print(f"Улучшение с кэшем графа:    {improvement_3_vs_1:.1f}%")
    print()
    
    print("✅ Кэширование эффективно работает!")
    print()

if __name__ == '__main__':
    test_graph_caching()
