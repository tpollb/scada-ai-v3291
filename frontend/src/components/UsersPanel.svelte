<!-- svelte-ignore a11y_label_has_associated_control -->
<script lang="ts">
import { onMount } from 'svelte'
import api from '../lib/api'
import { currentUser } from '../stores/auth'
import { Plus, Key, Trash2, X, Save, AlertCircle } from 'lucide-svelte'

interface UserInfo {
  username: string
  role: string
  display_name: string
}

let users = $state<UserInfo[]>([])
let loading = $state(true)
let error = $state<string | null>(null)

let showAddModal = $state(false)
let newUsername = $state('')
let newDisplayName = $state('')
let newRole = $state('operator')
let newPassword = $state('')
let adding = $state(false)

let showPasswordModal = $state(false)
let passwordUsername = $state('')
let newPasswordValue = $state('')
let changingPassword = $state(false)

let deleteConfirm = $state<string | null>(null)
let deleting = $state(false)

onMount(async () => {
  await loadUsers()
})

async function loadUsers() {
  loading = true
  error = null
  try {
    users = await api.get('api/v1/auth/users').json<UserInfo[]>()
  } catch (e: any) {
    error = e?.message || 'Не удалось загрузить пользователей'
  } finally {
    loading = false
  }
}

async function addUser() {
  if (!newUsername.trim()) return
  adding = true
  error = null
  try {
    await api.post('api/v1/auth/users', {
      json: {
        username: newUsername.trim(),
        password: newPassword,
        role: newRole,
        display_name: newDisplayName.trim() || newUsername.trim()
      }
    })
    showAddModal = false
    newUsername = ''
    newDisplayName = ''
    newPassword = ''
    await loadUsers()
  } catch (e: any) {
    error = e?.message || 'Ошибка создания пользователя'
  } finally {
    adding = false
  }
}

function openPasswordModal(username: string) {
  passwordUsername = username
  newPasswordValue = ''
  showPasswordModal = true
}

async function changePassword() {
  if (!newPasswordValue.trim()) return
  changingPassword = true
  error = null
  try {
    await api.put(`api/v1/auth/users/${passwordUsername}/password`, {
      json: { new_password: newPasswordValue }
    })
    showPasswordModal = false
    newPasswordValue = ''
  } catch (e: any) {
    error = e?.message || 'Ошибка смены пароля'
  } finally {
    changingPassword = false
  }
}

async function deleteUser(username: string) {
  deleting = true
  error = null
  try {
    await api.delete(`api/v1/auth/users/${username}`)
    deleteConfirm = null
    await loadUsers()
  } catch (e: any) {
    error = e?.message || 'Ошибка удаления'
  } finally {
    deleting = false
  }
}
</script>

