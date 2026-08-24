#!/usr/bin/env python3
"""
Исправление порядка middleware в main.py.
CORS должен быть добавлен ПОСЛЕДНИМ, чтобы оборачивать все остальные middleware 
и добавлять заголовки даже к ответам с ошибками (401, 403 и т.д.).
"""
from pathlib import Path

filepath = Path("backend/main.py")
if not filepath.exists():
    print("❌ Файл backend/main.py не найден")
    exit(1)

content = filepath.read_text(encoding="utf-8")

# 1. Удаляем старый блок CORS middleware
old_cors_block = """# CORS middleware
app.add_middleware(
CORSMiddleware,
allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
allow_credentials=False,
allow_methods=["*"],
allow_headers=["*"],
)"""

content = content.replace(old_cors_block, "")

# 2. Формируем правильный блок middleware
correct_middleware_block = """
# ============================================================================
# Middleware (Порядок критически важен!)
# CORSMiddleware должен быть добавлен ПОСЛЕДНИМ, чтобы быть ПЕРВЫМ в цепочке 
# выполнения и добавлять CORS-заголовки ко всем ответам, включая ошибки.
# ============================================================================
from core.middleware.license import LicenseMiddleware
app.add_middleware(LicenseMiddleware)

from core.auth.middleware import AuthMiddleware
app.add_middleware(AuthMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,  # Обязательно True для работы с заголовком Authorization
    allow_methods=["*"],
    allow_headers=["*"],
)
"""

# 3. Вставляем блок после инициализации FastAPI app
if "app = FastAPI(" in content and "CORSMiddleware" not in content:
    # Находим конец инициализации app
    content = content.replace(
        "    lifespan=lifespan\n)",
        "    lifespan=lifespan\n)\n" + correct_middleware_block
    )
else:
    # Fallback: вставляем перед первым роутером
    content = content.replace(
        'app.include_router(chat.router, tags=["chat"])',
        correct_middleware_block + '\napp.include_router(chat.router, tags=["chat"])'
    )

filepath.write_text(content, encoding="utf-8")
print("✅ Порядок middleware в main.py исправлен!")
print("   Теперь CORS заголовки будут добавляться ко всем ответам.")