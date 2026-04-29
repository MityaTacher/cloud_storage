<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { cloudApi } from '@/api/cloud'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import type { Directory, CloudFile, DirectoryBase } from '@/types'

const route = useRoute()
const auth = useAuthStore()
const toast = useToastStore()
const public_link = route.params.public_link as string

const folder = ref<Directory | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)
const savingFileIds = ref<Set<number>>(new Set())
const savingFolder = ref(false)

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`
  if (bytes < 1073741824) return `${(bytes / 1048576).toFixed(1)} MB`
  return `${(bytes / 1073741824).toFixed(1)} GB`
}

function fileIcon(filename: string): string {
  const ext = filename.split('.').pop()?.toLowerCase() ?? ''
  const map: Record<string, string> = {
    pdf: '📄', doc: '📝', docx: '📝', txt: '📝',
    xls: '📊', xlsx: '📊', csv: '📊',
    jpg: '🖼️', jpeg: '🖼️', png: '🖼️', gif: '🖼️', webp: '🖼️', svg: '🖼️',
    mp4: '🎬', mov: '🎬', avi: '🎬', mkv: '🎬',
    mp3: '🎵', wav: '🎵', flac: '🎵',
    zip: '📦', rar: '📦', '7z': '📦', tar: '📦', gz: '📦',
  }
  return map[ext] ?? '📄'
}

async function saveFileToMyCloud(file: CloudFile) {
  savingFileIds.value.add(file.id)
  try {
    await cloudApi.savePublicFile(file.uid)
    toast.success(`"${file.filename}" saved to your cloud!`)
  } catch (e: any) {
    toast.error(e?.response?.data?.detail ?? `Failed to save "${file.filename}"`)
  } finally {
    savingFileIds.value.delete(file.id)
  }
}

async function saveFolderToMyCloud() {
  if (!folder.value) return
  savingFolder.value = true
  try {
    await cloudApi.savePublicFolder(public_link)
    toast.success(`Folder "${folder.value.name}" saved to your cloud!`)
  } catch (e: any) {
    toast.error(e?.response?.data?.detail ?? 'Failed to save folder')
  } finally {
    savingFolder.value = false
  }
}

onMounted(async () => {
  try {
    const { data } = await cloudApi.getPublicFolderMeta(public_link)
    folder.value = data
  } catch {
    error.value = 'This folder is not available or has been made private.'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="share-page">
    <div class="auth-glow auth-glow-1" />
    <div class="auth-glow auth-glow-2" />

    <!-- Top bar -->
    <header class="share-topbar">
      <div style="display:flex;align-items:center;gap:10px">
        <div class="sidebar-logo-icon" style="width:30px;height:30px;font-size:15px">☁️</div>
        <span style="font-size:16px;font-weight:700;color:var(--color-text-primary)">CloudVault</span>
      </div>
      <div style="display:flex; gap:10px;">
        <router-link v-if="auth.isAuthenticated" to="/" class="btn btn-ghost btn-sm">
          <i class="pi pi-home" /> My Dashboard
        </router-link>
        <router-link v-else to="/login" class="btn btn-ghost btn-sm">
          <i class="pi pi-sign-in" /> Sign in
        </router-link>
      </div>
    </header>

    <main style="flex:1;padding:32px 20px;max-width:860px;width:100%;margin:0 auto;position:relative;z-index:1">

      <!-- Loading skeletons -->
      <div v-if="loading">
        <div class="skeleton" style="height:32px;width:200px;margin-bottom:24px" />
        <div style="display:flex;flex-direction:column;gap:12px">
          <div v-for="i in 4" :key="i" class="skeleton" style="height:60px;border-radius:var(--radius-md)" />
        </div>
      </div>

      <!-- Error -->
      <div v-else-if="error" class="glass-card" style="padding:60px;text-align:center;display:flex;flex-direction:column;align-items:center;gap:16px">
        <div style="font-size:64px">🔒</div>
        <h1 style="font-size:20px;font-weight:700;color:var(--color-text-primary)">Access denied</h1>
        <p style="font-size:14px;color:var(--color-text-muted)">{{ error }}</p>
        <router-link to="/" class="btn btn-primary"><i class="pi pi-home" /> Go to CloudVault</router-link>
      </div>

      <!-- Folder contents -->
      <template v-else-if="folder">
        <!-- Header -->
        <div style="display:flex;align-items:center;gap:14px;margin-bottom:28px">
          <div style="font-size:42px;line-height:1">📁</div>
          <div style="flex:1">
            <h1 style="font-size:24px;font-weight:800;color:var(--color-text-primary)">{{ folder.name }}</h1>
            <div style="display:flex;align-items:center;gap:10px;margin-top:4px">
              <span class="badge badge-public"><i class="pi pi-globe" style="margin-right:4px" />Public folder</span>
              <span style="font-size:13px;color:var(--color-text-muted)">
                {{ folder.children.length }} folder{{ folder.children.length !== 1 ? 's' : '' }} ·
                {{ folder.files.length }} file{{ folder.files.length !== 1 ? 's' : '' }}
              </span>
            </div>
          </div>
          
          <div style="margin-left: auto; display:flex; gap: 10px;">
             <a 
                :href="cloudApi.getPublicFolderDirectDownload(public_link)" 
                class="btn btn-ghost" 
                download
             >
                <i class="pi pi-file-archive" />
                Download as ZIP
             </a>
             
             <button 
                v-if="auth.isAuthenticated"
                @click="saveFolderToMyCloud" 
                class="btn btn-primary" 
                :disabled="savingFolder"
             >
                <span v-if="savingFolder" class="spinner" style="border-top-color:#fff; width:14px; height:14px"></span>
                <i v-else class="pi pi-cloud-download" />
                Save full folder
             </button>
          </div>
        </div>

        <!-- Empty -->
        <div
          v-if="!folder.children.length && !folder.files.length"
          class="empty-state"
        >
          <div class="empty-state-icon">📂</div>
          <div class="empty-state-title">This folder is empty</div>
        </div>

        <!-- Sub-folders -->
        <div v-if="folder.children.length" style="margin-bottom:28px">
          <h2 class="section-label">Folders</h2>
          <div style="display:flex;flex-direction:column;gap:2px">
            <div
              v-for="child in folder.children"
              :key="child.uid"
              class="public-row"
            >
              <span style="font-size:22px">📁</span>
              <span style="flex:1;font-size:14px;font-weight:500;color:var(--color-text-primary)">
                {{ child.name }}
              </span>
              <span
                v-if="child.access_level === 1"
                class="badge badge-public"
              >Public</span>
              <span v-else class="badge badge-private">Private</span>
            </div>
          </div>
        </div>

        <!-- Files -->
        <div v-if="folder.files.length">
          <h2 class="section-label">Files</h2>
          <div style="display:flex;flex-direction:column;gap:2px">
            <div
              v-for="file in folder.files"
              :key="file.id"
              class="public-row"
            >
              <span style="font-size:22px">{{ fileIcon(file.filename) }}</span>
              <div style="flex:1;min-width:0">
                <div style="font-size:14px;font-weight:500;color:var(--color-text-primary);overflow:hidden;text-overflow:ellipsis;white-space:nowrap">
                  {{ file.filename }}
                </div>
                <div style="font-size:12px;color:var(--color-text-muted)">{{ formatSize(file.size_bytes) }}</div>
              </div>
              
              <template v-if="file.access_level === 1">
                <button 
                  v-if="auth.isAuthenticated"
                  @click="saveFileToMyCloud(file)" 
                  class="btn btn-sm btn-ghost" 
                  :disabled="savingFileIds.has(file.id)"
                  title="Save to My Cloud"
                >
                  <span v-if="savingFileIds.has(file.id)" class="spinner" style="width:12px;height:12px;border-top-color:var(--color-accent)"></span>
                  <i v-else class="pi pi-cloud-download" />
                </button>
                <a
                  :href="cloudApi.getPublicFileDirectDownload(file.uid)"
                  class="btn btn-sm btn-primary"
                  download
                  :id="`dl-public-file-${file.id}`"
                >
                  <i class="pi pi-download" /> Download
                </a>
              </template>
              <span v-else class="badge badge-private">Private</span>
            </div>
          </div>
        </div>
      </template>
    </main>

    <footer style="text-align:center;padding:20px;font-size:13px;color:var(--color-text-muted);position:relative;z-index:1">
      Shared via <strong style="color:var(--color-text-secondary)">CloudVault</strong> ·
      <router-link to="/register" style="color:var(--color-accent);text-decoration:none">Create your own cloud</router-link>
    </footer>
  </div>
</template>

<style scoped>
.share-page {
  min-height: 100vh;
  background: var(--color-bg-primary);
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
}
.share-topbar {
  height: 60px;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-bg-secondary);
  position: relative;
  z-index: 1;
}
.section-label {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-text-muted);
  margin-bottom: 10px;
}
.public-row {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 16px;
  border-radius: var(--radius-md);
  border: 1px solid transparent;
  transition: all 0.15s;
}
.public-row:hover {
  background: var(--color-bg-hover);
  border-color: var(--color-border);
}
</style>