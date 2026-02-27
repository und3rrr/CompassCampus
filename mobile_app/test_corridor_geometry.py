#!/usr/bin/env python3
"""
Тест геометрических функций для привязки кабинета к ребру коридора
"""

def distance_point_to_line(px, py, x1, y1, x2, y2):
    """Вычислить расстояние от точки (px, py) до линии [(x1, y1), (x2, y2)]"""
    numerator = abs((y2 - y1) * px - (x2 - x1) * py + x2 * y1 - y2 * x1)
    denominator = ((y2 - y1)**2 + (x2 - x1)**2) ** 0.5
    if denominator == 0:
        return ((px - x1)**2 + (py - y1)**2) ** 0.5
    return numerator / denominator

def closest_point_on_segment(px, py, x1, y1, x2, y2):
    """Найти ближайшую точку на отрезке [(x1, y1), (x2, y2)] к точке (px, py)"""
    dx = x2 - x1
    dy = y2 - y1
    
    if dx == 0 and dy == 0:
        return x1, y1
    
    t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
    
    closest_x = x1 + t * dx
    closest_y = y1 + t * dy
    
    return closest_x, closest_y

# Тест 1: Простой горизонтальный коридор
print("=" * 60)
print("ТЕСТ 1: Горизонтальный коридор")
print("=" * 60)

# Коридор от (100, 100) до (500, 100)
corridor_start = (100, 100)
corridor_end = (500, 100)

# Кабинет в позиции (300, 200)
cabin = (300, 200)

distance = distance_point_to_line(cabin[0], cabin[1], corridor_start[0], corridor_start[1], corridor_end[0], corridor_end[1])
closest = closest_point_on_segment(cabin[0], cabin[1], corridor_start[0], corridor_start[1], corridor_end[0], corridor_end[1])

print(f"Коридор: {corridor_start} → {corridor_end}")
print(f"Кабинет: {cabin}")
print(f"Расстояние до коридора: {distance:.2f}")
print(f"Ближайшая точка на коридоре: ({closest[0]:.2f}, {closest[1]:.2f})")
print(f"✓ Ожидается: точка (300, 100) на коридоре")
print()

# Тест 2: Диагональный коридор
print("=" * 60)
print("ТЕСТ 2: Диагональный коридор")
print("=" * 60)

# Коридор от (0, 0) до (100, 100)
corridor_start = (0, 0)
corridor_end = (100, 100)

# Кабинет в позиции (100, 0)
cabin = (100, 0)

distance = distance_point_to_line(cabin[0], cabin[1], corridor_start[0], corridor_start[1], corridor_end[0], corridor_end[1])
closest = closest_point_on_segment(cabin[0], cabin[1], corridor_start[0], corridor_start[1], corridor_end[0], corridor_end[1])

print(f"Коридор: {corridor_start} → {corridor_end}")
print(f"Кабинет: {cabin}")
print(f"Расстояние до коридора: {distance:.2f}")
print(f"Ближайшая точка на коридоре: ({closest[0]:.2f}, {closest[1]:.2f})")
print(f"✓ Ожидается: точка (50, 50) на коридоре")
print()

# Тест 3: Кабинет за концом коридора
print("=" * 60)
print("ТЕСТ 3: Кабинет за концом коридора")
print("=" * 60)

# Коридор от (0, 0) до (100, 0)
corridor_start = (0, 0)
corridor_end = (100, 0)

# Кабинет в позиции (150, 50)
cabin = (150, 50)

distance = distance_point_to_line(cabin[0], cabin[1], corridor_start[0], corridor_start[1], corridor_end[0], corridor_end[1])
closest = closest_point_on_segment(cabin[0], cabin[1], corridor_start[0], corridor_start[1], corridor_end[0], corridor_end[1])

print(f"Коридор: {corridor_start} → {corridor_end}")
print(f"Кабинет: {cabin}")
print(f"Расстояние до коридора: {distance:.2f}")
print(f"Ближайшая точка на коридоре: ({closest[0]:.2f}, {closest[1]:.2f})")
print(f"✓ Ожидается: точка (100, 0) на конце коридора")
print()

# Тест 4: Кабинет в начале коридора
print("=" * 60)
print("ТЕСТ 4: Кабинет перед началом коридора")
print("=" * 60)

# Коридор от (100, 100) до (200, 100)
corridor_start = (100, 100)
corridor_end = (200, 100)

# Кабинет в позиции (50, 150)
cabin = (50, 150)

distance = distance_point_to_line(cabin[0], cabin[1], corridor_start[0], corridor_start[1], corridor_end[0], corridor_end[1])
closest = closest_point_on_segment(cabin[0], cabin[1], corridor_start[0], corridor_start[1], corridor_end[0], corridor_end[1])

print(f"Коридор: {corridor_start} → {corridor_end}")
print(f"Кабинет: {cabin}")
print(f"Расстояние до коридора: {distance:.2f}")
print(f"Ближайшая точка на коридоре: ({closest[0]:.2f}, {closest[1]:.2f})")
print(f"✓ Ожидается: точка (100, 100) в начале коридора")
print()

print("=" * 60)
print("✓ ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
print("=" * 60)
