<script lang="ts">
import { onMount } from 'svelte'
import { licenseStatus, fetchLicenseStatus, uploadLicense } from '../stores/license'
import { Shield, ShieldCheck, ShieldAlert, ShieldX, Upload, FileText, CheckCircle, XCircle, AlertCircle } from 'lucide-svelte'

let uploading = $state(false)
let message = $state<{type: 'success' | 'error', text: string} | null>(null)
let dragOver = $state(false)

const MAX_FILE_SIZE = 1024 * 1024 // 1MB

onMount(async () => {
  await fetchLicenseStatus()
})

async function handleFileSelect(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files && input.files.length > 0) {
    await uploadFile(input.files[0])
    input.value = '' // Reset input
  }
}

function handleDragOver(event: DragEvent) {
  event.preventDefault()
  dragOver = true
}

function handleDragLeave() {
  dragOver = false
}

async function handleDrop(event: DragEvent) {
  event.preventDefault()
  dragOver = false
  
  if (event.dataTransfer?.files && event.dataTransfer.files.length > 0) {
    await uploadFile(event.dataTransfer.files[0])
  }
}

async function uploadFile(file: File) {
  message = null
  
  // Валидация расширения
  if (!file.name.endsWith('.lic')) {
    message = { type: 'error', text: 'Файл должен иметь расширение .lic' }
    return
  }
  
  // Валидация размера
  if (file.size > MAX_FILE_SIZE) {
    message = { type: 'error', text: 'Размер файла не должен превышать 1MB' }
    return
  }
  
  uploading = true
  
  try {
    const result = await uploadLicense(file)
    message = { type: result.success ? 'success' : 'error', text: result.message }
    
    // Очищаем сообщение через 5 секунд
    setTimeout(() => { message = null }, 5000)
  } catch (e: any) {
    message = { type: 'error', text: e?.message || 'Ошибка загрузки лицензии' }
  } finally {
    uploading = false
  }
}
</script>

