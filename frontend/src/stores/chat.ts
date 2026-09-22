import { writable } from 'svelte/store'
// Генерация ID сообщений с фолбэком для non-secure contexts
function generateId(): string {
    if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
        return generateId()
    }
    // Fallback: Math.random + Date.now (достаточно для ID сообщений)
    return `${Date.now()}-${Math.random().toString(36).slice(2, 11)}`
}

export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: number
}

export const messages = writable<Message[]>([])
export const isLoading = writable(false)

export function addMessage(role: Message['role'], content: string) {
  messages.update(msgs => [...msgs, {
    id: generateId(),
    role,
    content,
    timestamp: Date.now()
  }])
}

export function clearMessages() {
  messages.set([])
}
