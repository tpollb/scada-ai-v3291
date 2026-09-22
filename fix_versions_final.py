#!/usr/bin/env python3
"""
Фикс оставшихся старых версий (3 файла).
"""
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
NEW_VER = "3.3.3.0"

print("=" * 70)
print(f"Фикс оставшихся версий → {NEW_VER}")
print("=" * 70)

# 1. frontend/package.json — версия npm пакета
pkg_json = ROOT / "frontend" / "package.json"
if pkg_json.exists():
    c = pkg_json.read_text(encoding="utf-8")
    if '"version": "3.2.9.1"' in c:
        c = c.replace('"version": "3.2.9.1"', f'"version": "{NEW_VER}"')
        pkg_json.write_text(c, encoding="utf-8")
        print("  v frontend/package.json")
    else:
        print("  - frontend/package.json (уже обновлено)")

# 2. Config.svelte — хардкод в хидере
config_svelte = ROOT / "frontend" / "src" / "routes" / "Config.svelte"
if config_svelte.exists():
    c = config_svelte.read_text(encoding="utf-8")
    old = '<span class="text-sm text-neutral-500">v3.3.2.3</span>'
    new = f'<span class="text-sm text-neutral-500">v{NEW_VER}</span>'
    if old in c:
        c = c.replace(old, new)
        config_svelte.write_text(c, encoding="utf-8")
        print("  v frontend/src/routes/Config.svelte")
    else:
        print("  - Config.svelte (уже обновлено)")

# 3. Home.svelte — хардкод в хидере
home_svelte = ROOT / "frontend" / "src" / "routes" / "Home.svelte"
if home_svelte.exists():
    c = home_svelte.read_text(encoding="utf-8")
    old = 'SCADA.AI <span class="text-neutral-400 dark:text-neutral-500">v3.3.2.3</span>'
    new = f'SCADA.AI <span class="text-neutral-400 dark:text-neutral-500">v{NEW_VER}</span>'
    if old in c:
        c = c.replace(old, new)
        home_svelte.write_text(c, encoding="utf-8")
        print("  v frontend/src/routes/Home.svelte")
    else:
        print("  - Home.svelte (уже обновлено)")

print("\n" + "=" * 70)
print("Готово! Обновлены:")
print("  • Версия npm-пакета")
print("  • Хидер Config.svelte")
print("  • Хидер Home.svelte")
print("=" * 70)
print("\nСледующий шаг:")
print("  python scan_versions.py  # проверка")
print("  git add .")
print("  git commit -m 'fix: обновлены оставшиеся версии до 3.3.3.0'")
print("  git push origin main")