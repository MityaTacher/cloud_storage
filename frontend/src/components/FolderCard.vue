<script setup lang="ts">
import { ref } from 'vue'
import type { DirectoryBase } from '@/types'

const props = defineProps<{ folder: DirectoryBase }>()

const emit = defineEmits<{
  open: [folder: DirectoryBase]
  share: [folder: DirectoryBase]
  delete: [folder: DirectoryBase]
  dropFile: [fileId: number, folderUid: string]
  download: [folder: DirectoryBase]
  rename: [folder: DirectoryBase]
}>()

const isDragOver = ref(false)

function onDrop(e: DragEvent) {
  isDragOver.value = false
  const rawData = e.dataTransfer?.getData('application/json')
  if (rawData) {
    try {
      const data = JSON.parse(rawData)
      if (data.type === 'file') {
        emit('dropFile', data.id, props.folder.uid)
      }
    } catch (err) {}
  }
}
</script>

<template>
  <div
    class="file-card folder-card"
    :class="{ 'drag-over': isDragOver }"
    :title="folder.name"
    @dblclick="emit('open', folder)"
    :id="`folder-${folder.uid}`"
    @dragover.prevent="isDragOver = true"
    @dragleave="isDragOver = false"
    @drop.stop.prevent="onDrop"
  >
    <!-- Access badge -->
    <span :class="['badge', folder.access_level === 1 ? 'badge-public' : 'badge-private']" style="position:absolute;top:8px;left:8px">
      {{ folder.access_level === 1 ? 'Public' : 'Private' }}
    </span>

    <!-- Actions -->
    <div class="file-actions">
      <button class="icon-btn" @click.stop="emit('download', folder)" title="Download as ZIP">
        <i class="pi pi-download" />
      </button>
      <button class="icon-btn" @click.stop="emit('open', folder)" :title="`Open ${folder.name}`" :id="`open-folder-${folder.uid}`">
        <i class="pi pi-arrow-right" />
      </button>
      <button class="icon-btn" @click.stop="emit('rename', folder)" :title="`Rename ${folder.name}`" :id="`rename-folder-${folder.uid}`">
        <i class="pi pi-pencil" />
      </button>
      <button class="icon-btn" @click.stop="emit('share', folder)" :title="`Share ${folder.name}`" :id="`share-folder-${folder.uid}`">
        <i class="pi pi-share-alt" />
      </button>
      <button class="icon-btn danger" @click.stop="emit('delete', folder)" :title="`Delete ${folder.name}`" :id="`delete-folder-${folder.uid}`">
        <i class="pi pi-trash" />
      </button>
    </div>

    <div class="file-icon">📁</div>
    <div class="file-name">{{ folder.name }}</div>
    <div class="file-size" style="color:var(--color-text-muted);font-size:11px">Folder</div>
  </div>
</template>

<style scoped>
.folder-card { cursor: pointer; }
.folder-card.drag-over {
  border-color: var(--color-accent);
  background: var(--color-accent-muted);
}
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