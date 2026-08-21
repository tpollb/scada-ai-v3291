#!/usr/bin/env python3
"""
Генерация пары RSA-2048 ключей для подписи лицензий.
Приватный ключ хранится у разработчика, публичный распространяется с приложением.
"""
import sys
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

def main():
    print("Генерация RSA-2048 ключей для системы лицензирования SCADA.AI...")
    
    # Создаём папку для ключей, если её нет
    keys_dir = Path(__file__).parent.parent / "backend" / "core" / "license" / "keys"
    keys_dir.mkdir(parents=True, exist_ok=True)
    
    private_key_path = keys_dir / "private_key.pem"
    public_key_path = keys_dir / "public_key.pem"
    
    # Генерируем приватный ключ
    print("  [1/3] Генерация приватного ключа (RSA-2048)...")
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    
    # Сохраняем приватный ключ (без пароля для автоматизации, храните безопасно!)
    print("  [2/3] Сохранение приватного ключа...")
    pem_private = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    private_key_path.write_bytes(pem_private)
    
    # Извлекаем и сохраняем публичный ключ
    print("  [3/3] Сохранение публичного ключа...")
    public_key = private_key.public_key()
    pem_public = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    public_key_path.write_bytes(pem_public)
    
    print("\n" + "="*60)
    print("✅ Ключи успешно сгенерированы!")
    print("="*60)
    print(f"Приватный ключ (ДЛЯ РАЗРАБОТЧИКА): {private_key_path}")
    print(f"Публичный ключ (ДЛЯ ПРИЛОЖЕНИЯ) : {public_key_path}")
    print("\n⚠️  ВАЖНО: Никогда не передавайте private_key.pem клиентам!")
    print("   Скопируйте public_key.pem в .env как LICENSE_PUBLIC_KEY или оставьте в папке keys.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
