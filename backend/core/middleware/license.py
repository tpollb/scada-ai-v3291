"""License Middleware — проверяет срок действия и grace period"""
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from core.license.manager import get_license_manager
from structlog import get_logger

log = get_logger()

class LicenseMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Пропускаем проверки для самих endpoints лицензии и базовых путей
        if request.url.path.startswith("/api/v1/license") or request.url.path in ["/", "/health", "/debug/routes"]:
            return await call_next(request)

        license_mgr = get_license_manager()
        if not license_mgr:
            log.warning("License manager not initialized")
            return await call_next(request)

        status = license_mgr.get_status()
        
        # Если лицензия истекла и grace period закончился
        if status.expired:
            log.warning("License expired and grace period ended", path=request.url.path)
            raise HTTPException(
                status_code=402,
                detail="Срок действия лицензии истек. Пожалуйста, обновите лицензию."
            )
        
        response = await call_next(request)
        
        # Если в grace period, добавляем заголовок-предупреждение для фронтенда
        if status.in_grace_period:
            response.headers["X-License-Warning"] = f"grace_period; days_remaining={status.days_remaining}"
            
        return response
