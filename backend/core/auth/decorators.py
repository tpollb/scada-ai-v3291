"""Auth Decorators — проверка ролей пользователя"""
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
