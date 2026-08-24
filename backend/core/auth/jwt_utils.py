"""JWT utilities — генерация и валидация токенов"""
import jwt
from datetime import datetime, timezone, timedelta
from typing import Optional
from structlog import get_logger
from config.settings import settings

log = get_logger()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Создаёт JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm
    )
    
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """Декодирует и валидирует JWT токен"""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except jwt.ExpiredSignatureError:
        log.warning("Token expired")
        return None
    except jwt.JWTError as e:
        log.warning("Invalid token", error=str(e))
        return None
    except Exception as e:
        log.error("Token decode failed", error=str(e))
        return None
