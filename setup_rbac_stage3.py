#!/usr/bin/env python3
"""
SCADA.AI RBAC — Этап 3: Frontend авторизация
1. Создание stores/auth.ts (управление токеном и пользователем)
2. Создание components/LoginModal.svelte (окно входа)
3. Модификация lib/api.ts (interceptor для токена и обработка 401)
4. Модификация routes/Home.svelte (интеграция LoginModal и UserMenu)

Запуск: python setup_rbac_stage3.py
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.resolve()

# ============================================================================
# 1. Создание frontend/src/stores/auth.ts
# ============================================================================

def create_auth_store():
    filepath = PROJECT_ROOT / "frontend" / "src" / "stores" / "auth.ts"
    
    content = '''import { writable, derived } from 'svelte/store'
import { navigate } from './ui'

export interface User {
  username: string
  role: 'admin' | 'engineer' | 'operator' | 'boss'
  display_name: string
}

export const currentUser = writable<User | null>(null)
export const accessToken = writable<string | null>(null)

// Инициализация из localStorage при старте
const savedToken = localStorage.getItem('scada_ai_token')
const savedUser = localStorage.getItem('scada_ai_user')

if (savedToken) accessToken.set(savedToken)
if (savedUser) {
  try {
    currentUser.set(JSON.parse(savedUser))
  } catch (e) {
    console.error('Failed to parse saved user', e)
  }
}

export const isAuthenticated = derived(
  [currentUser, accessToken],
  ([$currentUser, $accessToken]) => !!$currentUser && !!$accessToken
)

export async function login(username: string, password: string): Promise<{ success: boolean; error?: string }> {
  try {
    const response = await fetch('http://localhost:8081/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    })
    
    if (!response.ok) {
      const errorData = await response.json()
      return { success: false, error: errorData.detail || 'Ошибка авторизации' }
    }
    
    const data = await response.json()
    
    accessToken.set(data.access_token)
    currentUser.set(data.user)
    
    localStorage.setItem('scada_ai_token', data.access_token)
    localStorage.setItem('scada_ai_user', JSON.stringify(data.user))
    
    return { success: true }
  } catch (e: any) {
    return { success: false, error: e?.message || 'Ошибка соединения' }
  }
}

export function logout() {
  accessToken.set(null)
  currentUser.set(null)
  localStorage.removeItem('scada_ai_token')
  localStorage.removeItem('scada_ai_user')
  navigate('operator') // или на страницу логина, если она отдельная
}

export function hasRole(allowedRoles: string[]): boolean {
  let user: User | null = null
  currentUser.subscribe(value => { user = value })()
  return user ? allowedRoles.includes(user.role) : false
}
'''
    
    filepath.write_text(content, encoding="utf-8")
    print("  ✓ Создан: frontend/src/stores/auth.ts")
    return True


# ============================================================================
# 2. Создание frontend/src/components/LoginModal.svelte
# ============================================================================

def create_login_modal():
    filepath = PROJECT_ROOT / "frontend" / "src" / "components" / "LoginModal.svelte"
    
    content = '''<script lang="ts">
import { login } from '../stores/auth'
import { Shield } from 'lucide-svelte'

export let isOpen = false

let username = $state('')
let password = $state('')
let isLoading = $state(false)
let error = $state<string | null>(null)

async function handleSubmit() {
  if (!username || !password) {
    error = 'Введите логин и пароль'
    return
  }
  
  isLoading = true
  error = null
  
  const result = await login(username, password)
  
  if (result.success) {
    isOpen = false
    username = ''
    password = ''
  } else {
    error = result.error || 'Неверный логин или пароль'
  }
  
  isLoading = false
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter') {
    handleSubmit()
  }
}
</script>

{#if isOpen}
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
    <div class="bg-white dark:bg-neutral-800 rounded-lg shadow-2xl w-full max-w-md p-6 border border-neutral-200 dark:border-neutral-700">
      <div class="flex items-center gap-3 mb-6">
        <div class="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
          <Shield size={24} class="text-blue-600 dark:text-blue-400" />
        </div>
        <div>
          <h2 class="text-xl font-semibold text-neutral-900 dark:text-neutral-100">Вход в систему</h2>
          <p class="text-sm text-neutral-500 dark:text-neutral-400">SCADA.AI v3.3.1.1</p>
        </div>
      </div>
      
      <form on:submit|preventDefault={handleSubmit} class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1">Логин</label>
          <input 
            type="text" 
            bind:value={username} 
            on:keydown={handleKeydown}
            class="w-full px-3 py-2 border border-neutral-300 dark:border-neutral-600 rounded-md bg-white dark:bg-neutral-900 text-neutral-900 dark:text-neutral-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="admin"
            autocomplete="username"
          />
        </div>
        
        <div>
          <label class="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1">Пароль</label>
          <input 
            type="password" 
            bind:value={password} 
            on:keydown={handleKeydown}
            class="w-full px-3 py-2 border border-neutral-300 dark:border-neutral-600 rounded-md bg-white dark:bg-neutral-900 text-neutral-900 dark:text-neutral-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="••••••••"
            autocomplete="current-password"
          />
        </div>
        
        {#if error}
          <div class="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md text-sm text-red-700 dark:text-red-300">
            {error}
          </div>
        {/if}
        
        <button 
          type="submit" 
          disabled={isLoading}
          class="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-medium rounded-md transition focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:focus:ring-offset-neutral-800"
        >
          {isLoading ? 'Вход...' : 'Войти'}
        </button>
      </form>
      
      <div class="mt-4 text-center text-xs text-neutral-500 dark:text-neutral-400">
        Демо-доступ: admin / admin123
      </div>
    </div>
  </div>
{/if}
'''
    
    filepath.write_text(content, encoding="utf-8")
    print("  ✓ Создан: frontend/src/components/LoginModal.svelte")
    return True


# ============================================================================
# 3. Модификация frontend/src/lib/api.ts
# ============================================================================

def update_api_ts():
    filepath = PROJECT_ROOT / "frontend" / "src" / "lib" / "api.ts"
    
    if not filepath.exists():
        print("  ⚠️  frontend/src/lib/api.ts не найден, пропускаем")
        return True
    
    content = filepath.read_text(encoding="utf-8")
    
    # Проверяем, добавлен ли уже interceptor
    if "scada_ai_token" in content:
        print("  ⚠️  Interceptor для токена уже добавлен, пропускаем")
        return True
    
    # Если используется ky (как в предыдущих версиях)
    if "import ky from 'ky'" in content or "from 'ky'" in content:
        # Находим создание экземпляра ky и добавляем hooks
        old_ky = "export const api = ky.create({"
        new_ky = """export const api = ky.create({
  prefixUrl: 'http://localhost:8081',
  timeout: 180000,
  hooks: {
    beforeRequest: [
      request => {
        const token = localStorage.getItem('scada_ai_token')
        if (token) {
          request.headers.set('Authorization', `Bearer ${token}`)
        }
      }
    ],
    afterResponse: [
      async (request, options, response) => {
        if (response.status === 401) {
          localStorage.removeItem('scada_ai_token')
          localStorage.removeItem('scada_ai_user')
          window.location.reload()
        }
        return response
      }
    ]
  }
})"""
        if old_ky in content:
            content = content.replace(old_ky, new_ky)
        else:
            # Альтернативный вариант, если api объявлен иначе
            content = content.replace(
                "export const api = ky.extend({",
                """export const api = ky.extend({
  prefixUrl: 'http://localhost:8081',
  timeout: 180000,
  hooks: {
    beforeRequest: [
      request => {
        const token = localStorage.getItem('scada_ai_token')
        if (token) {
          request.headers.set('Authorization', `Bearer ${token}`)
        }
      }
    ],
    afterResponse: [
      async (request, options, response) => {
        if (response.status === 401) {
          localStorage.removeItem('scada_ai_token')
          localStorage.removeItem('scada_ai_user')
          window.location.reload()
        }
        return response
      }
    ]
  }
})"""
            )
    else:
        # Если используется fetch wrapper, добавляем логику туда
        print("  ⚠️  Не удалось автоматически обновить api.ts (не найден ky). Проверьте вручную.")
        return True
    
    filepath.write_text(content, encoding="utf-8")
    print("  ✓ Обновлён: frontend/src/lib/api.ts (добавлен interceptor для токена)")
    return True


# ============================================================================
# 4. Модификация frontend/src/routes/Home.svelte
# ============================================================================

def update_home_svelte():
    filepath = PROJECT_ROOT / "frontend" / "src" / "routes" / "Home.svelte"
    
    if not filepath.exists():
        print("  ⚠️  frontend/src/routes/Home.svelte не найден, пропускаем")
        return True
    
    content = filepath.read_text(encoding="utf-8")
    
    # 1. Добавляем импорты
    if "import LoginModal" not in content:
        content = content.replace(
            "import WidgetRouter from '../components/WidgetRouter.svelte'",
            "import WidgetRouter from '../components/WidgetRouter.svelte'\nimport LoginModal from '../components/LoginModal.svelte'"
        )
    
    if "import { isAuthenticated, currentUser }" not in content:
        content = content.replace(
            "import { licenseStatus, fetchLicenseStatus, startSession, endSession } from '../stores/license'",
            "import { licenseStatus, fetchLicenseStatus, startSession, endSession } from '../stores/license'\nimport { isAuthenticated, currentUser, logout } from '../stores/auth'"
        )
    
    # 2. Добавляем переменную showLoginModal
    if "let showLoginModal" not in content:
        content = content.replace(
            "let ddaForceTab = $state<'overview' | 'correlations' | 'table' | 'interpretation' | null>(null)",
            "let ddaForceTab = $state<'overview' | 'correlations' | 'table' | 'interpretation' | null>(null)\nlet showLoginModal = $derived(!$isAuthenticated)"
        )
    
    # 3. Добавляем UserMenu в хидер (справа от Online)
    if "UserMenu" not in content and "logout()" not in content:
        # Находим блок с Online и добавляем кнопку выхода
        old_online = '''<div class="flex items-center gap-2 text-sm text-neutral-700 dark:text-neutral-300 ml-2">
        <span class="w-2 h-2 rounded-full bg-green-500"></span>
        <span class="font-medium">Online</span>
      </div>'''
        
        new_online = '''<div class="flex items-center gap-2 text-sm text-neutral-700 dark:text-neutral-300 ml-2">
        <span class="w-2 h-2 rounded-full bg-green-500"></span>
        <span class="font-medium">Online</span>
      </div>
      {#if $isAuthenticated && $currentUser}
        <div class="flex items-center gap-3 ml-4 pl-4 border-l border-neutral-300 dark:border-neutral-600">
          <span class="text-sm font-medium text-neutral-800 dark:text-neutral-200">{$currentUser.display_name}</span>
          <button type="button" onclick={logout} class="text-xs px-3 py-1.5 bg-neutral-200 dark:bg-neutral-700 hover:bg-neutral-300 dark:hover:bg-neutral-600 text-neutral-800 dark:text-neutral-200 rounded transition">
            Выход
          </button>
        </div>
      {/if}'''
        
        if old_online in content:
            content = content.replace(old_online, new_online)
    
    # 4. Добавляем LoginModal в конец компонента (перед закрывающим div)
    if "<LoginModal isOpen={showLoginModal} />" not in content:
        # Находим последний закрывающий div основного контейнера
        content = content.rstrip()
        if content.endswith("</div>"):
            content = content + "\n\n<LoginModal isOpen={showLoginModal} />\n"
    
    filepath.write_text(content, encoding="utf-8")
    print("  ✓ Обновлён: frontend/src/routes/Home.svelte (интеграция LoginModal и UserMenu)")
    return True


# ============================================================================
# Main
# ============================================================================

def main() -> int:
    print("=" * 70)
    print("SCADA.AI RBAC — Этап 3: Frontend авторизация")
    print("=" * 70)
    print(f"\nКорень проекта: {PROJECT_ROOT}\n")
    
    success = True
    
    if not create_auth_store(): success = False
    if not create_login_modal(): success = False
    if not update_api_ts(): success = False
    if not update_home_svelte(): success = False
    
    if success:
        print(f"\n{'=' * 70}")
        print("✅ Этап 3 завершён!")
        print(f"{'=' * 70}")
        print("\nЧто было сделано:")
        print("  1. Создан frontend/src/stores/auth.ts (управление токеном и пользователем)")
        print("  2. Создан frontend/src/components/LoginModal.svelte (красивое окно входа)")
        print("  3. Обновлён frontend/src/lib/api.ts (автоматическая подстановка токена и logout при 401)")
        print("  4. Обновлён frontend/src/routes/Home.svelte (показ модалки если не авторизован, кнопка выхода)")
        print("\nСледующие шаги:")
        print("  1. Перезапустите frontend (npm run dev)")
        print("  2. Откройте браузер. Если вы не авторизованы, появится окно входа.")
        print("  3. Введите admin / admin123 и нажмите 'Войти'.")
        print("  4. В правом верхнем углу должно появиться имя 'Администратор' и кнопка 'Выход'.")
        print("  5. Этап 4: Frontend — UI (UsersPanel и блокировка DDA по ролям)")
        print()
        return 0
    else:
        print(f"\n{'=' * 70}")
        print("❌ ОШИБКИ при выполнении Этапа 3")
        print(f"{'=' * 70}")
        return 1


if __name__ == "__main__":
    sys.exit(main())