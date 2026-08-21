#!/usr/bin/env python3
"""
SCADA.AI v3.3.0 — Финализация релиза (исправленная версия)
1. Удаление старой записи о v3.3.0 из CHANGELOG.md
2. Обновление MODULES.md (правильный путь: backend/docs/)
3. Создание LICENSING.md в backend/docs/
4. Обновление версий

Запуск: python finalize_v330_fixed.py
"""
import sys
import re
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.resolve()
NEW_VERSION = "3.3.0"
TODAY = datetime.now().strftime("%Y-%m-%d")

# ============================================================================
# 1. Удаление старой записи о v3.3.0 из CHANGELOG.md
# ============================================================================

def clean_changelog():
    print("\n[1/4] Очистка старой записи о v3.3.0 из CHANGELOG.md...")
    
    changelog_path = PROJECT_ROOT / "backend" / "docs" / "CHANGELOG.md"
    if not changelog_path.exists():
        print("  !!! CHANGELOG.md не найден")
        return False
    
    content = changelog_path.read_text(encoding="utf-8")
    
    # Ищем и удаляем блок [3.3.0] до следующего [x.x.x] или конца файла
    # Паттерн: от ## [3.3.0] до следующего ## [ или конца
    pattern = r'## \[3\.3\.0\][^\]]*?- \d{4}-\d{2}-\d{2}.*?(?=\n## \[|\Z)'
    
    new_content = re.sub(pattern, '', content, flags=re.DOTALL)
    
    if content != new_content:
        changelog_path.write_text(new_content, encoding="utf-8")
        print("  ✓ Старая запись о v3.3.0 удалена")
        return True
    else:
        print("  - Запись о v3.3.0 не найдена (возможно уже чистый)")
        return True


# ============================================================================
# 2. Обновление версий
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
    print("\n[2/4] Обновление версий в файлах...")
    
    # settings.py
    update_version_in_file(
        PROJECT_ROOT / "backend" / "config" / "settings.py",
        r'app_version:\s*str\s*=\s*"[^"]+"',
        f'app_version: str = "{NEW_VERSION}"'
    )
    
    # main.py
    update_version_in_file(
        PROJECT_ROOT / "backend" / "main.py",
        r'SCADA\.AI v\d+\.\d+\.\d+',
        f'SCADA.AI v{NEW_VERSION}'
    )
    
    # Home.svelte
    update_version_in_file(
        PROJECT_ROOT / "frontend" / "src" / "routes" / "Home.svelte",
        r'v3\.\d+\.\d+\.\d+',
        f'v{NEW_VERSION}'
    )
    
    # Config.svelte
    update_version_in_file(
        PROJECT_ROOT / "frontend" / "src" / "routes" / "Config.svelte",
        r'v3\.\d+\.\d+\.\d+',
        f'v{NEW_VERSION}'
    )
    
    # Project_full_description.md
    update_version_in_file(
        PROJECT_ROOT / "Project_full_description.md",
        r'Версия:\s*\d+\.\d+\.\d+',
        f'Версия: {NEW_VERSION}'
    )
    update_version_in_file(
        PROJECT_ROOT / "Project_full_description.md",
        r'SCADA\.AI v\d+\.\d+\.\d+',
        f'SCADA.AI v{NEW_VERSION}'
    )
    
    # ARCHITECTURE.md
    update_version_in_file(
        PROJECT_ROOT / "ARCHITECTURE.md",
        r'Версия:\s*\d+\.\d+\.\d+',
        f'Версия: {NEW_VERSION}'
    )


# ============================================================================
# 3. Создание backend/docs/LICENSING.md
# ============================================================================

