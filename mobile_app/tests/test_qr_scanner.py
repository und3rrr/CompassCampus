"""
Автоматические тесты для QR Scanner функций
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from services.qr_service import QRCodeService, QRCodeMapping
import unittest
from pathlib import Path
import shutil


class TestQRScanner(unittest.TestCase):
    """Тесты QR сканера"""

    def setUp(self):
        """Инициализация перед каждым тестом"""
        self.qr_dir = ".test_qr_codes"
        self.qr_service = QRCodeService(qr_dir=self.qr_dir)
        # Очищаем данные перед каждым тестом
        if os.path.exists(self.qr_dir):
            shutil.rmtree(self.qr_dir)
        os.makedirs(self.qr_dir, exist_ok=True)
        self.qr_service = QRCodeService(qr_dir=self.qr_dir)

    def tearDown(self):
        """Очистка после каждого теста"""
        if os.path.exists(self.qr_dir):
            shutil.rmtree(self.qr_dir)

    def test_create_qr_mapping(self):
        """Тест создания QR кода"""
        qr_code = self.qr_service.create_qr_mapping(
            node_id="101",
            node_name="Аудитория 101",
            floor=1,
            created_by="admin"
        )
        
        # Проверяем, что QR код создан
        self.assertIsNotNone(qr_code)
        self.assertIsInstance(qr_code, str)
        self.assertGreater(len(qr_code), 0)
        
        print(f"✅ QR код создан: {qr_code}")

    def test_get_location_by_qr(self):
        """Тест получения локации по QR коду"""
        # Создаём QR код
        qr_code = self.qr_service.create_qr_mapping(
            node_id="101",
            node_name="Аудитория 101",
            floor=1,
            created_by="admin"
        )
        
        # Получаем локацию
        mapping = self.qr_service.get_location_by_qr(qr_code)
        
        # Проверяем результат
        self.assertIsNotNone(mapping)
        self.assertIsInstance(mapping, QRCodeMapping)
        self.assertEqual(mapping.node_id, "101")
        self.assertEqual(mapping.node_name, "Аудитория 101")
        self.assertEqual(mapping.floor, 1)
        
        print(f"✅ Локация найдена: {mapping.node_name} (Этаж {mapping.floor})")

    def test_unknown_qr_code(self):
        """Тест с неизвестным QR кодом"""
        mapping = self.qr_service.get_location_by_qr("unknown_code")
        
        # Проверяем, что локация не найдена
        self.assertIsNone(mapping)
        
        print("✅ Неизвестный QR код корректно обработан")

    def test_multiple_qr_codes(self):
        """Тест с несколькими QR кодами"""
        codes = []
        expected_nodes = [
            ("101", "Аудитория 101", 1),
            ("202", "Аудитория 202", 2),
            ("303", "Аудитория 303", 3),
        ]
        
        # Создаём несколько QR кодов
        for node_id, name, floor in expected_nodes:
            code = self.qr_service.create_qr_mapping(
                node_id=node_id,
                node_name=name,
                floor=floor,
                created_by="admin"
            )
            codes.append((code, node_id, name, floor))
        
        # Проверяем каждый код
        for code, expected_id, expected_name, expected_floor in codes:
            mapping = self.qr_service.get_location_by_qr(code)
            self.assertIsNotNone(mapping)
            self.assertEqual(mapping.node_id, expected_id)
            self.assertEqual(mapping.node_name, expected_name)
            self.assertEqual(mapping.floor, expected_floor)
        
        print(f"✅ Создано и проверено {len(codes)} QR кодов")

    def test_persistence(self):
        """Тест сохранения данных на диск"""
        # Создаём QR код
        qr_code = self.qr_service.create_qr_mapping(
            node_id="101",
            node_name="Аудитория 101",
            floor=1,
            created_by="admin"
        )
        
        # Проверяем, что данные сохранены
        data_file = os.path.join(self.qr_dir, 'qr_mappings.json')
        self.assertTrue(os.path.exists(data_file))
        
        # Создаём новый сервис и проверяем, что данные загружены
        new_service = QRCodeService(qr_dir=self.qr_dir)
        mapping = new_service.get_location_by_qr(qr_code)
        
        self.assertIsNotNone(mapping)
        self.assertEqual(mapping.node_id, "101")
        
        print("✅ Данные успешно сохранены и загружены")


if __name__ == '__main__':
    # Запускаем тесты с подробным выводом
    unittest.main(verbosity=2)
