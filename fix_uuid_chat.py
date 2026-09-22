#!/usr/bin/env python3
"""
Фикс crypto.randomUUID в chat.ts — добавляет полифилл для non-secure contexts.

Запуск: python fix_uuid_chat.py
"""
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
chat_ts = ROOT / "frontend" / "src" / "stores" / "chat.ts"

if not chat_ts.exists():
    print(f"❌ Файл не найден: {chat_ts}")
    exit(1)

content = chat_ts.read_text(encoding="utf-8")

# Проверяем, не применено ли уже
if "generateId" in content and "crypto.randomUUID()" not in content:
    print("⚠️  Уже применено — ничего делать не нужно")
    exit(0)

if "crypto.randomUUID()" not in content:
    print("⚠️  crypto.randomUUID() не найден в файле")
    exit(0)

# Полифилл
POLYFILL = """// Генерация ID сообщений с фолбэком для non-secure contexts
function generateId(): string {
    if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
        return crypto.randomUUID()
    }
    // Fallback: Math.random + Date.now (достаточно для ID сообщений)
    return `${Date.now()}-${Math.random().toString(36).slice(2, 11)}`
}

"""

# Добавляем полифилл после импортов
lines = content.split('\n')
insert_pos = 0
for i, line in enumerate(lines):
    if line.strip().startswith('import '):
        insert_pos = i + 1
    elif line.strip() and not line.strip().startswith('//') and insert_pos > 0:
        break

# Вставляем полифилл
lines.insert(insert_pos, POLYFILL.rstrip())

# Собираем обратно
content = '\n'.join(lines)

# Заменяем crypto.randomUUID() на generateId()
content = content.replace("crypto.randomUUID()", "generateId()")

# Сохраняем
chat_ts.write_text(content, encoding="utf-8")

print("=" * 60)
print("Фикс crypto.randomUUID в chat.ts")
print("=" * 60)
print("  ✓ Добавлена функция generateId() с фолбэком")
print("  ✓ Заменён вызов crypto.randomUUID()")
print()
print("Теперь чат работает в:")
print("  • http://localhost:5173  (secure context)")
print("  • http://172.27.10.97:5173  (non-secure context)")
print()
print("Обнови страницу (Ctrl+Shift+R) и проверь чат с другого компьютера.")