#!/usr/bin/env python3
"""
Генерация тестового файла лицензии (.lic) для SCADA.AI
Использует приватный ключ для подписи JWT-токена.
"""
import sys
import uuid
import jwt
from pathlib import Path
from datetime import datetime, timedelta, timezone

def main():
    print("Генерация тестовой лицензии SCADA.AI...")
    
    # Пути
    keys_dir = Path(__file__).parent.parent / "backend" / "core" / "license" / "keys"
    private_key_path = keys_dir / "private_key.pem"
    output_lic_path = Path(__file__).parent.parent / "license.lic"
    
    if not private_key_path.exists():
        print(f"❌ ОШИБКА: Приватный ключ не найден: {private_key_path}")
        print("   Сначала запустите: python scripts/generate_keys.py")
        return 1
    
    # Читаем приватный ключ
    private_key_pem = private_key_path.read_bytes()
    
    # Формируем payload лицензии
    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=365)  # Лицензия на 1 год
    
    payload = {
        "license_id": str(uuid.uuid4()),
        "customer": "ООО Тестовая Компания",
        "issued_at": now.isoformat(),
        "expires_at": expires.isoformat(),
        "license_type": "enterprise",
        "features": ["health", "analytics", "deep_analysis", "energy_electricity", "energy_water", "energy_heat", "logs"],
        "max_concurrent_users": 10,
        "grace_period_days": 3
    }
    
    print("  [1/2] Формирование payload...")
    print(f"   Клиент: {payload['customer']}")
    print(f"   Тип: {payload['license_type']}")
    print(f"   Истекает: {payload['expires_at']}")
    
    # Подписываем токен
    print("  [2/2] Подпись токена (RS256)...")
    try:
        token = jwt.encode(payload, private_key_pem, algorithm="RS256")
    except Exception as e:
        print(f"❌ ОШИБКА подписи: {e}")
        print("   Убедитесь, что установлен PyJWT: pip install PyJWT[crypto]")
        return 1
    
    # Сохраняем в файл
    output_lic_path.write_text(token, encoding="utf-8")
    
    print("\n" + "="*60)
    print("✅ Лицензия успешно сгенерирована!")
    print("="*60)
    print(f"Файл лицензии: {output_lic_path}")
    print("\nДля проверки поместите этот файл в корень проекта")
    print("и укажите в .env: LICENSE_FILE=license.lic")
    return 0

if __name__ == "__main__":
    sys.exit(main())
