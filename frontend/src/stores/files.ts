import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { cloudApi } from '@/api/cloud'
import type { CloudFile, DirectoryBase, DirectoryRoot, UploadTask } from '@/types'

export interface BreadcrumbEntry {
  uid: string | null
  name: string
}

export const useFileStore = defineStore('files', () => {
  const folders = ref<DirectoryBase[]>([])
  const files = ref<CloudFile[]>([])
  const currentFolderUid = ref<string | null>(null)
  const breadcrumbs = ref<BreadcrumbEntry[]>([{ uid: null, name: 'My Cloud' }])
  const loading = ref(false)
  const uploads = ref<UploadTask[]>([])

  const totalItems = computed(() => folders.value.length + files.value.length)
  const hasItems = computed(() => totalItems.value > 0)

  function setContents(data: DirectoryRoot) {
    folders.value = data.children
    files.value = data.files.filter(f => f.status === 'READY')
  }

  async function loadRoot() {
    loading.value = true
    try {
      const { data } = await cloudApi.getRoot()
      setContents(data)
      currentFolderUid.value = null
      breadcrumbs.value = [{ uid: null, name: 'My Cloud' }]
    } finally {
      loading.value = false
    }
  }

  async function openFolder(uid: string, name: string) {
    loading.value = true
    try {
      const { data } = await cloudApi.getDirectory(uid)
      setContents(data)
      currentFolderUid.value = uid
      if (!breadcrumbs.value.find((b) => b.uid === uid)) {
        breadcrumbs.value.push({ uid, name })
      }
    } finally {
      loading.value = false
    }
  }

  async function navigateBreadcrumb(entry: BreadcrumbEntry) {
    const idx = breadcrumbs.value.findIndex((b) => b.uid === entry.uid)
    breadcrumbs.value = breadcrumbs.value.slice(0, idx + 1)
    if (entry.uid === null) {
      await loadRoot()
    } else {
      loading.value = true
      try {
        const { data } = await cloudApi.getDirectory(entry.uid)
        setContents(data)
        currentFolderUid.value = entry.uid
      } finally {
        loading.value = false
      }
    }
  }

  async function createFolder(name: string) {
    const { data } = await cloudApi.createFolder(name, currentFolderUid.value)
    folders.value.push(data)
    return data
  }

  async function deleteFolder(uid: string) {
    await cloudApi.deleteFolder(uid)
    folders.value = folders.value.filter((f) => f.uid !== uid)
  }

  async function patchFolderAccess(uid: string, level: number) {
    await cloudApi.patchFolderAccess(uid, level)
    const f = folders.value.find((x) => x.uid === uid)
    if (f) f.access_level = level
    if (level === 1) {
      files.value.forEach((file) => {
        if (file.parent_uid === uid) file.access_level = 1
      })
    }
  }

  async function uploadFile(file: File, overrideParentUid?: string | null) {
    const targetUid = overrideParentUid !== undefined ? overrideParentUid : currentFolderUid.value
    const taskId = crypto.randomUUID()
    const task: UploadTask = { id: taskId, name: file.name, progress: 0, done: false, error: false }
    uploads.value.push(task)

    try {
      const { data } = await cloudApi.uploadFile(file, targetUid, (pct) => {
        const t = uploads.value.find((u) => u.id === taskId)
        if (t) t.progress = pct
      })
      
      if (targetUid === currentFolderUid.value) {
        files.value.push(data)
      }
      
      const t = uploads.value.find((u) => u.id === taskId)
      if (t) t.done = true
      setTimeout(() => {
        uploads.value = uploads.value.filter((u) => u.id !== taskId)
      }, 2000)
      return data
    } catch (e) {
      const t = uploads.value.find((u) => u.id === taskId)
      if (t) t.error = true
      setTimeout(() => {
        uploads.value = uploads.value.filter((u) => u.id !== taskId)
      }, 3000)
      throw e
    }
  }

  async function deleteFile(id: number) {
    await cloudApi.deleteFile(id)
    files.value = files.value.filter((f) => f.id !== id)
  }

  async function patchFileAccess(id: number, level: number) {
    await cloudApi.patchFileAccess(id, level)
    const f = files.value.find((x) => x.id === id)
    if (f) f.access_level = level
  }

  async function moveFile(id: number, targetFolderUid: string | null) {
    await cloudApi.moveFile(id, targetFolderUid)
    files.value = files.value.filter((f) => f.id !== id)
  }

  async function renameFile(id: number, newName: string) {
    const { data } = await cloudApi.renameFile(id, newName)
    const f = files.value.find(x => x.id === id)
    if (f) f.filename = data.filename
  }

  async function renameFolder(uid: string, newName: string) {
    const { data } = await cloudApi.renameFolder(uid, newName)
    const f = folders.value.find(x => x.uid === uid)
    if (f) f.name = data.name
  }

  function downloadFile(id: number, filename?: string) {
    const url = cloudApi.getFileDownloadUrl(id)
    const token = localStorage.getItem('access_token')

    fetch(url, { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => {
        if (r.status === 307 || r.ok) return r.url;
        throw new Error(`HTTP ${r.status}`)
      })
      .then((finalUrl) => {
        const link = document.createElement('a')
        link.href = finalUrl
        link.download = filename ?? files.value.find((x) => x.id === id)?.filename ?? 'download'
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
      })
      .catch((e) => console.error('Download failed', e))
  }

  function downloadFolder(uid: string, folderName: string) {
    const url = cloudApi.getFolderDownloadUrl(uid)
    const token = localStorage.getItem('access_token')

    fetch(url, { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.blob()
      })
      .then((blob) => {
        const link = document.createElement('a')
        link.href = URL.createObjectURL(blob)
        link.download = `${folderName}.zip`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        setTimeout(() => URL.revokeObjectURL(link.href), 60_000)
      })
      .catch((e) => console.error('Folder download failed', e))
  }

  return {
    folders,
    files,
    currentFolderUid,
    breadcrumbs,
    loading,
    uploads,
    totalItems,
    hasItems,
    loadRoot,
    openFolder,
    navigateBreadcrumb,
    createFolder,
    deleteFolder,
    patchFolderAccess,
    uploadFile,
    deleteFile,
    patchFileAccess,
    moveFile,
    renameFile,
    renameFolder,
    downloadFile,
    downloadFolder,
  }
})