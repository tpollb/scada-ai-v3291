#!/usr/bin/env python3
"""
SCADA.AI v3.3.1.1 — Финализация релиза
1. Обновление версии во всех файлах до 3.3.1.1
2. Обновление CHANGELOG.md с описанием новых функций
3. Подготовка к Git push

Запуск: python finalize_v3311.py
"""
import sys
import re
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.resolve()
DOCS_DIR = PROJECT_ROOT / "backend" / "docs"
NEW_VERSION = "3.3.1.1"
TODAY = datetime.now().strftime("%Y-%m-%d")

def update_version_in_file(filepath: Path, pattern: str, replacement: str) -> bool:
    if not filepath.exists():
        print(f"  ⚠️ Файл не найден: {filepath.relative_to(PROJECT_ROOT)}")
        return False
    content = filepath.read_text(encoding="utf-8")
    new_content = re.sub(pattern, replacement, content)
    if content != new_content:
        filepath.write_text(new_content, encoding="utf-8")
        print(f"  ✓ {filepath.relative_to(PROJECT_ROOT)}")
        return True
    return False

def update_versions():
    print("\n[1/2] Обновление версий до 3.3.1.1...")
    
    # Backend
    update_version_in_file(PROJECT_ROOT / "backend" / "config" / "settings.py", r'app_version:\s*str\s*=\s*"[^"]+"', f'app_version: str = "{NEW_VERSION}"')
    update_version_in_file(PROJECT_ROOT / "backend" / "main.py", r'SCADA\.AI v\d+(?:\.\d+)*', f'SCADA.AI v{NEW_VERSION}')
    
    # Frontend
    update_version_in_file(PROJECT_ROOT / "frontend" / "src" / "routes" / "Home.svelte", r'v\d+(?:\.\d+)*', f'v{NEW_VERSION}')
    update_version_in_file(PROJECT_ROOT / "frontend" / "src" / "routes" / "Config.svelte", r'v\d+(?:\.\d+)*', f'v{NEW_VERSION}')
    
    # Docs & Descriptions
    update_version_in_file(PROJECT_ROOT / "Project_full_description.md", r'Версия:\s*\d+(?:\.\d+)*', f'Версия: {NEW_VERSION}')
    update_version_in_file(PROJECT_ROOT / "Project_full_description.md", r'SCADA\.AI v\d+(?:\.\d+)*', f'SCADA.AI v{NEW_VERSION}')
    update_version_in_file(DOCS_DIR / "ARCHITECTURE.md", r'Версия:\s*\d+(?:\.\d+)*', f'Версия: {NEW_VERSION}')
    update_version_in_file(DOCS_DIR / "README.md", r'SCADA\.AI v\d+(?:\.\d+)*', f'SCADA.AI v{NEW_VERSION}')
    update_version_in_file(DOCS_DIR / "README.md", r'Версия:\s*\d+(?:\.\d+)*', f'Версия: {NEW_VERSION}')

def update_changelog():
    print("\n[2/2] Обновление CHANGELOG.md...")
    changelog_path = DOCS_DIR / "CHANGELOG.md"
    
    new_entry = f"""## [{NEW_VERSION}] - {TODAY}

### ✨ Добавлено
- **Вкладка "Лицензия" в Конфигураторе:**
  - Полноценный UI для просмотра статуса лицензии (клиент, тип, срок, сессии, доступные модули).
  - Drag & Drop зона и кнопка для загрузки нового файла `.lic`.
  - Валидация формата и размера файла на стороне клиента.
  - Автоматическое обновление статуса после успешной загрузки.

### 🔧 Технические улучшения
- Добавлена функция `uploadLicense` в `frontend/src/stores/license.ts`.
- Создан компонент `LicensePanel.svelte` и интегрирован в `Config.svelte` как отдельная вкладка.
- Улучшена обработка ошибок при загрузке лицензии через UI.

"""
    
    if changelog_path.exists():
        content = changelog_path.read_text(encoding="utf-8")
        if f"[{NEW_VERSION}]" not in content:
            if "Changelog" in content:
                content = content.replace("Changelog", f"Changelog\n\n{new_entry}")
            else:
                content = new_entry + content
            changelog_path.write_text(content, encoding="utf-8")
            print("  ✓ CHANGELOG.md обновлён")
    else:
        changelog_path.write_text(f"# Changelog\n\n{new_entry}", encoding="utf-8")
        print("  ✓ CHANGELOG.md создан и обновлён")

def main() -> int:
    print("=" * 70)
    print(f"SCADA.AI v{NEW_VERSION} — Финализация")
    print("=" * 70)
    
    update_versions()
    update_changelog()
    
    print("\n" + "=" * 70)
    print("✅ ГОТОВО! Версия 3.3.1.1 зафиксирована.")
    print("=" * 70)
    print("\nВыполни следующие команды в терминале для пуша в Git:")
    print("  git add .")
    print(f'  git commit -m "chore: release v{NEW_VERSION} — add License tab to Configurator"')
    print(f"  git tag -a v{NEW_VERSION} -m \"Release version {NEW_VERSION}\"")
    print("  git push origin main")
    print(f"  git push origin v{NEW_VERSION}")
    print()
    return 0

if __name__ == "__main__":
    sys.exit(main())