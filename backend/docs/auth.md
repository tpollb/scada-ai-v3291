
# Авторизация и ролевая модель SCADA.AI

**Версия**: 3.3.2.1
**Дата последнего обновления**: 2026-08-24
**Автор**: Усков Сергей Евгеньевич

---

## Оглавление

1. [Обзор системы авторизации](#обзор-системы-авторизации)
2. [Ролевая модель](#ролевая-модель)
3. [Архитектура](#архитектура)
4. [Файлы и компоненты](#файлы-и-компоненты)
5. [Механизм работы](#механизм-работы)
6. [Ролевая защита на бэкенде](#ролевая-защита-на-бэкенде)
7. [Ролевая защита на фронтенде](#ролевая-защита-на-фронтенде)
8. [API Endpoints](#api-endpoints)
9. [Управление пользователями](#управление-пользователями)
10. [Лицензирование и авторизация](#лицензирование-и-авторизация)
11. [Защита от краевых случаев](#защита-от-краевых-случаев)
12. [Примеры кода](#примеры-кода)
13. [Известные проблемы](#известные-проблемы)
14. [Быстрый старт](#быстрый-старт)

---

## Обзор системы авторизации

Система авторизации добавлена в **v3.3.2.0** и обеспечивает разграничение доступа к функциям системы в зависимости от роли пользователя.

### Что реализовано

- **Ролевая модель** — 4 роли с различными уровнями доступа
- **JWT-токены** — аутентификация через Authorization: Bearer
- **AuthMiddleware** — проверка токенов на уровне middleware
- **Ролевая защита API** — require_role зависимости на уровне endpoints
- **Управление пользователями** — создание, удаление, смена пароля (только admin)
- **Скрытие UI по ролям** — условный рендеринг элементов интерфейса

### Технологический стек

**Backend:**
- `python-jose[cryptography]` — JWT токены (создание, проверка)
- `bcrypt` — хеширование паролей
- `structlog` — логирование событий авторизации

**Frontend:**
- `svelte/store` — управление состоянием авторизации
- `ky` v2 — HTTP клиент с обработкой 401/402/403
- `lucide-svelte` — иконки для ролей

---

## Ролевая модель

### Роли и права доступа

| Роль | Описание | Доступ |
|------|----------|--------|
| `admin` | Полный доступ | Все функции, включая управление пользователями и лицензиями |
| `engineer` | Инженер | Конфигуратор, DDA, логи, чат (без управления пользователями) |
| `operator` | Оператор | Чат, базовые функции (без конфигуратора и DDA) |
| `boss` | Руководитель | Только просмотр (без настроек и анализов) |

### Матрица доступов

| Функция | admin | engineer | operator | boss |
|---------|-------|----------|----------|------|
| Чат с AI | ✅ | ✅ | ✅ | ✅ |
| Здоровье здания | ✅ | ✅ | ✅ | ✅ |
| Просмотр логов | ✅ | ✅ | ✅ | ❌ |
| DDA (Deep Analysis) | ✅ | ✅ | ❌ | ❌ |
| Конфигуратор | ✅ | ✅ | ❌ | ❌ |
| Управление пользователями | ✅ | ❌ | ❌ | ❌ |
| Загрузка лицензии | ✅ | ❌ | ❌ | ❌ |

### Иерархия ролей

```
admin (полный доступ)
├── engineer (конфигуратор, DDA, логи)
├── operator (чат, базовые функции)
└── boss (только просмотр)
```

---

## Архитектура

### Схема потока аутентификации

```
┌──────────────────────────────────────────────────────────────┐
│                        Frontend (Svelte 5)                   │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              LoginModal.svelte                          │  │
│  │  - Форма входа (логин + пароль)                        │  │
│  │  - Обработка ошибок                                    │  │
│  │  - Демо-доступ: admin / admin123                       │  │
│  └────────────────────────────────────────────────────────┘  │
│           │                                                  │
│           │ POST /api/v1/auth/login                          │
│           ▼                                                  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              auth.ts (store)                            │  │
│  │  - currentUser, accessToken                            │  │
│  │  - login(), logout(), hasRole()                        │  │
│  │  - Сохранение в localStorage                           │  │
│  │  - Восстановление сессии при перезагрузке              │  │
│  └────────────────────────────────────────────────────────┘  │
│           │                                                  │
│           │ Authorization: Bearer <token>                    │
│           ▼                                                  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              api.ts (ky HTTP клиент)                   │  │
│  │  - customFetch с обработкой 401/402/403                │  │
│  │  - Автоматическое добавление Authorization             │  │
│  │  - Автоматическое добавление Content-Type              │  │
│  └────────────────────────────────────────────────────────┘  │
│           │                                                  │
│           │ UI условный рендеринг по ролям                   │
│           ▼                                                  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              Компоненты                                 │  │
│  │  - Config.svelte: вкладка "Пользователи" (только admin)│  │
│  │  - Home.svelte: кнопка выхода, имя пользователя        │  │
│  │  - UsersPanel.svelte: управление пользователями        │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────┼───────────────────────────────┘
                               │
                               ▼
┌────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                         │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Middleware Chain                       │  │
│  │  1. LicenseMiddleware (проверка лицензии)                 │  │
│  │  2. AuthMiddleware (проверка JWT)                         │  │
│  │  3. CORSMiddleware (последний в добавлении)               │  │
│  └──────────────────────────────────────────────────────────┘  │
│           │                                                    │
│           │ request.state.user                                  │
│           ▼                                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    API Routers                            │  │
│  │  /api/v1/auth/*  (публичный: только /login)              │  │
│  │  /config/*       (ADMIN + ENGINEER)                       │  │
│  │  /api/v1/deep_analysis/*  (ADMIN + ENGINEER)             │  │
│  └──────────────────────────────────────────────────────────┘  │
│           │                                                    │
│           │ require_role(UserRole.ADMIN, ...)                   │
│           ▼                                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    core/auth/                             │  │
│  │  models.py        — User, UserRole                        │  │
│  │  password.py      — bcrypt хеширование                    │  │
│  │  jwt_utils.py     — JWT encode/decode                     │  │
│  │  storage.py       — UserStorage (users.json)              │  │
│  │  middleware.py    — AuthMiddleware                        │  │
│  │  dependencies.py  — get_current_user, require_role        │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌────────────────────────────────────────────────────────────────┐
│                   Хранилище пользователей                       │
│                   backend/data/users.json                       │
│                                                                │
│  admin / engineer / operator / boss                             │
│  Пароли хешируются через bcrypt                                 │
└────────────────────────────────────────────────────────────────┘
```

### Порядок middleware в main.py

```python
# Порядок добавления критически важен!
# CORSMiddleware должен быть добавлен ПОСЛЕДНИМ, чтобы быть ПЕРВЫМ
# в цепочке выполнения и добавлять CORS-заголовки ко всем ответам, включая ошибки.

from core.middleware.license import LicenseMiddleware
from core.auth.middleware import AuthMiddleware

app.add_middleware(LicenseMiddleware)
app.add_middleware(AuthMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,  # Обязательно True для работы с заголовком Authorization
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Файлы и компоненты

### Backend

```
backend/
├── core/
│   └── auth/                        # Авторизация и роли (v3.3.2.0+)
│       ├── __init__.py              # Экспорт всех компонентов
│       ├── models.py                # User, UserRole (Enum)
│       ├── password.py              # bcrypt хеширование
│       ├── jwt_utils.py             # JWT encode/decode
│       ├── storage.py               # UserStorage (чтение/запись users.json)
│       ├── middleware.py            # AuthMiddleware
│       └── dependencies.py          # get_current_user, require_role
│
├── api/
│   └── routes/
│       └── auth.py                  # Endpoints авторизации
│
└── data/
    └── users.json                   # Хранилище пользователей
```

### Frontend

```
frontend/src/
├── stores/
│   └── auth.ts                      # currentUser, accessToken, hasRole()
│
├── lib/
│   └── api.ts                       # ky v2 с обработкой 401/402/403
│
├── components/
│   ├── LoginModal.svelte            # Модальное окно входа
│   └── UsersPanel.svelte            # Управление пользователями (только admin)
│
└── routes/
    ├── Home.svelte                  # Отображение пользователя, кнопка выхода
    └── Config.svelte                # Вкладка "Пользователи" (только admin)
```

---

## Механизм работы

### 1. Логин

```
Пользователь вводит логин/пароль в LoginModal
↓
POST /api/v1/auth/login
{ "username": "admin", "password": "admin123" }
↓
Backend:
1. Ищем пользователя в users.json
2. Проверяем пароль через bcrypt.verify_password()
3. Если пароль неверный → 401 "Неверный логин или пароль"
4. Генерируем JWT токен с payload: { "sub": username, "role": role }
5. Обновляем last_login
6. Возвращаем: { "access_token": "...", "user": { username, role, display_name } }
↓
Frontend:
1. Сохраняем токен в localStorage: scada_ai_token
2. Сохраняем пользователя в localStorage: scada_ai_user
3. Устанавливаем currentUser и accessToken в stores
4. Запускаем сессию лицензии: startSession()
5. LoginModal автоматически скрывается (из-за $isAuthenticated)
```

### 2. Аутентифицированный запрос

```
Пользователь делает запрос (например, к /chat)
↓
Frontend (api.ts customFetch):
1. Читаем токен из localStorage
2. Добавляем заголовок: Authorization: Bearer <token>
3. Добавляем заголовок: Content-Type: application/json (если тело есть)
4. Отправляем запрос
↓
Backend (AuthMiddleware):
1. Проверяем метод: если OPTIONS → пропускаем (CORS preflight)
2. Проверяем путь: если публичный → пропускаем
3. Читаем заголовок Authorization
4. Извлекаем токен из "Bearer <token>"
5. Декодируем JWT через jwt_utils.decode_access_token()
6. Если токен невалидный/истёкший → 401
7. Извлекаем username из payload["sub"]
8. Ищем пользователя в users.json
9. Если пользователь не найден → 401
10. Устанавливаем request.state.user = user
11. Передаём запрос дальше в роутер
↓
Роутер (например, /config/*):
1. Зависимость require_role(UserRole.ADMIN, UserRole.ENGINEER)
2. Если роль пользователя не в списке → 403 "Доступ запрещён"
3. Если роль разрешена → выполняем обработчик
```

### 3. Обработка ошибок на фронтенде

```
Ответ с статусом 401:
1. Удаляем токен из localStorage
2. Удаляем пользователя из localStorage
3. Перезагружаем страницу → показывается LoginModal

Ответ с статусом 402:
1. Показываем алерт "Срок действия лицензии истёк"
2. Бросаем исключение "License expired"

Ответ с статусом 403:
1. Читаем тело ответа: { "detail": "Доступ запрещён..." }
2. Бросаем исключение с текстом ошибки
3. Компонент показывает ошибку пользователю
```

### 4. Выход из системы

```
Пользователь нажимает кнопку "Выход" в Home.svelte
↓
Frontend (auth.ts logout()):
1. Устанавливаем currentUser = null
2. Устанавливаем accessToken = null
3. Удаляем токен из localStorage
4. Удаляем пользователя из localStorage
5. Перенаправляем на страницу оператора
↓
Поскольку $isAuthenticated = false → показывается LoginModal
```

### 5. Восстановление сессии при перезагрузке

```
При загрузке страницы (инициализация auth.ts):
1. Читаем токен из localStorage: scada_ai_token
2. Если токен есть:
   a. Устанавливаем accessToken
   b. Динамически импортируем license.ts
   c. Вызываем startSession() для восстановления сессии
3. Читаем пользователя из localStorage: scada_ai_user
4. Если пользователь есть → устанавливаем currentUser
5. Поскольку $isAuthenticated = true → LoginModal НЕ показывается
```

---

## Ролевая защита на бэкенде

### AuthMiddleware

```python
# backend/core/auth/middleware.py
class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Разрешаем OPTIONS запросы (CORS preflight) без проверки токена
        if request.method == "OPTIONS":
            return await call_next(request)

        # Пропускаем публичные endpoints
        public_paths = [
            "/",
            "/health",
            "/debug/routes",
            "/api/v1/auth/login",
            "/system/info",
            "/api/v1/license/status",
        ]
        if request.url.path in public_paths or request.url.path.startswith("/docs"):
            return await call_next(request)

        # Получаем токен из заголовка
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Отсутствует или невалидный токен авторизации"}
            )

        token = auth_header.split(" ")[1]
        payload = decode_access_token(token)
        if not payload:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Истёкший или невалидный токен"}
            )

        username = payload.get("sub")
        if not username:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Невалидный токен: отсутствует sub"}
            )

        storage = get_user_storage()
        user = storage.get_user(username)
        if not user:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Пользователь не найден"}
            )

        # Сохраняем пользователя в state запроса
        request.state.user = user
        return await call_next(request)
```

### Ролевые зависимости

```python
# backend/core/auth/dependencies.py

async def get_current_user(request: Request) -> User:
    """Получает текущего пользователя из request.state"""
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется аутентификация"
        )
    return user


def require_role(*roles: UserRole):
    """Зависимость: пропускает только пользователей с указанными ролями"""
    async def role_checker(request: Request) -> User:
        user = getattr(request.state, "user", None)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Требуется аутентификация"
            )
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Доступ запрещён. Требуется роль: {', '.join(r.value for r in roles)}"
            )
        return user
    return role_checker
```

### Использование в роутерах

```python
# backend/api/routes/config.py
from fastapi import APIRouter, Depends
from core.auth.dependencies import require_role
from core.auth.models import UserRole

router = APIRouter(
    prefix="/config",
    tags=["config"],
    dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.ENGINEER))]
)


# backend/api/routes/auth.py
@router.get("/users", response_model=list[UserResponse])
async def list_users(current_user: User = Depends(require_role(UserRole.ADMIN))):
    """Получить список всех пользователей (только admin)"""
    storage = get_user_storage()
    users = storage.get_all_users()
    return [UserResponse(username=u.username, role=u.role, display_name=u.display_name) for u in users]
```

### Защищённые роуты

| Роут | Роли | Описание |
|------|------|----------|
| `/config/*` | ADMIN + ENGINEER | Все настройки конфигуратора |
| `/api/v1/deep_analysis/*` | ADMIN + ENGINEER | DDA анализ |
| `/api/v1/auth/users` | ADMIN | Список пользователей |
| `/api/v1/auth/users/{username}` | ADMIN | Удаление пользователя |
| `/api/v1/auth/users/{username}/password` | ADMIN | Смена пароля |
| `/api/v1/license/upload` | ADMIN | Загрузка лицензии |

---

## Ролевая защита на фронтенде

### Скрытие элементов по ролям

```svelte
<!-- Config.svelte: вкладка "Пользователи" видна только для admin -->
{#if $currentUser?.role === 'admin'}
<button type="button" onclick={() => activeTab = 'users'} class="...">
    <Users size={14} />
    Пользователи
</button>
{/if}
```

### Проверка роли через hasRole()

```typescript
// frontend/src/stores/auth.ts
import { get } from 'svelte/store'

export function hasRole(allowedRoles: string[]): boolean {
    const user = get(currentUser)
    return user ? allowedRoles.includes(user.role) : false
}

// Использование:
if (hasRole(['admin', 'engineer'])) {
    // Доступ разрешён
}
```

### Отображение пользователя в шапке

```svelte
<!-- Home.svelte -->
{#if $isAuthenticated && $currentUser}
<div class="flex items-center gap-3 ml-4 pl-4 border-l border-neutral-300 dark:border-neutral-600">
    <span class="text-sm font-medium text-neutral-800 dark:text-neutral-200">
        {$currentUser.display_name}
    </span>
    <button type="button" onclick={logout} class="text-xs px-3 py-1.5 ...">
        Выход
    </button>
</div>
{/if}
```

---

## API Endpoints

### Публичные (без авторизации)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/api/v1/auth/login` | Аутентификация |
| GET | `/api/v1/license/status` | Статус лицензии |
| GET | `/health` | Проверка работоспособности |
| GET | `/` | Root endpoint |

### Требуют авторизации (любая роль)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/api/v1/auth/logout` | Выход из системы |
| GET | `/api/v1/auth/me` | Текущий пользователь |
| POST | `/chat` | Диалог с AI |
| GET | `/health/*` | Health endpoints |
| POST | `/api/v1/license/session/start` | Создание сессии |
| POST | `/api/v1/license/session/heartbeat` | Heartbeat сессии |
| POST | `/api/v1/license/session/end` | Завершение сессии |

### Требуют ADMIN + ENGINEER

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/config/modules` | Список модулей |
| PUT | `/config/modules/{name}/enabled` | Включить/выключить модуль |
| GET | `/config/env` | Системная конфигурация |
| PUT | `/config/env` | Обновить конфигурацию |
| POST | `/api/v1/deep_analysis/analyze` | Запуск DDA анализа |
| POST | `/api/v1/deep_analysis/ab` | A/B сравнение |
| GET | `/api/v1/deep_analysis/tags` | Список тегов |

### Требуют ADMIN

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/api/v1/auth/users` | Список пользователей |
| POST | `/api/v1/auth/users` | Создание пользователя |
| DELETE | `/api/v1/auth/users/{username}` | Удаление пользователя |
| PUT | `/api/v1/auth/users/{username}/password` | Смена пароля |
| POST | `/api/v1/license/upload` | Загрузка лицензии |

### Примеры запросов

#### Логин

```bash
curl -X POST http://localhost:8081/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

**Ответ:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "username": "admin",
    "role": "admin",
    "display_name": "Администратор"
  }
}
```

#### Список пользователей (только admin)

```bash
curl http://localhost:8081/api/v1/auth/users \
  -H "Authorization: Bearer <admin-token>"
```

**Ответ:**
```json
[
  {"username": "admin", "role": "admin", "display_name": "Администратор"},
  {"username": "engineer", "role": "engineer", "display_name": "Инженер"},
  {"username": "operator", "role": "operator", "display_name": "Оператор"},
  {"username": "boss", "role": "boss", "display_name": "Руководитель"}
]
```

#### Создание пользователя

```bash
curl -X POST http://localhost:8081/api/v1/auth/users \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <admin-token>" \
  -d '{
    "username": "newuser",
    "password": "password123",
    "role": "operator",
    "display_name": "Новый пользователь"
  }'
```

#### Смена пароля

```bash
curl -X PUT http://localhost:8081/api/v1/auth/users/newuser/password \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <admin-token>" \
  -d '{"new_password": "newpassword123"}'
```

#### Удаление пользователя

```bash
curl -X DELETE http://localhost:8081/api/v1/auth/users/newuser \
  -H "Authorization: Bearer <admin-token>"
```

---

## Управление пользователями

### Хранилище пользователей

Файл: `backend/data/users.json`

```json
{
  "admin": {
    "username": "admin",
    "password_hash": "$2b$12$...",
    "role": "admin",
    "display_name": "Администратор",
    "created_at": "2026-08-01T00:00:00",
    "last_login": "2026-08-24T12:00:00"
  },
  "engineer": {
    "username": "engineer",
    "password_hash": "$2b$12$...",
    "role": "engineer",
    "display_name": "Инженер",
    "created_at": "2026-08-01T00:00:00",
    "last_login": null
  },
  "operator": {
    "username": "operator",
    "password_hash": "$2b$12$...",
    "role": "operator",
    "display_name": "Оператор",
    "created_at": "2026-08-01T00:00:00",
    "last_login": null
  },
  "boss": {
    "username": "boss",
    "password_hash": "$2b$12$...",
    "role": "boss",
    "display_name": "Руководитель",
    "created_at": "2026-08-01T00:00:00",
    "last_login": null
  }
}
```

### Параметры пользователей

| Поле | Тип | Описание |
|------|-----|----------|
| `username` | string | Логин (уникальный) |
| `password_hash` | string | bcrypt хеш пароля |
| `role` | string | Роль пользователя |
| `display_name` | string | Отображаемое имя |
| `created_at` | datetime | Дата создания |
| `last_login` | datetime/null | Последний вход |

### Защита от удаления себя

```python
# backend/api/routes/auth.py
@router.delete("/users/{username}")
async def delete_user(username: str, current_user: User = Depends(require_role(UserRole.ADMIN))):
    """Удалить пользователя (только admin)"""
    if username == current_user.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя удалить самого себя"
        )
    # ... удаление
```

---

## Лицензирование и авторизация

### Связь двух систем

Авторизация и лицензирование работают совместно:

1. **AuthMiddleware** проверяет токен и устанавливает `request.state.user`
2. **LicenseMiddleware** проверяет срок действия лицензии и лимит сессий
3. **Порядок middleware**: License → Auth → CORS

### Взаимодействие

```
Пользователь входит в систему
↓
1. Аутентификация (проверка логина/пароля)
2. Создание сессии лицензии: POST /api/v1/license/session/start
3. Heartbeat каждые 30 секунд: POST /api/v1/license/session/heartbeat
4. При выходе: завершение сессии: POST /api/v1/license/session/end
```

### Ограничения по лицензиям

| Тип лицензии | Макс. пользователей |
|-------------|---------------------|
| `trial` | 1 |
| `basic` | 3 |
| `standard` | 10 |
| `enterprise` | 100+ |

При превышении лимита одновременных подключений возвращаем **403** "Лимит пользователей исчерпан".

---

## Защита от краевых случаев

### Истёкший токен

```
Токен истёк → JWT decode возвращает ошибку
↓
Фронтенд получает 401
↓
1. Удаляем токен из localStorage
2. Удаляем пользователя из localStorage
3. Перезагружаем страницу
↓
Показывается LoginModal
```

### Невалидный токен

```
Токен повреждён или не соответствует секретному ключу
↓
Фронтенд получает 401 "Невалидный или истёкший токен"
↓
То же поведение, что и для истёкшего токена
```

### Пользователь не найден

```
Токен валидный, но пользователя нет в users.json
(например, пользователь был удалён после входа)
↓
Фронтенд получает 401 "Пользователь не найден"
↓
То же поведение, что и для истёкшего токена
```

### Недостаточные права

```
Пользователь с ролью "operator" пытается открыть конфигуратор
↓
Фронтенд скрывает кнопку конфигуратора (условный рендеринг)
Но если пользователь всё же попытается открыть /config/*:
↓
Backend возвращает 403 "Доступ запрещён. Требуется роль: admin, engineer"
↓
Фронтенд показывает ошибку пользователю
```

### Восстановление сессии при перезагрузке

```
Пользователь перезагружает страницу
↓
1. Читаем токен из localStorage
2. Если токен есть → вызываем startSession()
3. Backend проверяет токен (он ещё валиден)
4. Восстанавливаем сессию лицензии
5. Пользователь остаётся в системе
```

---

## Примеры кода

### Референс: защита от краевых случаев

Как и в `modules/deep_analysis/analyzers/ab.py`, система авторизации использует безопасные хелперы:

```python
# backend/core/auth/jwt_utils.py
def decode_access_token(token: str) -> Optional[dict]:
    """Декодирует JWT токен. Возвращает None при любой ошибке."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        log.warning("Token expired")
        return None
    except jwt.InvalidTokenError as e:
        log.warning("Invalid token", error=str(e))
        return None
    except Exception as e:
        log.error("Token decode failed", error=str(e))
        return None
```

```python
# backend/core/auth/password.py
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет пароль. Возвращает False при любой ошибке."""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception as e:
        log.error("Password verification failed", error=str(e))
        return False
```

### Пример: полный цикл авторизации

```typescript
// frontend/src/stores/auth.ts

// 1. Логин
const result = await login('admin', 'admin123')
if (result.success) {
    // Токен сохранён, сессия запущена
}

// 2. Проверка роли
if (hasRole(['admin', 'engineer'])) {
    // Доступ разрешён
}

// 3. Выход
logout()
```

---

## Известные проблемы

### Текущие ограничения

1. **Локальное хранилище пользователей** — `users.json` не подходит для кластера
   - **Решение для продакшена**: миграция на PostgreSQL

2. **In-memory сессии лицензий** — при перезапуске backend счётчик сессий обнуляется
   - **Решение для продакшена**: использовать Redis

3. **JWT без refresh токена** — после истечения токена нужно заново входить
   - **Решение**: добавить refresh токены

4. **Нет двухфакторной аутентификации**
   - **Решение**: добавить 2FA для критичных систем

### Решённые проблемы

| Проблема | Решение | Версия |
|----------|---------|--------|
| Ошибка 422 при завершении сессии | Клонирование заголовков в `customFetch` | 3.3.2.1 |
| Потеря заголовков в `ky` v2 | Использование `new Request(input, { headers })` | 3.3.2.1 |
| Антипаттерн с `Promise` и `subscribe` | Заменён на `get(sessionId)` | 3.3.2.1 |
| Вкладка "Пользователи" не рендерилась | Добавлен блок `{:else if activeTab === 'users'}` | 3.3.2.1 |

---

## Быстрый старт

### Демо-доступ

| Логин | Пароль | Роль | Доступ |
|-------|--------|------|--------|
| admin | admin123 | admin | Полный |
| engineer | engineer123 | engineer | Конфигуратор, DDA |
| operator | operator123 | operator | Чат, базовые функции |
| boss | boss123 | boss | Только просмотр |

### Проверка ролевой модели

```bash
# Попытка доступа к /config как operator (должен быть 403)
curl http://localhost:8081/config/modules \
  -H "Authorization: Bearer <operator-token>"

# Доступ к /config как engineer (должен быть 200)
curl http://localhost:8081/config/modules \
  -H "Authorization: Bearer <engineer-token>"
```

---

## Ссылки на документацию

- [ARCHITECTURE.md](ARCHITECTURE.md) — архитектура системы
- [MODULES.md](MODULES.md) — описание модулей
- [LICENSING.md](LICENSING.md) — система лицензирования
- [CHANGELOG.md](CHANGELOG.md) — история изменений

---

**Версия**: 3.3.2.1
**Дата**: 2026-08-24
**Автор**: Усков Сергей Евгеньевич
```

---