"""
Система авторизации и управления профилями пользователей
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from datetime import datetime
import json
import os
import logging

logger = logging.getLogger(__name__)


class UserRole(Enum):
    """Роли пользователя"""
    GUEST = "guest"
    STUDENT = "student"
    ADMIN = "admin"


class UserPermission(Enum):
    """Права доступа"""
    VIEW_MAP = "view_map"
    EDIT_MAP = "edit_map"
    CLOSE_ROUTES = "close_routes"
    VIEW_ANALYTICS = "view_analytics"
    MANAGE_USERS = "manage_users"


@dataclass
class VisitHistory:
    """История посещения узла"""
    node_id: str
    node_name: str
    floor: int
    timestamp: datetime = field(default_factory=datetime.now)
    duration_seconds: Optional[int] = None  # Как долго пользователь был в узле

    def to_dict(self) -> dict:
        return {
            'node_id': self.node_id,
            'node_name': self.node_name,
            'floor': self.floor,
            'timestamp': self.timestamp.isoformat(),
            'duration_seconds': self.duration_seconds
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            node_id=data['node_id'],
            node_name=data['node_name'],
            floor=data['floor'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            duration_seconds=data.get('duration_seconds')
        )


@dataclass
class UserProfile:
    """Профиль пользователя"""
    user_id: str
    username: str
    role: UserRole
    email: Optional[str] = None
    
    # История посещений (только для студентов и админов)
    visit_history: List[VisitHistory] = field(default_factory=list)
    
    # Последнее местоположение
    last_location: Optional[str] = None
    last_location_time: Optional[datetime] = None
    
    # QR коды связанные с пользователем (для админов)
    qr_codes: Dict[str, str] = field(default_factory=dict)  # {qr_code: node_id}
    
    # Закрытые маршруты (для админов)
    closed_routes: List[tuple] = field(default_factory=list)  # [(from_id, to_id), ...]
    
    created_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None

    def get_permissions(self) -> List[UserPermission]:
        """Получить список прав для данной роли"""
        permissions = {
            UserRole.GUEST: [UserPermission.VIEW_MAP],
            UserRole.STUDENT: [
                UserPermission.VIEW_MAP,
                UserPermission.VIEW_ANALYTICS
            ],
            UserRole.ADMIN: [
                UserPermission.VIEW_MAP,
                UserPermission.EDIT_MAP,
                UserPermission.CLOSE_ROUTES,
                UserPermission.VIEW_ANALYTICS,
                UserPermission.MANAGE_USERS
            ]
        }
        return permissions.get(self.role, [])

    def has_permission(self, permission: UserPermission) -> bool:
        """Проверить наличие прав"""
        return permission in self.get_permissions()

    def add_visit(self, node_id: str, node_name: str, floor: int):
        """Добавить узел в историю посещений"""
        if self.role in [UserRole.STUDENT, UserRole.ADMIN]:
            self.visit_history.append(VisitHistory(
                node_id=node_id,
                node_name=node_name,
                floor=floor
            ))
            self.last_location = node_id
            self.last_location_time = datetime.now()

    def to_dict(self) -> dict:
        """Сериализовать профиль"""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'role': self.role.value,
            'email': self.email,
            'visit_history': [v.to_dict() for v in self.visit_history],
            'last_location': self.last_location,
            'last_location_time': self.last_location_time.isoformat() if self.last_location_time else None,
            'qr_codes': self.qr_codes,
            'closed_routes': self.closed_routes,
            'created_at': self.created_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Десериализовать профиль"""
        return cls(
            user_id=data['user_id'],
            username=data['username'],
            role=UserRole(data['role']),
            email=data.get('email'),
            visit_history=[VisitHistory.from_dict(v) for v in data.get('visit_history', [])],
            last_location=data.get('last_location'),
            last_location_time=datetime.fromisoformat(data['last_location_time']) if data.get('last_location_time') else None,
            qr_codes=data.get('qr_codes', {}),
            closed_routes=data.get('closed_routes', []),
            created_at=datetime.fromisoformat(data.get('created_at', datetime.now().isoformat())),
            last_login=datetime.fromisoformat(data['last_login']) if data.get('last_login') else None
        )


