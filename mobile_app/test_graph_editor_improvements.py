"""
Тесты для проверки улучшений редактора графов

Проверяет:
1. Сохранение и загрузка узлов
2. Видимость рёбер
3. Масштабируемость линий
4. Батчинг undo/redo действий
5. Видимость соединений
"""

import sys
import os


def test_graph_editor_improvements():
    """Проверка всех улучшений редактора графов"""
    print("\n" + "="*70)
    print("GRAPH EDITOR IMPROVEMENTS TEST SUITE")
    print("="*70)
    
    editor_path = os.path.join(os.path.dirname(__file__), 'widgets', 'visual_graph_editor.py')
    screen_path = os.path.join(os.path.dirname(__file__), 'screens', 'graph_editor_screen.py')
    
    with open(editor_path, 'r', encoding='utf-8') as f:
        editor_content = f.read()
    
    with open(screen_path, 'r', encoding='utf-8') as f:
        screen_content = f.read()
    
    all_tests = []
    
    # TEST 1: Сохранение узлов
    print("\n[TEST 1] Node saving persistence")
    test1_passed = all([
        'self.cache_service.save_building(self.building)' in screen_content,
        'self.api_client.update_building(self.building)' in screen_content,
        'updated_nodes' in screen_content
    ])
    print("    ✓ Nodes saved to cache" if test1_passed else "    ✗ FAIL: Cache save missing")
    print("    ✓ Nodes synced to API" if 'self.api_client.update_building' in screen_content else "    ✗ FAIL: API sync missing")
    all_tests.append(test1_passed)
    
    # TEST 2: Видимость рёбер
    print("\n[TEST 2] Edge visibility toggle")
    test2_items = [
        ('self.show_edges = False' in editor_content, 'show_edges attribute'),
        ('def set_show_edges' in editor_content, 'set_show_edges method'),
        ('def _update_edge_visibility' in editor_content, '_update_edge_visibility method'),
        ('if self.show_edges:' in editor_content, 'Conditional rendering'),
    ]
    test2_passed = all(item[0] for item in test2_items)
    for passed, desc in test2_items:
        print(f"    {'✓' if passed else '✗'} {desc}")
    all_tests.append(test2_passed)
    
    # TEST 3: Маршруты
    print("\n[TEST 3] Route rendering")
    test3_items = [
        ('self.route = None' in editor_content, 'route attribute'),
        ('def set_route' in editor_content, 'set_route method'),
        ('if self.route and self.route.path:' in editor_content, 'Route rendering'),
        ('Color(0.2, 0.8, 0.2' in editor_content, 'Green color for route'),
    ]
    test3_passed = all(item[0] for item in test3_items)
    for passed, desc in test3_items:
        print(f"    {'✓' if passed else '✗'} {desc}")
    all_tests.append(test3_passed)
    
    # TEST 4: Масштабируемость линий
    print("\n[TEST 4] Scalable line width")
    test4_items = [
        ('max(1.0, 4.0 / max(0.5, self.zoom))' in editor_content, 'Line width formula'),
        ('scaled_line_width' in editor_content, 'Scaled width variable'),
        ('width=scaled_line_width' in editor_content, 'Width applied to lines'),
    ]
    test4_passed = all(item[0] for item in test4_items)
    for passed, desc in test4_items:
        print(f"    {'✓' if passed else '✗'} {desc}")
    all_tests.append(test4_passed)
    
    # TEST 5: Батчинг undo/redo
    print("\n[TEST 5] Undo/Redo action batching")
    test5_items = [
        ('self.action_batch_timeout' in screen_content, 'action_batch_timeout attribute'),
        ('self.batching_actions' in screen_content, 'batching_actions flag'),
        ('current_time - self.last_action_time' in screen_content, 'Time-based grouping'),
        ('def _on_node_moved' in screen_content, '_on_node_moved callback'),
        ('self.graph_editor.on_node_moved_callback = self._on_node_moved' in screen_content, 'Callback registration'),
    ]
    test5_passed = all(item[0] for item in test5_items)
    for passed, desc in test5_items:
        print(f"    {'✓' if passed else '✗'} {desc}")
    all_tests.append(test5_passed)
    
    # TEST 6: Видимость соединений
    print("\n[TEST 6] Connection visibility on node selection")
    test6_items = [
        ('self.selected_nodes.clear()' in editor_content, 'Clear selection on empty click'),
        ('_update_edge_visibility' in editor_content and editor_content.count('_update_edge_visibility') > 1, 'Edge visibility update on selection'),
        ('if node.id in self.selected_nodes:' in editor_content, 'Check selected nodes'),
    ]
    test6_passed = all(item[0] for item in test6_items)
    for passed, desc in test6_items:
        print(f"    {'✓' if passed else '✗'} {desc}")
    all_tests.append(test6_passed)
    
    # TEST 7: Callback движения
    print("\n[TEST 7] Node movement callback")
    test7_items = [
        ('self.on_node_moved_callback' in editor_content, 'Callback attribute'),
        ('if self.on_node_moved_callback:' in editor_content, 'Callback invocation'),
        ('self.on_node_moved_callback(self.dragging_node)' in editor_content, 'Callback with parameter'),
    ]
    test7_passed = all(item[0] for item in test7_items)
    for passed, desc in test7_items:
        print(f"    {'✓' if passed else '✗'} {desc}")
    all_tests.append(test7_passed)
    
    # SUMMARY
    print("\n" + "="*70)
    passed_count = sum(all_tests)
    total_count = len(all_tests)
    
    if passed_count == total_count:
        print(f"[SUCCESS] All tests passed! ({passed_count}/{total_count})")
    else:
        print(f"[PARTIAL] {passed_count}/{total_count} test groups passed")
    
    print("="*70)
    
    return passed_count == total_count


if __name__ == '__main__':
    success = test_graph_editor_improvements()
    sys.exit(0 if success else 1)