<div class="max-w-4xl mx-auto space-y-6">
  <section class="bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded">
    <div class="px-4 py-3 border-b border-neutral-200 dark:border-neutral-700 flex items-center justify-between">
      <h3 class="font-semibold text-neutral-900 dark:text-neutral-100">Пользователи системы</h3>
      <button type="button" onclick={() => showAddModal = true} class="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition">
        <Plus size={14} />
        Добавить
      </button>
    </div>
    <div class="p-4">
      {#if error}
        <div class="mb-4 px-4 py-2 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded text-sm text-red-900 dark:text-red-100 flex items-center gap-2">
          <AlertCircle size={16} />
          {error}
        </div>
      {/if}
      
      {#if loading}
        <div class="text-center py-8 text-neutral-500">Загрузка...</div>
      {:else if users.length === 0}
        <div class="text-center py-8 text-neutral-500">Пользователи не найдены</div>
      {:else}
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-neutral-200 dark:border-neutral-700">
                <th class="text-left py-2 px-3 text-neutral-600 dark:text-neutral-400 font-medium">Логин</th>
                <th class="text-left py-2 px-3 text-neutral-600 dark:text-neutral-400 font-medium">Роль</th>
                <th class="text-left py-2 px-3 text-neutral-600 dark:text-neutral-400 font-medium">Имя</th>
                <th class="text-right py-2 px-3 text-neutral-600 dark:text-neutral-400 font-medium">Действия</th>
              </tr>
            </thead>
            <tbody>
              {#each users as user (user.username)}
                <tr class="border-b border-neutral-100 dark:border-neutral-700/50 hover:bg-neutral-50 dark:hover:bg-neutral-700/30 transition">
                  <td class="py-2.5 px-3 font-mono text-xs">{user.username}</td>
                  <td class="py-2.5 px-3">
                    <span class="px-2 py-0.5 text-xs rounded {
                      user.role === 'admin' ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300' :
                      user.role === 'engineer' ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300' :
                      user.role === 'operator' ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300' :
                      'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300'
                    }">{user.role}</span>
                  </td>
                  <td class="py-2.5 px-3 text-neutral-900 dark:text-neutral-100">{user.display_name}</td>
                  <td class="py-2.5 px-3 text-right">
                    <button type="button" onclick={() => openPasswordModal(user.username)} class="p-1 text-neutral-500 hover:text-blue-600 transition" title="Сменить пароль">
                      <Key size={14} />
                    </button>
                    {#if $currentUser?.username !== user.username}
                      <button type="button" onclick={() => deleteConfirm = user.username} class="p-1 text-neutral-500 hover:text-red-600 transition ml-1" title="Удалить">
                        <Trash2 size={14} />
                      </button>
                    {/if}
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      {/if}
    </div>
  </section>
</div>

{#if showAddModal}
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
    <div class="bg-white dark:bg-neutral-800 rounded-lg shadow-xl w-full max-w-md">
      <div class="px-6 py-4 border-b border-neutral-200 dark:border-neutral-700 flex items-center justify-between">
        <h3 class="text-lg font-semibold text-neutral-900 dark:text-neutral-100">Новый пользователь</h3>
        <button type="button" onclick={() => showAddModal = false} class="text-neutral-500 hover:text-neutral-700 dark:hover:text-neutral-300">
          <X size={20} />
        </button>
      </div>
      <div class="p-6 space-y-4">
        <label class="block">
          <span class="block text-xs font-medium text-neutral-600 dark:text-neutral-400 uppercase tracking-wide mb-1">Логин</span>
          <input type="text" bind:value={newUsername} class="w-full px-3 py-2 border border-neutral-300 dark:border-neutral-600 dark:bg-neutral-900 rounded text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="operator1" />
        </label>
        <label class="block">
          <span class="block text-xs font-medium text-neutral-600 dark:text-neutral-400 uppercase tracking-wide mb-1">Отображаемое имя</span>
          <input type="text" bind:value={newDisplayName} class="w-full px-3 py-2 border border-neutral-300 dark:border-neutral-600 dark:bg-neutral-900 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Оператор 1" />
        </label>
        <label class="block">
          <span class="block text-xs font-medium text-neutral-600 dark:text-neutral-400 uppercase tracking-wide mb-1">Роль</span>
          <select bind:value={newRole} class="w-full px-3 py-2 border border-neutral-300 dark:border-neutral-600 dark:bg-neutral-900 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="admin">admin</option>
            <option value="engineer">engineer</option>
            <option value="operator">operator</option>
            <option value="boss">boss</option>
          </select>
        </label>
        <label class="block">
          <span class="block text-xs font-medium text-neutral-600 dark:text-neutral-400 uppercase tracking-wide mb-1">Пароль</span>
          <input type="password" bind:value={newPassword} class="w-full px-3 py-2 border border-neutral-300 dark:border-neutral-600 dark:bg-neutral-900 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </label>
      </div>
      <div class="px-6 py-4 border-t border-neutral-200 dark:border-neutral-700 flex justify-end gap-3">
        <button type="button" onclick={() => showAddModal = false} class="px-4 py-2 border border-neutral-300 dark:border-neutral-600 rounded hover:bg-neutral-50 dark:hover:bg-neutral-700 transition text-sm">Отмена</button>
        <button type="button" onclick={addUser} disabled={adding} class="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 transition text-sm font-medium">
          <Save size={16} />
          {adding ? 'Создание...' : 'Создать'}
        </button>
      </div>
    </div>
  </div>
{/if}

{#if showPasswordModal}
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
    <div class="bg-white dark:bg-neutral-800 rounded-lg shadow-xl w-full max-w-md">
      <div class="px-6 py-4 border-b border-neutral-200 dark:border-neutral-700 flex items-center justify-between">
        <h3 class="text-lg font-semibold text-neutral-900 dark:text-neutral-100">Смена пароля: {passwordUsername}</h3>
        <button type="button" onclick={() => showPasswordModal = false} class="text-neutral-500 hover:text-neutral-700 dark:hover:text-neutral-300">
          <X size={20} />
        </button>
      </div>
      <div class="p-6">
        <label class="block">
          <span class="block text-xs font-medium text-neutral-600 dark:text-neutral-400 uppercase tracking-wide mb-1">Новый пароль</span>
          <input type="password" bind:value={newPasswordValue} class="w-full px-3 py-2 border border-neutral-300 dark:border-neutral-600 dark:bg-neutral-900 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </label>
      </div>
      <div class="px-6 py-4 border-t border-neutral-200 dark:border-neutral-700 flex justify-end gap-3">
        <button type="button" onclick={() => showPasswordModal = false} class="px-4 py-2 border border-neutral-300 dark:border-neutral-600 rounded hover:bg-neutral-50 dark:hover:bg-neutral-700 transition text-sm">Отмена</button>
        <button type="button" onclick={changePassword} disabled={changingPassword} class="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 transition text-sm font-medium">
          <Save size={16} />
          {changingPassword ? 'Сохранение...' : 'Сохранить'}
        </button>
      </div>
    </div>
  </div>
{/if}

{#if deleteConfirm}
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
    <div class="bg-white dark:bg-neutral-800 rounded-lg shadow-xl w-full max-w-sm">
      <div class="p-6">
        <h3 class="text-lg font-semibold text-neutral-900 dark:text-neutral-100 mb-2">Удалить пользователя?</h3>
        <p class="text-sm text-neutral-600 dark:text-neutral-400 mb-4">
          Пользователь <span class="font-mono font-medium">{deleteConfirm}</span> будет удалён. Действие необратимо.
        </p>
      </div>
      <div class="px-6 py-4 border-t border-neutral-200 dark:border-neutral-700 flex justify-end gap-3">
        <button type="button" onclick={() => deleteConfirm = null} class="px-4 py-2 border border-neutral-300 dark:border-neutral-600 rounded hover:bg-neutral-50 dark:hover:bg-neutral-700 transition text-sm">Отмена</button>
        <button type="button" onclick={() => deleteUser(deleteConfirm)} disabled={deleting} class="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50 transition text-sm font-medium">
          {deleting ? 'Удаление...' : 'Удалить'}
        </button>
      </div>
    </div>
  </div>
{/if}
