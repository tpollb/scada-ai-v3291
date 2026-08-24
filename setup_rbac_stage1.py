#!/usr/bin/env python3
"""
SCADA.AI RBAC — Этап 1: Backend основа аутентификации
1. Создание модуля core/auth/ с моделями, password utils, JWT, storage
2. Создание API endpoints для аутентификации
3. Создание users.json с предустановленными пользователями
4. Модификация main.py для подключения роутера

Запуск: python setup_rbac_stage1.py
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.resolve()

# ============================================================================
# 1. Создание core/auth/models.py
# ============================================================================

def create_auth_models():
    auth_dir = PROJECT_ROOT / "backend" / "core" / "auth"
    auth_dir.mkdir(parents=True, exist_ok=True)
    
    filepath = auth_dir / "models.py"
    
    content = '''"""Auth models — Pydantic schemas for authentication"""
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from typing import Optional

class UserRole(str, Enum):
    """Роли пользователей"""
    ADMIN = "admin"
    ENGINEER = "engineer"
    OPERATOR = "operator"
    BOSS = "boss"

class User(BaseModel):
    """Модель пользователя (для хранения в users.json)"""
    username: str = Field(..., description="Логин")
    password_hash: str = Field(..., description="Хеш пароля (bcrypt)")
    role: UserRole = Field(..., description="Роль пользователя")
    display_name: str = Field(..., description="Отображаемое имя")
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    last_login: Optional[datetime] = None

class LoginRequest(BaseModel):
    """Запрос на аутентификацию"""
    username: str
    password: str

class LoginResponse(BaseModel):
    """Ответ после успешной аутентификации"""
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"

class UserResponse(BaseModel):
    """Публичная информация о пользователе (без пароля)"""
    username: str
    role: UserRole
    display_name: str

class ChangePasswordRequest(BaseModel):
    """Запрос на смену пароля"""
    new_password: str

class UserCreateRequest(BaseModel):
    """Запрос на создание пользователя"""
    username: str
    password: str
    role: UserRole
    display_name: str
'''
    
    filepath.write_text(content, encoding="utf-8")
    print(f"  ✓ Создан: backend/core/auth/models.py")
    return True


# ============================================================================
# 2. Создание core/auth/password.py
# ============================================================================

def create_password_utils():
    filepath = PROJECT_ROOT / "backend" / "core" / "auth" / "password.py"
    
    content = '''"""Password utilities — bcrypt hashing"""
import bcrypt
from structlog import get_logger

log = get_logger()

def hash_password(password: str) -> str:
    """Хеширует пароль с использованием bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет соответствие пароля хешу"""
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception as e:
        log.error("Password verification failed", error=str(e))
        return False
'''
    
    filepath.write_text(content, encoding="utf-8")
    print(f"  ✓ Создан: backend/core/auth/password.py")
    return True


# ============================================================================
# 3. Создание core/auth/jwt_utils.py
# ============================================================================

def create_jwt_utils():
    filepath = PROJECT_ROOT / "backend" / "core" / "auth" / "jwt_utils.py"
    
    content = '''"""JWT utilities — генерация и валидация токенов"""
import jwt
from datetime import datetime, timezone, timedelta
from typing import Optional
from structlog import get_logger
from config.settings import settings

log = get_logger()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Создаёт JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm
    )
    
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """Декодирует и валидирует JWT токен"""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except jwt.ExpiredSignatureError:
        log.warning("Token expired")
        return None
    except jwt.JWTError as e:
        log.warning("Invalid token", error=str(e))
        return None
    except Exception as e:
        log.error("Token decode failed", error=str(e))
        return None
'''
    
    filepath.write_text(content, encoding="utf-8")
    print(f"  ✓ Создан: backend/core/auth/jwt_utils.py")
    return True


# ============================================================================
# 4. Создание core/auth/storage.py
# ============================================================================

def create_user_storage():
    filepath = PROJECT_ROOT / "backend" / "core" / "auth" / "storage.py"
    
    content = '''"""User storage — хранилище пользователей (JSON файл)"""
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
'''
    
    filepath.write_text(content, encoding="utf-8")
    print(f"  ✓ Создан: backend/core/auth/storage.py")
    return True


# ============================================================================
# 5. Создание core/auth/__init__.py
# ============================================================================

def create_auth_init():
    filepath = PROJECT_ROOT / "backend" / "core" / "auth" / "__init__.py"
    
    content = '''"""Auth module — аутентификация и авторизация"""
from .models import User, UserRole, LoginRequest, LoginResponse, UserResponse, UserCreateRequest, ChangePasswordRequest
from .password import hash_password, verify_password
from .jwt_utils import create_access_token, decode_access_token
from .storage import UserStorage, get_user_storage

__all__ = [
    'User', 'UserRole', 'LoginRequest', 'LoginResponse', 'UserResponse', 'UserCreateRequest', 'ChangePasswordRequest',
    'hash_password', 'verify_password',
    'create_access_token', 'decode_access_token',
    'UserStorage', 'get_user_storage'
]
'''
    
    filepath.write_text(content, encoding="utf-8")
    print(f"  ✓ Создан: backend/core/auth/__init__.py")
    return True


# ============================================================================
# 6. Создание api/routes/auth.py
# ============================================================================

def create_auth_routes():
    filepath = PROJECT_ROOT / "backend" / "api" / "routes" / "auth.py"
    
    content = '''"""Auth API — аутентификация и управление пользователями"""
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from structlog import get_logger
from core.auth import (
    LoginRequest, LoginResponse, UserResponse, UserCreateRequest, ChangePasswordRequest,
    verify_password, create_access_token, decode_access_token,
    get_user_storage, User, UserRole, hash_password
)

log = get_logger()

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Получает текущего пользователя из JWT токена"""
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Невалидный или истёкший токен")
    
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Невалидный токен")
    
    storage = get_user_storage()
    user = storage.get_user(username)
    
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Пользователь не найден")
    
    return user

