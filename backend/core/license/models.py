"""License models — Pydantic schemas for license validation"""
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from typing import Optional


class LicenseType(str, Enum):
    """Типы лицензий с разным набором фич"""
    TRIAL = "trial"           # hello, health, logs (14 дней)
    BASIC = "basic"           # + energy_* (1 год)
    STANDARD = "standard"     # + analytics (1 год)
    ENTERPRISE = "enterprise" # + deep_analysis, без лимитов (1-3 года)


class License(BaseModel):
    """Структура лицензии (payload JWT)"""
    license_id: str = Field(..., description="Уникальный ID лицензии (UUID)")
    customer: str = Field(..., description="Название организации")
    issued_at: datetime = Field(..., description="Дата выдачи")
    expires_at: datetime = Field(..., description="Дата истечения")
    license_type: LicenseType = Field(..., description="Тип лицензии")
    features: list[str] = Field(default_factory=list, description="Доступные модули/фичи")
    max_concurrent_users: int = Field(default=10, description="Максимум одновременных пользователей")
    grace_period_days: int = Field(default=3, description="Grace period после истечения (дни)")

    class Config:
        json_schema_extra = {
            "example": {
                "license_id": "550e8400-e29b-41d4-a716-446655440000",
                "customer": "ООО Ромашка",
                "issued_at": "2026-01-01T00:00:00Z",
                "expires_at": "2027-01-01T00:00:00Z",
                "license_type": "enterprise",
                "features": ["health", "analytics", "deep_analysis", "energy"],
                "max_concurrent_users": 10,
                "grace_period_days": 3,
            }
        }


class LicenseStatus(BaseModel):
    """Текущий статус лицензии (для API response)"""
    valid: bool = Field(..., description="Лицензия валидна (не истекла или в grace period)")
    expired: bool = Field(..., description="Лицензия истекла (после grace period)")
    in_grace_period: bool = Field(..., description="Находится в grace period")
    days_remaining: int = Field(..., description="Дней до истечения (может быть отрицательным)")
    license_type: LicenseType = Field(..., description="Тип лицензии")
    features: list[str] = Field(default_factory=list, description="Доступные фичи")
    customer: str = Field(..., description="Клиент")
    max_concurrent_users: int = Field(..., description="Лимит пользователей")
    current_users: int = Field(default=0, description="Текущее количество пользователей")
