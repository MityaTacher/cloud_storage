<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'

const router = useRouter()
const auth = useAuthStore()
const toast = useToastStore()

const form = reactive({ username: '', password: '' })
const showPassword = ref(false)

const errors = reactive({ username: '', password: '' })

function validate() {
  errors.username = form.username.trim() ? '' : 'Username is required'
  errors.password = form.password ? '' : 'Password is required'
  return !errors.username && !errors.password
}

async function submit() {
  if (!validate()) return
  const ok = await auth.login({ username: form.username, password: form.password })
  if (ok) {
    toast.success('Welcome back!')
    router.push('/')
  } else {
    toast.error(auth.error ?? 'Login failed')
  }
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-glow auth-glow-1" />
    <div class="auth-glow auth-glow-2" />

    <div class="auth-card">
      <!-- Header -->
      <div style="text-align:center;margin-bottom:36px">
        <div style="font-size:48px;margin-bottom:12px">☁️</div>
        <h1 style="font-size:26px;font-weight:800;color:var(--color-text-primary);margin-bottom:6px">
          Welcome back
        </h1>
        <p style="font-size:14px;color:var(--color-text-muted)">
          Sign in to your CloudVault account
        </p>
      </div>

      <!-- Form -->
      <form @submit.prevent="submit" novalidate style="display:flex;flex-direction:column;gap:20px">
        <!-- Username -->
        <div>
          <label class="form-label" for="login-username">Username</label>
          <div style="position:relative">
            <i class="pi pi-user" style="position:absolute;left:14px;top:50%;transform:translateY(-50%);color:var(--color-text-muted);font-size:14px" />
            <input
              id="login-username"
              v-model="form.username"
              :class="['form-input', { error: errors.username }]"
              style="padding-left:42px"
              type="text"
              placeholder="your_username"
              autocomplete="username"
              @input="errors.username = ''"
            />
          </div>
          <p v-if="errors.username" class="form-error">{{ errors.username }}</p>
        </div>

        <!-- Password -->
        <div>
          <label class="form-label" for="login-password">Password</label>
          <div style="position:relative">
            <i class="pi pi-lock" style="position:absolute;left:14px;top:50%;transform:translateY(-50%);color:var(--color-text-muted);font-size:14px" />
            <input
              id="login-password"
              v-model="form.password"
              :class="['form-input', { error: errors.password }]"
              style="padding-left:42px;padding-right:42px"
              :type="showPassword ? 'text' : 'password'"
              placeholder="••••••••"
              autocomplete="current-password"
              @input="errors.password = ''"
            />
            <button
              type="button"
              style="position:absolute;right:14px;top:50%;transform:translateY(-50%);background:none;border:none;cursor:pointer;color:var(--color-text-muted);font-size:14px;padding:0"
              @click="showPassword = !showPassword"
              :aria-label="showPassword ? 'Hide password' : 'Show password'"
            >
              <i :class="showPassword ? 'pi pi-eye-slash' : 'pi pi-eye'" />
            </button>
          </div>
          <p v-if="errors.password" class="form-error">{{ errors.password }}</p>
        </div>

        <!-- Submit -->
        <button
          id="login-submit-btn"
          type="submit"
          class="btn btn-primary"
          :disabled="auth.loading"
          style="width:100%;justify-content:center;padding:14px;font-size:15px;margin-top:4px"
        >
          <span v-if="auth.loading" class="spinner" />
          <i v-else class="pi pi-sign-in" />
          {{ auth.loading ? 'Signing in…' : 'Sign in' }}
        </button>
      </form>

      <!-- Divider -->
      <div style="display:flex;align-items:center;gap:12px;margin:24px 0">
        <div style="flex:1;height:1px;background:var(--color-border)" />
        <span style="font-size:12px;color:var(--color-text-muted)">Don't have an account?</span>
        <div style="flex:1;height:1px;background:var(--color-border)" />
      </div>

      <router-link
        to="/register"
        class="btn btn-ghost"
        style="width:100%;justify-content:center"
        id="go-register-btn"
      >
        Create account
      </router-link>
    </div>
  </div>
</template>
