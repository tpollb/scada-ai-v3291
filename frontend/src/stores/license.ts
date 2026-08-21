import api from '../lib/api'
import { writable } from 'svelte/store'

export interface LicenseStatus {
  valid: boolean
  expired: boolean
  in_grace_period: boolean
  days_remaining: number
  license_type: string
  features: string[]
  customer: string
  max_concurrent_users: number
  current_users: number
}

export const licenseStatus = writable<LicenseStatus | null>(null)
export const licenseError = writable<string | null>(null)

export async function fetchLicenseStatus() {
  try {
    const response = await fetch('http://localhost:8081/api/v1/license/status')
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }
    const status: LicenseStatus = await response.json()
    licenseStatus.set(status)
    licenseError.set(null)
    return status
  } catch (e: any) {
    licenseError.set(e?.message || 'Failed to fetch license status')
    return null
  }
}

export const sessionId = writable<string | null>(null)


// ============================================================================
// Session Management
// ============================================================================

let heartbeatInterval: ReturnType<typeof setInterval> | null = null

const SESSION_STORAGE_KEY = 'scada_ai_session_id'

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
}
