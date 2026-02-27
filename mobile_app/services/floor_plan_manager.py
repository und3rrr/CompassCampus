"""
Менеджер планов этажей из Sweet Home 3D (SVG)
Управляет загрузкой, кэшированием и отображением планов
"""
import os
from typing import Dict, Optional, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class FloorPlanManager:
    """Менеджер для управления коллекцией планов этажей в формате SVG/PNG"""

    def __init__(self, plans_folder: str = None):
        """
        Инициализировать менеджер планов этажей

        Args:
            plans_folder: Папка с файлами планов (SVG/PNG)
        """
        self.plans_folder = plans_folder or "assets/floor_plans"
        self.cached_plans: Dict[int, str] = {}  # floor_number -> file_path
        self.auto_detected_plans: Dict[int, str] = {}
        
        # Автоматически сканируем папку при инициализации
        self.auto_detected_plans = self.scan_folder()

    def scan_folder(self) -> Dict[int, str]:
        """
        Сканировать папку на наличие файлов PNG планов этажей
        Приоритет: PNG > SVG (PNG предпочтительнее)

        Returns:
            Словарь {floor_number: file_path}
        """
        if not os.path.exists(self.plans_folder):
            logger.warning(f"Plans folder not found: {self.plans_folder}")
            return {}

        detected = {}
        png_files = {}
        svg_files = {}

        try:
            # Первый проход - собираем PNG и SVG отдельно
            for filename in os.listdir(self.plans_folder):
                if filename.endswith('.png'):
                    file_path = os.path.join(self.plans_folder, filename)
                    floor_num = self._extract_floor_number(filename)
                    if floor_num not in png_files:
                        png_files[floor_num] = file_path
                elif filename.endswith('.svg'):
                    file_path = os.path.join(self.plans_folder, filename)
                    floor_num = self._extract_floor_number(filename)
                    if floor_num not in svg_files:
                        svg_files[floor_num] = file_path
                elif filename.endswith(('.jpg', '.jpeg')):
                    file_path = os.path.join(self.plans_folder, filename)
                    floor_num = self._extract_floor_number(filename)
                    if floor_num not in detected:
                        detected[floor_num] = file_path
            
            # PNG имеют приоритет
            for floor_num, file_path in png_files.items():
                detected[floor_num] = file_path
                logger.debug(f"Detected floor plan (PNG): {floor_num} -> {os.path.basename(file_path)}")
            
            # SVG используются если PNG не найдено (обратная совместимость)
            for floor_num, file_path in svg_files.items():
                if floor_num not in detected:
                    detected[floor_num] = file_path
                    logger.debug(f"Detected floor plan (SVG fallback): {floor_num} -> {os.path.basename(file_path)}")
                else:
                    logger.debug(f"Floor {floor_num} PNG found, skipping SVG")

            self.auto_detected_plans = detected
            logger.info(f"Found {len(detected)} floor plans in {self.plans_folder} (PNG mode)")

        except Exception as e:
            logger.error(f"Error scanning plans folder: {e}")

        return detected

    def get_plan_file(self, floor_number: int) -> Optional[str]:
        """
        Получить путь к файлу плана для определённого этажа

        Args:
            floor_number: Номер этажа

        Returns:
            Путь к файлу или None если не найден
        """
        # Проверяем кэш
        if floor_number in self.cached_plans:
            return self.cached_plans[floor_number]

        # Проверяем автоопределённые планы
        if floor_number in self.auto_detected_plans:
            file_path = self.auto_detected_plans[floor_number]
            self.cached_plans[floor_number] = file_path
            return file_path

        return None

    def register_plan(self, floor_number: int, file_path: str) -> bool:
        """
        Зарегистрировать план этажа вручную

        Args:
            floor_number: Номер этажа
            file_path: Полный путь к файлу плана

        Returns:
            True если успешно, False если файл не существует
        """
        if not os.path.exists(file_path):
            logger.error(f"Plan file not found: {file_path}")
            return False

        self.cached_plans[floor_number] = file_path
        logger.info(f"Registered plan for floor {floor_number}: {file_path}")
        return True

    def has_plan(self, floor_number: int) -> bool:
        """Проверить наличие плана для этажа"""
        self.scan_folder()  # Обновляем при каждой проверке
        return floor_number in self.auto_detected_plans or floor_number in self.cached_plans

    def get_available_floors(self) -> List[int]:
        """Получить список номеров этажей с доступными планами"""
        self.scan_folder()
        floors = sorted(
            set(list(self.cached_plans.keys()) + list(self.auto_detected_plans.keys()))
        )
        return floors

    @staticmethod
    def _extract_floor_number(filename: str) -> int:
        """
        Извлечь номер этажа из имени файла

        Поддерживает паттерны:
        - floor1.svg, floor_1.svg, floor-1.svg
        - etaj1.svg, этаж1.svg, этаж-1.svg
        - level1.svg, level-1.svg
        - 1floor.svg, 1этаж.svg, -1floor.svg
        """
        filename_lower = filename.lower()
        filename_no_ext = Path(filename).stem.lower()

        patterns = [
            ('floor', 'этаж', 'level', 'etaj'),  # prefix patterns
        ]

        # Ищем число в имени файла
        for pattern in patterns[0]:
            if pattern in filename_no_ext:
                idx = filename_no_ext.find(pattern)
                after = filename_no_ext[idx + len(pattern):]

                # Ищем первое число после паттерна (может быть отрицательное)
                for i, char in enumerate(after):
                    is_minus = char == '-'
                    if char.isdigit() or is_minus:
                        # Собираем все цифры подряд, включая минус
                        number_str = char
                        for j in range(i + 1, len(after)):
                            if after[j].isdigit():
                                number_str += after[j]
                            else:
                                break

                        try:
                            return int(number_str)
                        except ValueError:
                            continue

        # Если не найдено - ищем просто первое число в имени (включая отрицательные)
        for i, char in enumerate(filename_no_ext):
            is_minus = char == '-'
            if char.isdigit() or is_minus:
                # Собираем число со знаком
                number_str = char
                for j in range(i + 1, len(filename_no_ext)):
                    if filename_no_ext[j].isdigit():
                        number_str += filename_no_ext[j]
                    else:
                        break
                try:
                    return int(number_str)
                except ValueError:
                    continue

        # По умолчанию этаж 1
        return 1

    def convert_svg_to_png(self, floor_number: int, output_dpi: int = 96) -> bool:
        """
        Конвертировать SVG план в PNG формат

        Args:
            floor_number: Номер этажа
            output_dpi: DPI для конверсии

        Returns:
            True если успешно
        """
        svg_path = self.get_plan_file(floor_number)

        if not svg_path or not svg_path.endswith('.svg'):
            logger.warning(f"No SVG file found for floor {floor_number}")
            return False

        try:
            from services.svg_loader import SVGLoader

            floor_plan = SVGLoader.load_svg_file(svg_path)
            png_path = svg_path.replace('.svg', '.png')

            success = SVGLoader.save_as_png(floor_plan, png_path, output_dpi)

            if success:
                # Обновляем путь на PNG для этажа
                self.cached_plans[floor_number] = png_path
                logger.info(f"Converted floor {floor_number} SVG to PNG: {png_path}")

            return success

        except ImportError:
            logger.error(
                "cairosvg not installed. Install with: pip install cairosvg"
            )
            return False
        except Exception as e:
            logger.error(f"Error converting SVG to PNG: {e}")
            return False

    @staticmethod
    def create_svg_template(output_path: str = "assets/floor_plans/floor1.svg"):
        """
        Создать шаблон SVG файла для тестирования

        Args:
            output_path: Путь для сохранения шаблона
        """
        svg_template = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="800" viewBox="0 0 1000 800">
  <!-- Фон -->
  <rect width="1000" height="800" fill="#f5f5f5"/>
  
  <!-- Стены (внешние) -->
  <line x1="50" y1="50" x2="950" y2="50" stroke="black" stroke-width="2"/>
  <line x1="950" y1="50" x2="950" y2="750" stroke="black" stroke-width="2"/>
  <line x1="950" y1="750" x2="50" y2="750" stroke="black" stroke-width="2"/>
  <line x1="50" y1="750" x2="50" y2="50" stroke="black" stroke-width="2"/>
  
  <!-- Комната 1 -->
  <polygon points="100,100 300,100 300,300 100,300" fill="#cce5ff" stroke="black" stroke-width="1"/>
  <text x="150" y="200" text-anchor="middle" font-size="14" fill="black">Room 1</text>
  
  <!-- Комната 2 -->
  <polygon points="350,100 550,100 550,300 350,300" fill="#ccffcc" stroke="black" stroke-width="1"/>
  <text x="450" y="200" text-anchor="middle" font-size="14" fill="black">Room 2</text>
  
  <!-- Коридор -->
  <polygon points="600,100 900,100 900,300 600,300" fill="#f0f0f0" stroke="black" stroke-width="1"/>
  <text x="750" y="200" text-anchor="middle" font-size="14" fill="black">Corridor</text>
  
  <!-- Лестница -->
  <polygon points="100,350 200,350 200,450 100,450" fill="#ffcc99" stroke="black" stroke-width="1"/>
  <text x="150" y="405" text-anchor="middle" font-size="12" fill="black">Stairs</text>
  
  <!-- Лифт -->
  <polygon points="250,350 350,350 350,450 250,450" fill="#ff9999" stroke="black" stroke-width="1"/>
  <text x="300" y="405" text-anchor="middle" font-size="12" fill="black">Elevator</text>
</svg>
'''

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(svg_template)

            logger.info(f"Created SVG template: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error creating SVG template: {e}")
            return False
