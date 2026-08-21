"""License manager — загрузка, проверка, кэш лицензии"""
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
from structlog import get_logger
from .models import License, LicenseStatus, LicenseType
from .validator import LicenseValidator, LicenseValidationError
from .session_tracker import SessionTracker

log = get_logger()


class LicenseManager:
    """Управляет лицензией: загрузка, проверка, feature gates"""

    def __init__(self, license_file: Path, public_key: str, grace_period_days: int = 3):
        self.license_file = Path(license_file)
        self.validator = LicenseValidator(public_key)
        self.grace_period_days = grace_period_days
        self._license: Optional[License] = None
        self._load_error: Optional[str] = None
        self.session_tracker = SessionTracker()

    def load(self) -> bool:
        """
        Загружает и валидирует лицензию

        Returns:
            True если лицензия загружена успешно
        """
        try:
            self._license = self.validator.validate(self.license_file)
            self._load_error = None
            log.info(
                "License loaded successfully",
                license_id=self._license.license_id,
                customer=self._license.customer,
                expires=self._license.expires_at.isoformat(),
            )
            return True
        except LicenseValidationError as e:
            self._license = None
            self._load_error = str(e)
            log.error("License validation failed", error=str(e))
            return False
        except Exception as e:
            self._license = None
            self._load_error = f"Unexpected error: {e}"
            log.error("License load failed", error=str(e))
            return False

    def get_status(self) -> LicenseStatus:
        """Возвращает текущий статус лицензии"""
        if not self._license:
            return LicenseStatus(
                valid=False,
                expired=True,
                in_grace_period=False,
                days_remaining=0,
                license_type=LicenseType.TRIAL,
                features=[],
                customer="Unknown",
                max_concurrent_users=0,
                current_users=self.session_tracker.active_count(),
            )

        now = datetime.now(timezone.utc)
        expires = self._license.expires_at

        # Убедимся что expires в UTC
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)

        days_remaining = (expires - now).days
        expired = now > expires
        in_grace_period = expired and (now - expires).days < self.grace_period_days

        # Лицензия валидна если:
        # 1. Не истекла ИЛИ
        # 2. В grace period
        valid = not expired or in_grace_period

        return LicenseStatus(
            valid=valid,
            expired=expired and not in_grace_period,
            in_grace_period=in_grace_period,
            days_remaining=days_remaining,
            license_type=self._license.license_type,
            features=self._license.features,
            customer=self._license.customer,
            max_concurrent_users=self._license.max_concurrent_users,
            current_users=self.session_tracker.active_count(),
        )

    def is_valid(self) -> bool:
        """Проверяет валидность лицензии (не истекла или в grace period)"""
        return self.get_status().valid

    def is_expired(self) -> bool:
        """Проверяет истекла ли лицензия (после grace period)"""
        return self.get_status().expired

    def in_grace_period(self) -> bool:
        """Проверяет находится ли лицензия в grace period"""
        return self.get_status().in_grace_period

    def has_feature(self, feature: str) -> bool:
        """Проверяет доступность фичи/модуля"""
        if not self._license:
            return False

        # Базовые модули всегда доступны
        if feature in ["hello", "logs"]:
            return True

        return feature in self._license.features

    def get_features(self) -> list[str]:
        """Возвращает список доступных фич"""
        if not self._license:
            return []
        return self._license.features

    def can_add_session(self) -> bool:
        """Проверяет можно ли добавить новую сессию"""
        if not self._license:
            return False
        return self.session_tracker.active_count() < self._license.max_concurrent_users

    def add_session(self, session_id: str) -> bool:
        """Добавляет сессию. Returns True если успешно"""
        if not self.can_add_session():
            return False
        self.session_tracker.add(session_id)
        return True

    def remove_session(self, session_id: str):
        """Удаляет сессию"""
        self.session_tracker.remove(session_id)

    def heartbeat(self, session_id: str):
        """Обновляет heartbeat сессии"""
        self.session_tracker.heartbeat(session_id)

    @property
    def license(self) -> Optional[License]:
        """Возвращает текущую лицензию (или None)"""
        return self._license

    @property
    def load_error(self) -> Optional[str]:
        """Возвращает ошибку загрузки (если была)"""
        return self._load_error


# Singleton
_manager: Optional[LicenseManager] = None


def get_license_manager() -> Optional[LicenseManager]:
    """Получить глобальный LicenseManager"""
    return _manager


def set_license_manager(manager: LicenseManager):
    """Установить глобальный LicenseManager"""
    global _manager
    _manager = manager


def init_license_manager(license_file: str, public_key: str, grace_period_days: int = 3) -> LicenseManager:
    """Инициализировать и загрузить LicenseManager"""
    manager = LicenseManager(
        license_file=Path(license_file),
        public_key=public_key,
        grace_period_days=grace_period_days,
    )
    manager.load()
    set_license_manager(manager)
    return manager
