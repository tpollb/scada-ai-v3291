import { writable, derived, get } from 'svelte/store'
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
    
    // Запускаем сессию после успешного входа
    const { startSession } = await import('./license')
    await startSession()
    
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
  const user = get(currentUser)
  return user ? allowedRoles.includes(user.role) : false
}
