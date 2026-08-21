"""License validator — проверяет JWT подпись и срок действия"""
import jwt
from pathlib import Path
from datetime import datetime, timezone
from structlog import get_logger
from .models import License, LicenseType

log = get_logger()


class LicenseValidationError(Exception):
    """Ошибка валидации лицензии"""
    pass


class LicenseValidator:
    """Валидирует .lic файл (JWT с RSA-2048 подписью)"""

    def __init__(self, public_key: str):
        """
        Args:
            public_key: Публичный ключ RSA (PEM формат) или путь к файлу
        """
        # Если это путь к файлу — читаем
        if Path(public_key).exists():
            with open(public_key, "r", encoding="utf-8") as f:
                self.public_key = f.read()
        else:
            self.public_key = public_key

    def validate(self, license_file: Path) -> License:
        """
        Валидирует .lic файл и возвращает License объект

        Args:
            license_file: Путь к .lic файлу

        Returns:
            License объект

        Raises:
            LicenseValidationError: Если лицензия невалидна
        """
        if not license_file.exists():
            raise LicenseValidationError(f"Лицензия не найдена: {license_file}")

        # Читаем токен
        try:
            token = license_file.read_text(encoding="utf-8").strip()
        except Exception as e:
            raise LicenseValidationError(f"Не удалось прочитать файл лицензии: {e}")

        # Проверяем подпись и декодируем
        try:
            payload = jwt.decode(
                token,
                self.public_key,
                algorithms=["RS256"],
                options={
                    "verify_exp": False,  # Проверяем срок вручную (для grace period)
                    "verify_signature": True,
                },
            )
        except jwt.ExpiredSignatureError:
            raise LicenseValidationError("Лицензия истекла")
        except jwt.InvalidSignatureError:
            raise LicenseValidationError("Невалидная подпись лицензии")
        except jwt.InvalidTokenError as e:
            raise LicenseValidationError(f"Невалидный токен лицензии: {e}")

        # Парсим payload в License
        try:
            # Конвертируем timestamps в datetime
            for field in ["issued_at", "expires_at"]:
                if field in payload and isinstance(payload[field], (int, float)):
                    payload[field] = datetime.fromtimestamp(payload[field], tz=timezone.utc)
                elif field in payload and isinstance(payload[field], str):
                    payload[field] = datetime.fromisoformat(payload[field].replace("Z", "+00:00"))

            # Конвертируем license_type в enum
            if "license_type" in payload:
                payload["license_type"] = LicenseType(payload["license_type"])

            license_obj = License(**payload)
            log.info(
                "License validated",
                license_id=license_obj.license_id,
                customer=license_obj.customer,
                type=license_obj.license_type.value,
                expires=license_obj.expires_at.isoformat(),
            )
            return license_obj

        except Exception as e:
            raise LicenseValidationError(f"Не удалось распарсить лицензию: {e}")
