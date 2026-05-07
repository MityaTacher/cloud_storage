<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useFileStore } from '@/stores/files'
import { useToastStore } from '@/stores/toast'
import { useThemeStore } from '@/stores/theme'
import { cloudApi } from '@/api/cloud'
import type { CloudFile, DirectoryBase } from '@/types'

import Sidebar from '@/components/Sidebar.vue'
import Breadcrumb from '@/components/Breadcrumb.vue'
import FileCard from '@/components/FileCard.vue'
import FolderCard from '@/components/FolderCard.vue'
import NewFolderModal from '@/components/NewFolderModal.vue'
import ShareModal from '@/components/ShareModal.vue'
import DeleteModal from '@/components/DeleteModal.vue'

const store = useFileStore()
const toast = useToastStore()
const theme = useThemeStore()

// ── Modal state ──
const showNewFolder = ref(false)
const shareTarget = ref<{ item: CloudFile | DirectoryBase; type: 'file' | 'folder' } | null>(null)
const deleteTarget = ref<{ item: CloudFile | DirectoryBase; type: 'file' | 'folder' } | null>(null)

// ── Drag-and-drop ──
const dragOver = ref(false)
const fileInputRef = ref<HTMLInputElement | null>(null)
const folderInputRef = ref<HTMLInputElement | null>(null)

// ── Load on mount ──
onMounted(() => store.loadRoot())

// Вспомогательная функция для безопасного извлечения текста ошибки
function getErrorMsg(err: any, fallback: string): string {
  console.error('Upload error:', err)
  if (err?.response?.data?.detail) {
    const detail = err.response.data.detail
    return Array.isArray(detail) ? detail.map((d: any) => d.msg).join(', ') : String(detail)
  }
  return err?.message || fallback
}

// ── File upload handlers ──
function triggerUpload() { fileInputRef.value?.click() }
function triggerFolderUpload() { folderInputRef.value?.click() }

async function handleFileInput(e: Event) {
  const input = e.target as HTMLInputElement
  if (!input.files?.length) return
  const files = Array.from(input.files)
  
  try {
    for (const file of files) {
      try {
        await store.uploadFile(file)
        toast.success(`"${file.name}" uploaded`)
      } catch (err: any) {
        toast.error(getErrorMsg(err, `Failed to upload "${file.name}"`))
      }
    }
  } finally {
    input.value = '' // Очищаем только в самом конце
  }
}

function handleGlobalDragEnter(e: DragEvent) {
  if (e.dataTransfer?.types.includes('Files')) {
    dragOver.value = true
  }
}

async function onDrop(e: DragEvent) {
  dragOver.value = false
  const files = Array.from(e.dataTransfer?.files ?? [])
  if (!files.length) return

  for (const file of files) {
    try {
      await store.uploadFile(file)
      toast.success(`"${file.name}" uploaded`)
    } catch (err: any) {
      toast.error(getErrorMsg(err, `Failed to upload "${file.name}"`))
    }
  }
}

// ── Автоматическое создание папок при загрузке ──
async function getOrCreateFolder(name: string, parentUid: string | null): Promise<string> {
  try {
    const { data } = await cloudApi.createFolder(name, parentUid)
    return data.uid
  } catch (e: any) {
    // Если папка уже существует (Конфликт 409), достаем её UID
    if (e.response?.status === 409) {
      let contents
      if (parentUid) {
        const res = await cloudApi.getDirectory(parentUid)
        contents = res.data.children
      } else {
        const res = await cloudApi.getRoot()
        contents = res.data.children
      }
      const existing = contents.find((c: any) => c.name === name)
      if (existing) return existing.uid
    }
    throw e
  }
}

