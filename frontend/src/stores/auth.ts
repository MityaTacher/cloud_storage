import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'
import type { User, LoginForm, RegisterForm } from '@/types'

// Функция для чтения JWT токена
function parseJwt(token: string) {
  try {
    const base64Url = token.split('.')[1]
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
    return JSON.parse(window.atob(base64))
  } catch (e) {
    return null
  }
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const accessToken = ref<string | null>(localStorage.getItem('access_token'))
  const refreshToken = ref<string | null>(localStorage.getItem('refresh_token'))
  const loading = ref(false)
  const error = ref<string | null>(null)

  const isAuthenticated = computed(() => !!accessToken.value)
  
  // Достаем роль прямо из токена
  const tokenPayload = computed(() => accessToken.value ? parseJwt(accessToken.value) : null)
  const isAdmin = computed(() => tokenPayload.value?.role === 'admin')

  function setTokens(access: string, refresh: string) {
    accessToken.value = access
    refreshToken.value = refresh
    localStorage.setItem('access_token', access)
    localStorage.setItem('refresh_token', refresh)
  }

  function clearAuth() {
    user.value = null
    accessToken.value = null
    refreshToken.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  async function login(form: LoginForm) {
    loading.value = true
    error.value = null
    try {
      const { data } = await authApi.login(form)
      setTokens(data.access_token, data.refresh_token)
      return true
    } catch (e: any) {
      error.value = e?.response?.data?.detail ?? 'Login failed'
      return false
    } finally {
      loading.value = false
    }
  }

  async function register(form: RegisterForm) {
    loading.value = true
    error.value = null
    try {
      await authApi.register(form)
      return true
    } catch (e: any) {
      const detail = e?.response?.data?.detail
      error.value = Array.isArray(detail)
        ? detail.map((d: any) => d.msg).join(', ')
        : (detail ?? 'Registration failed')
      return false
    } finally {
      loading.value = false
    }
  }

  function logout() {
    clearAuth()
  }

  return {
    user,
    accessToken,
    refreshToken,
    loading,
    error,
    isAuthenticated,
    isAdmin, // Экспортируем флаг админа
    login,
    register,
    logout,
    setTokens,
  }
})