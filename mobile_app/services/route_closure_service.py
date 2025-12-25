"""
Сервис для управления закрытыми маршрутами и ремонтами
"""
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Set
from datetime import datetime, timedelta
from enum import Enum
import json
import os
import logging

logger = logging.getLogger(__name__)


class ClosureType(Enum):
    """Типы закрытия маршрута"""
    MAINTENANCE = "maintenance"  # Техническое обслуживание
    REPAIR = "repair"  # Ремонт
    CLEANING = "cleaning"  # Уборка
    EMERGENCY = "emergency"  # Чрезвычайная ситуация
    OTHER = "other"  # Другое


@dataclass
class RouteClosure:
    """Закрытие маршрута (ребра или узла)"""
    closure_id: str
    from_id: Optional[str] = None  # Если None - это узел
    to_id: Optional[str] = None
    closure_type: ClosureType = ClosureType.MAINTENANCE
    reason: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    created_by: Optional[str] = None  # admin_id
    scheduled_until: Optional[datetime] = None  # Когда планируется открыть
    active: bool = True
    description: Optional[str] = None

    def is_expired(self) -> bool:
        """Проверить истёк ли срок закрытия"""
        if self.scheduled_until:
            return datetime.now() > self.scheduled_until
        return False

    def to_dict(self) -> dict:
        return {
            'closure_id': self.closure_id,
            'from_id': self.from_id,
            'to_id': self.to_id,
            'closure_type': self.closure_type.value,
            'reason': self.reason,
            'created_at': self.created_at.isoformat(),
            'created_by': self.created_by,
            'scheduled_until': self.scheduled_until.isoformat() if self.scheduled_until else None,
            'active': self.active,
            'description': self.description
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            closure_id=data['closure_id'],
            from_id=data.get('from_id'),
            to_id=data.get('to_id'),
            closure_type=ClosureType(data.get('closure_type', 'maintenance')),
            reason=data.get('reason', ''),
            created_at=datetime.fromisoformat(data.get('created_at', datetime.now().isoformat())),
            created_by=data.get('created_by'),
            scheduled_until=datetime.fromisoformat(data['scheduled_until']) if data.get('scheduled_until') else None,
            active=data.get('active', True),
            description=data.get('description')
        )


class RouteClosureService:
    """Сервис управления закрытыми маршрутами"""

    def __init__(self, closure_dir: str = ".closures"):
        self.closure_dir = closure_dir
        self.closures: dict = {}
        os.makedirs(closure_dir, exist_ok=True)
        self._load_closures()

    def _get_closure_file_path(self) -> str:
        """Получить путь к файлу с закрытиями"""
        return os.path.join(self.closure_dir, "closures.json")

    def _load_closures(self):
        """Загрузить закрытия из файла"""
        try:
            path = self._get_closure_file_path()
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for closure_id, closure_data in data.items():
                        closure = RouteClosure.from_dict(closure_data)
                        # Проверить истечение срока
                        if closure.is_expired():
                            closure.active = False
                        self.closures[closure_id] = closure
                logger.info(f"Loaded {len(self.closures)} closures")
        except Exception as e:
            logger.error(f"Failed to load closures: {e}")

    def _save_closures(self):
        """Сохранить закрытия в файл"""
        try:
            path = self._get_closure_file_path()
            data = {cid: c.to_dict() for cid, c in self.closures.items()}
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info("Closures saved")
        except Exception as e:
            logger.error(f"Failed to save closures: {e}")

    def close_route(
        self,
        from_id: str,
        to_id: str,
        closure_type: ClosureType = ClosureType.MAINTENANCE,
        reason: str = "",
        created_by: Optional[str] = None,
        scheduled_until: Optional[datetime] = None,
        description: Optional[str] = None
    ) -> str:
        """
        Закрыть маршрут (ребро)
        
        Args:
            from_id: ID начального узла
            to_id: ID конечного узла
            closure_type: Тип закрытия
            reason: Причина закрытия
            created_by: ID администратора
            scheduled_until: Когда планируется открыть
            description: Подробное описание
            
        Returns:
            closure_id
        """
        import uuid
        closure_id = str(uuid.uuid4())
        
        closure = RouteClosure(
            closure_id=closure_id,
            from_id=from_id,
            to_id=to_id,
            closure_type=closure_type,
            reason=reason,
            created_by=created_by,
            scheduled_until=scheduled_until,
            description=description
        )
        
        self.closures[closure_id] = closure
        self._save_closures()
        logger.info(f"Closed route: {from_id} -> {to_id}, reason: {reason}")
        
        return closure_id

    def close_node(
        self,
        node_id: str,
        closure_type: ClosureType = ClosureType.MAINTENANCE,
        reason: str = "",
        created_by: Optional[str] = None,
        scheduled_until: Optional[datetime] = None,
        description: Optional[str] = None
    ) -> str:
        """
        Закрыть узел (помещение/зону)
        
        Args:
            node_id: ID узла
            closure_type: Тип закрытия
            reason: Причина
            created_by: ID администратора
            scheduled_until: Когда планируется открыть
            description: Описание
            
        Returns:
            closure_id
        """
        import uuid
        closure_id = str(uuid.uuid4())
        
        closure = RouteClosure(
            closure_id=closure_id,
            from_id=node_id,  # Для узла используем from_id
            to_id=None,
            closure_type=closure_type,
            reason=reason,
            created_by=created_by,
            scheduled_until=scheduled_until,
            description=description
        )
        
        self.closures[closure_id] = closure
        self._save_closures()
        logger.info(f"Closed node: {node_id}, reason: {reason}")
        
        return closure_id

    def open_route(self, closure_id: str) -> bool:
        """Открыть закрытый маршрут"""
        if closure_id in self.closures:
            self.closures[closure_id].active = False
            self._save_closures()
            logger.info(f"Opened closure: {closure_id}")
            return True
        return False

    def is_route_closed(self, from_id: str, to_id: str) -> bool:
        """Проверить закрыт ли маршрут"""
        for closure in self.closures.values():
            if (closure.active and not closure.is_expired() and
                closure.from_id == from_id and closure.to_id == to_id):
                return True
        return False

    def is_node_closed(self, node_id: str) -> bool:
        """Проверить закрыт ли узел"""
        for closure in self.closures.values():
            if (closure.active and not closure.is_expired() and
                closure.from_id == node_id and closure.to_id is None):
                return True
        return False

    def get_closure_reason(self, from_id: str, to_id: str) -> Optional[str]:
        """Получить причину закрытия маршрута"""
        for closure in self.closures.values():
            if (closure.active and not closure.is_expired() and
                closure.from_id == from_id and closure.to_id == to_id):
                return closure.reason or closure.closure_type.value
        return None

    def get_active_closures(self) -> List[RouteClosure]:
        """Получить все активные закрытия"""
        active = []
        for closure in self.closures.values():
            if closure.active and not closure.is_expired():
                active.append(closure)
        return active

    def get_closed_edges(self) -> Set[Tuple[str, str]]:
        """Получить множество закрытых маршрутов (рёбер)"""
        closed = set()
        for closure in self.get_active_closures():
            if closure.to_id:  # Это ребро, а не узел
                closed.add((closure.from_id, closure.to_id))
        return closed

    def get_closed_nodes(self) -> Set[str]:
        """Получить множество закрытых узлов"""
        closed = set()
        for closure in self.get_active_closures():
            if closure.to_id is None:  # Это узел
                closed.add(closure.from_id)
        return closed
