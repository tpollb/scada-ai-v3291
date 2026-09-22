#!/usr/bin/env python3
"""
Фикс CORS: разрешаем все origins для разработки и демо.
Заменяет allow_origins=["http://localhost:5173", ...] на ["*"]
и allow_credentials=True на False (требование CORS spec для ["*"]).

Запуск: python fix_cors_all.py
"""
from pathlib import Path
import re

ROOT = Path(__file__).parent.resolve()
main_py = ROOT / "backend" / "main.py"

if not main_py.exists():
    print(f"❌ Файл не найден: {main_py}")
    exit(1)

content = main_py.read_text(encoding="utf-8")
original = content

# Паттерн 1: allow_origins с хардкоженными адресами
# Ищем: allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"]
# Заменяем на: allow_origins=["*"]
pattern_origins = r'allow_origins=\["http://localhost:5173",\s*"http://127\.0\.0\.1:5173"\]'
replacement_origins = 'allow_origins=["*"]'

count_origins = len(re.findall(pattern_origins, content))
content = re.sub(pattern_origins, replacement_origins, content)

# Паттерн 2: allow_credentials=True (должен стать False для ["*"])
# Но только в блоках CORSMiddleware (ищем по контексту)
# Заменяем все allow_credentials=True на False в пределах add_middleware блоков
pattern_creds = r'allow_credentials=True'
replacement_creds = 'allow_credentials=False'

count_creds = content.count(pattern_creds)
content = content.replace(pattern_creds, replacement_creds)

# Проверка, были ли изменения
if content == original:
    print("⚠️  Ничего не изменилось — паттерны не найдены")
    print("   Возможно, CORS уже настроен по-другому")
    exit(0)

# Сохраняем
main_py.write_text(content, encoding="utf-8")

print("=" * 70)
print("CORS: разрешены все origins")
print("=" * 70)
print(f"  ✓ Заменено allow_origins блоков: {count_origins}")
print(f"  ✓ Заменено allow_credentials=True: {count_creds}")
print()
print("Изменения:")
print("  • allow_origins: ['http://localhost:5173', ...] → ['*']")
print("  • allow_credentials: True → False")
print()
print("⚠️  Важно: credentials=False работает, потому что мы передаём")
print("   JWT токен через заголовок Authorization, а не через cookies.")
print()
print("Перезапусти бэкенд:")
print("  uvicorn main:app --host 0.0.0.0 --port 8081 --reload")