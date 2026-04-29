<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { cloudApi } from '@/api/cloud'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import type { CloudFile } from '@/types'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const toast = useToastStore()

const uid = route.params.uid as string

const file = ref<CloudFile | null>(null)
const loading = ref(true)
const saving = ref(false)
const error = ref<string | null>(null)

const icon = computed(() => {
  if (!file.value) return '📄'
  const ext = file.value.filename.split('.').pop()?.toLowerCase() ?? ''
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
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`
  if (bytes < 1073741824) return `${(bytes / 1048576).toFixed(1)} MB`
  return `${(bytes / 1073741824).toFixed(1)} GB`
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    year: 'numeric', month: 'long', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

async function saveToMyCloud() {
  if (!file.value) return
  saving.value = true
  try {
    await cloudApi.savePublicFile(file.value.uid)
    toast.success(`"${file.value.filename}" saved to your cloud!`)
  } catch (e: any) {
    toast.error(e?.response?.data?.detail ?? 'Failed to save file')
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  try {
    const { data } = await cloudApi.getPublicFileMeta(uid)
    file.value = data
  } catch {
    error.value = 'This file is not available or has been made private.'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="share-page">
    <!-- Animated background -->
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

    <!-- Content -->
    <main class="share-main">
      <!-- Loading -->
      <div v-if="loading" class="share-card" style="align-items:center;gap:20px">
        <div class="skeleton" style="width:80px;height:80px;border-radius:var(--radius-lg)" />
        <div class="skeleton" style="width:200px;height:24px" />
        <div class="skeleton" style="width:140px;height:16px" />
      </div>

      <!-- Error -->
      <div v-else-if="error" class="share-card" style="align-items:center;gap:16px;text-align:center">
        <div style="font-size:64px">🔒</div>
        <h1 style="font-size:20px;font-weight:700;color:var(--color-text-primary)">Access denied</h1>
        <p style="font-size:14px;color:var(--color-text-muted)">{{ error }}</p>
        <router-link to="/" class="btn btn-primary">
          <i class="pi pi-home" /> Go to CloudVault
        </router-link>
      </div>

      <!-- File preview card -->
      <div v-else-if="file" class="share-card">
        <!-- Icon -->
        <div style="font-size:80px;line-height:1;margin-bottom:8px">{{ icon }}</div>

        <!-- Name -->
        <h1 style="font-size:22px;font-weight:800;color:var(--color-text-primary);text-align:center;word-break:break-word;max-width:480px">
          {{ file.filename }}
        </h1>

        <!-- Meta pills -->
        <div class="share-meta-row">
          <span class="share-pill">
            <i class="pi pi-database" />
            {{ formatSize(file.size_bytes) }}
          </span>
          <span class="share-pill">
            <i class="pi pi-calendar" />
            {{ formatDate(file.loaded_at) }}
          </span>
          <span class="badge badge-public">
            <i class="pi pi-globe" style="margin-right:4px" /> Public
          </span>
        </div>

        <!-- Divider -->
        <div style="width:100%;height:1px;background:var(--color-border);margin:8px 0" />

        <div style="display:flex; gap:12px; flex-wrap:wrap; justify-content:center; margin-top: 10px;">
          <a
            :href="cloudApi.getPublicFileDirectDownload(file.uid)"
            class="btn btn-primary"
            style="font-size:15px;padding:12px 24px"
            download
            id="public-download-btn"
          >
            <i class="pi pi-download" /> Download
          </a>

          <button 
            v-if="auth.isAuthenticated"
            @click="saveToMyCloud" 
            class="btn btn-ghost" 
            style="font-size:15px;padding:12px 24px; border-color:var(--color-accent); color:var(--color-accent);"
            :disabled="saving"
          >
            <span v-if="saving" class="spinner" style="border-top-color:var(--color-accent)"></span>
            <i v-else class="pi pi-cloud-download" /> Save to My Cloud
          </button>
        </div>

        <p style="font-size:12px;color:var(--color-text-muted);margin-top:4px">
          No sign-in required to download
        </p>
      </div>
    </main>

    <!-- Footer -->
    <footer style="text-align:center;padding:20px;font-size:13px;color:var(--color-text-muted)">
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

.share-main {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  position: relative;
  z-index: 1;
}

.share-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  padding: 48px 40px;
  width: 100%;
  max-width: 520px;
  box-shadow: var(--shadow-card);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  animation: slideUp 0.3s ease;
}

.share-meta-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: center;
}

.share-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: 99px;
  background: var(--color-bg-primary);
  border: 1px solid var(--color-border);
  font-size: 13px;
  color: var(--color-text-secondary);
}
</style>