async function handleFolderInput(e: Event) {
  const input = e.target as HTMLInputElement
  if (!input.files?.length) return
  
  const files = Array.from(input.files)
  toast.info(`Preparing to upload ${files.length} file(s) from folder...`)
  
  // Кэшируем ID созданных директорий, чтобы не делать лишних API запросов
  const folderUidCache = new Map<string, string | null>()

  try {
    // Проходим по каждому файлу СТРОГО последовательно
    for (const file of files) {
      const path = file.webkitRelativePath
      
      // На всякий случай: если браузер не поддерживает webkitRelativePath
      if (!path) {
        try {
          await store.uploadFile(file)
        } catch (err: any) {
          toast.error(getErrorMsg(err, `Failed to upload "${file.name}"`))
        }
        continue
      }

      const parts = path.split('/')
      const folderParts = parts.slice(0, -1) // Все части, кроме самого файла
      
      let currentParentUid = store.currentFolderUid
      let currentPathAcc = ''

      try {
        // Идем по каждой вложенной папке и последовательно создаем их
        for (const part of folderParts) {
          currentPathAcc = currentPathAcc ? `${currentPathAcc}/${part}` : part
          
          if (folderUidCache.has(currentPathAcc)) {
            currentParentUid = folderUidCache.get(currentPathAcc)!
          } else {
            const newUid = await getOrCreateFolder(part, currentParentUid)
            folderUidCache.set(currentPathAcc, newUid)
            currentParentUid = newUid
          }
        }

        // Загружаем сам файл строго после того, как папка создана
        await store.uploadFile(file, currentParentUid)
        
      } catch (err: any) {
        toast.error(getErrorMsg(err, `Failed to process "${file.name}"`))
      }
    }
    
    toast.success('Folder upload complete!')
  } finally {
    // Очищаем input только после окончания всех загрузок
    input.value = ''
    
    // Обновляем текущую директорию чтобы подтянуть новые папки и файлы визуально
    if (store.currentFolderUid) {
       const currentCrumb = store.breadcrumbs[store.breadcrumbs.length - 1]
       store.openFolder(store.currentFolderUid, currentCrumb.name)
    } else {
       store.loadRoot()
    }
  }
}

async function handleDropFileMove(fileId: number, folderUid: string) {
  try {
    await store.moveFile(fileId, folderUid)
    toast.success('File moved successfully')
  } catch (e: any) {
    toast.error(getErrorMsg(e, 'Failed to move file'))
  }
}

// ── Folder open ──
function openFolder(folder: DirectoryBase) {
  store.openFolder(folder.uid, folder.name)
}

// ── Actions ──
function shareFile(file: CloudFile) { shareTarget.value = { item: file, type: 'file' } }
function shareFolder(folder: DirectoryBase) { shareTarget.value = { item: folder, type: 'folder' } }
function deleteFile(file: CloudFile) { deleteTarget.value = { item: file, type: 'file' } }
function deleteFolder(folder: DirectoryBase) { deleteTarget.value = { item: folder, type: 'folder' } }
function downloadFile(file: CloudFile) {
  store.downloadFile(file.id, file.filename)
  toast.info(`Downloading "${file.filename}"…`)
}
function downloadFolderAsZip(folder: DirectoryBase) {
  store.downloadFolder(folder.uid, folder.name)
  toast.info(`Archiving "${folder.name}"...`)
}

// ── Search ──
const search = ref('')
</script>

