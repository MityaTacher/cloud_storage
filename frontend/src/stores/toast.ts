import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Toast, ToastType } from '@/types'

export const useToastStore = defineStore('toast', () => {
  const toasts = ref<Toast[]>([])

  function add(message: string, type: ToastType = 'info') {
    const id = crypto.randomUUID()
    toasts.value.push({ id, message, type })
    setTimeout(() => {
      toasts.value = toasts.value.filter((t) => t.id !== id)
    }, 3000)
  }

  function success(msg: string) { add(msg, 'success') }
  function error(msg: string) { add(msg, 'error') }
  function info(msg: string) { add(msg, 'info') }

  return { toasts, success, error, info }
})
