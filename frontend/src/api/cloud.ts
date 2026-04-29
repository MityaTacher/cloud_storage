import api from './axios'
import axios from 'axios'
import type { Directory, DirectoryRoot, CloudFile } from '@/types'

const publicApi = axios.create({ baseURL: '/api' })

export const cloudApi = {
  getRoot(): Promise<{ data: DirectoryRoot }> {
    return api.get('/users/cloud')
  },

  getDirectory(uid: string): Promise<{ data: Directory }> {
    return api.get(`/folders/${uid}`)
  },

  createFolder(name: string, parent_uid: string | null): Promise<{ data: Directory }> {
    const params = new URLSearchParams()
    params.append('name', name)
    if (parent_uid) params.append('parent_uid', parent_uid)
    return api.post(`/folders/?${params.toString()}`)
  },

  deleteFolder(uid: string): Promise<void> {
    return api.delete(`/folders/${uid}`)
  },

  patchFolderAccess(uid: string, access_level: number): Promise<{ data: unknown }> {
    return api.patch(`/folders/${uid}?access_level=${access_level}`)
  },

  uploadFile(
    file: File,
    parent_uid: string | null,
    onProgress?: (pct: number) => void,
  ): Promise<{ data: CloudFile }> {
    const form = new FormData()
    form.append('file', file)
    const params = parent_uid ? `?parent_uid=${parent_uid}` : ''
    return api.post(`/files/${params}`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress(e) {
        if (e.total) onProgress?.(Math.round((e.loaded / e.total) * 100))
      },
    })
  },

  deleteFile(id: number): Promise<void> {
    return api.delete(`/files/${id}`)
  },

  getFileDownloadUrl(id: number): string {
    return `/api/files/${id}/download`
  },

  getFolderDownloadUrl(uid: string): string {
    return `/api/folders/${uid}/download`
  },

  patchFileAccess(id: number, access_level: number): Promise<{ data: string }> {
    return api.patch(`/files/${id}?access_level=${access_level}`)
  },

  moveFile(id: number, parent_uid: string | null): Promise<{ data: CloudFile }> {
    const params = parent_uid ? `?parent_uid=${parent_uid}` : ''
    return api.patch(`/files/${id}/move${params}`)
  },

  getPublicFileUrl(uid: string): string {
    return `${window.location.origin}/share/file/${uid}`
  },

  getPublicFolderUrl(public_link: string): string {
    return `${window.location.origin}/share/folder/${public_link}`
  },

  getPublicFileMeta(uid: string): Promise<{ data: CloudFile }> {
    return publicApi.get(`/files/public/${uid}`)
  },

  getPublicFileDirectDownload(uid: string): string {
    return `/api/files/public/${uid}/download`
  },

  getPublicFolderDirectDownload(public_link: string): string {
    return `/api/folders/public/${public_link}/download`
  },

  getPublicFolderMeta(public_link: string): Promise<{ data: Directory }> {
    return publicApi.get(`/folders/public/${public_link}`)
  },

  savePublicFile(uid: string): Promise<{ data: CloudFile }> {
    return api.post(`/files/public/${uid}/save`)
  },

  savePublicFolder(public_link: string): Promise<{ data: Directory }> {
    return api.post(`/folders/public/${public_link}/save`)
  },
}