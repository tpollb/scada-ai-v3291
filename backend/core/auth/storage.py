"""User storage — хранилище пользователей (JSON файл)"""
import json
from pathlib import Path
from datetime import datetime
from typing import Optional
from structlog import get_logger
from .models import User, UserRole
from .password import hash_password

log = get_logger()

USERS_FILE = Path(__file__).parent.parent.parent.parent / "data" / "users.json"

class UserStorage:
    """Управляет хранилищем пользователей"""
    
    def __init__(self, users_file: Path = USERS_FILE):
        self.users_file = users_file
        self._users: dict[str, User] = {}
        self.load()
    
    def load(self):
        """Загружает пользователей из файла"""
        if not self.users_file.exists():
            log.warning("Users file not found, creating default", path=str(self.users_file))
            self._create_default_users()
            return
        
        try:
            with open(self.users_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self._users = {}
            for user_data in data.get('users', []):
                user = User(**user_data)
                self._users[user.username] = user
            
            log.info("Users loaded", count=len(self._users))
        except Exception as e:
            log.error("Failed to load users", error=str(e))
            self._create_default_users()
    
    def save(self):
        """Сохраняет пользователей в файл"""
        try:
            self.users_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'users': [user.model_dump() for user in self._users.values()]
            }
            
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            log.info("Users saved", count=len(self._users))
        except Exception as e:
            log.error("Failed to save users", error=str(e))
    
    def _create_default_users(self):
        """Создаёт предустановленных пользователей"""
        default_users = [
            {'username': 'admin', 'password': 'admin123', 'role': UserRole.ADMIN, 'display_name': 'Администратор'},
            {'username': 'engineer', 'password': 'engineer123', 'role': UserRole.ENGINEER, 'display_name': 'Инженер'},
            {'username': 'operator', 'password': 'operator123', 'role': UserRole.OPERATOR, 'display_name': 'Оператор'},
            {'username': 'boss', 'password': 'boss123', 'role': UserRole.BOSS, 'display_name': 'Руководитель'}
        ]
        
        self._users = {}
        for user_data in default_users:
            user = User(
                username=user_data['username'],
                password_hash=hash_password(user_data['password']),
                role=user_data['role'],
                display_name=user_data['display_name']
            )
            self._users[user.username] = user
        
        self.save()
        log.info("Default users created", count=len(self._users))
    
    def get_user(self, username: str) -> Optional[User]:
        return self._users.get(username)
    
    def get_all_users(self) -> list[User]:
        return list(self._users.values())
    
    def create_user(self, user: User) -> bool:
        if user.username in self._users:
            return False
        self._users[user.username] = user
        self.save()
        return True
    
    def update_user(self, username: str, updates: dict) -> bool:
        if username not in self._users:
            return False
        user = self._users[username]
        for key, value in updates.items():
            if hasattr(user, key):
                setattr(user, key, value)
        self.save()
        return True
    
    def delete_user(self, username: str) -> bool:
        if username not in self._users:
            return False
        del self._users[username]
        self.save()
        return True
    
    def change_password(self, username: str, new_password: str) -> bool:
        if username not in self._users:
            return False
        self._users[username].password_hash = hash_password(new_password)
        self.save()
        return True
    
    def update_last_login(self, username: str):
        if username in self._users:
            self._users[username].last_login = datetime.now()
            self.save()

_storage: Optional[UserStorage] = None

def get_user_storage() -> UserStorage:
    global _storage
    if _storage is None:
        _storage = UserStorage()
    return _storage
