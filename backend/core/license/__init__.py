"""License module — система лицензирования SCADA.AI"""
from .manager import (
    LicenseManager,
    get_license_manager,
    set_license_manager,
    init_license_manager,
)
from .models import License, LicenseStatus, LicenseType
from .validator import LicenseValidator, LicenseValidationError
from .session_tracker import SessionTracker

__all__ = [
    "LicenseManager",
    "get_license_manager",
    "set_license_manager",
    "init_license_manager",
    "License",
    "LicenseStatus",
    "LicenseType",
    "LicenseValidator",
    "LicenseValidationError",
    "SessionTracker",
]
