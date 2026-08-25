#!/usr/bin/env python3
"""SCADA.AI Release v3.3.2.3"""
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.resolve()
NEW_VER = "3.3.2.3"
TODAY = datetime.now().strftime("%Y-%m-%d")
OLD = ["3.3.2.2", "3.3.2.1", "3.3.2.0", "3.3.1.1", "3.3.0.1.1", "3.2.9.1", "3.2.9"]

print(f"SCADA.AI Release v{NEW_VER}")

# 1. Обновление версий в файлах
files = [
    "backend/config/settings.py",
    "backend/main.py",
    "frontend/src/routes/Home.svelte",
    "frontend/src/routes/Config.svelte",
    "frontend/src/components/LoginModal.svelte",
]
for f in files:
    p = ROOT / f
    if p.exists():
        c = p.read_text(encoding="utf-8")
        for o in OLD:
            c = c.replace(o, NEW_VER)
        p.write_text(c, encoding="utf-8")
        print(f"  v {f}")
    else:
        print(f"  - {f} (не найден)")

# 2. Обновление CHANGELOG
changelog = ROOT / "CHANGELOG.md"
entry = f"""
## [{NEW_VER}] - {TODAY}

### Обновлена страница входа
- Фоновое изображение `logo.gif` с затемнением
- Новый заголовок `AI.SCADA` (AI синий, SCADA светлосерый, шрифт `font-mono`)
- Современный дизайн: уменьшенное окно, узкие поля ввода, тёмная кнопка с синим кантом
- Динамическая версия в футере (загружается из `/system/info`)
- Убрано автозаполнение полей (`autocomplete="off"`, без `placeholder`)

"""
if changelog.exists():
    c = changelog.read_text(encoding="utf-8")
    if f"[{NEW_VER}]" not in c:
        lines = c.split("\n")
        idx = 0
        for i, line in enumerate(lines):
            if line.strip().startswith("#"):
                idx = i + 1
                break
        lines.insert(idx, entry)
        changelog.write_text("\n".join(lines), encoding="utf-8")
        print("  v CHANGELOG.md")
    else:
        print("  - CHANGELOG.md (запись уже есть)")
else:
    changelog.write_text(f"# Changelog\n{entry}", encoding="utf-8")
    print("  v CHANGELOG.md (создан)")

print(f"\nRelease v{NEW_VER} готов!")