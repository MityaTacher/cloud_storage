import api from './axios'
import type { StorageNode, AdminDashboardData } from '@/types'

export const adminApi = {
  getNodes(): Promise<{ data: StorageNode[] }> {
    return api.get('/v1/users/nodes/stats')
  },
  getDashboardData(): Promise<{ data: AdminDashboardData }> {
    return api.get('/v1/users/admin/dashboard')
  },
  deleteUser(userId: number): Promise<void> {
    return api.delete(`/v1/users/${userId}`)
  }
}