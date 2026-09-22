#!/usr/bin/env python3
"""
Сканер использования crypto.randomUUID во фронтенде.
Ищет все вхождения и показывает контекст для безопасного патча.

Запуск: python scan_uuid.py
"""
from pathlib import Path
import re

ROOT = Path(__file__).parent.resolve()
FRONTEND_SRC = ROOT / "frontend" / "src"

if not FRONTEND_SRC.exists():
    print(f"❌ Папка не найдена: {FRONTEND_SRC}")
    exit(1)

# Расширения для сканирования
EXTENSIONS = ['.ts', '.svelte', '.js']

# Паттерны для поиска
PATTERNS = [
    (r'crypto\.randomUUID\s*\(', 'crypto.randomUUID()'),
    (r'window\.crypto\.randomUUID\s*\(', 'window.crypto.randomUUID()'),
    (r'globalThis\.crypto\.randomUUID\s*\(', 'globalThis.crypto.randomUUID()'),
]

# Исключения
EXCLUDE_DIRS = {'node_modules', '.git', 'dist', '.svelte-kit', 'build'}

def should_scan(path: Path) -> bool:
    for exc in EXCLUDE_DIRS:
        if exc in path.parts:
            return False
    return path.suffix.lower() in EXTENSIONS

print("=" * 80)
print(f"СКАНИРОВАНИЕ: {FRONTEND_SRC}")
print("=" * 80)

findings = []
files_with_generate_id = []
file_count = 0

for path in FRONTEND_SRC.rglob('*'):
    if not path.is_file() or not should_scan(path):
        continue
    
    file_count += 1
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue
    
    lines = content.split('\n')
    
    # Проверяем, есть ли уже полифилл (частичный фикс)
    has_generate_id = 'function generateId' in content or 'const generateId' in content
    if has_generate_id:
        files_with_generate_id.append(str(path.relative_to(ROOT)))
    
    # Ищем вхождения
    for line_num, line in enumerate(lines, 1):
        for pattern, description in PATTERNS:
            if re.search(pattern, line):
                # Контекст: 2 строки до и после
                start = max(0, line_num - 3)
                end = min(len(lines), line_num + 2)
                context = []
                for i in range(start, end):
                    marker = ">>>" if i == line_num - 1 else "   "
                    context.append(f"  {marker} L{i+1}: {lines[i][:120]}")
                
                findings.append({
                    'file': str(path.relative_to(ROOT)),
                    'line': line_num,
                    'type': description,
                    'text': line.strip()[:120],
                    'context': context
                })

print(f"\nПросканировано файлов: {file_count}")
print(f"Найдено вхождений: {len(findings)}")

if files_with_generate_id:
    print(f"Файлов с уже добавленным generateId: {len(files_with_generate_id)}")

# === Детальный вывод ===
if findings:
    print("\n" + "=" * 80)
    print("НАЙДЕННЫЕ ИСПОЛЬЗОВАНИЯ (с контекстом)")
    print("=" * 80)
    
    # Группируем по файлам
    by_file = {}
    for f in findings:
        by_file.setdefault(f['file'], []).append(f)
    
    for filepath, file_findings in sorted(by_file.items()):
        has_fix = filepath in files_with_generate_id
        status = "⚠️  УЖЕ ЕСТЬ generateId" if has_fix else "❌ НУЖЕН ФИКС"
        print(f"\n📄 {filepath}  [{status}]")
        print(f"   Вхождений: {len(file_findings)}")
        for f in file_findings:
            print(f"\n   Строка {f['line']} [{f['type']}]:")
            for ctx_line in f['context']:
                print(f"   {ctx_line}")
else:
    print("\n✅ Вхождений не найдено!")

# === Проверка других источников UUID ===
print("\n" + "=" * 80)
print("ПРОВЕРКА АЛЬТЕРНАТИВНЫХ ГЕНЕРАТОРОВ")
print("=" * 80)

alt_patterns = [
    (r'uuidv4|uuid\.v4', 'uuid library'),
    (r'Math\.random.*toString\(16\)', 'Math.random hex'),
    (r'Date\.now\(\).*toString\(36\)', 'Date.now base36'),
]

alt_findings = []
for path in FRONTEND_SRC.rglob('*'):
    if not path.is_file() or not should_scan(path):
        continue
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue
    
    for pattern, description in alt_patterns:
        if re.search(pattern, content):
            alt_findings.append((str(path.relative_to(ROOT)), description))

if alt_findings:
    print("\nНайдены альтернативные генераторы:")
    for filepath, description in alt_findings:
        print(f"  📄 {filepath} — {description}")
else:
    print("\n✅ Альтернативных генераторов не найдено")

# === Итог ===
print("\n" + "=" * 80)
print("ИТОГ")
print("=" * 80)
if not findings:
    print("✅ crypto.randomUUID нигде не используется — патч не нужен")
else:
    needs_fix = [f['file'] for f in findings if f['file'] not in files_with_generate_id]
    unique_files = sorted(set(needs_fix))
    print(f"❌ Файлов, требующих фикса: {len(unique_files)}")
    for f in unique_files:
        print(f"   • {f}")

print("\nПришли мне вывод этого скрипта — дам точный патч.")