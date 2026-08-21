#!/usr/bin/env python3
"""
SCADA.AI License System — Этап 7: Система учёта сессий
1. Backend API endpoints для управления сессиями
2. Frontend store с функциями сессий
3. Интеграция в Home.svelte и Config.svelte

Запуск: python setup_license_stage7.py
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
# 2. Frontend: Store сессий
# ============================================================================

def update_license_store():
    """Добавляет функции управления сессиями в license.ts"""
    filepath = PROJECT_ROOT / "frontend" / "src" / "stores" / "license.ts"
    
    if not filepath.exists():
        print(f"❌ ОШИБКА: Файл не найден: {filepath}")
        return False
    
    content = filepath.read_text(encoding="utf-8")
    
    # Проверяем что функции ещё не добавлены
    if "startSession" in content:
        print("  ⚠️  Функции сессий уже есть в license.ts, пропускаем")
        return True
    
    # Добавляем импорты
    if "import api from" not in content:
        content = "import api from '../lib/api'\n" + content
    
    # Добавляем sessionId store
    if "export const sessionId" not in content:
        content += "\nexport const sessionId = writable<string | null>(null)\n"
    
    # Добавляем функции
    session_functions = '''

// ============================================================================
// Session Management
// ============================================================================

const SESSION_STORAGE_KEY = 'scada_ai_session_id'
let heartbeatInterval: ReturnType<typeof setInterval> | null = null

export async function startSession() {
  // Проверяем есть ли сохранённый session_id в sessionStorage
  const savedSessionId = sessionStorage.getItem(SESSION_STORAGE_KEY)
  
  if (savedSessionId) {
    // Используем существующую сессию (при F5 не создаём новую)
    sessionId.set(savedSessionId)
    
    // Запускаем heartbeat для существующей сессии
    if (heartbeatInterval) clearInterval(heartbeatInterval)
    heartbeatInterval = setInterval(heartbeatSession, 30000)
    
    console.log('✅ Reusing existing session:', savedSessionId)
    return savedSessionId
  }
  
  // Создаём новую сессию
  try {
    const response = await api.post('api/v1/license/session/start').json<{session_id: string, status: string}>()
    sessionId.set(response.session_id)
    sessionStorage.setItem(SESSION_STORAGE_KEY, response.session_id)
    
    // Запускаем heartbeat каждые 30 секунд
    if (heartbeatInterval) clearInterval(heartbeatInterval)
    heartbeatInterval = setInterval(heartbeatSession, 30000)
    
    console.log('✅ New session created:', response.session_id)
    return response.session_id
  } catch (e: any) {
    console.error('❌ Failed to start session:', e)
    return null
  }
}

export async function heartbeatSession() {
  const sid = await new Promise<string | null>(resolve => {
    sessionId.subscribe(value => resolve(value))()
  })
  
  if (!sid) return
  
  try {
    await api.post('api/v1/license/session/heartbeat', {
      json: { session_id: sid }
    })
  } catch (e: any) {
    console.error('❌ Heartbeat failed:', e)
  }
}

export async function endSession() {
  const sid = await new Promise<string | null>(resolve => {
    sessionId.subscribe(value => resolve(value))()
  })
  
  if (!sid) return
  
  try {
    await api.post('api/v1/license/session/end', {
      json: { session_id: sid }
    })
    sessionId.set(null)
    sessionStorage.removeItem(SESSION_STORAGE_KEY)
    
    if (heartbeatInterval) {
      clearInterval(heartbeatInterval)
      heartbeatInterval = null
    }
    
    console.log('✅ Session ended:', sid)
  } catch (e: any) {
    console.error('❌ Failed to end session:', e)
  }
}
'''
    
    content += session_functions
    filepath.write_text(content, encoding="utf-8")
    print(f"  ✓ Обновлён: frontend/src/stores/license.ts")
    return True


# ============================================================================
# 3. Frontend: Интеграция в Home.svelte
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
# 4. Frontend: Интеграция в Config.svelte
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
    print("SCADA.AI License System — Этап 7: Система учёта сессий")
    print("=" * 70)
    print(f"\nКорень проекта: {PROJECT_ROOT}\n")
    
    print("Выполняю изменения...\n")
    
    success = True
    
    if not update_license_routes():
        success = False
    
    if not update_license_store():
        success = False
    
    if not integrate_home_sessions():
        success = False
    
    if not integrate_config_sessions():
        success = False
    
    if success:
        print(f"\n{'=' * 70}")
        print("✅ Этап 7 завершён!")
        print(f"{'=' * 70}")
        print("\nЧто было сделано:")
        print("  1. Добавлены backend endpoints для сессий:")
        print("     - POST /api/v1/license/session/start")
        print("     - POST /api/v1/license/session/heartbeat")
        print("     - POST /api/v1/license/session/end")
        print("  2. Добавлены frontend функции: startSession, heartbeatSession, endSession")
        print("  3. Используется sessionStorage для сохранения session_id (при F5 не создаётся новая сессия)")
        print("  4. Интегрированы вызовы сессий в Home.svelte и Config.svelte")
        print("\nСледующие шаги:")
        print("  1. Перезапусти backend: uvicorn main:app --reload --host 0.0.0.0 --port 8081")
        print("  2. Перезапусти frontend: npm run dev")
        print("  3. Открой браузер и проверь:")
        print("     - В логах backend должно быть: 'Session started' или 'Reusing existing session'")
        print("     - В блоке лицензии в сайдбаре: 'Сессии: 1 / 10'")
        print("     - При F5 счётчик НЕ должен увеличиваться")
        print()
        return 0
    else:
        print(f"\n{'=' * 70}")
        print("❌ ОШИБКИ при выполнении Этапа 7")
        print(f"{'=' * 70}")
        return 1


if __name__ == "__main__":
    sys.exit(main())