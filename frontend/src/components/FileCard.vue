<script setup lang="ts">
import { computed } from 'vue'
import type { CloudFile } from '@/types'

const props = defineProps<{
  file: CloudFile
}>()

const emit = defineEmits<{
  download: [file: CloudFile]
  share: [file: CloudFile]
  delete: [file: CloudFile]
  rename: [file: CloudFile]
}>()

const icon = computed(() => {
  const ext = props.file.filename.split('.').pop()?.toLowerCase() ?? ''
  const map: Record<string, string> = {
    pdf: '📄', doc: '📝', docx: '📝', txt: '📝',
    xls: '📊', xlsx: '📊', csv: '📊',
    ppt: '📋', pptx: '📋',
    jpg: '🖼️', jpeg: '🖼️', png: '🖼️', gif: '🖼️', svg: '🖼️', webp: '🖼️',
    mp4: '🎬', mov: '🎬', avi: '🎬', mkv: '🎬',
    mp3: '🎵', wav: '🎵', flac: '🎵',
    zip: '📦', rar: '📦', '7z': '📦', tar: '📦', gz: '📦',
    js: '⚙️', ts: '⚙️', py: '⚙️', json: '⚙️', html: '⚙️', css: '⚙️',
  }
  return map[ext] ?? '📄'
})

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`
}

function onDragStart(e: DragEvent) {
  if (e.dataTransfer) {
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('application/json', JSON.stringify({ type: 'file', id: props.file.id }))
  }
}
</script>

<template>
  <div 
    class="file-card" 
    :title="file.filename" 
    @dblclick="emit('download', file)"
    draggable="true"
    @dragstart="onDragStart"
  >
    <!-- Access badge -->
    <span :class="['badge', file.access_level === 1 ? 'badge-public' : 'badge-private']" style="position:absolute;top:8px;left:8px">
      {{ file.access_level === 1 ? 'Public' : 'Private' }}
    </span>

    <!-- Action buttons -->
    <div class="file-actions">
      <button class="icon-btn" @click.stop="emit('download', file)" :title="'Download ' + file.filename" :id="`download-file-${file.id}`">
        <i class="pi pi-download" />
      </button>
      <button class="icon-btn" @click.stop="emit('rename', file)" :title="'Rename ' + file.filename" :id="`rename-file-${file.id}`">
        <i class="pi pi-pencil" />
      </button>
      <button class="icon-btn" @click.stop="emit('share', file)" :title="'Share ' + file.filename" :id="`share-file-${file.id}`">
        <i class="pi pi-share-alt" />
      </button>
      <button class="icon-btn danger" @click.stop="emit('delete', file)" :title="'Delete ' + file.filename" :id="`delete-file-${file.id}`">
        <i class="pi pi-trash" />
      </button>
    </div>

    <div class="file-icon">{{ icon }}</div>
    <div class="file-name">{{ file.filename }}</div>
    <div class="file-size">{{ formatSize(file.size_bytes) }}</div>
  </div>
</template>

<style scoped>
.icon-btn {
  width: 26px;
  height: 26px;
  border-radius: 6px;
  border: none;
  background: var(--color-bg-secondary);
  color: var(--color-text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  transition: all 0.15s;
}
.icon-btn:hover { background: var(--color-accent-muted); color: var(--color-accent-light); }
.icon-btn.danger:hover { background: rgba(239,68,68,0.15); color: var(--color-danger); }
</style>