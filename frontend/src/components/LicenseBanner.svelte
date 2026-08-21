<script lang="ts">
  import { licenseStatus } from '../stores/license'
  import { AlertTriangle, XCircle } from 'lucide-svelte'
  
  $: status = $licenseStatus
  $: showWarning = status?.in_grace_period
  $: showExpired = status?.expired
</script>

{#if showWarning}
  <div class="bg-yellow-50 dark:bg-yellow-900/20 border-b border-yellow-200 dark:border-yellow-800 px-6 py-3 flex items-center gap-3">
    <AlertTriangle size={18} class="text-yellow-600 dark:text-yellow-400 flex-shrink-0" />
    <div class="flex-1 text-sm">
      <span class="font-semibold text-yellow-900 dark:text-yellow-100">Лицензия истекает</span>
      <span class="text-yellow-700 dark:text-yellow-300 ml-2">
        Осталось дней: <span class="font-mono font-bold">{status?.days_remaining}</span>
      </span>
      <span class="text-yellow-600 dark:text-yellow-400 ml-2">
        Обратитесь к администратору для продления.
      </span>
    </div>
  </div>
{:else if showExpired}
  <div class="bg-red-50 dark:bg-red-900/20 border-b border-red-200 dark:border-red-800 px-6 py-3 flex items-center gap-3">
    <XCircle size={18} class="text-red-600 dark:text-red-400 flex-shrink-0" />
    <div class="flex-1 text-sm">
      <span class="font-semibold text-red-900 dark:text-red-100">Лицензия истекла</span>
      <span class="text-red-700 dark:text-red-300 ml-2">
        Система заблокирована. Обратитесь к администратору для продления лицензии.
      </span>
    </div>
  </div>
{/if}