def create_licensing_doc():
    print("\n[3/4] Создание backend/docs/LICENSING.md...")
    
    docs_dir = PROJECT_ROOT / "backend" / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    licensing_md = docs_dir / "LICENSING.md"
    
    content = f"""# Система лицензирования SCADA.AI

> Добавлено в версии {NEW_VERSION} ({TODAY})

Система лицензирования обеспечивает защиту программного обеспечения, управление доступом к модулям (feature gates) и контроль количества одновременных пользователей в закрытых контурах (offline).

## 🔐 Архитектура и безопасность

- **Формат:** JWT (JSON Web Token) с криптографической подписью RSA-2048
- **Защита:** Файл `.lic` невозможно модифицировать без приватного ключа разработчика
- **Работа:** Полностью offline. Проверка подписи осуществляется с помощью публичного ключа, зашитого в приложение
- **Привязка:** К количеству одновременных сессий (concurrent users). Аппаратная привязка (hardware binding) отсутствует для удобства замены серверов

## 📦 Типы лицензий

| Тип | Доступные модули | Срок действия |
|-----|------------------|---------------|
| `trial` | `hello`, `health`, `logs` | 14 дней |
| `basic` | + `energy_*` | 1 год |
| `standard` | + `analytics` | 1 год |
| `enterprise` | + `deep_analysis`, без лимитов | 1–3 года |

!!! note
    Базовые модули `hello` и `logs` доступны всегда, даже при истекшей лицензии, для базовой диагностики.

## ⏳ Grace Period (Льготный период)

После истечения срока действия лицензии система предоставляет **Grace Period** (по умолчанию 3 дня).

- В этот период **все функции продолжают работать**
- В интерфейсе отображается жёлтый предупреждающий баннер с количеством оставшихся дней
- После окончания Grace Period доступ к API блокируется (HTTP 402), отображается красный баннер

## 👥 Контроль сессий

Лицензия ограничивает количество одновременных подключений (`max_concurrent_users`).

- Отслеживание осуществляется через in-memory счётчик с таймаутом неактивности (30 минут)
- При превышении лимита новые запросы отклоняются с ошибкой HTTP 403

## 🛠️ Генерация лицензий (Для разработчика)

В проекте предусмотрены CLI-скрипты в папке `scripts/`:

### 1. Генерация ключей (выполняется один раз)

!!! code-block bash
    python scripts/generate_keys.py

Создаёт:
- `backend/core/license/keys/private_key.pem` — **ДЛЯ РАЗРАБОТЧИКА** (никому не передавать!)
- `backend/core/license/keys/public_key.pem` — для приложения

### 2. Генерация файла лицензии

!!! code-block bash
    python scripts/generate_license.py

Создаёт файл `license.lic` в корне проекта.

## ⚙️ Применение лицензии

1. Поместите файл `license.lic` в корень проекта
2. Убедитесь, что в `.env` указаны корректные пути (по умолчанию настроено автоматически):
   !!! code-block env
       LICENSE_FILE=license.lic
       LICENSE_PUBLIC_KEY=backend/core/license/keys/public_key.pem
       LICENSE_GRACE_PERIOD_DAYS=3
3. Перезапустите Backend

## 📊 Проверка статуса лицензии

### Через API

!!! code-block bash
    curl http://localhost:8081/api/v1/license/status
    curl http://localhost:8081/api/v1/license/info

### Через UI

Конфигуратор → вкладка "Лицензия" — просмотр статуса и загрузка новых файлов `.lic`.

## 🏗️ Структура файлов

!!! code-block
    backend/core/license/
    ├── __init__.py              # Экспорт LicenseManager
    ├── models.py                # Pydantic модели (License, LicenseStatus, LicenseType)
    ├── validator.py             # Проверка JWT подписи
    ├── manager.py               # LicenseManager (singleton)
    ├── session_tracker.py       # Счётчик concurrent users
    └── keys/
        ├── private_key.pem      # Приватный ключ (у разработчика)
        └── public_key.pem       # Публичный ключ (в приложении)

## 🔧 Интеграция с модулями

Начиная с версии {NEW_VERSION}, загрузка модулей контролируется системой лицензирования через `core/module_registry.py`.

**Принцип работы:**
1. При старте приложения `LicenseManager` валидирует файл `.lic`
2. Метод `load_all_with_license()` получает список разрешённых фич (`features`) из лицензии
3. Модули, отсутствующие в списке `features`, **не загружаются** в реестр (за исключением базовых `hello` и `logs`)
4. Попытка вызвать API эндпоинт отключённого модуля вернёт ошибку или модуль просто не будет найден в роутинге

Это гарантирует, что клиент не сможет получить доступ к функционалу (например, Deep Analysis), не приобретя соответствующий тип лицензии (`enterprise`), даже если изменит переменную `ENABLED_MODULES` в `.env`.

## 🚨 Middleware

Глобальный `LicenseMiddleware` проверяет срок действия лицензии для всех API-запросов:
- Если лицензия истекла и grace period закончился → HTTP 402
- Если в grace period → добавляется заголовок `X-License-Warning`
- Если превышен лимит пользователей → HTTP 403

## 📝 Зависимости

!!! code-block
    PyJWT[crypto]>=2.8.0
    cryptography>=41.0.0
"""
    
    licensing_md.write_text(content, encoding="utf-8")
    print(f"  ✓ Создан: backend/docs/LICENSING.md")


