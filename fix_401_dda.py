#!/usr/bin/env python3
"""
Фикс 401 на DDA endpoints — гибкая версия.
Ищет fetch по URL и добавляет Authorization header.

Запуск: python fix_401_dda.py
"""
from pathlib import Path
import re

ROOT = Path(__file__).parent.resolve()
applied = []
errors = []

def patch_dda_interpretation(path: Path):
    """Патчит DDAInterpretation.svelte — интерпретация (стриминг)"""
    if not path.exists():
        errors.append(f"Файл не найден: {path}")
        return
    
    content = path.read_text(encoding="utf-8")
    
    # Проверяем, не применён ли уже
    if "localStorage.getItem('scada_ai_token')" in content:
        applied.append(f"  - DDAInterpretation.svelte (уже применено)")
        return
    
    # Ищем блок с fetch на interpret/stream
    # Паттерн: fetch('...interpret/stream', { ... headers: { 'Content-Type': ... } ... })
    
    # Вариант 1: ищем точную строку с URL
    old_pattern = r"const response = await fetch\('http://localhost:8081/api/v1/deep_analysis/interpret/stream', \{\s*method: 'POST',\s*headers: \{ 'Content-Type': 'application/json' \},"
    
    new_text = """const token = localStorage.getItem('scada_ai_token')
      const response = await fetch('http://localhost:8081/api/v1/deep_analysis/interpret/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },"""
    
    if re.search(old_pattern, content):
        content = re.sub(old_pattern, new_text, content, count=1)
        path.write_text(content, encoding="utf-8")
        applied.append(f"  v DDAInterpretation.svelte (interpret/stream)")
        return
    
    # Вариант 2: ищем по URL + headers (более гибко)
    url_marker = "http://localhost:8081/api/v1/deep_analysis/interpret/stream"
    headers_marker = "headers: { 'Content-Type': 'application/json' }"
    
    if url_marker in content and headers_marker in content:
        # Находим позицию URL
        url_pos = content.find(url_marker)
        # Ищем headers после URL (в пределах 200 символов)
        search_area = content[url_pos:url_pos + 300]
        
        if headers_marker in search_area:
            # Заменяем headers в этой области
            old_headers = "headers: { 'Content-Type': 'application/json' }"
            new_headers = """headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        }"""
            
            # Добавляем получение токена перед fetch
            fetch_line = "const response = await fetch"
            if fetch_line in content:
                # Вставляем получение токена перед строкой с fetch
                content = content.replace(
                    fetch_line,
                    f"const token = localStorage.getItem('scada_ai_token')\n      {fetch_line}",
                    1
                )
                # Заменяем headers
                content = content.replace(old_headers, new_headers, 1)
                path.write_text(content, encoding="utf-8")
                applied.append(f"  v DDAInterpretation.svelte (interpret/stream)")
                return
    
    errors.append(f"Не удалось найти паттерн в DDAInterpretation.svelte")


def patch_ab_comparison(path: Path):
    """Патчит ABComparisonModal.svelte — A/B анализ"""
    if not path.exists():
        errors.append(f"Файл не найден: {path}")
        return
    
    content = path.read_text(encoding="utf-8")
    
    # Проверяем, не применён ли уже
    if "localStorage.getItem('scada_ai_token')" in content:
        applied.append(f"  - ABComparisonModal.svelte (уже применено)")
        return
    
    # Ищем блок с fetch на deep_analysis/ab
    url_marker = "http://localhost:8081/api/v1/deep_analysis/ab"
    headers_marker = "headers: { 'Content-Type': 'application/json' }"
    
    if url_marker in content and headers_marker in content:
        # Находим позицию URL
        url_pos = content.find(url_marker)
        # Ищем headers после URL (в пределах 200 символов)
        search_area = content[url_pos:url_pos + 300]
        
        if headers_marker in search_area:
            # Заменяем headers
            old_headers = "headers: { 'Content-Type': 'application/json' }"
            new_headers = """headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        }"""
            
            # Добавляем получение токена перед fetch
            fetch_line = "const response = await fetch"
            if fetch_line in content:
                # Вставляем получение токена перед строкой с fetch
                content = content.replace(
                    fetch_line,
                    f"const token = localStorage.getItem('scada_ai_token')\n      {fetch_line}",
                    1
                )
                # Заменяем headers
                content = content.replace(old_headers, new_headers, 1)
                path.write_text(content, encoding="utf-8")
                applied.append(f"  v ABComparisonModal.svelte (deep_analysis/ab)")
                return
    
    errors.append(f"Не удалось найти паттерн в ABComparisonModal.svelte")


# === Запуск ===
patch_dda_interpretation(ROOT / "frontend" / "src" / "components" / "DDAInterpretation.svelte")
patch_ab_comparison(ROOT / "frontend" / "src" / "components" / "ABComparisonModal.svelte")

# === Результат ===
print("=" * 60)
print("Фикс 401 на DDA endpoints")
print("=" * 60)

if applied:
    print("\nПрименено:")
    for a in applied:
        print(a)

if errors:
    print("\nОШИБКИ:")
    for e in errors:
        print(f"  !!! {e}")

if not errors and applied:
    print("\nГотово! Обнови страницу (Ctrl+Shift+R) и проверь:")
    print("  1. DDA анализ -> вкладка 'Интерпретация' -> генерация")
    print("  2. A/B сравнение -> запуск сравнения")
    print("  Оба должны работать без 401.")