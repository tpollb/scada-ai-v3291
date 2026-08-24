#!/usr/bin/env python3
"""
SCADA.AI — Bump version to 3.3.2.0
Обновляет версию во всех файлах и добавляет запись в CHANGELOG.
"""
import re
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.resolve()
NEW_VERSION = "3.3.2.0"
TODAY = datetime.now().strftime("%Y-%m-%d")

# ============================================================================
# 1. Обновление версий в файлах
# ============================================================================

def update_file_version(filepath: Path, patterns: list[tuple[str, str]]):
    """Заменяет версии в файле по списку паттернов."""
    if not filepath.exists():
        print(f"  ⚠️  Файл не найден: {filepath.relative_to(PROJECT_ROOT)}")
        return False
    
    content = filepath.read_text(encoding="utf-8")
    original = content
    
    for old, new in patterns:
        content = content.replace(old, new)
    
    if content != original:
        filepath.write_text(content, encoding="utf-8")
        print(f"  ✓ {filepath.relative_to(PROJECT_ROOT)}")
        return True
    return False

def update_versions():
    print("\n[1/2] Обновление версий...")
    
    # backend/config/settings.py
    update_file_version(
        PROJECT_ROOT / "backend" / "config" / "settings.py",
        [('app_version: str = "3.3.1.1"', f'app_version: str = "{NEW_VERSION}"'),
         ('app_version: str = "3.3.0.0"', f'app_version: str = "{NEW_VERSION}"')]
    )
    
    # frontend/src/routes/Home.svelte
    update_file_version(
        PROJECT_ROOT / "frontend" / "src" / "routes" / "Home.svelte",
        [("v3.3.1.1", f"v{NEW_VERSION}"), ("v3.3.0.0", f"v{NEW_VERSION}")]
    )
    
    # frontend/src/routes/Config.svelte
    update_file_version(
        PROJECT_ROOT / "frontend" / "src" / "routes" / "Config.svelte",
        [("v3.3.1.1", f"v{NEW_VERSION}"), ("v3.3.0.0", f"v{NEW_VERSION}")]
    )
    
    # frontend/src/components/LoginModal.svelte
    update_file_version(
        PROJECT_ROOT / "frontend" / "src" / "components" / "LoginModal.svelte",
        [("SCADA.AI v3.3.1.1", f"SCADA.AI v{NEW_VERSION}"),
         ("SCADA.AI v3.3.0.0", f"SCADA.AI v{NEW_VERSION}")]
    )
    
    # backend/docs/ARCHITECTURE.md
    update_file_version(
        PROJECT_ROOT / "backend" / "docs" / "ARCHITECTURE.md",
        [("**Версия:** 3.3.1.0", f"**Версия:** {NEW_VERSION}"),
         ("**Версия:** 3.3.0.0", f"**Версия:** {NEW_VERSION}")]
    )
    
    # Project_full_description.md
    update_file_version(
        PROJECT_ROOT / "Project_full_description.md",
        [("**Версия:** 3.3.1.0", f"**Версия:** {NEW_VERSION}"),
         ("**Версия:** 3.3.0.0", f"**Версия:** {NEW_VERSION}"),
         ("**Версия:** 3.3.1.1", f"**Версия:** {NEW_VERSION}")]
    )

# ============================================================================
# 2. Обновление CHANGELOG.md
# ============================================================================

def update_changelog():
    print("\n[2/2] Обновление CHANGELOG.md...")
    changelog_path = PROJECT_ROOT / "backend" / "docs" / "CHANGELOG.md"
    
    new_entry = f"""## [{NEW_VERSION}] - {TODAY}

### ✨ Добавлено
- **Система авторизации и ролевая модель:**
  - 4 предустановленные роли: `admin`, `engineer`, `operator`, `boss`.
  - Локальное хранение пользователей в `backend/data/users.json` с хешированием паролей (bcrypt).
  - Endpoints: `POST /api/v1/auth/login`, `POST /api/v1/auth/logout`, `GET /api/v1/auth/me`.
  - Управление пользователями (только `admin`): `GET/POST/DELETE /api/v1/auth/users`, `PUT /users/{{username}}/password`.
- **AuthMiddleware:**
  - Проверка JWT-токена на всех запросах (кроме публичных путей).
  - Установка `request.state.user` для использования в роутерах.
  - Корректная обработка `OPTIONS` (CORS preflight).
- **Управление сессиями лицензий:**
  - `POST /api/v1/license/session/start` — создание сессии.
  - `POST /api/v1/license/session/heartbeat` — продление сессии (каждые 30 сек).
  - `POST /api/v1/license/session/end` — завершение сессии.
  - Лимит одновременных подключений согласно лицензии.
- **Вкладка «Лицензия» в Конфигураторе:**
  - Просмотр статуса лицензии (клиент, тип, срок, сессии, доступные модули).
  - Drag & Drop загрузка файла `.lic` с валидацией (расширение, размер до 1МБ).
  - Автоматическое обновление статуса после загрузки.
- **Фронтенд-авторизация:**
  - `LoginModal.svelte` — модальное окно входа при запуске.
  - Отображение имени пользователя и кнопка «Выход» в шапке.
  - Хранение токена в `localStorage`, автоматическая подстановка в запросы.
  - Обработка 401 (автоматический выход и перезагрузка).

### 🔧 Технические улучшения
- Создан модуль `backend/core/auth/` (models, password, jwt_utils, storage, middleware).
- Создан `backend/api/routes/auth.py` с полным набором endpoints.
- Создан `frontend/src/stores/auth.ts` для управления состоянием авторизации.
- Обновлён `frontend/src/lib/api.ts` — корректная работа с `ky` v2 и `Request` объектами.
- Обновлён `frontend/src/stores/license.ts` — безопасное чтение стора через `get()`.

### 🛡️ Безопасность
- Пароли хранятся только в виде хешей (bcrypt).
- JWT-токены с секретным ключом и временем жизни 24 часа.
- `allow_credentials=True` в CORS для корректной работы с заголовками.

"""
    
    if changelog_path.exists():
        content = changelog_path.read_text(encoding="utf-8")
        if f"[{NEW_VERSION}]" not in content:
            # Вставляем после первой строки заголовка
            lines = content.split('\n')
            # Находим первую строку, начинающуюся с ## [
            insert_idx = 0
            for i, line in enumerate(lines):
                if line.startswith('## ['):
                    insert_idx = i
                    break
            
            lines.insert(insert_idx, new_entry)
            changelog_path.write_text('\n'.join(lines), encoding="utf-8")
            print("  ✓ CHANGELOG.md обновлён")
        else:
            print("  - Запись уже существует")
    else:
        changelog_path.write_text(f"# Changelog\n\n{new_entry}", encoding="utf-8")
        print("  ✓ CHANGELOG.md создан")

# ============================================================================
# Main
# ============================================================================

def main():
    print("=" * 70)
    print(f"SCADA.AI — Bump version to {NEW_VERSION}")
    print("=" * 70)
    
    update_versions()
    update_changelog()
    
    print("\n" + "=" * 70)
    print(f"✅ Версия обновлена до {NEW_VERSION}")
    print("=" * 70)
    print("\nВыполни в терминале:")
    print("  git add .")
    print(f'  git commit -m "chore: release v{NEW_VERSION} — авторизация, роли, сессии, вкладка лицензии"')
    print(f"  git tag -a v{NEW_VERSION} -m \"Release version {NEW_VERSION}\"")
    print("  git push origin main")
    print(f"  git push origin v{NEW_VERSION}")

if __name__ == "__main__":
    main()