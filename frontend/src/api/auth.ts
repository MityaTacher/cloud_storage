import api from './axios'
import type { LoginForm, RegisterForm, TokenResponse, User } from '@/types'

export const authApi = {
  login(form: LoginForm): Promise<{ data: TokenResponse }> {
    const params = new URLSearchParams()
    params.append('username', form.username)
    params.append('password', form.password)
    return api.post('/users/token', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
  },

  register(form: RegisterForm): Promise<{ data: User }> {
    return api.post('/users/', {
      email: form.email,
      username: form.username,
      password: form.password,
    })
  },

  refresh(token: string): Promise<{ data: TokenResponse }> {
    return api.post('/users/refresh', { token })
  },
}