<div class="max-w-4xl mx-auto space-y-6">
  <!-- Статус лицензии -->
  <section class="bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded">
    <div class="px-4 py-3 border-b border-neutral-200 dark:border-neutral-700 flex items-center gap-2">
      {#if $licenseStatus?.expired}
        <ShieldX size={18} class="text-red-600 dark:text-red-400" />
      {:else if $licenseStatus?.in_grace_period}
        <ShieldAlert size={14} class="text-yellow-600 dark:text-yellow-400" />
      {:else if $licenseStatus?.valid}
        <ShieldCheck size={18} class="text-green-600 dark:text-green-400" />
      {:else}
        <AlertCircle size={18} class="text-neutral-500" />
      {/if}
      <h3 class="font-semibold text-neutral-900 dark:text-neutral-100">Статус лицензии</h3>
    </div>
    <div class="p-4 space-y-3">
      {#if $licenseStatus}
        <div class="grid grid-cols-2 gap-4">
          <div>
            <div class="text-xs text-neutral-500 dark:text-neutral-400 uppercase tracking-wide mb-1">Клиент</div>
            <div class="text-sm font-medium text-neutral-900 dark:text-neutral-100">
              {$licenseStatus.customer || 'Неизвестно'}
            </div>
          </div>
          <div>
            <div class="text-xs text-neutral-500 dark:text-neutral-400 uppercase tracking-wide mb-1">Тип</div>
            <div class="text-sm font-mono text-neutral-900 dark:text-neutral-100">
              {#if $licenseStatus.license_type === 'trial'}Пробная
              {:else if $licenseStatus.license_type === 'basic'}Базовая
              {:else if $licenseStatus.license_type === 'standard'}Стандартная
              {:else if $licenseStatus.license_type === 'enterprise'}Корпоративная
              {:else}{$licenseStatus.license_type || '—'}
              {/if}
            </div>
          </div>
          <div>
            <div class="text-xs text-neutral-500 dark:text-neutral-400 uppercase tracking-wide mb-1">Статус</div>
            <div class="text-sm font-mono {
              $licenseStatus.expired ? 'text-red-600 dark:text-red-400' :
              $licenseStatus.in_grace_period ? 'text-yellow-600 dark:text-yellow-400' :
              'text-green-600 dark:text-green-400'
            }">
              {#if $licenseStatus.expired}
                Истекла
              {:else if $licenseStatus.in_grace_period}
                Истекает ({$licenseStatus.days_remaining} дн.)
              {:else if $licenseStatus.valid}
                Действует
              {:else}
                Не загружена
              {/if}
            </div>
          </div>
          <div>
            <div class="text-xs text-neutral-500 dark:text-neutral-400 uppercase tracking-wide mb-1">Сессии</div>
            <div class="text-sm font-mono text-neutral-900 dark:text-neutral-100">
              {$licenseStatus.current_users ?? 0} / {$licenseStatus.max_concurrent_users ?? 0}
            </div>
          </div>
        </div>
        
        {#if $licenseStatus.features && $licenseStatus.features.length > 0}
          <div>
            <div class="text-xs text-neutral-500 dark:text-neutral-400 uppercase tracking-wide mb-2">Доступные модули</div>
            <div class="flex flex-wrap gap-1">
              {#each $licenseStatus.features as feature}
                <span class="px-2 py-0.5 bg-neutral-100 dark:bg-neutral-700 border border-neutral-200 dark:border-neutral-600 rounded text-xs font-mono text-neutral-700 dark:text-neutral-300">
                  {feature}
                </span>
              {/each}
            </div>
          </div>
        {/if}
      {:else}
        <div class="text-center py-8 text-neutral-500 dark:text-neutral-400">
          <AlertCircle size={32} class="mx-auto mb-2 opacity-50" />
          <div class="text-sm">Лицензия не загружена</div>
          <div class="text-xs mt-1">Загрузите файл .lic для активации системы</div>
        </div>
      {/if}
    </div>
  </section>
  
  <!-- Загрузка новой лицензии -->
  <section class="bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded">
    <div class="px-4 py-3 border-b border-neutral-200 dark:border-neutral-700 flex items-center gap-2">
      <Upload size={18} class="text-neutral-600 dark:text-neutral-400" />
      <h3 class="font-semibold text-neutral-900 dark:text-neutral-100">Загрузить новую лицензию</h3>
    </div>
    <div class="p-4 space-y-4">
      <!-- Drag & drop зона -->
      <div
        class="border-2 border-dashed rounded-lg p-8 text-center transition {
          dragOver
            ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
            : 'border-neutral-300 dark:border-neutral-600 hover:border-neutral-400 dark:hover:border-neutral-500'
        }"
        ondragover={handleDragOver}
        ondragleave={handleDragLeave}
        ondrop={handleDrop}
      >
        <FileText size={48} class="mx-auto mb-3 text-neutral-400 dark:text-neutral-500" />
        <div class="text-sm text-neutral-700 dark:text-neutral-300 mb-2">
          Перетащите файл лицензии сюда
        </div>
        <div class="text-xs text-neutral-500 dark:text-neutral-400 mb-4">
          или выберите файл вручную
        </div>
        <label class="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition text-sm font-medium cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed">
          <Upload size={16} />
          {uploading ? 'Загрузка...' : 'Выбрать файл'}
          <input
            type="file"
            accept=".lic"
            class="hidden"
            onchange={handleFileSelect}
            disabled={uploading}
          />
        </label>
      </div>
      
      <!-- Сообщение -->
      {#if message}
        <div class="flex items-start gap-2 p-3 rounded {
          message.type === 'success'
            ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800'
            : 'bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800'
        }">
          {#if message.type === 'success'}
            <CheckCircle size={18} class="text-green-600 dark:text-green-400 flex-shrink-0 mt-0.5" />
          {:else}
            <XCircle size={18} class="text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
          {/if}
          <div class="text-sm {
            message.type === 'success'
              ? 'text-green-900 dark:text-green-100'
              : 'text-red-900 dark:text-red-100'
          }">
            {message.text}
          </div>
        </div>
      {/if}
      
      <!-- Подсказка -->
      <div class="text-xs text-neutral-500 dark:text-neutral-400">
        <div class="font-medium mb-1">Требования к файлу лицензии:</div>
        <ul class="list-disc list-inside space-y-0.5">
          <li>Расширение: <span class="font-mono">.lic</span></li>
          <li>Максимальный размер: 1MB</li>
          <li>Формат: JWT с подписью RSA-2048</li>
        </ul>
      </div>
    </div>
  </section>
</div>
