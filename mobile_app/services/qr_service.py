"""
Сервис для работы с QR кодами и их привязкой к местоположениям
"""
from dataclasses import dataclass, field
from typing import Optional, Dict
from datetime import datetime
import json
import os
import logging
import uuid

logger = logging.getLogger(__name__)


@dataclass
class QRCodeMapping:
    """Привязка QR кода к местоположению"""
    qr_code: str
    node_id: str
    node_name: str
    floor: int
    created_at: datetime = field(default_factory=datetime.now)
    created_by: Optional[str] = None  # admin_id
    description: Optional[str] = None
    active: bool = True

    def to_dict(self) -> dict:
        return {
            'qr_code': self.qr_code,
            'node_id': self.node_id,
            'node_name': self.node_name,
            'floor': self.floor,
            'created_at': self.created_at.isoformat(),
            'created_by': self.created_by,
            'description': self.description,
            'active': self.active
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            qr_code=data['qr_code'],
            node_id=data['node_id'],
            node_name=data['node_name'],
            floor=data['floor'],
            created_at=datetime.fromisoformat(data.get('created_at', datetime.now().isoformat())),
            created_by=data.get('created_by'),
            description=data.get('description'),
            active=data.get('active', True)
        )


class QRCodeService:
    """Сервис для управления QR кодами"""

    def __init__(self, qr_dir: str = ".qr_codes"):
        self.qr_dir = qr_dir
        self.qr_codes: Dict[str, QRCodeMapping] = {}
        os.makedirs(qr_dir, exist_ok=True)
        self._load_qr_codes()

    def _get_qr_file_path(self) -> str:
        """Получить путь к файлу с QR кодами"""
        return os.path.join(self.qr_dir, "qr_mappings.json")

    def _load_qr_codes(self):
        """Загрузить все QR коды из файла"""
        try:
            path = self._get_qr_file_path()
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for qr_code, mapping_data in data.items():
                        self.qr_codes[qr_code] = QRCodeMapping.from_dict(mapping_data)
                logger.info(f"Loaded {len(self.qr_codes)} QR code mappings")
        except Exception as e:
            logger.error(f"Failed to load QR codes: {e}")

    def _save_qr_codes(self):
        """Сохранить все QR коды в файл"""
        try:
            path = self._get_qr_file_path()
            data = {qr: mapping.to_dict() for qr, mapping in self.qr_codes.items()}
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info("QR codes saved")
        except Exception as e:
            logger.error(f"Failed to save QR codes: {e}")

    def create_qr_mapping(
        self,
        node_id: str,
        node_name: str,
        floor: int,
        created_by: Optional[str] = None,
        description: Optional[str] = None
    ) -> str:
        """
        Создать новое QR сопоставление
        
        Args:
            node_id: ID узла на карте
            node_name: Название узла
            floor: Этаж
            created_by: ID администратора, создавшего сопоставление
            description: Описание (опционально)
            
        Returns:
            QR код (строка)
        """
        qr_code = self._generate_qr_code(node_id)
        
        mapping = QRCodeMapping(
            qr_code=qr_code,
            node_id=node_id,
            node_name=node_name,
            floor=floor,
            created_by=created_by,
            description=description
        )
        
        self.qr_codes[qr_code] = mapping
        self._save_qr_codes()
        logger.info(f"Created QR mapping: {qr_code} -> {node_name}")
        
        return qr_code

    def get_location_by_qr(self, qr_code: str) -> Optional[QRCodeMapping]:
        """
        Получить местоположение по QR коду
        
        Args:
            qr_code: QR код
            
        Returns:
            QRCodeMapping или None если не найден
        """
        mapping = self.qr_codes.get(qr_code)
        if mapping and mapping.active:
            return mapping
        return None

    def delete_qr_mapping(self, qr_code: str) -> bool:
        """Удалить QR сопоставление"""
        if qr_code in self.qr_codes:
            del self.qr_codes[qr_code]
            self._save_qr_codes()
            logger.info(f"Deleted QR mapping: {qr_code}")
            return True
        return False

    def deactivate_qr_mapping(self, qr_code: str) -> bool:
        """Деактивировать QR сопоставление (не удалять, но отключить)"""
        if qr_code in self.qr_codes:
            self.qr_codes[qr_code].active = False
            self._save_qr_codes()
            logger.info(f"Deactivated QR mapping: {qr_code}")
            return True
        return False

    def get_all_qr_codes(self, active_only: bool = True) -> Dict[str, QRCodeMapping]:
        """Получить все QR коды"""
        if active_only:
            return {qr: m for qr, m in self.qr_codes.items() if m.active}
        return self.qr_codes.copy()

    def get_qr_codes_by_node(self, node_id: str) -> list:
        """Получить все QR коды для узла"""
        return [m for m in self.qr_codes.values() if m.node_id == node_id]

    def _generate_qr_code(self, node_id: str) -> str:
        """
        Генерировать QR код
        
        В реальном приложении это была бы ссылка, содержащая:
        - campuscompass://locate/node_id
        или
        - https://campuscompass.app/locate/node_id
        
        Для примера используем простой формат
        """
        unique_id = str(uuid.uuid4())[:8]
        return f"CC-{node_id}-{unique_id}"

    @staticmethod
    def generate_qr_url(node_id: str, app_name: str = "campuscompass") -> str:
        """
        Генерировать URL для QR кода (для сканирования)
        
        Args:
            node_id: ID узла
            app_name: Имя приложения
            
        Returns:
            URL, который можно закодировать в QR
        """
        return f"{app_name}://locate/{node_id}"

    @staticmethod
    def parse_qr_code(qr_data: str) -> Optional[str]:
        """
        Распарсить данные из QR кода
        
        Args:
            qr_data: Данные отсканированного QR кода
            
        Returns:
            node_id или None если невалиден
        """
        # Проверить несколько форматов
        formats = [
            ("campuscompass://locate/", "campuscompass://locate/"),
            ("https://campuscompass.app/locate/", "https://campuscompass.app/locate/"),
            ("CC-", "CC-"),
        ]
        
        for prefix, separator in formats:
            if qr_data.startswith(prefix):
                parts = qr_data[len(prefix):].split('-')
                if parts:
                    return parts[0]
        
        return None
