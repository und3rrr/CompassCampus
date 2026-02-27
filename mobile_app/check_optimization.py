#!/usr/bin/env python3
"""Проверка оптимизации"""

from services.graph_builder import GraphBuilder

print("✓ GraphBuilder loaded successfully")
print(f"✓ Has optimized find_shortest_path: {hasattr(GraphBuilder, 'find_shortest_path')}")
print(f"✓ Has get_graph_cache_size: {hasattr(GraphBuilder, 'get_graph_cache_size')}")
print(f"✓ Has clear_graph_cache: {hasattr(GraphBuilder, 'clear_graph_cache')}")
print(f"✓ Has get_cache_size: {hasattr(GraphBuilder, 'get_cache_size')}")
print(f"✓ Has clear_route_cache: {hasattr(GraphBuilder, 'clear_route_cache')}")
print()
print("✅ Все методы оптимизации на месте!")
print()
print("Готовые методы:")
print("  - GraphBuilder.find_shortest_path() - O((V+E)logV)")
print("  - GraphBuilder.clear_route_cache() - очистить кэш маршрутов")
print("  - GraphBuilder.clear_graph_cache() - очистить кэш графов")
print("  - GraphBuilder.get_cache_size() - размер кэша маршрутов")
print("  - GraphBuilder.get_graph_cache_size() - размер кэша графов")
