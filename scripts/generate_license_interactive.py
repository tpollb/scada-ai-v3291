#!/usr/bin/env python3
"""
Интерактивный генератор лицензий SCADA.AI
Запускается в терминале, задаёт вопросы и создаёт .lic файл.

Запуск: python scripts/generate_license_interactive.py
"""
import sys
import uuid
import jwt
from pathlib import Path
from datetime import datetime, timedelta, timezone

# ============================================================================
# Константы
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
DEFAULT_PRIVATE_KEY = PROJECT_ROOT / "backend" / "core" / "license" / "keys" / "private_key.pem"
DEFAULT_OUTPUT = PROJECT_ROOT / "license.lic"

# Все доступные модули (кроме базовых hello/logs, которые всегда включены)
ALL_MODULES = [
    ("health", "Мониторинг здоровья системы"),
    ("energy_electricity", "Учёт электроэнергии"),
    ("energy_water", "Учёт воды"),
    ("energy_heat", "Учёт тепла"),
    ("analytics", "Тренд-анализ и прогнозы"),
    ("deep_analysis", "Глубокий анализ данных (DDA, A/B)"),
]

# Шаблоны лицензий (для быстрого выбора)
LICENSE_PRESETS = {
    "trial": {
        "name": "Trial (пробная)",
        "months": 1,
        "users": 3,
        "features": ["health"],
        "description": "Базовый мониторинг здоровья на 1 месяц",
    },
    "basic": {
        "name": "Basic (базовая)",
        "months": 12,
        "users": 5,
        "features": ["health", "energy_electricity", "energy_water", "energy_heat"],
        "description": "Мониторинг + энергоучёт на 1 год",
    },
    "standard": {
        "name": "Standard (стандартная)",
        "months": 12,
        "users": 10,
        "features": ["health", "energy_electricity", "energy_water", "energy_heat", "analytics"],
        "description": "Мониторинг + энергоучёт + аналитика на 1 год",
    },
    "enterprise": {
        "name": "Enterprise (корпоративная)",
        "months": 24,
        "users": 50,
        "features": ["health", "energy_electricity", "energy_water", "energy_heat", "analytics", "deep_analysis"],
        "description": "Полный функционал на 2 года",
    },
    "custom": {
        "name": "Custom (настроить вручную)",
        "months": None,
        "users": None,
        "features": None,
        "description": "Индивидуальная настройка всех параметров",
    },
}

# ============================================================================
# Утилиты ввода
# ============================================================================

def print_header():
    print("\n" + "=" * 70)
    print("  SCADA.AI — Генератор лицензий")
    print("=" * 70)
    print()

def print_step(step: int, total: int, title: str):
    print(f"\n[{step}/{total}] {title}")
    print("-" * 50)

def ask_string(prompt: str, default: str = "", min_length: int = 1) -> str:
    while True:
        suffix = f" [{default}]" if default else ""
        value = input(f"  {prompt}{suffix}: ").strip()
        if not value and default:
            return default
        if len(value) < min_length:
            print(f"  ⚠️  Значение не может быть пустым")
            continue
        return value

def ask_int(prompt: str, default: int, min_value: int = 1, max_value: int = 9999) -> int:
    while True:
        value = input(f"  {prompt} [{default}]: ").strip()
        if not value:
            return default
        try:
            num = int(value)
            if num < min_value or num > max_value:
                print(f"  ⚠️  Значение должно быть от {min_value} до {max_value}")
                continue
            return num
        except ValueError:
            print(f"  ⚠️  Введите целое число")

def ask_yes_no(prompt: str, default: bool = True) -> bool:
    suffix = "[Y/n]" if default else "[y/N]"
    while True:
        value = input(f"  {prompt} {suffix}: ").strip().lower()
        if not value:
            return default
        if value in ("y", "yes", "да", "д", "1"):
            return True
        if value in ("n", "no", "нет", "н", "0"):
            return False
        print("  ⚠️  Введите y/yes или n/no")

def ask_choice(prompt: str, choices: list[tuple[str, str]]) -> str:
    print(f"  {prompt}")
    for i, (key, description) in enumerate(choices, 1):
        print(f"    {i}. {key} — {description}")
    while True:
        value = input(f"  Ваш выбор (1-{len(choices)}): ").strip()
        try:
            idx = int(value)
            if 1 <= idx <= len(choices):
                return choices[idx - 1][0]
            print(f"  ⚠️  Введите число от 1 до {len(choices)}")
        except ValueError:
            # Может быть введён ключ напрямую
            if value in [c[0] for c in choices]:
                return value
            print(f"  ⚠️  Неверный выбор")

# ============================================================================
# Основная логика
# ============================================================================

def select_preset() -> str:
    print_step(1, 5, "Тип лицензии")
    choices = [(k, v["description"]) for k, v in LICENSE_PRESETS.items()]
    return ask_choice("Выберите шаблон лицензии:", choices)

def ask_customer() -> str:
    print_step(2, 5, "Владелец лицензии")
    return ask_string("Название организации", default="ООО «Компания»")

def ask_duration() -> int:
    print_step(3, 5, "Срок действия")
    return ask_int("Срок (месяцев)", default=12, min_value=1, max_value=120)

def ask_users() -> int:
    print_step(4, 5, "Количество пользователей")
    return ask_int("Максимум одновременных подключений", default=5, min_value=1, max_value=1000)

