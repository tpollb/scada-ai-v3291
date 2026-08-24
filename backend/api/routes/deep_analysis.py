"""Deep Analysis API router — connects module api.py to FastAPI.

Доступ: только admin и engineer.
"""
from fastapi import APIRouter, Depends

from modules.deep_analysis.api import router as module_router
from core.auth.dependencies import require_role
from core.auth.models import UserRole

deep_analysis_router = APIRouter(
    prefix="/api/v1",
    dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.ENGINEER))]
)
deep_analysis_router.include_router(module_router)

router = deep_analysis_router
