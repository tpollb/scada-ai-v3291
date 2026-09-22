#!/usr/bin/env python3
"""
Сканер старых версий в проекте.
Ищет все вхождения версий 3.3.x.x, 3.2.x.x и показывает контекст.

Запуск: python scan_versions.py
"""
from pathlib import Path
import re

ROOT = Path(__file__).parent.resolve()

# Расширения файлов для сканирования
EXTENSIONS = ['.svelte', '.ts', '.js', '.py', '.json', '.yaml', '.yml', '.md', '.txt', '.toml']

# Старые версии для поиска (регулярки)
OLD_VERSIONS = [
    r'3\.3\.2\.3',
    r'3\.3\.2\.2',
    r'3\.3\.2\.1',
    r'3\.3\.2\.0',
    r'3\.3\.1\.1',
    r'3\.3\.0\.1\.1',
    r'3\.3\.0',
    r'3\.2\.9\.1',
    r'3\.2\.9',
    r'3\.2\.5',
]

# Исключения (файлы, где старые версии — это нормально)
EXCLUDE_FILES = {
    'CHANGELOG.md',           # история версий
    'Project_full_description.md',  # обновим отдельно если надо
}

# Исключения (папки)
EXCLUDE_DIRS = {'node_modules', '.git', 'venv', '__pycache__', 'dist', '.svelte-kit', 'build'}

def should_scan(path: Path) -> bool:
    for exc in EXCLUDE_DIRS:
        if exc in path.parts:
            return False
    if path.name in EXCLUDE_FILES:
        return False
    return path.suffix.lower() in EXTENSIONS

print("=" * 80)
print(f"СКАНИРОВАНИЕ СТАРЫХ ВЕРСИЙ: {ROOT}")
print("=" * 80)

findings = []
file_count = 0

for path in ROOT.rglob('*'):
    if not path.is_file() or not should_scan(path):
        continue
    
    file_count += 1
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue
    
    lines = content.split('\n')
    
    for line_num, line in enumerate(lines, 1):
        for pattern in OLD_VERSIONS:
            if re.search(pattern, line):
                # Контекст
                start = max(0, line_num - 2)
                end = min(len(lines), line_num + 1)
                context = []
                for i in range(start, end):
                    marker = ">>>" if i == line_num - 1 else "   "
                    context.append(f"  {marker} L{i+1}: {lines[i][:120]}")
                
                findings.append({
                    'file': str(path.relative_to(ROOT)),
                    'line': line_num,
                    'version': pattern.replace(r'\.', '.'),
                    'text': line.strip()[:120],
                    'context': context
                })
                break  # одна версия на строку

print(f"\nПросканировано файлов: {file_count}")
print(f"Найдено вхождений старых версий: {len(findings)}")

if findings:
    print("\n" + "=" * 80)
    print("НАЙДЕННЫЕ СТАРЫЕ ВЕРСИИ")
    print("=" * 80)
    
    # Группируем по файлам
    by_file = {}
    for f in findings:
        by_file.setdefault(f['file'], []).append(f)
    
    for filepath, file_findings in sorted(by_file.items()):
        versions = sorted(set(f['version'] for f in file_findings))
        print(f"\n📄 {filepath}  [версии: {', '.join(versions)}]")
        print(f"   Вхождений: {len(file_findings)}")
        for f in file_findings:
            print(f"\n   Строка {f['line']} [{f['version']}]:")
            for ctx_line in f['context']:
                print(f"   {ctx_line}")

# === Итог ===
print("\n" + "=" * 80)
print("ИТОГ")
print("=" * 80)
if not findings:
    print("✅ Старых версий не найдено")
else:
    unique_files = sorted(set(f['file'] for f in findings))
    print(f"❌ Файлов со старыми версиями: {len(unique_files)}")
    for f in unique_files:
        file_findings = [x for x in findings if x['file'] == f]
        versions = sorted(set(x['version'] for x in file_findings))
        print(f"   • {f}  [{', '.join(versions)}]")

print("\nПришли мне вывод — я дам точечный патч-скрипт под каждый файл.")