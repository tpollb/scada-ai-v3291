<script lang="ts">
import { onMount } from 'svelte'
import { login } from '../stores/auth'
import api from '../lib/api'

let username = $state('')
let password = $state('')
let isLoading = $state(false)
let error = $state<string | null>(null)
let appVersion = $state('...')

onMount(async () => {
    try {
        const info = await api.get('system/info').json<{ app_version: string }>()
        appVersion = info.app_version
    } catch (e) {
        console.error('Failed to fetch system info:', e)
        appVersion = '3.3.2.3'
    }
})

async function handleSubmit() {
    if (!username || !password) {
        error = 'Введите логин и пароль'
        return
    }
    isLoading = true
    error = null
    const result = await login(username, password)
    if (result.success) {
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

<!-- Контейнер с фоновым изображением и затемнением -->
<div class="fixed inset-0 z-50 flex items-center justify-center">
    <!-- Фоновое изображение -->
    <div class="absolute inset-0 bg-cover bg-center bg-no-repeat" style="background-image: url('/media/logo.gif')"></div>
    <!-- Затемнение поверх картинки -->
    <div class="absolute inset-0 bg-black/70"></div>

    <!-- Карточка входа -->
    <div class="relative z-10 w-full max-w-sm p-5 bg-neutral-900/85 backdrop-blur-md rounded-lg shadow-2xl border border-neutral-700/50">
        <!-- Заголовок AI.SCADA -->
        <div class="text-center mb-6">
            <h1 class="text-3xl font-mono tracking-tight mb-1">
                <span class="text-blue-500">AI</span><span class="text-neutral-300">.SCADA</span>
            </h1>
            <p class="text-sm text-neutral-400">Вход в систему</p>
        </div>

        <!-- Форма входа -->
        <form onsubmit={(e) => { e.preventDefault(); handleSubmit(); }} class="space-y-3">
            <div>
                <label class="block text-sm text-neutral-300 mb-1">Логин</label>
                <input
                    type="text"
                    bind:value={username}
                    onkeydown={handleKeydown}
                    class="w-full px-3 py-1.5 border border-neutral-600 rounded-md bg-neutral-800 text-neutral-100 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    autocomplete="off"
                />
            </div>
            <div>
                <label class="block text-sm text-neutral-300 mb-1">Пароль</label>
                <input
                    type="password"
                    bind:value={password}
                    onkeydown={handleKeydown}
                    class="w-full px-3 py-1.5 border border-neutral-600 rounded-md bg-neutral-800 text-neutral-100 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    autocomplete="off"
                />
            </div>

            {#if error}
                <div class="p-2.5 bg-red-900/20 border border-red-800 rounded-md text-sm text-red-300">
                    {error}
                </div>
            {/if}

            <button
                type="submit"
                disabled={isLoading}
                class="w-full py-2 px-4 bg-neutral-900 border border-blue-500 text-neutral-100 rounded-md transition hover:bg-neutral-800 disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-neutral-900"
            >
                {isLoading ? 'Вход...' : 'Войти'}
            </button>
        </form>

        <!-- Версия внизу карточки -->
        <div class="mt-5 text-center text-xs font-mono tracking-tight text-neutral-500">
            v{appVersion}
        </div>
    </div>
</div>