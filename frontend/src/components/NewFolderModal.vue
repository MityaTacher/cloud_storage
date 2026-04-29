<script setup lang="ts">
import { ref } from 'vue'
import { useFileStore } from '@/stores/files'
import { useToastStore } from '@/stores/toast'

const emit = defineEmits<{ close: [] }>()
const store = useFileStore()
const toast = useToastStore()

const name = ref('')
const loading = ref(false)

async function submit() {
  const trimmed = name.value.trim()
  if (!trimmed) return
  loading.value = true
  try {
    await store.createFolder(trimmed)
    toast.success(`Folder "${trimmed}" created`)
    emit('close')
  } catch (e: any) {
    toast.error(e?.response?.data?.detail ?? 'Failed to create folder')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="modal-backdrop" @click.self="emit('close')">
    <div class="modal" role="dialog" aria-modal="true" aria-labelledby="new-folder-title">
      <div class="modal-header">
        <h2 class="modal-title" id="new-folder-title">
          <i class="pi pi-folder-plus" style="margin-right:10px;color:var(--color-accent)" />
          New Folder
        </h2>
        <button class="modal-close" @click="emit('close')" aria-label="Close"><i class="pi pi-times" /></button>
      </div>

      <form @submit.prevent="submit" style="display:flex;flex-direction:column;gap:20px">
        <div>
          <label class="form-label" for="folder-name">Folder name</label>
          <input
            id="folder-name"
            v-model="name"
            class="form-input"
            type="text"
            placeholder="e.g. Documents"
            autofocus
            maxlength="50"
          />
        </div>

        <div style="display:flex;gap:10px;justify-content:flex-end">
          <button type="button" class="btn btn-ghost" @click="emit('close')">Cancel</button>
          <button type="submit" class="btn btn-primary" :disabled="loading || !name.trim()">
            <span v-if="loading" class="spinner" style="width:14px;height:14px" />
            <i v-else class="pi pi-folder-plus" />
            Create
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
