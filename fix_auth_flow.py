#!/usr/bin/env python3
"""
Исправление потока аутентификации:
1. Добавление /system/info и /api/v1/license/status в публичные пути middleware.
2. Вызов startSession() только при наличии токена (при загрузке или после логина).
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.resolve()

# ============================================================================
# 1. Обновление backend/core/auth/middleware.py
# ============================================================================

def fix_middleware_public_paths():
    filepath = PROJECT_ROOT / "backend" / "core" / "auth" / "middleware.py"
    if not filepath.exists():
        print("❌ Файл middleware.py не найден")
        return False
    
    content = filepath.read_text(encoding="utf-8")
    
    # Обновляем список public_paths
    old_paths = '''public_paths = [
            "/",
            "/health",
            "/debug/routes",
            "/api/v1/auth/login",
        ]'''
    
    new_paths = '''public_paths = [
            "/",
            "/health",
            "/debug/routes",
            "/api/v1/auth/login",
            "/system/info",
            "/api/v1/license/status",
        ]'''
    
    if old_paths in content:
        content = content.replace(old_paths, new_paths)
        filepath.write_text(content, encoding="utf-8")
        print("  ✓ Обновлены публичные пути в AuthMiddleware")
    else:
        print("  ⚠️  Не удалось найти public_paths, возможно, уже обновлено или формат изменён")
    
    return True


# ============================================================================
# 2. Обновление frontend/src/stores/auth.ts
# ============================================================================

def fix_auth_store():
    filepath = PROJECT_ROOT / "frontend" / "src" / "stores" / "auth.ts"
    if not filepath.exists():
        print("❌ Файл auth.ts не найден")
        return False
    
    content = filepath.read_text(encoding="utf-8")
    
    # 1. Добавляем вызов startSession при инициализации, если есть токен
    old_init = '''// Инициализация из localStorage при старте
const savedToken = localStorage.getItem('scada_ai_token')
const savedUser = localStorage.getItem('scada_ai_user')

if (savedToken) accessToken.set(savedToken)
if (savedUser) {
  try {
    currentUser.set(JSON.parse(savedUser))
  } catch (e) {
    console.error('Failed to parse saved user', e)
  }
}'''
    
    new_init = '''// Инициализация из localStorage при старте
const savedToken = localStorage.getItem('scada_ai_token')
const savedUser = localStorage.getItem('scada_ai_user')

if (savedToken) {
  accessToken.set(savedToken)
  // Восстанавливаем сессию при перезагрузке страницы, если токен есть
  import('../stores/license').then(({ startSession }) => {
    startSession().catch(e => console.error('Failed to restore session:', e))
  })
}
if (savedUser) {
  try {
    currentUser.set(JSON.parse(savedUser))
  } catch (e) {
    console.error('Failed to parse saved user', e)
  }
}'''
    
    if old_init in content:
        content = content.replace(old_init, new_init)
    
    # 2. Добавляем вызов startSession после успешного логина
    old_login_success = '''    if (result.success) {
    isOpen = false
    username = ''
    password = ''
  }'''
  # Это из LoginModal, но нам нужно в auth.ts
  # Найдем место в login() функции
  
    old_login_return = '''    localStorage.setItem('scada_ai_token', data.access_token)
    localStorage.setItem('scada_ai_user', JSON.stringify(data.user))
    
    return { success: true }'''
    
    new_login_return = '''    localStorage.setItem('scada_ai_token', data.access_token)
    localStorage.setItem('scada_ai_user', JSON.stringify(data.user))
    
    // Запускаем сессию после успешного входа
    const { startSession } = await import('./license')
    await startSession()
    
    return { success: true }'''
    
    if old_login_return in content:
        content = content.replace(old_login_return, new_login_return)
        print("  ✓ Добавлен вызов startSession() после успешного логина и при инициализации")
    else:
        print("  ⚠️  Не удалось найти место для вставки startSession в login()")
    
    filepath.write_text(content, encoding="utf-8")
    return True


# ============================================================================
# 3. Обновление frontend/src/routes/Home.svelte
# ============================================================================

def fix_home_svelte():
    filepath = PROJECT_ROOT / "frontend" / "src" / "routes" / "Home.svelte"
    if not filepath.exists():
        print("❌ Файл Home.svelte не найден")
        return False
    
    content = filepath.read_text(encoding="utf-8")
    
    # Убираем startSession из onMount, так как теперь он вызывается в auth.ts
    # Но оставляем его в try/catch на всякий случай, просто чтобы не ломать, 
    # или лучше убрать, чтобы не было лишних 401 до логина.
    
    old_onmount = '''onMount(async () => {
  try { health = await getHealth() } catch (e) { console.error('Failed to fetch health:', e) }
  try { systemInfo = await api.get('system/info').json<SystemInfo>() } catch (e) { console.error('Failed to fetch system info:', e) }
  try { await fetchLicenseStatus() } catch (e) { console.error('Failed to fetch license status:', e) }
  try { await startSession() } catch (e) { console.error('Failed to start session:', e) }
})'''
    
    new_onmount = '''onMount(async () => {
  try { health = await getHealth() } catch (e) { console.error('Failed to fetch health:', e) }
  try { systemInfo = await api.get('system/info').json<SystemInfo>() } catch (e) { console.error('Failed to fetch system info:', e) }
  try { await fetchLicenseStatus() } catch (e) { console.error('Failed to fetch license status:', e) }
  // startSession() теперь вызывается внутри auth.ts при инициализации или логине
})'''
    
    if old_onmount in content:
        content = content.replace(old_onmount, new_onmount)
        print("  ✓ Убран дублирующий вызов startSession() из onMount в Home.svelte")
    
    # Также нужно убрать импорт startSession, если он больше не используется напрямую здесь
    # Но он может использоваться в onDestroy, так что оставим импорт.
    
    filepath.write_text(content, encoding="utf-8")
    return True


# ============================================================================
# Main
# ============================================================================

def main() -> int:
    print("=" * 70)
    print("Исправление потока аутентификации (401 ошибки)")
    print("=" * 70)
    
    success = True
    if not fix_middleware_public_paths(): success = False
    if not fix_auth_store(): success = False
    if not fix_home_svelte(): success = False
    
    if success:
        print("\n✅ Исправления применены!")
        print("\nСледующие шаги:")
        print("1. Перезапусти backend (Ctrl+C, затем uvicorn main:app --reload ...)")
        print("2. Обнови страницу в браузере (Ctrl + F5)")
        print("3. Ты должен увидеть экран входа. Ошибок 401 в консоли быть не должно.")
        print("4. Введи admin / admin123. После входа сессия создастся, и данные загрузятся.")
    else:
        print("\n❌ Ошибки при применении исправлений")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())