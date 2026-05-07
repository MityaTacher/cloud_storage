<script setup lang="ts">
import { ref, computed } from 'vue'
import { useFileStore } from '@/stores/files'
import { useToastStore } from '@/stores/toast'
import { cloudApi } from '@/api/cloud'
import type { CloudFile, DirectoryBase } from '@/types'

const props = defineProps<{ item: CloudFile | DirectoryBase; type: 'file' | 'folder' }>()
const emit = defineEmits<{ close: [] }>()

const store = useFileStore()
const toast = useToastStore()
const loading = ref(false)

const currentLevel = computed(() => props.item.access_level)
const isPublic = computed(() => currentLevel.value === 1)

const publicLink = computed(() => {
  if (!isPublic.value) return ''
  if (props.type === 'file') {
    return cloudApi.getPublicFileUrl((props.item as CloudFile).uid)
  } else {
    return cloudApi.getPublicFolderUrl((props.item as DirectoryBase).public_link)
  }
})

async function toggle() {
  loading.value = true
  try {
    const newLevel = isPublic.value ? 0 : 1
    if (props.type === 'file') {
      await store.patchFileAccess((props.item as CloudFile).id, newLevel)
    } else {
      await store.patchFolderAccess((props.item as DirectoryBase).uid, newLevel)
    }
    toast.success(newLevel === 1 ? 'Now public' : 'Now private')
  } catch (e: any) {
    toast.error(e?.response?.data?.detail ?? 'Failed to change access')
  } finally {
    loading.value = false
  }
}

function copyLink() {
  navigator.clipboard.writeText(publicLink.value)
  toast.success('Link copied!')
}

const itemName = computed(() =>
  props.type === 'file' ? (props.item as CloudFile).filename : (props.item as DirectoryBase).name
)
</script>

<template>
  <div class="modal-backdrop" @click.self="emit('close')">
    <div class="modal" role="dialog" aria-modal="true" aria-labelledby="share-title">
      <div class="modal-header">
        <h2 class="modal-title" id="share-title">
          <i class="pi pi-share-alt" style="margin-right:10px;color:var(--color-accent)" />
          Share
        </h2>
        <button class="modal-close" @click="emit('close')" aria-label="Close"><i class="pi pi-times" /></button>
      </div>

      <div style="display:flex;flex-direction:column;gap:20px">
        <div style="font-size:14px;color:var(--color-text-secondary)">
          <strong style="color:var(--color-text-primary)">{{ itemName }}</strong>
        </div>

        <!-- Access toggle -->
        <div style="display:flex;align-items:center;justify-content:space-between;padding:16px;background:var(--color-bg-primary);border-radius:var(--radius-md);border:1px solid var(--color-border)">
          <div style="display:flex;flex-direction:column;gap:4px">
            <span style="font-size:14px;font-weight:600;color:var(--color-text-primary)">
              Public access
            </span>
            <span style="font-size:12px;color:var(--color-text-muted)">
              Anyone with the link can view
            </span>
          </div>
          <button
            :class="['toggle-btn', { active: isPublic }]"
            @click="toggle"
            :disabled="loading"
            :aria-checked="isPublic"
            role="switch"
            aria-label="Toggle public access"
          >
            <span class="toggle-thumb" />
          </button>
        </div>

        <!-- Public link -->
        <Transition name="slide-up">
          <div v-if="isPublic" style="display:flex;flex-direction:column;gap:8px">
            <label class="form-label">Public link</label>
            <div class="share-link-box">
              <span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ publicLink }}</span>
              <button class="btn btn-sm btn-primary" @click="copyLink" id="copy-link-btn">
                <i class="pi pi-copy" />
                Copy
              </button>
            </div>
          </div>
        </Transition>

        <div style="display:flex;justify-content:flex-end">
          <button class="btn btn-ghost" @click="emit('close')">Done</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.toggle-btn {
  width: 48px;
  height: 26px;
  border-radius: 99px;
  background: var(--color-border);
  border: none;
  cursor: pointer;
  position: relative;
  transition: background 0.25s ease;
  flex-shrink: 0;
}
.toggle-btn.active { background: var(--color-accent); }
.toggle-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.toggle-thumb {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #fff;
  transition: transform 0.25s ease;
  box-shadow: 0 1px 4px rgba(0,0,0,0.3);
}
.toggle-btn.active .toggle-thumb { transform: translateX(22px); }
</style>