def require_role(*roles: UserRole):
    """Декоратор для проверки роли пользователя"""
    async def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Доступ запрещён. Требуется роль: {', '.join(r.value for r in roles)}"
            )
        return current_user
    return role_checker

@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest):
    """Аутентификация пользователя"""
    storage = get_user_storage()
    user = storage.get_user(req.username)
    
    if not user or not verify_password(req.password, user.password_hash):
        log.warning("Login failed", username=req.username)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный логин или пароль")
    
    access_token = create_access_token(data={"sub": user.username, "role": user.role.value})
    storage.update_last_login(user.username)
    
    log.info("User logged in", username=user.username, role=user.role.value)
    
    return LoginResponse(
        access_token=access_token,
        user=UserResponse(username=user.username, role=user.role, display_name=user.display_name)
    )

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Выход из системы"""
    log.info("User logged out", username=current_user.username)
    return {"status": "ok", "message": "Вы вышли из системы"}

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Получить информацию о текущем пользователе"""
    return UserResponse(username=current_user.username, role=current_user.role, display_name=current_user.display_name)

@router.get("/users", response_model=list[UserResponse])
async def list_users(current_user: User = Depends(require_role(UserRole.ADMIN))):
    """Получить список всех пользователей (только admin)"""
    storage = get_user_storage()
    users = storage.get_all_users()
    return [UserResponse(username=u.username, role=u.role, display_name=u.display_name) for u in users]

@router.post("/users", response_model=UserResponse)
async def create_user(req: UserCreateRequest, current_user: User = Depends(require_role(UserRole.ADMIN))):
    """Создать нового пользователя (только admin)"""
    storage = get_user_storage()
    
    if storage.get_user(req.username):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Пользователь с таким логином уже существует")
    
    user = User(
        username=req.username,
        password_hash=hash_password(req.password),
        role=req.role,
        display_name=req.display_name
    )
    
    if not storage.create_user(user):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Не удалось создать пользователя")
    
    log.info("User created", username=user.username, role=user.role.value, created_by=current_user.username)
    return UserResponse(username=user.username, role=user.role, display_name=user.display_name)

@router.delete("/users/{username}")
async def delete_user(username: str, current_user: User = Depends(require_role(UserRole.ADMIN))):
    """Удалить пользователя (только admin)"""
    if username == current_user.username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Нельзя удалить самого себя")
    
    storage = get_user_storage()
    if not storage.delete_user(username):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    
    log.info("User deleted", username=username, deleted_by=current_user.username)
    return {"status": "ok", "message": f"Пользователь {username} удалён"}

@router.put("/users/{username}/password")
async def change_password(username: str, req: ChangePasswordRequest, current_user: User = Depends(require_role(UserRole.ADMIN))):
    """Сменить пароль пользователя (только admin)"""
    storage = get_user_storage()
    
    if not storage.change_password(username, req.new_password):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    
    log.info("Password changed", username=username, changed_by=current_user.username)
    return {"status": "ok", "message": "Пароль изменён"}
