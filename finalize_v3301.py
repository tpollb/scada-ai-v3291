#!/usr/bin/env python3
"""
SCADA.AI v3.3.0.1 — Финализация релиза (исправленная версия)
Все файлы документации находятся в /backend/docs/

Запуск: python finalize_v3301_fixed.py
"""
import sys
import re
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.resolve()
DOCS_DIR = PROJECT_ROOT / "backend" / "docs"
NEW_VERSION = "3.3.0.1"
TODAY = datetime.now().strftime("%Y-%m-%d")

# ============================================================================
# 1. Обновление версий
# ============================================================================

def update_version_in_file(filepath: Path, pattern: str, replacement: str) -> bool:
    if not filepath.exists():
        print(f"  !!! Файл не найден: {filepath.relative_to(PROJECT_ROOT)}")
        return False
    content = filepath.read_text(encoding="utf-8")
    new_content = re.sub(pattern, replacement, content)
    if content != new_content:
        filepath.write_text(new_content, encoding="utf-8")
        print(f"  ✓ Обновлена версия: {filepath.relative_to(PROJECT_ROOT)}")
        return True
    else:
        print(f"  - Без изменений: {filepath.relative_to(PROJECT_ROOT)}")
        return False


def update_versions():
    print("\n[1/3] Обновление версий в файлах...")
    
    # Backend
    update_version_in_file(
        PROJECT_ROOT / "backend" / "config" / "settings.py",
        r'app_version:\s*str\s*=\s*"[^"]+"',
        f'app_version: str = "{NEW_VERSION}"'
    )
    
    update_version_in_file(
        PROJECT_ROOT / "backend" / "main.py",
        r'SCADA\.AI v\d+\.\d+\.\d+',
        f'SCADA.AI v{NEW_VERSION}'
    )
    
    # Frontend
    update_version_in_file(
        PROJECT_ROOT / "frontend" / "src" / "routes" / "Home.svelte",
        r'v3\.\d+\.\d+',
        f'v{NEW_VERSION}'
    )
    
    update_version_in_file(
        PROJECT_ROOT / "frontend" / "src" / "routes" / "Config.svelte",
        r'v3\.\d+\.\d+',
        f'v{NEW_VERSION}'
    )
    
    # Документация (все файлы в backend/docs/)
    update_version_in_file(
        DOCS_DIR / "Project_full_description.md",
        r'Версия:\s*\d+\.\d+\.\d+',
        f'Версия: {NEW_VERSION}'
    )
    update_version_in_file(
        DOCS_DIR / "Project_full_description.md",
        r'SCADA\.AI v\d+\.\d+\.\d+',
        f'SCADA.AI v{NEW_VERSION}'
    )
    
    update_version_in_file(
        DOCS_DIR / "ARCHITECTURE.md",
        r'Версия:\s*\d+\.\d+\.\d+',
        f'Версия: {NEW_VERSION}'
    )
    update_version_in_file(
        DOCS_DIR / "ARCHITECTURE.md",
        r'SCADA\.AI v\d+\.\d+\.\d+',
        f'SCADA.AI v{NEW_VERSION}'
    )
    
    update_version_in_file(
        DOCS_DIR / "README.md",
        r'SCADA\.AI v\d+\.\d+\.\d+',
        f'SCADA.AI v{NEW_VERSION}'
    )
    update_version_in_file(
        DOCS_DIR / "README.md",
        r'Версия:\s*\d+\.\d+\.\d+',
        f'Версия: {NEW_VERSION}'
    )


# ============================================================================
# 2. Обновление README.md
# ============================================================================

def update_readme():
    print("\n[2/3] Обновление README.md...")
    
    readme = DOCS_DIR / "README.md"
    if not readme.exists():
        print("  !!! README.md не найден в backend/docs/")
        return False
    
    content = readme.read_text(encoding="utf-8")
    
    # 1. Обновляем заголовок
    content = re.sub(
        r'# SCADA\.AI v\d+\.\d+\.\d+',
        f'# SCADA.AI v{NEW_VERSION}',
        content
    )
    
    # 2. Добавляем раздел о лицензировании после "Возможности"
    if "🔐 Система лицензирования" not in content:
        licensing_section = """

## 🔐 Система лицензирования

SCADA.AI v3.3.0.1 включает полноценную систему лицензирования для управления доступом к функционалу:

- **JWT-токены с RSA-2048 подписью** — защита от модификации
- **Grace Period** — 3 дня после истечения лицензии для продления
- **Feature Gates** — модули загружаются только если разрешены лицензией
- **Контроль сессий** — ограничение одновременных подключений
- **Offline работа** — не требует подключения к серверу разработчика

### Типы лицензий

| Тип | Доступные модули | Срок |
|-----|------------------|------|
| `trial` | `hello`, `health`, `logs` | 14 дней |
| `basic` | + `energy_*` | 1 год |
| `standard` | + `analytics` | 1 год |
| `enterprise` | + `deep_analysis` | 1–3 года |

Подробная документация: [docs/LICENSING.md](docs/LICENSING.md)

"""
        # Вставляем перед "## Модули"
        content = content.replace("\n## Модули", licensing_section + "## Модули")
    
    # 3. Обновляем дату релиза
    content = re.sub(
        r'Дата релиза:\s*\d{4}-\d{2}-\d{2}',
        f'Дата релиза: {TODAY}',
        content
    )
    
    # 4. Обновляем версию в футере
    content = re.sub(
        r'Версия:\s*\d+\.\d+\.\d+',
        f'Версия: {NEW_VERSION}',
        content
    )
    
    readme.write_text(content, encoding="utf-8")
    print("  ✓ README.md обновлён")
    return True


# ============================================================================
# 3. Обновление MODULES.md
# ============================================================================

def update_modules():
    print("\n[3/3] Обновление MODULES.md...")
    
    modules = DOCS_DIR / "MODULES.md"
    if not modules.exists():
        print("  !!! MODULES.md не найден в backend/docs/")
        return False
    
    content = modules.read_text(encoding="utf-8")
    
    # Обновляем версию если есть
    content = re.sub(
        r'v\d+\.\d+\.\d+',
        f'v{NEW_VERSION}',
        content
    )
    
    modules.write_text(content, encoding="utf-8")
    print("  ✓ MODULES.md обновлён")
    return True


# ============================================================================
# Main
# ============================================================================

def main() -> int:
    print("=" * 70)
    print(f"SCADA.AI v{NEW_VERSION} — Финализация релиза")
    print("=" * 70)
    print(f"\nКорень проекта: {PROJECT_ROOT}")
    print(f"Папка документации: {DOCS_DIR.relative_to(PROJECT_ROOT)}")
    print(f"Дата: {TODAY}")
    
    update_versions()
    update_readme()
    update_modules()
    
    print("\n" + "=" * 70)
    print(f"✅ ФИНАЛИЗАЦИЯ v{NEW_VERSION} ЗАВЕРШЕНА УСПЕШНО!")
    print("=" * 70)
    print("\nСледующие шаги (Git):")
    print("  git add .")
    print(f'  git commit -m "chore: release v{NEW_VERSION} — documentation update"')
    print(f"  git tag -a v{NEW_VERSION} -m \"Release version {NEW_VERSION}\"")
    print("  git push origin main")
    print(f"  git push origin v{NEW_VERSION}")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())