class AuthenticationService:
    """Сервис аутентификации и управления профилями"""

    def __init__(self, profile_dir: str = ".profiles"):
        self.profile_dir = profile_dir
        self.current_user: Optional[UserProfile] = None
        os.makedirs(profile_dir, exist_ok=True)
        
        # Попытаться загрузить последнего пользователя
        self._load_last_user()

    def _get_profile_path(self, user_id: str) -> str:
        """Получить путь к файлу профиля"""
        return os.path.join(self.profile_dir, f"{user_id}.json")

    def login_as_guest(self) -> UserProfile:
        """Войти как гость"""
        guest_profile = UserProfile(
            user_id="guest",
            username="Гость",
            role=UserRole.GUEST
        )
        self.current_user = guest_profile
        logger.info("Logged in as guest")
        return guest_profile

    def login_student(self, username: str, email: str, student_id: str) -> UserProfile:
        """Войти как студент"""
        profile = UserProfile(
            user_id=student_id,
            username=username,
            role=UserRole.STUDENT,
            email=email
        )
        profile.last_login = datetime.now()
        self.current_user = profile
        self._save_profile(profile)
        logger.info(f"Logged in as student: {username}")
        return profile

    def login_admin(self, username: str, email: str, admin_id: str, password: str) -> Optional[UserProfile]:
        """Войти как администратор"""
        # TODO: Проверить пароль против хеша (для реальной системы)
        profile = UserProfile(
            user_id=admin_id,
            username=username,
            role=UserRole.ADMIN,
            email=email
        )
        profile.last_login = datetime.now()
        self.current_user = profile
        self._save_profile(profile)
        logger.info(f"Logged in as admin: {username}")
        return profile

    def logout(self):
        """Выйти из системы"""
        if self.current_user:
            self._save_profile(self.current_user)
            logger.info(f"Logged out: {self.current_user.username}")
        self.current_user = None

    def _save_profile(self, profile: UserProfile):
        """Сохранить профиль в файл"""
        try:
            path = self._get_profile_path(profile.user_id)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(profile.to_dict(), f, ensure_ascii=False, indent=2)
            logger.info(f"Profile saved: {profile.user_id}")
        except Exception as e:
            logger.error(f"Failed to save profile: {e}")

    def _load_profile(self, user_id: str) -> Optional[UserProfile]:
        """Загрузить профиль из файла"""
        try:
            path = self._get_profile_path(user_id)
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return UserProfile.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load profile: {e}")
        return None

    def _load_last_user(self):
        """Загрузить последнего пользователя"""
        last_user_path = os.path.join(self.profile_dir, ".last_user")
        try:
            if os.path.exists(last_user_path):
                with open(last_user_path, 'r') as f:
                    user_id = f.read().strip()
                    profile = self._load_profile(user_id)
                    if profile:
                        self.current_user = profile
                        logger.info(f"Loaded last user: {user_id}")
        except Exception as e:
            logger.error(f"Failed to load last user: {e}")

    def _save_last_user(self):
        """Сохранить ID последнего пользователя"""
        try:
            if self.current_user and self.current_user.role != UserRole.GUEST:
                last_user_path = os.path.join(self.profile_dir, ".last_user")
                with open(last_user_path, 'w') as f:
                    f.write(self.current_user.user_id)
        except Exception as e:
            logger.error(f"Failed to save last user: {e}")

    def get_current_user(self) -> Optional[UserProfile]:
        """Получить текущего пользователя"""
        return self.current_user

    def is_authenticated(self) -> bool:
        """Проверить, авторизован ли пользователь"""
        return self.current_user is not None and self.current_user.role != UserRole.GUEST

    def has_permission(self, permission: UserPermission) -> bool:
        """Проверить право текущего пользователя"""
        if not self.current_user:
            return False
        return self.current_user.has_permission(permission)
