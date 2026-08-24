#!/usr/bin/env python3
from pathlib import Path

filepath = Path("main.py")
content = filepath.read_text(encoding="utf-8")

# Исправляем строку импорта, добавляя auth
content = content.replace(
    "from api.routes import chat, config, health, system, docs, energy, analytics, deep_analysis, license",
    "from api.routes import chat, config, health, system, docs, energy, analytics, deep_analysis, license, auth"
)

filepath.write_text(content, encoding="utf-8")
print("✅ Импорт auth в main.py исправлен!")