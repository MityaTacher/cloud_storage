<script setup lang="ts">
import { ref } from 'vue'
import { useFileStore } from '@/stores/files'
import { useToastStore } from '@/stores/toast'
import type { CloudFile, DirectoryBase } from '@/types'

const props = defineProps<{ item: CloudFile | DirectoryBase; type: 'file' | 'folder' }>()
const emit = defineEmits<{ close: [] }>()

const store = useFileStore()
const toast = useToastStore()

const originalName = props.type === 'file' ? (props.item as CloudFile).filename : (props.item as DirectoryBase).name
const newName = ref(originalName)
const loading = ref(false)

async function submit() {
  const trimmed = newName.value.trim()
  if (!trimmed || trimmed === originalName) return emit('close')
  
  loading.value = true
  try {
    if (props.type === 'file') {
      await store.renameFile((props.item as CloudFile).id, trimmed)
    } else {
      await store.renameFolder((props.item as DirectoryBase).uid, trimmed)
    }
    toast.success('Renamed successfully')
    emit('close')
  } catch (e: any) {
    toast.error(e?.response?.data?.detail ?? 'Failed to rename')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="modal-backdrop" @click.self="emit('close')">
    <div class="modal" role="dialog" aria-modal="true">
      <div class="modal-header">
        <h2 class="modal-title">
          <i class="pi pi-pencil" style="margin-right:10px;color:var(--color-accent)" />
          Rename {{ type }}
        </h2>
        <button class="modal-close" @click="emit('close')"><i class="pi pi-times" /></button>
      </div>

      <form @submit.prevent="submit" style="display:flex;flex-direction:column;gap:20px">
        <div>
          <label class="form-label">New name</label>
          <input v-model="newName" class="form-input" type="text" autofocus />
        </div>

        <div style="display:flex;gap:10px;justify-content:flex-end">
          <button type="button" class="btn btn-ghost" @click="emit('close')">Cancel</button>
          <button type="submit" class="btn btn-primary" :disabled="loading || !newName.trim()">
            <span v-if="loading" class="spinner" style="width:14px;height:14px" />
            <i v-else class="pi pi-check" />
            Save
          </button>
        </div>
      </form>
    </div>
  </div>
</template>