"""Auth Middleware — проверка JWT и установка пользователя в request.state"""
from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from structlog import get_logger
from .jwt_utils import decode_access_token
from .storage import get_user_storage

log = get_logger()

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Разрешаем OPTIONS запросы (CORS preflight) без проверки токена
        if request.method == "OPTIONS":
            return await call_next(request)

        # Пропускаем публичные endpoints
        public_paths = [
            "/",
            "/health",
            "/debug/routes",
            "/api/v1/auth/login",
            "/system/info",
            "/api/v1/license/status",
        ]
        
        # Проверяем точное совпадение или префикс для docs
        if request.url.path in public_paths or request.url.path.startswith("/docs"):
            return await call_next(request)
            
        # Получаем токен из заголовка
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Отсутствует или невалидный токен авторизации"}
            )
            
        token = auth_header.split(" ")[1]
        payload = decode_access_token(token)
        
        if not payload:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Истёкший или невалидный токен"}
            )
            
        username = payload.get("sub")
        if not username:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Невалидный токен: отсутствует sub"}
            )
            
        storage = get_user_storage()
        user = storage.get_user(username)
        
        if not user:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Пользователь не найден"}
            )
            
        # Сохраняем пользователя в state запроса для использования в endpoints
        request.state.user = user
        
        return await call_next(request)
