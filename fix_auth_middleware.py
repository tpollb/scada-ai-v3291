#!/usr/bin/env python3
"""
Исправление AuthMiddleware для корректного возврата 401 вместо 500
при отсутствии токена.
"""
from pathlib import Path

filepath = Path("backend/core/auth/middleware.py")

if not filepath.exists():
    print("❌ Файл не найден")
    exit(1)

content = filepath.read_text(encoding="utf-8")

# Заменяем HTTPException на JSONResponse для надёжности в middleware
old_code = '''from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from structlog import get_logger
from .jwt_utils import decode_access_token
from .storage import get_user_storage'''

new_code = '''from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from structlog import get_logger
from .jwt_utils import decode_access_token
from .storage import get_user_storage'''

content = content.replace(old_code, new_code)

# Заменяем все raise HTTPException на return JSONResponse внутри dispatch
content = content.replace(
    '''        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Отсутствует или невалидный токен авторизации"
            )''',
    '''        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Отсутствует или невалидный токен авторизации"}
            )'''
)

content = content.replace(
    '''        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Истёкший или невалидный токен"
            )''',
    '''        if not payload:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Истёкший или невалидный токен"}
            )'''
)

content = content.replace(
    '''        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Невалидный токен: отсутствует sub"
            )''',
    '''        if not username:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Невалидный токен: отсутствует sub"}
            )'''
)

content = content.replace(
    '''        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Пользователь не найден"
            )''',
    '''        if not user:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Пользователь не найден"}
            )'''
)

filepath.write_text(content, encoding="utf-8")
print("✅ AuthMiddleware исправлен! Теперь он корректно возвращает 401 JSON вместо 500.")