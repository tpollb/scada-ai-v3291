"""Auth models — Pydantic schemas for authentication"""
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
