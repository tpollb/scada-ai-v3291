#!/usr/bin/env python3
"""
SCADA.AI Release v3.3.3.0 — мультидоступ и подготовка к проду
"""
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.resolve()
NEW_VER = "3.3.3.0"
TODAY = datetime.now().strftime("%Y-%m-%d")
OLD_VERS = ["3.3.2.3", "3.3.2.2", "3.3.2.1", "3.3.2.0"]

print(f"SCADA.AI Release v{NEW_VER}")
print("=" * 70)

# ============================================================================
# 1. Обновление версий в файлах
# ============================================================================
files_to_update = [
    "backend/config/settings.py",
    "backend/main.py",
    "frontend/src/components/LoginModal.svelte",
]

updated = []
for f in files_to_update:
    path = ROOT / f
    if not path.exists():
        print(f"  - {f} (не найден)")
        continue
    
    content = path.read_text(encoding="utf-8")
    changed = False
    for old in OLD_VERS:
        if old in content:
            content = content.replace(old, NEW_VER)
            changed = True
    
    if changed:
        path.write_text(content, encoding="utf-8")
        updated.append(f)
        print(f"  ✓ {f}")

# ============================================================================
# 2. Обновление CHANGELOG.md (backend/docs/CHANGELOG.md)
# ============================================================================
changelog_path = ROOT / "backend" / "docs" / "CHANGELOG.md"

changelog_entry = f"""
## [{NEW_VER}] - {TODAY}

### 🔥 Мультидоступ и подготовка к продакшену

**Исправлено:**
- Фикс 401 на DDA endpoints — добавлен Authorization заголовок к нативным fetch запросам
  - `DDAInterpretation.svelte` — интерпретация результатов
  - `ABComparisonModal.svelte` — A/B сравнение
- Убран захардкоженный `localhost:8081` из всех фронтенд-файлов
  - `api.ts` — основной HTTP клиент
  - `auth.ts` — логин
  - `license.ts` — статус и загрузка лицензии
  - `DDAInterpretation.svelte` — стриминг интерпретации
  - `ABComparisonModal.svelte` — A/B анализ
  - Теперь хост определяется динамически из `window.location` или `.env`
- Фикс `crypto.randomUUID` для non-secure contexts (http://IP:port)
  - Добавлен полифилл `generateId()` в `chat.ts`
- CORS настроен для мультидоступа
  - `allow_origins=["*"]` для разработки и демо
  - `allow_credentials=False` (JWT в заголовке, не в cookies)

**Добавлено:**
- Поддержка подключения с других машин по сети
- Динамическое определение хоста API через `VITE_API_BASE_URL` или `window.location`

**Проверено:**
- Мультидоступ работает: логин, DDA, чат с другой машины
- Все модули доступны по сети (health, analytics, deep_analysis, energy)

### Технические детали
- `frontend/src/lib/api.ts` — `API_BASE` вместо хардкода
- `frontend/src/stores/chat.ts` — полифилл `generateId()`
- `backend/main.py` — CORS `allow_origins=["*"]`, `allow_credentials=False`

"""

if changelog_path.exists():
    content = changelog_path.read_text(encoding="utf-8")
    if f"[{NEW_VER}]" not in content:
        lines = content.split("\n")
        insert_pos = 0
        for i, line in enumerate(lines):
            if line.strip().startswith("#"):
                insert_pos = i + 1
                break
        lines.insert(insert_pos, changelog_entry)
        changelog_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"  ✓ backend/docs/CHANGELOG.md")
    else:
        print(f"  - CHANGELOG.md (запись уже есть)")
else:
    print(f"  ! {changelog_path} — файл не найден, создаю")
    changelog_path.parent.mkdir(parents=True, exist_ok=True)
    changelog_path.write_text(f"# Changelog\n{changelog_entry}", encoding="utf-8")

# ============================================================================
# 3. Итог
# ============================================================================
print("\n" + "=" * 70)
print(f"Release v{NEW_VER} готов!")
print("=" * 70)
print(f"\nОбновлено файлов: {len(updated) + 1}")
print("\nСледующий шаг:")
print("  git add .")
print("  git commit -m 'release: v3.3.3.0 — мультидоступ и подготовка к проду'")
print("  git tag -a v3.3.3.0 -m 'Release v3.3.3.0'")
print("  git push origin main")
print("  git push origin v3.3.3.0")