"""License API — управление лицензией"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
import uuid
from pathlib import Path
from structlog import get_logger
from core.license.manager import get_license_manager, init_license_manager
from config.settings import settings

log = get_logger()

# Pydantic модели для сессий
class SessionStartResponse(BaseModel):
    session_id: str
    status: str
    message: str

class SessionHeartbeatRequest(BaseModel):
    session_id: str

class SessionEndRequest(BaseModel):
    session_id: str

router = APIRouter(prefix="/api/v1/license", tags=["license"])

@router.get("/status")
async def get_license_status():
    """Возвращает текущий статус лицензии"""
    license_mgr = get_license_manager()
    if not license_mgr:
        return {"valid": False, "error": "License manager not initialized"}
    
    status = license_mgr.get_status()
    return status.model_dump()

@router.get("/info")
async def get_license_info():
    """Публичная информация о лицензии"""
    license_mgr = get_license_manager()
    if not license_mgr:
        return {"customer": "Unknown", "valid": False}
    
    status = license_mgr.get_status()
    return {
        "customer": status.customer,
        "license_type": status.license_type.value if hasattr(status.license_type, 'value') else str(status.license_type),
        "valid": status.valid,
        "expired": status.expired,
        "in_grace_period": status.in_grace_period,
        "days_remaining": status.days_remaining,
        "features": status.features,
        "max_concurrent_users": status.max_concurrent_users,
        "current_users": status.current_users,
    }

@router.post("/upload")
async def upload_license(file: UploadFile = File(...)):
    """Загружает и валидирует новую лицензию"""
    if not file.filename or not file.filename.endswith(".lic"):
        raise HTTPException(status_code=400, detail="Файл должен иметь расширение .lic")
    
    temp_path = Path(settings.license_file)
    content = await file.read()
    temp_path.write_bytes(content)
    
    try:
        mgr = init_license_manager(
            license_file=str(temp_path),
            public_key=settings.license_public_key,
            grace_period_days=settings.license_grace_period_days
        )
        if not mgr.is_valid():
            temp_path.unlink(missing_ok=True)
            raise HTTPException(status_code=400, detail=f"Невалидная лицензия: {mgr.load_error}")
        
        log.info("License uploaded and validated successfully", customer=mgr.license.customer)
        return {"status": "ok", "message": "Лицензия успешно загружена и применена"}
    except HTTPException:
        raise
    except Exception as e:
        log.error("License upload failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Session Management Endpoints
# ============================================================================

@router.post("/session/start", response_model=SessionStartResponse)
async def start_session():
    """
    Регистрирует новую сессию пользователя.
    Вызывается фронтендом при загрузке приложения.
    
    Returns:
        session_id: Уникальный идентификатор сессии
        status: "ok" если сессия зарегистрирована
        message: Сообщение о результате
    """
    license_mgr = get_license_manager()
    if not license_mgr:
        raise HTTPException(status_code=500, detail="License manager not initialized")
    
    # Проверяем лимит пользователей
    if not license_mgr.can_add_session():
        status = license_mgr.get_status()
        raise HTTPException(
            status_code=403,
            detail=f"Превышен лимит одновременных подключений: {status.max_concurrent_users}"
        )
    
    # Генерируем уникальный session_id
    session_id = str(uuid.uuid4())
    
    # Регистрируем сессию
    license_mgr.add_session(session_id)
    
    log.info("Session started", session_id=session_id, active_sessions=license_mgr.session_tracker.active_count())
    
    return SessionStartResponse(
        session_id=session_id,
        status="ok",
        message="Сессия успешно зарегистрирована"
    )


@router.post("/session/heartbeat")
async def session_heartbeat(req: SessionHeartbeatRequest):
    """
    Обновляет heartbeat сессии.
    Вызывается фронтендом каждые 30 секунд для поддержания сессии активной.
    
    Args:
        session_id: Идентификатор сессии
    
    Returns:
        status: "ok" если heartbeat обновлён
    """
    license_mgr = get_license_manager()
    if not license_mgr:
        raise HTTPException(status_code=500, detail="License manager not initialized")
    
    # Обновляем heartbeat
    license_mgr.heartbeat(req.session_id)
    
    log.debug("Session heartbeat", session_id=req.session_id)
    
    return {"status": "ok", "message": "Heartbeat обновлён"}


@router.post("/session/end")
async def end_session(req: SessionEndRequest):
    """
    Завершает сессию пользователя.
    Вызывается фронтендом при закрытии страницы или выходе.
    
    Args:
        session_id: Идентификатор сессии
    
    Returns:
        status: "ok" если сессия завершена
    """
    license_mgr = get_license_manager()
    if not license_mgr:
        raise HTTPException(status_code=500, detail="License manager not initialized")
    
    # Удаляем сессию
    license_mgr.remove_session(req.session_id)
    
    log.info("Session ended", session_id=req.session_id, active_sessions=license_mgr.session_tracker.active_count())
    
    return {"status": "ok", "message": "Сессия завершена"}
