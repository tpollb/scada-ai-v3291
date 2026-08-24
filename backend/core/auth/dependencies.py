"""Ролевые зависимости для FastAPI.

Используют request.state.user, установленный AuthMiddleware.
Это эффективнее повторного декодирования JWT через HTTPBearer.
"""
from fastapi import Request, HTTPException, status
from structlog import get_logger

from .models import UserRole, User

log = get_logger()


async def get_current_user(request: Request) -> User:
    """Получает пользователя из request.state (установлен AuthMiddleware)."""
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется аутентификация"
        )
    return user


def require_role(*roles: UserRole):
    """Зависимость: пропускает только пользователей с указанными ролями.

    Использование:
        router = APIRouter(dependencies=[Depends(require_role(UserRole.ADMIN))])
    """
    async def role_checker(request: Request) -> User:
        user = getattr(request.state, "user", None)
        if user is None:
            log.warning("Role check failed: no user", path=request.url.path)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Требуется аутентификация"
            )
        if user.role not in roles:
            log.warning(
                "Access denied: insufficient role",
                username=user.username,
                user_role=user.role.value,
                required=[r.value for r in roles],
                path=request.url.path
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Доступ запрещён. Требуется роль: {', '.join(r.value for r in roles)}"
            )
        return user
    return role_checker
