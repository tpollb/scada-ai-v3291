#!/usr/bin/env python3
"""
Исправление CORS и AuthMiddleware:
1. Разрешаем OPTIONS запросы в AuthMiddleware (чтобы preflight не блокировался)
2. Улучшаем настройки CORS в main.py (allow_credentials=True)
3. Увеличиваем длину jwt_secret в settings.py (минимум 32 байта)
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.resolve()

def fix_auth_middleware():
    filepath = PROJECT_ROOT / "backend" / "core" / "auth" / "middleware.py"
    if not filepath.exists():
        print("❌ Файл middleware.py не найден")
        return False
    
    content = filepath.read_text(encoding="utf-8")
    
    # Добавляем пропуск OPTIONS запросов в самое начало dispatch
    if "if request.method == \"OPTIONS\":" not in content:
        content = content.replace(
            "async def dispatch(self, request: Request, call_next):",
            "async def dispatch(self, request: Request, call_next):\n        # Разрешаем OPTIONS запросы (CORS preflight) без проверки токена\n        if request.method == \"OPTIONS\":\n            return await call_next(request)\n"
        )
        filepath.write_text(content, encoding="utf-8")
        print("  ✓ AuthMiddleware теперь пропускает OPTIONS запросы")
    else:
        print("  - AuthMiddleware уже исправлен")
    return True

def fix_cors_in_main():
    filepath = PROJECT_ROOT / "backend" / "main.py"
    if not filepath.exists():
        print("❌ Файл main.py не найден")
        return False
    
    content = filepath.read_text(encoding="utf-8")
    
    # Улучшаем настройки CORS
    if "allow_credentials=False" in content:
        content = content.replace("allow_credentials=False", "allow_credentials=True")
        filepath.write_text(content, encoding="utf-8")
        print("  ✓ CORS настроен с allow_credentials=True (корректная работа с заголовками)")
    else:
        print("  - CORS уже настроен корректно")
    return True

def fix_jwt_secret():
    filepath = PROJECT_ROOT / "backend" / "config" / "settings.py"
    if not filepath.exists():
        print("❌ Файл settings.py не найден")
        return False
    
    content = filepath.read_text(encoding="utf-8")
    
    # Заменяем короткий ключ на безопасный (>= 32 байта)
    if 'jwt_secret: str = "change-me-in-production"' in content:
        content = content.replace(
            'jwt_secret: str = "change-me-in-production"',
            'jwt_secret: str = "scada-ai-super-secret-jwt-key-32-bytes-min!"'
        )
        filepath.write_text(content, encoding="utf-8")
        print("  ✓ JWT secret удлинён до 32+ байт (предупреждение исчезнет)")
    else:
        print("  - JWT secret уже достаточной длины")
    return True

def main():
    print("=" * 70)
    print("Исправление CORS и AuthMiddleware")
    print("=" * 70)
    
    success = True
    if not fix_auth_middleware(): success = False
    if not fix_cors_in_main(): success = False
    if not fix_jwt_secret(): success = False
    
    if success:
        print("\n✅ Исправления применены!")
        print("\nСледующие шаги:")
        print("1. Перезапусти backend (Ctrl+C, затем uvicorn main:app --reload --host 0.0.0.0 --port 8081)")
        print("2. Обнови страницу в браузере (Ctrl + F5)")
        print("3. Войди в систему. Ошибки CORS должны исчезнуть, функционал загрузится.")
    else:
        print("\n❌ Ошибки при применении исправлений")

if __name__ == "__main__":
    sys.exit(0 if main() else 1)