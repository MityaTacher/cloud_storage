<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'

const router = useRouter()
const auth = useAuthStore()
const toast = useToastStore()

const form = reactive({ email: '', username: '', password: '', confirmPassword: '' })
const showPassword = ref(false)

const errors = reactive({ email: '', username: '', password: '', confirmPassword: '' })

function validate() {
  errors.email = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email) ? '' : 'Valid email is required'
  errors.username = form.username.trim().length >= 3 ? '' : 'Username must be at least 3 characters'
  errors.password = form.password.length >= 4 ? '' : 'Password must be at least 4 characters'
  errors.confirmPassword = form.password === form.confirmPassword ? '' : 'Passwords do not match'
  return !errors.email && !errors.username && !errors.password && !errors.confirmPassword
}

async function submit() {
  if (!validate()) return
  const ok = await auth.register({ email: form.email, username: form.username, password: form.password })
  if (ok) {
    toast.success('Account created! Please sign in.')
    router.push('/login')
  } else {
    toast.error(auth.error ?? 'Registration failed')
  }
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-glow auth-glow-1" />
    <div class="auth-glow auth-glow-2" />

    <div class="auth-card" style="max-width:440px">
      <!-- Header -->
      <div style="text-align:center;margin-bottom:32px">
        <div style="font-size:48px;margin-bottom:12px">☁️</div>
        <h1 style="font-size:26px;font-weight:800;color:var(--color-text-primary);margin-bottom:6px">
          Create account
        </h1>
        <p style="font-size:14px;color:var(--color-text-muted)">
          Join CloudVault — your personal cloud storage
        </p>
      </div>

      <form @submit.prevent="submit" novalidate style="display:flex;flex-direction:column;gap:18px">
        <!-- Email -->
        <div>
          <label class="form-label" for="reg-email">Email</label>
          <div style="position:relative">
            <i class="pi pi-envelope" style="position:absolute;left:14px;top:50%;transform:translateY(-50%);color:var(--color-text-muted);font-size:14px" />
            <input
              id="reg-email"
              v-model="form.email"
              :class="['form-input', { error: errors.email }]"
              style="padding-left:42px"
              type="email"
              placeholder="you@example.com"
              autocomplete="email"
              @input="errors.email = ''"
            />
          </div>
          <p v-if="errors.email" class="form-error">{{ errors.email }}</p>
        </div>

        <!-- Username -->
        <div>
          <label class="form-label" for="reg-username">Username</label>
          <div style="position:relative">
            <i class="pi pi-user" style="position:absolute;left:14px;top:50%;transform:translateY(-50%);color:var(--color-text-muted);font-size:14px" />
            <input
              id="reg-username"
              v-model="form.username"
              :class="['form-input', { error: errors.username }]"
              style="padding-left:42px"
              type="text"
              placeholder="cool_username"
              autocomplete="username"
              @input="errors.username = ''"
            />
          </div>
          <p v-if="errors.username" class="form-error">{{ errors.username }}</p>
        </div>

        <!-- Password -->
        <div>
          <label class="form-label" for="reg-password">Password</label>
          <div style="position:relative">
            <i class="pi pi-lock" style="position:absolute;left:14px;top:50%;transform:translateY(-50%);color:var(--color-text-muted);font-size:14px" />
            <input
              id="reg-password"
              v-model="form.password"
              :class="['form-input', { error: errors.password }]"
              style="padding-left:42px;padding-right:42px"
              :type="showPassword ? 'text' : 'password'"
              placeholder="min 4 characters"
              autocomplete="new-password"
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

        <!-- Confirm password -->
        <div>
          <label class="form-label" for="reg-confirm">Confirm password</label>
          <div style="position:relative">
            <i class="pi pi-lock" style="position:absolute;left:14px;top:50%;transform:translateY(-50%);color:var(--color-text-muted);font-size:14px" />
            <input
              id="reg-confirm"
              v-model="form.confirmPassword"
              :class="['form-input', { error: errors.confirmPassword }]"
              style="padding-left:42px"
              type="password"
              placeholder="repeat password"
              autocomplete="new-password"
              @input="errors.confirmPassword = ''"
            />
          </div>
          <p v-if="errors.confirmPassword" class="form-error">{{ errors.confirmPassword }}</p>
        </div>

        <!-- Strength indicator -->
        <div v-if="form.password" style="display:flex;gap:4px">
          <div
            v-for="i in 4"
            :key="i"
            style="height:3px;flex:1;border-radius:99px;transition:background 0.2s"
            :style="{
              background: form.password.length >= i * 2
                ? i <= 2 ? '#ef4444' : i === 3 ? '#f59e0b' : '#22c55e'
                : 'var(--color-border)'
            }"
          />
        </div>

        <button
          id="register-submit-btn"
          type="submit"
          class="btn btn-primary"
          :disabled="auth.loading"
          style="width:100%;justify-content:center;padding:14px;font-size:15px;margin-top:4px"
        >
          <span v-if="auth.loading" class="spinner" />
          <i v-else class="pi pi-user-plus" />
          {{ auth.loading ? 'Creating…' : 'Create account' }}
        </button>
      </form>

      <div style="display:flex;align-items:center;gap:12px;margin:24px 0">
        <div style="flex:1;height:1px;background:var(--color-border)" />
        <span style="font-size:12px;color:var(--color-text-muted)">Already have an account?</span>
        <div style="flex:1;height:1px;background:var(--color-border)" />
      </div>

      <router-link
        to="/login"
        class="btn btn-ghost"
        style="width:100%;justify-content:center"
        id="go-login-btn"
      >
        Sign in
      </router-link>
    </div>
  </div>
</template>
