<script setup lang="ts">
import { ref } from 'vue'
import { useFileStore } from '@/stores/files'
import { useToastStore } from '@/stores/toast'
import type { CloudFile, DirectoryBase } from '@/types'

const props = defineProps<{ item: CloudFile | DirectoryBase; type: 'file' | 'folder' }>()
const emit = defineEmits<{ close: []; deleted: [] }>()
const store = useFileStore()
const toast = useToastStore()
const loading = ref(false)

const name = props.type === 'file'
  ? (props.item as CloudFile).filename
  : (props.item as DirectoryBase).name

async function confirm() {
  loading.value = true
  try {
    if (props.type === 'file') {
      await store.deleteFile((props.item as CloudFile).id)
    } else {
      await store.deleteFolder((props.item as DirectoryBase).uid)
    }
    toast.success(`"${name}" deleted`)
    emit('deleted')
    emit('close')
  } catch (e: any) {
    toast.error(e?.response?.data?.detail ?? 'Delete failed')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="modal-backdrop" @click.self="emit('close')">
    <div class="modal" style="max-width:400px" role="dialog" aria-modal="true" aria-labelledby="delete-title">
      <div class="modal-header">
        <h2 class="modal-title" id="delete-title" style="color:var(--color-danger)">
          <i class="pi pi-trash" style="margin-right:10px" />
          Delete {{ type }}
        </h2>
        <button class="modal-close" @click="emit('close')" aria-label="Close"><i class="pi pi-times" /></button>
      </div>

      <p style="font-size:14px;color:var(--color-text-secondary);margin-bottom:24px;line-height:1.6">
        Are you sure you want to delete
        <strong style="color:var(--color-text-primary)">"{{ name }}"</strong>?
        <span v-if="type === 'folder'"> This will also delete all contents inside.</span>
        This action cannot be undone.
      </p>

      <div style="display:flex;gap:10px;justify-content:flex-end">
        <button class="btn btn-ghost" @click="emit('close')">Cancel</button>
        <button class="btn btn-danger" @click="confirm" :disabled="loading" id="confirm-delete-btn">
          <span v-if="loading" class="spinner" style="width:14px;height:14px;border-color:rgba(255,255,255,0.3);border-top-color:#fff" />
          <i v-else class="pi pi-trash" />
          Delete
        </button>
      </div>
    </div>
  </div>
</template>
