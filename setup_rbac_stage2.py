#!/usr/bin/env python3
"""
SCADA.AI RBAC — Этап 2: Backend авторизация (Middleware + Decorators)
1. Создание middleware для проверки JWT и установки request.state.user
2. Создание декоратора @require_role для защиты endpoints
3. Интеграция middleware в main.py

Запуск: python setup_rbac_stage2.py
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.resolve()

# ============================================================================
# 1. Создание core/auth/middleware.py
# ============================================================================

def create_auth_middleware():
    filepath = PROJECT_ROOT / "backend" / "core" / "auth" / "middleware.py"
    
    content = '''"""Auth Middleware — проверка JWT и установка пользователя в request.state"""
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from structlog import get_logger
from .jwt_utils import decode_access_token
from .storage import get_user_storage

log = get_logger()

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Пропускаем публичные endpoints
        public_paths = [
            "/",
            "/health",
            "/debug/routes",
            "/api/v1/auth/login",
        ]
        
        # Проверяем точное совпадение или префикс для docs
        if request.url.path in public_paths or request.url.path.startswith("/docs"):
            return await call_next(request)
            
        # Получаем токен из заголовка
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Отсутствует или невалидный токен авторизации"
            )
            
        token = auth_header.split(" ")[1]
        payload = decode_access_token(token)
        
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Истёкший или невалидный токен"
            )
            
        username = payload.get("sub")
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Невалидный токен: отсутствует sub"
            )
            
        storage = get_user_storage()
        user = storage.get_user(username)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Пользователь не найден"
            )
            
        # Сохраняем пользователя в state запроса для использования в endpoints
        request.state.user = user
        
        return await call_next(request)
'''
    filepath.write_text(content, encoding="utf-8")
    print("  ✓ Создан: backend/core/auth/middleware.py")
    return True


# ============================================================================
# 2. Создание core/auth/decorators.py
# ============================================================================

def create_auth_decorators():
    filepath = PROJECT_ROOT / "backend" / "core" / "auth" / "decorators.py"
    
    content = '''"""Auth Decorators — проверка ролей пользователя"""
from fastapi import HTTPException, status, Request
from .models import UserRole

def require_role(*allowed_roles: UserRole):
    """
    Декоратор зависимости для проверки роли пользователя.
    Использование: current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.ENGINEER))
    """
    async def role_checker(request: Request):
        user = getattr(request.state, "user", None)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Требуется аутентификация"
            )
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Доступ запрещён. Требуется одна из ролей: {', '.join(r.value for r in allowed_roles)}"
            )
        return user
    return role_checker

def require_auth(request: Request):
    """
    Декоратор зависимости для проверки только факта аутентификации (любая роль).
    """
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется аутентификация"
        )
    return user
'''
    filepath.write_text(content, encoding="utf-8")
    print("  ✓ Создан: backend/core/auth/decorators.py")
    return True


# ============================================================================
# 3. Обновление main.py
# ============================================================================

def update_main_py():
    filepath = PROJECT_ROOT / "backend" / "main.py"
    
    if not filepath.exists():
        print(f"❌ ОШИБКА: Файл не найден: {filepath}")
        return False
    
    content = filepath.read_text(encoding="utf-8")
    
    # Добавляем импорт AuthMiddleware
    if "from core.auth.middleware import AuthMiddleware" not in content:
        content = content.replace(
            "from core.middleware.license import LicenseMiddleware",
            "from core.middleware.license import LicenseMiddleware\nfrom core.auth.middleware import AuthMiddleware"
        )
    
    # Добавляем AuthMiddleware после LicenseMiddleware
    if "app.add_middleware(AuthMiddleware)" not in content:
        content = content.replace(
            "app.add_middleware(LicenseMiddleware)",
            "app.add_middleware(LicenseMiddleware)\napp.add_middleware(AuthMiddleware)"
        )
    
    filepath.write_text(content, encoding="utf-8")
    print("  ✓ Обновлён: backend/main.py (добавлен AuthMiddleware)")
    return True


# ============================================================================
# Main
# ============================================================================

def main() -> int:
    print("=" * 70)
    print("SCADA.AI RBAC — Этап 2: Backend авторизация (Middleware + Decorators)")
    print("=" * 70)
    print(f"\nКорень проекта: {PROJECT_ROOT}\n")
    
    success = True
    
    if not create_auth_middleware(): success = False
    if not create_auth_decorators(): success = False
    if not update_main_py(): success = False
    
    if success:
        print(f"\n{'=' * 70}")
        print("✅ Этап 2 завершён!")
        print(f"{'=' * 70}")
        print("\nЧто было сделано:")
        print("  1. Создан backend/core/auth/middleware.py (AuthMiddleware)")
        print("     - Проверяет заголовок Authorization: Bearer <token>")
        print("     - Декодирует JWT и проверяет пользователя")
        print("     - Сохраняет пользователя в request.state.user")
        print("  2. Создан backend/core/auth/decorators.py")
        print("     - require_role(*roles) — зависимость для проверки роли")
        print("     - require_auth — зависимость для проверки факта входа")
        print("  3. Обновлён backend/main.py (добавлен AuthMiddleware)")
        print("\nСледующие шаги:")
        print("  1. Перезапустите backend: uvicorn main:app --reload")
        print("  2. Проверьте, что публичные endpoints работают без токена:")
        print("     curl http://localhost:8081/health")
        print("  3. Проверьте, что защищённые endpoints требуют токен:")
        print("     curl http://localhost:8081/api/v1/auth/me")
        print("     (должен вернуть 401 Unauthorized)")
        print("  4. Проверьте доступ с токеном (вставьте свой токен из Этапа 1):")
        print('     curl http://localhost:8081/api/v1/auth/me -H "Authorization: Bearer <ВАШ_ТОКЕН>"')
        print("  5. Этап 3: Frontend — авторизация (LoginModal, auth store, api interceptor)")
        print()
        return 0
    else:
        print(f"\n{'=' * 70}")
        print("❌ ОШИБКИ при выполнении Этапа 2")
        print(f"{'=' * 70}")
        return 1


if __name__ == "__main__":
    sys.exit(main())