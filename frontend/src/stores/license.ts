import { writable, get } from 'svelte/store'
import api from '../lib/api'

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
export const sessionId = writable<string | null>(null)

let heartbeatInterval: ReturnType<typeof setInterval> | null = null

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

export async function uploadLicense(file: File): Promise<{success: boolean, message: string}> {
    try {
        const formData = new FormData()
        formData.append('file', file)
        
        const response = await fetch('http://localhost:8081/api/v1/license/upload', {
            method: 'POST',
            body: formData
        })
        
        if (!response.ok) {
            const error = await response.json()
            return { success: false, message: error.detail || `HTTP ${response.status}` }
        }
        
        const result = await response.json()
        await fetchLicenseStatus()
        
        return { success: true, message: result.message || 'Лицензия успешно загружена' }
    } catch (e: any) {
        return { success: false, message: e?.message || 'Ошибка соединения' }
    }
}

export async function startSession() {
    try {
        const response = await api.post('api/v1/license/session/start').json<{session_id: string, status: string}>()
        sessionId.set(response.session_id)
        
        if (heartbeatInterval) clearInterval(heartbeatInterval)
        heartbeatInterval = setInterval(heartbeatSession, 30000)
        
        console.log('✅ Session started:', response.session_id)
        return response.session_id
    } catch (e: any) {
        console.error('❌ Failed to start session:', e)
        return null
    }
}

export async function heartbeatSession() {
    const sid = get(sessionId)
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
    const sid = get(sessionId)
    
    // 🔍 ДИАГНОСТИКА: смотрим, что именно мы читаем из стора
    console.log('🔍 [endSession] Значение sid:', sid, '| Тип:', typeof sid)

    if (!sid || typeof sid !== 'string') {
        console.log('⚠️ endSession: session_id отсутствует или не является строкой. Пропускаем.')
        return
    }

    console.log('📤 [endSession] Формируем payload для отправки:', { session_id: sid })

    try {
        await api.post('api/v1/license/session/end', {
            json: { session_id: sid }
        })
        console.log('✅ Session ended successfully')
        
        sessionId.set(null)
        if (heartbeatInterval) {
            clearInterval(heartbeatInterval)
            heartbeatInterval = null
        }
    } catch (e: any) {
        console.error('❌ Failed to end session:', e)
        sessionId.set(null)
        if (heartbeatInterval) {
            clearInterval(heartbeatInterval)
            heartbeatInterval = null
        }
    }
}