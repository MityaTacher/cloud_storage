<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const theme = useThemeStore()
const router = useRouter()

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <aside class="sidebar">
    <!-- Logo -->
    <div class="sidebar-logo">
      <div class="sidebar-logo-icon">☁️</div>
      <span class="sidebar-logo-text">CloudVault</span>
    </div>

    <!-- Nav -->
    <nav class="sidebar-nav">
      <router-link to="/" class="sidebar-nav-item" active-class="active" id="nav-dashboard">
        <i class="pi pi-home nav-icon" />
        My Cloud
      </router-link>

      <router-link v-if="auth.isAdmin" to="/admin" class="sidebar-nav-item" active-class="active">
        <i class="pi pi-users nav-icon" style="color:var(--color-warning)" />
        Admin Panel
      </router-link>
    </nav>

    <!-- Footer -->
    <div class="sidebar-footer">
      <!-- Theme toggle -->
      <button class="sidebar-nav-item" style="width:100%;border:none;background:none;cursor:pointer" @click="theme.toggle()" id="theme-toggle-btn">
        <i :class="['nav-icon', theme.isDark ? 'pi pi-sun' : 'pi pi-moon']" />
        {{ theme.isDark ? 'Light mode' : 'Dark mode' }}
      </button>

      <!-- Logout -->
      <button class="sidebar-nav-item" style="width:100%;border:none;background:none;cursor:pointer;color:var(--color-danger)" @click="logout" id="logout-btn">
        <i class="pi pi-sign-out nav-icon" />
        Sign out
      </button>
    </div>
  </aside>
</template>
