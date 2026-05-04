<script setup lang="ts">
import { ref, computed } from 'vue'
import { useFileStore } from '@/stores/files'
import { useToastStore } from '@/stores/toast'

const props = defineProps<{ 
  item: any; 
  type: 'file' | 'folder' 
}>()

const emit = defineEmits(['close'])

const store = useFileStore()
const toast = useToastStore()

const loading = ref(false)
const newName = ref(props.type === 'file' ? props.item.filename : props.item.name)
const originalName = computed(() => props.type === 'file' ? props.item.filename : props.item.name)

async function submit() {
  const trimmed = newName.value.trim()
  if (!trimmed) return
  
  if (trimmed === originalName.value) {
    emit('close')
    return
  }

  loading.value = true
  try {
    if (props.type === 'file') {
      await store.renameFile(props.item.id, trimmed)
    } else {
      await store.renameFolder(props.item.uid, trimmed)
    }
    toast.success(`Renamed to "${trimmed}"`)
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
    <div class="modal" role="dialog" aria-modal="true" aria-labelledby="rename-title">
      <div class="modal-header">
        <h2 class="modal-title" id="rename-title">
          <i class="pi pi-pencil" style="margin-right:10px;color:var(--color-accent)" />
          Rename {{ type }}
        </h2>
        <button class="modal-close" @click="emit('close')" aria-label="Close"><i class="pi pi-times" /></button>
      </div>

      <form @submit.prevent="submit" style="display:flex;flex-direction:column;gap:20px">
        <div>
          <label class="form-label" for="item-name">New name</label>
          <input
            id="item-name"
            v-model="newName"
            class="form-input"
            type="text"
            autofocus
            maxlength="255"
          />
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