def ask_features(preset_features: list[str] | None) -> list[str]:
    print_step(5, 5, "Доступные модули")
    
    if preset_features is not None:
        print("  ✓ Используем модули из выбранного шаблона:")
        for mod_id, mod_name in ALL_MODULES:
            status = "✓" if mod_id in preset_features else "✗"
            print(f"    {status} {mod_id:20s} — {mod_name}")
        return preset_features
    
    print("  Настройте доступные модули (базовые hello и logs всегда включены):")
    print()
    
    selected = []
    for mod_id, mod_name in ALL_MODULES:
        if ask_yes_no(f"Включить «{mod_name}» ({mod_id})?", default=(mod_id == "health")):
            selected.append(mod_id)
    
    if not selected:
        print("\n  ⚠️  Вы не выбрали ни одного модуля. Включаем health по умолчанию.")
        selected = ["health"]
    
    return selected

def confirm_license(customer: str, months: int, users: int, features: list[str], grace_days: int) -> bool:
    print("\n" + "=" * 70)
    print("  ПОДТВЕРЖДЕНИЕ ЛИЦЕНЗИИ")
    print("=" * 70)
    print(f"  Владелец:       {customer}")
    print(f"  Срок:           {months} мес. (истечёт: {(datetime.now(timezone.utc) + timedelta(days=months*30)).strftime('%Y-%m-%d')})")
    print(f"  Подключения:    до {users} одновременно")
    print(f"  Grace period:   {grace_days} дн.")
    print(f"  Модули:         {', '.join(features)}")
    print("=" * 70)
    print()
    return ask_yes_no("Сгенерировать лицензию?", default=True)

def generate_license(
    customer: str,
    months: int,
    users: int,
    features: list[str],
    grace_days: int,
    private_key_path: Path,
    output_path: Path,
) -> bool:
    """Генерирует .lic файл. Возвращает True при успехе."""
    
    if not private_key_path.exists():
        print(f"\n❌ ОШИБКА: Приватный ключ не найден: {private_key_path}")
        print("   Сначала запустите: python scripts/generate_keys.py")
        return False
    
    private_key_pem = private_key_path.read_bytes()
    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=months * 30)
    
    # Определяем тип лицензии по набору фич
    license_type = "custom"
    if features == ["health"]:
        license_type = "trial"
    elif set(features) == {"health", "energy_electricity", "energy_water", "energy_heat"}:
        license_type = "basic"
    elif set(features) == {"health", "energy_electricity", "energy_water", "energy_heat", "analytics"}:
        license_type = "standard"
    elif set(features) == {"health", "energy_electricity", "energy_water", "energy_heat", "analytics", "deep_analysis"}:
        license_type = "enterprise"
    
    payload = {
        "license_id": str(uuid.uuid4()),
        "customer": customer,
        "issued_at": now.isoformat(),
        "expires_at": expires.isoformat(),
        "license_type": license_type,
        "features": features,
        "max_concurrent_users": users,
        "grace_period_days": grace_days,
    }
    
    try:
        token = jwt.encode(payload, private_key_pem, algorithm="RS256")
    except Exception as e:
        print(f"\n❌ ОШИБКА подписи: {e}")
        return False
    
    output_path.write_text(token, encoding="utf-8")
    
    print("\n" + "=" * 70)
    print("  ✅ ЛИЦЕНЗИЯ УСПЕШНО СГЕНЕРИРОВАНА!")
    print("=" * 70)
    print(f"  ID:             {payload['license_id']}")
    print(f"  Тип:            {license_type}")
    print(f"  Клиент:         {customer}")
    print(f"  Выдана:         {now.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"  Истекает:       {expires.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"  Grace period:   {grace_days} дн.")
    print(f"  Подключения:    до {users}")
    print(f"  Модули:         {', '.join(features)}")
    print(f"  Файл:           {output_path}")
    print(f"  Размер:         {output_path.stat().st_size} байт")
    print("=" * 70)
    print("\n📦 Передайте этот файл клиенту. Приватный ключ НЕ передавайте!")
    print("   Клиент должен поместить файл в корень проекта и перезапустить backend.")
    
    return True

def main() -> int:
    print_header()
    
    # 1. Выбор шаблона
    preset_key = select_preset()
    preset = LICENSE_PRESETS[preset_key]
    
    # 2. Владелец
    customer = ask_customer()
    
    # 3. Срок (если не задан в шаблоне)
    if preset["months"] is None:
        months = ask_duration()
    else:
        print_step(3, 5, "Срок действия")
        months = ask_int("Срок (месяцев)", default=preset["months"])
    
    # 4. Подключения (если не заданы в шаблоне)
    if preset["users"] is None:
        users = ask_users()
    else:
        print_step(4, 5, "Количество пользователей")
        users = ask_int("Максимум одновременных подключений", default=preset["users"])
    
    # 5. Модули (если не заданы в шаблоне)
    features = ask_features(preset["features"])
    
    # Grace period (всегда спрашиваем, но с дефолтом)
    print("\n[доп.] Grace period")
    print("-" * 50)
    grace_days = ask_int("Grace period после истечения (дней)", default=3, min_value=0, max_value=30)
    
    # Подтверждение
    if not confirm_license(customer, months, users, features, grace_days):
        print("\n❌ Отменено пользователем.")
        return 1
    
    # Путь к ключу и выходному файлу
    private_key_path = DEFAULT_PRIVATE_KEY
    output_path = DEFAULT_OUTPUT
    
    # Генерация
    success = generate_license(
        customer=customer,
        months=months,
        users=users,
        features=features,
        grace_days=grace_days,
        private_key_path=private_key_path,
        output_path=output_path,
    )
    
    return 0 if success else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n❌ Прервано пользователем.")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Непредвиденная ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)