# ============================================================================
# 4. Обновление backend/docs/MODULES.md
# ============================================================================

def update_modules_doc():
    print("\n[4/4] Обновление backend/docs/MODULES.md...")
    
    modules_md = PROJECT_ROOT / "backend" / "docs" / "MODULES.md"
    if not modules_md.exists():
        print("  !!! Файл MODULES.md не найден")
        return
    
    content = modules_md.read_text(encoding="utf-8")
    
    if "Управление доступом через лицензирование" in content:
        print("  - Раздел о лицензировании уже есть")
        return
    
    new_section = f"""

## 🔐 Управление доступом через лицензирование (v{NEW_VERSION})

Начиная с версии {NEW_VERSION}, загрузка модулей контролируется системой лицензирования (`core/module_registry.py`).

### Принцип работы

1. При старте приложения `LicenseManager` валидирует файл `.lic`
2. Метод `load_all_with_license()` получает список разрешённых фич (`features`) из лицензии
3. Модули, отсутствующие в списке `features`, **не загружаются** в реестр (за исключением базовых `hello` и `logs`)
4. Попытка вызвать API эндпоинт отключённого модуля вернёт ошибку или модуль просто не будет найден в роутинге

### Базовые модули

Модули `hello` и `logs` доступны **всегда**, даже при истекшей лицензии, для базовой диагностики.

### Таблица соответствия типов лицензий и модулей

| Модуль | trial | basic | standard | enterprise |
|--------|-------|-------|----------|------------|
| hello | ✅ | ✅ | ✅ | ✅ |
| logs | ✅ | ✅ | ✅ | ✅ |
| health | ✅ | ✅ | ✅ | ✅ |
| energy_electricity | ❌ | ✅ | ✅ | ✅ |
| energy_water | ❌ | ✅ | ✅ | ✅ |
| energy_heat | ❌ | ✅ | ✅ | ✅ |
| analytics | ❌ | ❌ | ✅ | ✅ |
| deep_analysis | ❌ | ❌ | ❌ | ✅ |

### Подробная документация

См. [LICENSING.md](LICENSING.md) для полной информации о системе лицензирования.
"""
    
    content += new_section
    modules_md.write_text(content, encoding="utf-8")
    print(f"  ✓ Обновлён: backend/docs/MODULES.md")


# ============================================================================
# Main
# ============================================================================

def main() -> int:
    print("=" * 70)
    print(f"SCADA.AI v{NEW_VERSION} — Финализация релиза (исправленная версия)")
    print("=" * 70)
    print(f"\nКорень проекта: {PROJECT_ROOT}")
    print(f"Дата: {TODAY}")
    
    clean_changelog()
    update_versions()
    create_licensing_doc()
    update_modules_doc()
    
    print("\n" + "=" * 70)
    print(f"✅ ФИНАЛИЗАЦИЯ v{NEW_VERSION} ЗАВЕРШЕНА УСПЕШНО!")
    print("=" * 70)
    print("\nСледующие шаги (Git):")
    print("  git add .")
    print(f'  git commit -m "feat: release v{NEW_VERSION} — offline licensing system"')
    print(f"  git tag -a v{NEW_VERSION} -m \"Release version {NEW_VERSION}: Licensing system\"")
    print("  git push origin main")
    print(f"  git push origin v{NEW_VERSION}")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())