import api from './axios'
import axios from 'axios'
import type { Directory, DirectoryRoot, CloudFile } from '@/types'

const publicApi = axios.create({ baseURL: '/api/v1' })

export const cloudApi = {
  getRoot(): Promise<{ data: DirectoryRoot }> {
    return api.get('/v1/users/cloud')
  },

  getDirectory(uid: string): Promise<{ data: Directory }> {
    return api.get(`/v1/folders/${uid}`)
  },

  createFolder(name: string, parent_uid: string | null): Promise<{ data: Directory }> {
    const params = new URLSearchParams()
    params.append('name', name)
    if (parent_uid) params.append('parent_uid', parent_uid)
    return api.post(`/v1/folders/?${params.toString()}`)
  },

  deleteFolder(uid: string): Promise<void> {
    return api.delete(`/v1/folders/${uid}`)
  },

  patchFolderAccess(uid: string, access_level: number): Promise<{ data: unknown }> {
    return api.patch(`/v1/folders/${uid}?access_level=${access_level}`)
  },

  async uploadFile(
    file: File,
    parent_uid: string | null,
    onProgress?: (pct: number) => void,
  ): Promise<{ data: CloudFile }> {
    const safeFilename = file.name.replace(/^.*[\\\/]/, '')
    const requestUrl = `/v1/files/upload-request?filename=${encodeURIComponent(safeFilename)}&size_bytes=${file.size}${parent_uid ? `&parent_uid=${parent_uid}` : ''}`
    
    const { data: requestData } = await api.post(requestUrl)
    
    const form = new FormData()
    form.append('file', file, safeFilename)
    
    await axios.post(`${requestData.upload_url}?token=${requestData.token}`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress(e) {
        if (e.total) onProgress?.(Math.round((e.loaded / e.total) * 100))
      },
    })

    const checkReady = async (): Promise<CloudFile> => {
      for (let i = 0; i < 20; i++) {
        const res = await api.get(`/v1/files/${requestData.file_id}`)
        if (res.data.status === 'READY') return res.data
        await new Promise((resolve) => setTimeout(resolve, 500))
      }
      throw new Error("File processing timeout")
    }

    const finalFile = await checkReady()
    return { data: finalFile }
  },

  deleteFile(id: number): Promise<void> {
    return api.delete(`/v1/files/${id}`)
  },

  getFileDownloadUrl(id: number): string {
    return `/api/v1/files/${id}/download`
  },

  getFolderDownloadUrl(uid: string): string {
    return `/api/v1/folders/${uid}/download`
  },

  patchFileAccess(id: number, access_level: number): Promise<{ data: string }> {
    return api.patch(`/v1/files/${id}?access_level=${access_level}`)
  },

  moveFile(id: number, parent_uid: string | null): Promise<{ data: CloudFile }> {
    const params = parent_uid ? `?parent_uid=${parent_uid}` : ''
    return api.patch(`/v1/files/${id}/move${params}`)
  },

  renameFile(id: number, new_name: string): Promise<{ data: CloudFile }> {
    return api.patch(`/v1/files/${id}/rename?new_name=${encodeURIComponent(new_name)}`)
  },

  renameFolder(uid: string, new_name: string): Promise<{ data: Directory }> {
    return api.patch(`/v1/folders/${uid}/rename?new_name=${encodeURIComponent(new_name)}`)
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
    return `/api/v1/files/public/${uid}/download`
  },

  getPublicFolderDirectDownload(public_link: string): string {
    return `/api/v1/folders/public/${public_link}/download`
  },

  getPublicFolderMeta(public_link: string): Promise<{ data: Directory }> {
    return publicApi.get(`/folders/public/${public_link}`)
  },

  savePublicFile(uid: string): Promise<{ data: CloudFile }> {
    return api.post(`/v1/files/public/${uid}/save`)
  },

  savePublicFolder(public_link: string): Promise<{ data: Directory }> {
    return api.post(`/v1/folders/public/${public_link}/save`)
  },
}