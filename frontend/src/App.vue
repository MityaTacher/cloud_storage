<script setup lang="ts">
import { RouterView } from 'vue-router'
import ToastContainer from '@/components/ToastContainer.vue'
import UploadProgress from '@/components/UploadProgress.vue'
import { useThemeStore } from '@/stores/theme'

// Initialise theme on app boot
useThemeStore()
</script>

<template>
  <RouterView />
  <ToastContainer />
  <UploadProgress />
</template>
