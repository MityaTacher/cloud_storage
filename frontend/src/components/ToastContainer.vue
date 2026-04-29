<script setup lang="ts">
import { useToastStore } from '@/stores/toast'
import { TransitionGroup } from 'vue'

const toast = useToastStore()

const icons: Record<string, string> = {
  success: 'pi pi-check-circle',
  error: 'pi pi-times-circle',
  info: 'pi pi-info-circle',
}
</script>

<template>
  <div class="toast-container" aria-live="polite">
    <TransitionGroup name="toast-slide">
      <div
        v-for="t in toast.toasts"
        :key="t.id"
        :class="['toast', t.type]"
        role="alert"
      >
        <i :class="icons[t.type]" />
        {{ t.message }}
      </div>
    </TransitionGroup>
  </div>
</template>

<style scoped>
.toast-slide-enter-active { transition: all 0.3s ease; }
.toast-slide-leave-active { transition: all 0.25s ease; }
.toast-slide-enter-from { transform: translateX(120%); opacity: 0; }
.toast-slide-leave-to { transform: translateX(120%); opacity: 0; }
</style>