<template>
  <div class="app-layout">
    <Sidebar />

    <div class="main-content">
      <!-- Top bar -->
      <header class="topbar">
        <Breadcrumb style="flex:1" />

        <!-- Search -->
        <div style="position:relative;width:240px; margin-right: auto;">
          <i class="pi pi-search" style="position:absolute;left:12px;top:50%;transform:translateY(-50%);color:var(--color-text-muted);font-size:13px" />
          <input
            id="search-input"
            v-model="search"
            class="form-input"
            style="padding-left:36px;height:38px;font-size:13px"
            type="search"
            placeholder="Search files…"
          />
        </div>

        <!-- Actions -->
        <button id="upload-btn" class="btn btn-primary btn-sm" @click="triggerUpload">
          <i class="pi pi-file" />
          Upload file
        </button>
        <button id="upload-folder-btn" class="btn btn-primary btn-sm" @click="triggerFolderUpload">
          <i class="pi pi-folder" />
          Upload folder
        </button>
        <button id="new-folder-btn" class="btn btn-ghost btn-sm" @click="showNewFolder = true">
          <i class="pi pi-folder-plus" />
          New folder
        </button>
        <button id="refresh-btn" class="btn btn-ghost btn-sm" @click="store.loadRoot()" :disabled="store.loading" style="padding:6px 10px">
          <i :class="['pi pi-refresh', { spinning: store.loading }]" />
        </button>

        <!-- Input для файлов -->
        <input
          ref="fileInputRef"
          type="file"
          multiple
          style="display:none"
          @change="handleFileInput"
        />
        <!-- Input с атрибутом webkitdirectory для загрузки папок целиком -->
        <input
          ref="folderInputRef"
          type="file"
          webkitdirectory
          multiple
          style="display:none"
          @change="handleFolderInput"
        />
      </header>

      <!-- Drop zone overlay -->
      <div
        style="position:relative;flex:1;overflow-y:auto"
        @dragover.prevent="handleGlobalDragEnter"
        @dragleave="dragOver = false"
        @drop.prevent="onDrop"
      >
        <!-- Drag overlay -->
        <Transition name="fade">
          <div
            v-if="dragOver"
            style="position:absolute;inset:0;z-index:50;display:flex;align-items:center;justify-content:center;background:var(--color-accent-muted);border:2px dashed var(--color-accent);border-radius:var(--radius-lg);margin:16px;pointer-events:none"
          >
            <div style="text-align:center;color:var(--color-accent-light)">
              <div style="font-size:48px;margin-bottom:12px">📂</div>
              <div style="font-size:18px;font-weight:700">Drop files to upload</div>
            </div>
          </div>
        </Transition>

        <div style="padding:24px">
          <!-- Loading skeletons -->
          <div v-if="store.loading" class="file-grid" style="margin-bottom:32px">
            <div v-for="i in 8" :key="i" class="skeleton" style="height:150px;border-radius:var(--radius-md)" />
          </div>

          <template v-else>
            <!-- Folders section -->
            <div
              v-if="store.folders.filter(f => !search || f.name.toLowerCase().includes(search.toLowerCase())).length"
              style="margin-bottom:32px"
            >
              <h2 style="font-size:13px;font-weight:600;color:var(--color-text-muted);text-transform:uppercase;letter-spacing:0.08em;margin-bottom:14px">
                Folders
              </h2>
              <div class="file-grid">
                <TransitionGroup name="fade">
                  <FolderCard
                    v-for="folder in store.folders.filter(f => !search || f.name.toLowerCase().includes(search.toLowerCase()))"
                    :key="folder.uid"
                    :folder="folder"
                    @open="openFolder"
                    @share="shareFolder"
                    @delete="deleteFolder"
                    @dropFile="handleDropFileMove"
                    @download="downloadFolderAsZip"
                  />
                </TransitionGroup>
              </div>
            </div>

            <!-- Files section -->
            <div
              v-if="store.files.filter(f => !search || f.filename.toLowerCase().includes(search.toLowerCase())).length"
            >
              <h2 style="font-size:13px;font-weight:600;color:var(--color-text-muted);text-transform:uppercase;letter-spacing:0.08em;margin-bottom:14px">
                Files
              </h2>
              <div class="file-grid">
                <TransitionGroup name="fade">
                  <FileCard
                    v-for="file in store.files.filter(f => !search || f.filename.toLowerCase().includes(search.toLowerCase()))"
                    :key="file.id"
                    :file="file"
                    @download="downloadFile"
                    @share="shareFile"
                    @delete="deleteFile"
                  />
                </TransitionGroup>
              </div>
            </div>

            <!-- Empty state -->
            <div
              v-if="!store.hasItems"
              class="empty-state"
            >
              <div class="empty-state-icon">☁️</div>
              <div class="empty-state-title">This folder is empty</div>
              <p class="empty-state-text">Drop files here or click to upload</p>
              <div style="display:flex; gap: 10px; margin-top:8px">
                <button class="btn btn-primary" @click.stop="triggerUpload">
                  <i class="pi pi-file" /> Upload files
                </button>
                <button class="btn btn-primary" @click.stop="triggerFolderUpload">
                  <i class="pi pi-folder" /> Upload folder
                </button>
              </div>
            </div>

            <!-- No search results -->
            <div
              v-if="store.hasItems && search && !store.folders.some(f => f.name.toLowerCase().includes(search.toLowerCase())) && !store.files.some(f => f.filename.toLowerCase().includes(search.toLowerCase()))"
              class="empty-state"
            >
              <div class="empty-state-icon">🔍</div>
              <div class="empty-state-title">No results for "{{ search }}"</div>
              <p class="empty-state-text">Try a different search term</p>
            </div>
          </template>
        </div>
      </div>
    </div>
  </div>

  <!-- Modals -->
  <Transition name="fade">
    <NewFolderModal v-if="showNewFolder" @close="showNewFolder = false" />
  </Transition>

  <Transition name="fade">
    <ShareModal
      v-if="shareTarget"
      :item="shareTarget.item"
      :type="shareTarget.type"
      @close="shareTarget = null"
    />
  </Transition>

  <Transition name="fade">
    <DeleteModal
      v-if="deleteTarget"
      :item="deleteTarget.item"
      :type="deleteTarget.type"
      @close="deleteTarget = null"
      @deleted="deleteTarget = null"
    />
  </Transition>
</template>

<style scoped>
.spinning {
  animation: spin 0.8s linear infinite;
}
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>