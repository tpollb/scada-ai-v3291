#!/usr/bin/env python3
"""
Генерация тестовых лицензий для проверки сценариев истечения срока.
"""
import sys
import uuid
import jwt
from pathlib import Path
from datetime import datetime, timedelta, timezone

PROJECT_ROOT = Path(__file__).parent.resolve()
KEYS_DIR = PROJECT_ROOT / "backend" / "core" / "license" / "keys"
PRIVATE_KEY_PATH = KEYS_DIR / "private_key.pem"

def generate_license(filename: str, days_offset: int, license_type: str, features: list):
    if not PRIVATE_KEY_PATH.exists():
        print(f"❌ ОШИБКА: Приватный ключ не найден: {PRIVATE_KEY_PATH}")
        return False
    
    private_key_pem = PRIVATE_KEY_PATH.read_bytes()
    now = datetime.now(timezone.utc)
    
    # Если days_offset отрицательный, лицензия уже истекла
    expires = now + timedelta(days=days_offset)
    
    payload = {
        "license_id": str(uuid.uuid4()),
        "customer": f"Тестовый Клиент ({filename})",
        "issued_at": (now - timedelta(days=30)).isoformat(),
        "expires_at": expires.isoformat(),
        "license_type": license_type,
        "features": features,
        "max_concurrent_users": 5,
        "grace_period_days": 3
    }
    
    token = jwt.encode(payload, private_key_pem, algorithm="RS256")
    output_path = PROJECT_ROOT / filename
    output_path.write_text(token, encoding="utf-8")
    
    print(f"✅ Создан: {filename}")
    print(f"   Истекает: {payload['expires_at']} (смещение: {days_offset} дн.)")
    print(f"   Фичи: {features}\n")
    return True

def main():
    print("Генерация тестовых лицензий...\n")
    
    # 1. Лицензия в Grace Period (истекла 1 день назад, grace period = 3 дня)
    generate_license(
        filename="license_grace_period.lic",
        days_offset=-1,
        license_type="enterprise",
        features=["health", "analytics", "deep_analysis", "energy_electricity"]
    )
    
    # 2. Лицензия ПОЛНОСТЬЮ истекла (истекла 10 дней назад)
    generate_license(
        filename="license_fully_expired.lic",
        days_offset=-10,
        license_type="enterprise",
        features=["health", "analytics"]
    )
    
    # 3. Trial лицензия (валидна, но НЕТ модуля health, чтобы проверить блокировку фич)
    generate_license(
        filename="license_trial_no_health.lic",
        days_offset=14,
        license_type="trial",
        features=["hello", "logs"] # health намеренно исключен
    )
    
    print("="*60)
    print("Готово! Теперь ты можешь подменять файл license.lic")
    print("этими тестовыми файлами и перезапускать backend.")
    print("="*60)

if __name__ == "__main__":
    sys.exit(main())