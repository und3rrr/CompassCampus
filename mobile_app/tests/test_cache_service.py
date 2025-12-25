"""
Unit тесты для Cache Service
"""
import pytest
import json
import os
from services.cache_service import CacheService


class TestCacheService:
    """Тесты для CacheService"""

    def test_initialization(self, cache_service):
        """Тест инициализации кэша"""
        assert os.path.exists(cache_service.cache_dir)
        assert cache_service.cache_dir.endswith('.cache')

    def test_set_and_get(self, cache_service):
        """Тест сохранения и получения значения"""
        test_value = {"key": "value", "number": 42}
        assert cache_service.set("test_key", test_value) is True
        retrieved_value = cache_service.get("test_key")
        assert retrieved_value == test_value

    def test_get_nonexistent_key(self, cache_service):
        """Тест получения несуществующего ключа"""
        result = cache_service.get("nonexistent_key")
        assert result is None

    def test_cache_expiry(self, cache_service):
        """Тест истечения кэша"""
        test_value = {"data": "test"}
        cache_service.set("expiring_key", test_value)

        # Получаем с истекшим временем
        result = cache_service.get("expiring_key", max_age_seconds=0)
        assert result is None

        # Получаем до истечения
        result = cache_service.get("expiring_key", max_age_seconds=3600)
        assert result == test_value

    def test_delete_existing_key(self, cache_service):
        """Тест удаления существующего ключа"""
        cache_service.set("delete_key", "value")
        assert cache_service.delete("delete_key") is True
        assert cache_service.get("delete_key") is None

    def test_delete_nonexistent_key(self, cache_service):
        """Тест удаления несуществующего ключа"""
        result = cache_service.delete("nonexistent_key")
        assert result is False

    def test_clear_cache(self, cache_service):
        """Тест очистки кэша"""
        cache_service.set("key1", "value1")
        cache_service.set("key2", "value2")
        cache_service.set("key3", "value3")

        assert cache_service.clear() is True
        assert cache_service.get("key1") is None
        assert cache_service.get("key2") is None
        assert cache_service.get("key3") is None

    def test_exists(self, cache_service):
        """Тест проверки существования ключа"""
        cache_service.set("existing_key", "value")
        assert cache_service.exists("existing_key") is True
        assert cache_service.exists("nonexistent_key") is False

    def test_cache_different_types(self, cache_service):
        """Тест кэширования различных типов данных"""
        # String
        cache_service.set("string_key", "hello")
        assert cache_service.get("string_key") == "hello"

        # List
        cache_service.set("list_key", [1, 2, 3])
        assert cache_service.get("list_key") == [1, 2, 3]

        # Dict
        cache_service.set("dict_key", {"a": 1, "b": 2})
        assert cache_service.get("dict_key") == {"a": 1, "b": 2}

        # Number
        cache_service.set("number_key", 42)
        assert cache_service.get("number_key") == 42

        # Boolean
        cache_service.set("bool_key", True)
        assert cache_service.get("bool_key") is True

    def test_cache_overwrite(self, cache_service):
        """Тест перезаписи значения в кэше"""
        cache_service.set("key", "value1")
        assert cache_service.get("key") == "value1"

        cache_service.set("key", "value2")
        assert cache_service.get("key") == "value2"

    def test_cache_path_generation(self, cache_service):
        """Тест правильного формирования пути кэша"""
        key = "test_key"
        expected_path = os.path.join(cache_service.cache_dir, "test_key.json")
        actual_path = cache_service._get_cache_path(key)
        assert actual_path == expected_path

    def test_cache_file_format(self, cache_service):
        """Тест формата файла кэша"""
        test_value = {"data": "test"}
        cache_service.set("format_test", test_value)

        # Читаем файл напрямую
        cache_path = cache_service._get_cache_path("format_test")
        with open(cache_path, 'r') as f:
            cache_data = json.load(f)

        assert "timestamp" in cache_data
        assert "value" in cache_data
        assert cache_data["value"] == test_value

    def test_large_data_caching(self, cache_service):
        """Тест кэширования больших объемов данных"""
        large_list = list(range(10000))
        assert cache_service.set("large_key", large_list) is True
        retrieved = cache_service.get("large_key")
        assert retrieved == large_list

    def test_special_characters_in_key(self, cache_service):
        """Тест работы с специальными символами в ключе"""
        key = "key_with-special.chars_123"
        value = "special_value"
        assert cache_service.set(key, value) is True
        assert cache_service.get(key) == value

    def test_concurrent_access_simulation(self, cache_service):
        """Тест симуляции одновременного доступа"""
        # Устанавливаем несколько ключей
        for i in range(100):
            cache_service.set(f"key_{i}", f"value_{i}")

        # Проверяем их наличие
        for i in range(100):
            assert cache_service.get(f"key_{i}") == f"value_{i}"

    def test_cache_persistence(self, cache_service):
        """Тест сохранения кэша между операциями"""
        cache_service.set("persistent_key", "persistent_value")

        # Создаем новый кэш с той же директорией
        new_cache = CacheService(cache_dir=cache_service.cache_dir)
        value = new_cache.get("persistent_key")
        assert value == "persistent_value"
