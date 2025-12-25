"""
Кэш-сервис для хранения данных на устройстве
"""
import json
import os
from typing import Any, Optional, Dict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class CacheService:
    """Сервис для работы с локальным кэшем"""

    def __init__(self, cache_dir: str = ".cache"):
        """
        Инициализация кэша

        Args:
            cache_dir: Директория для хранения кэша
        """
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

    def _get_cache_path(self, key: str) -> str:
        """Получить полный путь к файлу кэша"""
        return os.path.join(self.cache_dir, f"{key}.json")

    def get(self, key: str, max_age_seconds: int = 3600) -> Optional[Any]:
        """
        Получить значение из кэша

        Args:
            key: Ключ кэша
            max_age_seconds: Максимальный возраст данных в секундах

        Returns:
            Значение если найдено и не истекло, иначе None
        """
        cache_path = self._get_cache_path(key)

        if not os.path.exists(cache_path):
            return None

        try:
            with open(cache_path, 'r') as f:
                cache_data = json.load(f)

            # Проверяем возраст кэша
            timestamp = datetime.fromisoformat(cache_data.get("timestamp", ""))
            if datetime.now() - timestamp > timedelta(seconds=max_age_seconds):
                os.remove(cache_path)
                return None

            return cache_data.get("value")
        except Exception as e:
            logger.error(f"Error reading cache for key {key}: {e}")
            return None

    def set(self, key: str, value: Any) -> bool:
        """
        Сохранить значение в кэш

        Args:
            key: Ключ кэша
            value: Значение для сохранения

        Returns:
            True если успешно, False иначе
        """
        cache_path = self._get_cache_path(key)

        try:
            cache_data = {
                "timestamp": datetime.now().isoformat(),
                "value": value
            }
            with open(cache_path, 'w') as f:
                json.dump(cache_data, f)
            return True
        except Exception as e:
            logger.error(f"Error writing cache for key {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        Удалить значение из кэша

        Args:
            key: Ключ кэша

        Returns:
            True если удалено, False если не найдено
        """
        cache_path = self._get_cache_path(key)

        try:
            if os.path.exists(cache_path):
                os.remove(cache_path)
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting cache for key {key}: {e}")
            return False

    def clear(self) -> bool:
        """
        Очистить весь кэш

        Returns:
            True если успешно, False иначе
        """
        try:
            for file in os.listdir(self.cache_dir):
                if file.endswith('.json'):
                    os.remove(os.path.join(self.cache_dir, file))
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Проверить существование ключа в кэше"""
        return os.path.exists(self._get_cache_path(key))


# Глобальный экземпляр кэша
_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """Получить или создать глобальный экземпляр кэш-сервиса"""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service


def init_cache_service(cache_dir: str = ".cache"):
    """Инициализировать глобальный кэш-сервис"""
    global _cache_service
    _cache_service = CacheService(cache_dir=cache_dir)
