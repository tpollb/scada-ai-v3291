#!/usr/bin/env python3
"""
SCADA.AI License System — Этап 8: Полная система учёта сессий
1. Backend API endpoints для управления сессиями
2. Backend middleware логирование активности сессий
3. Frontend store с sessionStorage (при F5 не создаётся новая сессия)
4. Интеграция в Home.svelte и Config.svelte

Запуск: python setup_license_stage8.py
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.resolve()

# ============================================================================
# 1. Backend: API endpoints для сессий
# ============================================================================

def update_license_routes():
    """Добавляет endpoints для управления сессиями в license.py"""
    filepath = PROJECT_ROOT / "backend" / "api" / "routes" / "license.py"
    
    if not filepath.exists():
        print(f"❌ ОШИБКА: Файл не найден: {filepath}")
        return False
    
    content = filepath.read_text(encoding="utf-8")
    
    # Проверяем что endpoints ещё не добавлены
    if "/session/start" in content:
        print("  ⚠️  Endpoints для сессий уже существуют, пропускаем")
        return True
    
    # Добавляем импорты
    if "from pydantic import BaseModel" not in content:
        content = content.replace(
            "from fastapi import APIRouter, UploadFile, File, HTTPException",
            "from fastapi import APIRouter, UploadFile, File, HTTPException\nfrom pydantic import BaseModel\nimport uuid"
        )
    
    # Добавляем Pydantic модели перед router
    models_code = '''
# Pydantic модели для сессий
class SessionStartResponse(BaseModel):
    session_id: str
    status: str
    message: str

class SessionHeartbeatRequest(BaseModel):
    session_id: str

class SessionEndRequest(BaseModel):
    session_id: str

'''
    
    if "class SessionStartResponse" not in content:
        content = content.replace(
            'router = APIRouter(prefix="/api/v1/license", tags=["license"])',
            models_code + 'router = APIRouter(prefix="/api/v1/license", tags=["license"])'
        )
    
    # Добавляем endpoints в конец файла
    session_endpoints = '''

# ============================================================================
# Session Management Endpoints
# ============================================================================

@router.post("/session/start", response_model=SessionStartResponse)
async def start_session():
    """
    Регистрирует новую сессию пользователя.
    Вызывается фронтендом при загрузке приложения.
    
    Returns:
        session_id: Уникальный идентификатор сессии
        status: "ok" если сессия зарегистрирована
        message: Сообщение о результате
    """
    license_mgr = get_license_manager()
    if not license_mgr:
        raise HTTPException(status_code=500, detail="License manager not initialized")
    
    # Проверяем лимит пользователей
    if not license_mgr.can_add_session():
        status = license_mgr.get_status()
        raise HTTPException(
            status_code=403,
            detail=f"Превышен лимит одновременных подключений: {status.max_concurrent_users}"
        )
    
    # Генерируем уникальный session_id
    session_id = str(uuid.uuid4())
    
    # Регистрируем сессию
    license_mgr.add_session(session_id)
    
    log.info("Session started", session_id=session_id, active_sessions=license_mgr.session_tracker.active_count())
    
    return SessionStartResponse(
        session_id=session_id,
        status="ok",
        message="Сессия успешно зарегистрирована"
    )


@router.post("/session/heartbeat")
async def session_heartbeat(req: SessionHeartbeatRequest):
    """
    Обновляет heartbeat сессии.
    Вызывается фронтендом каждые 30 секунд для поддержания сессии активной.
    
    Args:
        session_id: Идентификатор сессии
    
    Returns:
        status: "ok" если heartbeat обновлён
    """
    license_mgr = get_license_manager()
    if not license_mgr:
        raise HTTPException(status_code=500, detail="License manager not initialized")
    
    # Обновляем heartbeat
    license_mgr.heartbeat(req.session_id)
    
    log.debug("Session heartbeat", session_id=req.session_id)
    
    return {"status": "ok", "message": "Heartbeat обновлён"}


@router.post("/session/end")
async def end_session(req: SessionEndRequest):
    """
    Завершает сессию пользователя.
    Вызывается фронтендом при закрытии страницы или выходе.
    
    Args:
        session_id: Идентификатор сессии
    
    Returns:
        status: "ok" если сессия завершена
    """
    license_mgr = get_license_manager()
    if not license_mgr:
        raise HTTPException(status_code=500, detail="License manager not initialized")
    
    # Удаляем сессию
    license_mgr.remove_session(req.session_id)
    
    log.info("Session ended", session_id=req.session_id, active_sessions=license_mgr.session_tracker.active_count())
    
    return {"status": "ok", "message": "Сессия завершена"}
'''
    
    # Добавляем endpoints в конец файла
    if "@router.post(\"/session/start\"" not in content:
        content += session_endpoints
    
    filepath.write_text(content, encoding="utf-8")
    print(f"  ✓ Обновлён: backend/api/routes/license.py")
    return True


# ============================================================================
# 2. Backend: Middleware логирование сессий
# ============================================================================

def update_license_middleware():
    """Добавляет логирование активности сессий в middleware"""
    filepath = PROJECT_ROOT / "backend" / "core" / "middleware" / "license.py"
    
    if not filepath.exists():
        print(f"❌ ОШИБКА: Файл не найден: {filepath}")
        return False
    
    content = filepath.read_text(encoding="utf-8")
    
    # Проверяем что логирование сессий ещё не добавлено
    if "X-Session-ID" in content:
        print("  ⚠️  Логирование сессий уже есть в middleware, пропускаем")
        return True
    
    # Находим место перед "response = await call_next(request)" и добавляем логирование
    old_code = '''    response = await call_next(request)
    
    # Если в grace period, добавляем заголовок-предупреждение для фронтенда
    if status.in_grace_period:
        response.headers["X-License-Warning"] = f"grace_period; days_remaining={status.days_remaining}"
        
    return response'''
    
    new_code = '''    # Логирование активности сессий (если передан X-Session-ID)
    session_id = request.headers.get("X-Session-ID")
    if session_id and license_mgr.session_tracker.is_active(session_id):
        license_mgr.heartbeat(session_id)
        log.debug("Session activity", session_id=session_id, path=request.url.path)
    
    response = await call_next(request)
    
    # Если в grace period, добавляем заголовок-предупреждение для фронтенда
    if status.in_grace_period:
        response.headers["X-License-Warning"] = f"grace_period; days_remaining={status.days_remaining}"
    
    # Добавляем информацию о сессиях в заголовки (для отладки)
    response.headers["X-Active-Sessions"] = str(license_mgr.session_tracker.active_count())
    response.headers["X-Max-Sessions"] = str(status.max_concurrent_users)
        
    return response'''
    
    if old_code in content:
        content = content.replace(old_code, new_code)
        filepath.write_text(content, encoding="utf-8")
        print(f"  ✓ Обновлён: backend/core/middleware/license.py")
        return True
    else:
        print("  ⚠️  Не найден маркер для вставки логирования сессий")
        return False


# ============================================================================
# 3. Frontend: Store сессий с sessionStorage
# ============================================================================

def update_license_store():
    """Добавляет sessionStorage логику в license.ts"""
    filepath = PROJECT_ROOT / "frontend" / "src" / "stores" / "license.ts"
    
    if not filepath.exists():
        print(f"❌ ОШИБКА: Файл не найден: {filepath}")
        return False
    
    content = filepath.read_text(encoding="utf-8")
    
    # Проверяем что sessionStorage ещё не добавлен
    if "SESSION_STORAGE_KEY" in content:
        print("  ⚠️  sessionStorage логика уже есть, пропускаем")
        return True
    
    # Заменяем startSession на версию с sessionStorage
    old_start = '''export async function startSession() {
  try {
    const response = await api.post('api/v1/license/session/start').json<{session_id: string, status: string}>()
    sessionId.set(response.session_id)
    
    // Запускаем heartbeat каждые 30 секунд
    if (heartbeatInterval) clearInterval(heartbeatInterval)
    heartbeatInterval = setInterval(heartbeatSession, 30000)
    
    console.log('✅ Session started:', response.session_id)
    return response.session_id
  } catch (e: any) {
    console.error('❌ Failed to start session:', e)
    return null
  }
}'''
    
    new_start = '''const SESSION_STORAGE_KEY = 'scada_ai_session_id'

export async function startSession() {
  // 1. Проверяем есть ли сохранённый session_id в sessionStorage
  let savedSessionId: string | null = null
  try {
    savedSessionId = sessionStorage.getItem(SESSION_STORAGE_KEY)
  } catch (e) {
    console.warn('sessionStorage недоступен, создаём новую сессию')
  }
  
  if (savedSessionId) {
    // Переиспользуем существующую сессию (при F5 не создаём новую)
    sessionId.set(savedSessionId)
    
    // Запускаем heartbeat для существующей сессии
    if (heartbeatInterval) clearInterval(heartbeatInterval)
    heartbeatInterval = setInterval(heartbeatSession, 30000)
    
    console.log('✅ Reusing existing session:', savedSessionId)
    return savedSessionId
  }
  
  // 2. Создаём новую сессию
  try {
    const response = await api.post('api/v1/license/session/start').json<{session_id: string, status: string}>()
    sessionId.set(response.session_id)
    
    // Сохраняем в sessionStorage
    try {
      sessionStorage.setItem(SESSION_STORAGE_KEY, response.session_id)
    } catch (e) {
      console.warn('Не удалось сохранить session_id в sessionStorage')
    }
    
    // Запускаем heartbeat каждые 30 секунд
    if (heartbeatInterval) clearInterval(heartbeatInterval)
    heartbeatInterval = setInterval(heartbeatSession, 30000)
    
    console.log('✅ New session created:', response.session_id)
    return response.session_id
  } catch (e: any) {
    console.error('❌ Failed to start session:', e)
    return null
  }
}'''
    
    if old_start in content:
        content = content.replace(old_start, new_start)
    
    # Заменяем endSession на версию с sessionStorage
    old_end = '''export async function endSession() {
  const sid = await new Promise<string | null>(resolve => {
    sessionId.subscribe(value => resolve(value))()
  })
  
  if (!sid) return
  
  try {
    await api.post('api/v1/license/session/end', {
      json: { session_id: sid }
    })
    sessionId.set(null)
    
    if (heartbeatInterval) {
      clearInterval(heartbeatInterval)
      heartbeatInterval = null
    }
    
    console.log('✅ Session ended:', sid)
  } catch (e: any) {
    console.error('❌ Failed to end session:', e)
  }
}'''
    
    new_end = '''export async function endSession() {
  const sid = await new Promise<string | null>(resolve => {
    sessionId.subscribe(value => resolve(value))()
  })
  
  if (!sid) return
  
  try {
    await api.post('api/v1/license/session/end', {
      json: { session_id: sid }
    })
    sessionId.set(null)
    
    // Удаляем из sessionStorage
    try {
      sessionStorage.removeItem(SESSION_STORAGE_KEY)
    } catch (e) {
      console.warn('Не удалось удалить session_id из sessionStorage')
    }
    
    if (heartbeatInterval) {
      clearInterval(heartbeatInterval)
      heartbeatInterval = null
    }
    
    console.log('✅ Session ended:', sid)
  } catch (e: any) {
    console.error('❌ Failed to end session:', e)
  }
}'''
    
    if old_end in content:
        content = content.replace(old_end, new_end)
    
    filepath.write_text(content, encoding="utf-8")
    print(f"  ✓ Обновлён: frontend/src/stores/license.ts")
    return True


# ============================================================================
# 4. Frontend: Интеграция в Home.svelte
# ============================================================================

def integrate_home_sessions():
    """Добавляет вызовы startSession/endSession в Home.svelte"""
    filepath = PROJECT_ROOT / "frontend" / "src" / "routes" / "Home.svelte"
    
    if not filepath.exists():
        print(f"❌ ОШИБКА: Файл не найден: {filepath}")
        return False
    
    content = filepath.read_text(encoding="utf-8")
    
    # Добавляем импорт startSession/endSession
    if "import { startSession, endSession }" not in content:
        content = content.replace(
            "import { licenseStatus, fetchLicenseStatus } from '../stores/license'",
            "import { licenseStatus, fetchLicenseStatus, startSession, endSession } from '../stores/license'"
        )
    
    # Добавляем вызов startSession в onMount
    if "await startSession()" not in content:
        content = content.replace(
            "try { await fetchLicenseStatus() } catch (e) { console.error('Failed to fetch license status:', e) }",
            "try { await fetchLicenseStatus() } catch (e) { console.error('Failed to fetch license status:', e) }\n  try { await startSession() } catch (e) { console.error('Failed to start session:', e) }"
        )
    
    # Добавляем onDestroy для endSession
    if "import { onDestroy }" not in content:
        content = content.replace(
            "import { onMount } from 'svelte'",
            "import { onMount, onDestroy } from 'svelte'"
        )
    
    # Добавляем onDestroy после onMount
    if "onDestroy(() => {" not in content:
        # Находим конец onMount блока
        marker = "try { await startSession() } catch (e) { console.error('Failed to start session:', e) }\n})"
        if marker in content:
            content = content.replace(
                marker,
                marker + "\n\nonDestroy(() => {\n  endSession()\n})"
            )
    
    filepath.write_text(content, encoding="utf-8")
    print(f"  ✓ Обновлён: frontend/src/routes/Home.svelte")
    return True


# ============================================================================
# 5. Frontend: Интеграция в Config.svelte
# ============================================================================

def integrate_config_sessions():
    """Добавляет вызовы startSession/endSession в Config.svelte"""
    filepath = PROJECT_ROOT / "frontend" / "src" / "routes" / "Config.svelte"
    
    if not filepath.exists():
        print(f"❌ ОШИБКА: Файл не найден: {filepath}")
        return False
    
    content = filepath.read_text(encoding="utf-8")
    
    # Проверяем что уже не интегрировано
    if "startSession" in content:
        print("  - Config.svelte уже интегрирован")
        return True
    
    # Добавляем импорты
    if "import { navigate } from '../stores/ui'" in content:
        content = content.replace(
            "import { navigate } from '../stores/ui'",
            "import { navigate } from '../stores/ui'\nimport { startSession, endSession } from '../stores/license'"
        )
    
    # Добавляем onDestroy
    if "import { onDestroy }" not in content:
        content = content.replace(
            "import { onMount } from 'svelte'",
            "import { onMount, onDestroy } from 'svelte'"
        )
    
    # Добавляем вызов startSession в onMount
    if "await startSession()" not in content:
        content = content.replace(
            "loading = false\n})",
            "loading = false\n  try { await startSession() } catch (e) { console.error('Failed to start session:', e) }\n})"
        )
    
    # Добавляем onDestroy
    if "onDestroy(() => {" not in content:
        content = content.replace(
            "loading = false\n  try { await startSession() } catch (e) { console.error('Failed to start session:', e) }\n})",
            "loading = false\n  try { await startSession() } catch (e) { console.error('Failed to start session:', e) }\n})\n\nonDestroy(() => {\n  endSession()\n})"
        )
    
    filepath.write_text(content, encoding="utf-8")
    print(f"  ✓ Обновлён: frontend/src/routes/Config.svelte")
    return True


# ============================================================================
# Main
# ============================================================================

def main() -> int:
    print("=" * 70)
    print("SCADA.AI License System — Этап 8: Полная система учёта сессий")
    print("=" * 70)
    print(f"\nКорень проекта: {PROJECT_ROOT}\n")
    
    print("Выполняю изменения...\n")
    
    success = True
    
    if not update_license_routes():
        success = False
    
    if not update_license_middleware():
        success = False
    
    if not update_license_store():
        success = False
    
    if not integrate_home_sessions():
        success = False
    
    if not integrate_config_sessions():
        success = False
    
    if success:
        print(f"\n{'=' * 70}")
        print("✅ Этап 8 завершён!")
        print(f"{'=' * 70}")
        print("\nЧто было сделано:")
        print("  1. Добавлены backend endpoints для сессий:")
        print("     - POST /api/v1/license/session/start")
        print("     - POST /api/v1/license/session/heartbeat")
        print("     - POST /api/v1/license/session/end")
        print("  2. Добавлено middleware логирование активности сессий")
        print("  3. Добавлена sessionStorage логика (при F5 не создаётся новая сессия)")
        print("  4. Интегрированы вызовы сессий в Home.svelte и Config.svelte")
        print("\nСледующие шаги:")
        print("  1. Перезапусти backend: uvicorn main:app --reload --host 0.0.0.0 --port 8081")
        print("  2. Перезапусти frontend: npm run dev")
        print("  3. Очисти sessionStorage в браузере (F12 → Application → Session Storage → Clear)")
        print("  4. Открой браузер и проверь:")
        print("     - В логах backend должно быть: 'Session started' или 'Reusing existing session'")
        print("     - В блоке лицензии в сайдбаре: 'Сессии: 1 / 10'")
        print("     - При F5 счётчик НЕ должен увеличиваться")
        print()
        return 0
    else:
        print(f"\n{'=' * 70}")
        print("❌ ОШИБКИ при выполнении Этапа 8")
        print(f"{'=' * 70}")
        return 1


if __name__ == "__main__":
    sys.exit(main())