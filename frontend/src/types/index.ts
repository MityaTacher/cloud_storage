// User types
export interface User {
  id: number
  email: string
  username: string
  role: string
  registered_at: string
}

export interface StorageNode {
  id: number
  name: string
  address: string
  total_space_bytes: number
  free_space_bytes: number
  rx_bytes_per_sec: number
  tx_bytes_per_sec: number
  cpu_percent: number
  ram_percent: number
  last_heartbeat: string
}

export interface AdminUser extends User {
  used_bytes: number
}

export interface AdminDashboardData {
  global: { total_files: number; total_size_bytes: number; total_public_links: number }
  file_types: Record<string, number>
  users: AdminUser[]
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

// File types
export interface CloudFile {
  id: number
  filename: string
  size_bytes: number
  loaded_at: string
  access_level: number // 0 = private, 1 = public
  uid: string
  parent_uid: string | null
  user_id: number
}

// Directory types
export interface DirectoryBase {
  name: string
  uid: string
  parent_uid: string | null
  access_level: number
  public_link: string
  created_at: string
}

export interface Directory extends DirectoryBase {
  children: DirectoryBase[]
  files: CloudFile[]
}

export interface DirectoryRoot {
  children: DirectoryBase[]
  files: CloudFile[]
}

// Auth forms
export interface LoginForm {
  username: string
  password: string
}

export interface RegisterForm {
  email: string
  username: string
  password: string
}

// Upload progress
export interface UploadTask {
  id: string
  name: string
  progress: number
  done: boolean
  error: boolean
}

// Toast
export type ToastType = 'success' | 'error' | 'info'
export interface Toast {
  id: string
  message: string
  type: ToastType
}
