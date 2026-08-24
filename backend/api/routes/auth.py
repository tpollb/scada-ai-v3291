"""Auth API — аутентификация и управление пользователями"""
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from structlog import get_logger
from core.auth import (
    LoginRequest, LoginResponse, UserResponse, UserCreateRequest, ChangePasswordRequest,
    verify_password, create_access_token, decode_access_token,
    get_user_storage, User, UserRole, hash_password
)

log = get_logger()

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Получает текущего пользователя из JWT токена"""
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Невалидный или истёкший токен")
    
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Невалидный токен")
    
    storage = get_user_storage()
    user = storage.get_user(username)
    
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Пользователь не найден")
    
    return user

def require_role(*roles: UserRole):
    """Декоратор для проверки роли пользователя"""
    async def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Доступ запрещён. Требуется роль: {', '.join(r.value for r in roles)}"
            )
        return current_user
    return role_checker

@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest):
    """Аутентификация пользователя"""
    storage = get_user_storage()
    user = storage.get_user(req.username)
    
    if not user or not verify_password(req.password, user.password_hash):
        log.warning("Login failed", username=req.username)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный логин или пароль")
    
    access_token = create_access_token(data={"sub": user.username, "role": user.role.value})
    storage.update_last_login(user.username)
    
    log.info("User logged in", username=user.username, role=user.role.value)
    
    return LoginResponse(
        access_token=access_token,
        user=UserResponse(username=user.username, role=user.role, display_name=user.display_name)
    )

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Выход из системы"""
    log.info("User logged out", username=current_user.username)
    return {"status": "ok", "message": "Вы вышли из системы"}

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Получить информацию о текущем пользователе"""
    return UserResponse(username=current_user.username, role=current_user.role, display_name=current_user.display_name)

@router.get("/users", response_model=list[UserResponse])
async def list_users(current_user: User = Depends(require_role(UserRole.ADMIN))):
    """Получить список всех пользователей (только admin)"""
    storage = get_user_storage()
    users = storage.get_all_users()
    return [UserResponse(username=u.username, role=u.role, display_name=u.display_name) for u in users]

@router.post("/users", response_model=UserResponse)
async def create_user(req: UserCreateRequest, current_user: User = Depends(require_role(UserRole.ADMIN))):
    """Создать нового пользователя (только admin)"""
    storage = get_user_storage()
    
    if storage.get_user(req.username):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Пользователь с таким логином уже существует")
    
    user = User(
        username=req.username,
        password_hash=hash_password(req.password),
        role=req.role,
        display_name=req.display_name
    )
    
    if not storage.create_user(user):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Не удалось создать пользователя")
    
    log.info("User created", username=user.username, role=user.role.value, created_by=current_user.username)
    return UserResponse(username=user.username, role=user.role, display_name=user.display_name)

@router.delete("/users/{username}")
async def delete_user(username: str, current_user: User = Depends(require_role(UserRole.ADMIN))):
    """Удалить пользователя (только admin)"""
    if username == current_user.username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Нельзя удалить самого себя")
    
    storage = get_user_storage()
    if not storage.delete_user(username):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    
    log.info("User deleted", username=username, deleted_by=current_user.username)
    return {"status": "ok", "message": f"Пользователь {username} удалён"}

@router.put("/users/{username}/password")
async def change_password(username: str, req: ChangePasswordRequest, current_user: User = Depends(require_role(UserRole.ADMIN))):
    """Сменить пароль пользователя (только admin)"""
    storage = get_user_storage()
    
    if not storage.change_password(username, req.new_password):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    
    log.info("Password changed", username=username, changed_by=current_user.username)
    return {"status": "ok", "message": "Пароль изменён"}
