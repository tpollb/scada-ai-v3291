"""Auth module — аутентификация и авторизация"""
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

from .dependencies import get_current_user, require_role