'''
    
    filepath.write_text(content, encoding="utf-8")
    print(f"  ✓ Создан: backend/api/routes/auth.py")
    return True


# ============================================================================
# 7. Модификация main.py
# ============================================================================

def update_main_py():
    filepath = PROJECT_ROOT / "backend" / "main.py"
    
    if not filepath.exists():
        print(f"❌ ОШИБКА: Файл не найден: {filepath}")
        return False
    
    content = filepath.read_text(encoding="utf-8")
    
    if "from api.routes import" in content and "auth" in content:
        print("  ⚠️  Роутер auth уже подключён, пропускаем")
        return True
    
    if "from api.routes import" in content:
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.strip().startswith("from api.routes import"):
                if "auth" not in line:
                    lines[i] = line.rstrip() + ", auth"
                break
        content = '\n'.join(lines)
    
    if 'app.include_router(auth.router)' not in content:
        marker = 'app.include_router(license.router)'
        if marker in content:
            content = content.replace(marker, marker + '\napp.include_router(auth.router)')
        else:
            content += '\napp.include_router(auth.router)'
    
    filepath.write_text(content, encoding="utf-8")
    print(f"  ✓ Обновлён: backend/main.py")
    return True


# ============================================================================
# 8. Проверка bcrypt в requirements.txt
# ============================================================================

def check_bcrypt_dependency():
    filepath = PROJECT_ROOT / "backend" / "requirements.txt"
    
    if not filepath.exists():
        print("  ⚠️  requirements.txt не найден, пропускаем")
        return True
    
    content = filepath.read_text(encoding="utf-8")
    
    if "bcrypt" not in content.lower():
        content += "\nbcrypt>=4.0.0\n"
        filepath.write_text(content, encoding="utf-8")
        print("  ✓ Добавлен bcrypt в requirements.txt")
    else:
        print("  - bcrypt уже есть в requirements.txt")
    
    return True


# ============================================================================
# 9. Добавление настроек JWT в settings.py
# ============================================================================

def update_settings():
    filepath = PROJECT_ROOT / "backend" / "config" / "settings.py"
    
    if not filepath.exists():
        print(f"❌ ОШИБКА: Файл не найден: {filepath}")
        return False
    
    content = filepath.read_text(encoding="utf-8")
    
    if "jwt_secret" in content:
        print("  ⚠️  JWT настройки уже есть, пропускаем")
        return True
    
    jwt_settings = '''
    # JWT Authentication
    jwt_secret: str = "scada-ai-super-secret-key-change-in-production-2026"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440  # 24 часа
'''
    
    # Находим конец класса Settings
    if "class Settings" in content:
        # Добавляем перед последней строкой класса
        content = content.rstrip()
        if content.endswith("settings = Settings()"):
            content = content.replace("settings = Settings()", jwt_settings + "\n\nsettings = Settings()")
        else:
            content += jwt_settings
    
    filepath.write_text(content, encoding="utf-8")
    print(f"  ✓ Обновлён: backend/config/settings.py")
    return True


# ============================================================================
# Main
# ============================================================================

def main() -> int:
    print("=" * 70)
    print("SCADA.AI RBAC — Этап 1: Backend основа аутентификации")
    print("=" * 70)
    print(f"\nКорень проекта: {PROJECT_ROOT}\n")
    
    print("Создаю модуль auth...\n")
    
    success = True
    
    if not create_auth_models(): success = False
    if not create_password_utils(): success = False
    if not create_jwt_utils(): success = False
    if not create_user_storage(): success = False
    if not create_auth_init(): success = False
    if not create_auth_routes(): success = False
    if not update_main_py(): success = False
    if not check_bcrypt_dependency(): success = False
    if not update_settings(): success = False
    
    if success:
        print(f"\n{'=' * 70}")
        print("✅ Этап 1 завершён!")
        print(f"{'=' * 70}")
        print("\nЧто было сделано:")
        print("  1. Создан модуль backend/core/auth/ с:")
        print("     - models.py — Pydantic модели (User, UserRole, LoginRequest/Response)")
        print("     - password.py — bcrypt хеширование паролей")
        print("     - jwt_utils.py — генерация/валидация JWT токенов")
        print("     - storage.py — хранилище пользователей (JSON файл)")
        print("     - __init__.py — экспорт модулей")
        print("  2. Создан backend/api/routes/auth.py с endpoints:")
        print("     - POST /api/v1/auth/login — аутентификация")
        print("     - POST /api/v1/auth/logout — выход")
        print("     - GET /api/v1/auth/me — текущий пользователь")
        print("     - GET /api/v1/auth/users — список пользователей (admin)")
        print("     - POST /api/v1/auth/users — создание пользователя (admin)")
        print("     - DELETE /api/v1/auth/users/{username} — удаление (admin)")
        print("     - PUT /api/v1/auth/users/{username}/password — смена пароля (admin)")
        print("  3. Подключён роутер auth в main.py")
        print("  4. Добавлен bcrypt в requirements.txt")
        print("  5. Добавлены JWT настройки в settings.py")
        print("\nСледующие шаги:")
        print("  1. Установите bcrypt: pip install bcrypt")
        print("  2. Перезапустите backend: uvicorn main:app --reload")
        print("  3. Проверьте что users.json создан в backend/data/")
        print("  4. Протестируйте login:")
        print('     curl -X POST http://localhost:8081/api/v1/auth/login \\')
        print('       -H "Content-Type: application/json" \\')
        print('       -d \'{"username":"admin","password":"admin123"}\'')
        print("  5. Этап 2: Backend — авторизация (middleware + декораторы)")
        print()
        return 0
    else:
        print(f"\n{'=' * 70}")
        print("❌ ОШИБКИ при выполнении Этапа 1")
        print(f"{'=' * 70}")
        return 1


if __name__ == "__main__":
    sys.exit(main())