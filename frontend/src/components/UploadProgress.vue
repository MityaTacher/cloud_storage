<script setup lang="ts">
import { useFileStore } from '@/stores/files'

const store = useFileStore()
</script>

<template>
  <Transition name="slide-up">
    <div v-if="store.uploads.length" class="upload-panel">
      <div class="upload-panel-header">
        <span>Uploading {{ store.uploads.length }} file(s)</span>
      </div>
      <div class="upload-list">
        <div v-for="task in store.uploads" :key="task.id" class="upload-item">
          <div class="upload-item-top">
            <i class="pi pi-file" />
            <span class="upload-name">{{ task.name }}</span>
            <span v-if="task.done" class="upload-status done"><i class="pi pi-check" /></span>
            <span v-else-if="task.error" class="upload-status err"><i class="pi pi-times" /></span>
            <span v-else class="upload-pct">{{ task.progress }}%</span>
          </div>
          <div class="upload-progress">
            <div
              class="upload-progress-bar"
              :style="{ width: task.done ? '100%' : `${task.progress}%`,
                        background: task.error ? '#ef4444' : undefined }"
            />
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.upload-panel {
  position: fixed;
  bottom: 24px;
  right: 24px;
  width: 320px;
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  z-index: 200;
  overflow: hidden;
}
.upload-panel-header {
  padding: 12px 16px;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-secondary);
  border-bottom: 1px solid var(--color-border);
}
.upload-list { padding: 12px; display: flex; flex-direction: column; gap: 10px; }
.upload-item {}
.upload-item-top {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
  font-size: 13px;
  color: var(--color-text-primary);
}
.upload-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.upload-pct { font-size: 12px; color: var(--color-text-muted); flex-shrink: 0; }
.upload-status.done { color: #22c55e; }
.upload-status.err { color: #ef4444; }
</style>
