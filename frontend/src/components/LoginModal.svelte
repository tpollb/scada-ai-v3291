<script lang="ts">
import { login } from '../stores/auth'
import { Shield } from 'lucide-svelte'

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
    // При успехе стор обновится, Home.svelte автоматически удалит этот компонент из DOM
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

<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
  <div class="bg-white dark:bg-neutral-800 rounded-lg shadow-2xl w-full max-w-md p-6 border border-neutral-200 dark:border-neutral-700">
    <div class="flex items-center gap-3 mb-6">
      <div class="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
        <Shield size={24} class="text-blue-600 dark:text-blue-400" />
      </div>
      <div>
        <h2 class="text-xl font-semibold text-neutral-900 dark:text-neutral-100">Вход в систему</h2>
        <p class="text-sm text-neutral-500 dark:text-neutral-400">SCADA.AI v3.3.2.0</p>
      </div>
    </div>
    
    <form onsubmit={(e) => { e.preventDefault(); handleSubmit(); }} class="space-y-4">
      <div>
        <label class="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1">Логин</label>
        <input 
          type="text" 
          bind:value={username} 
          onkeydown={handleKeydown}
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
          onkeydown={handleKeydown}
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