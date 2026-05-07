<script setup lang="ts">
import { useFileStore } from '@/stores/files'

const store = useFileStore()
</script>

<template>
  <nav class="breadcrumb" aria-label="Breadcrumb">
    <template v-for="(crumb, idx) in store.breadcrumbs" :key="crumb.uid ?? 'root'">
      <span
        :class="['breadcrumb-item', { active: idx === store.breadcrumbs.length - 1 }]"
        @click="idx < store.breadcrumbs.length - 1 && store.navigateBreadcrumb(crumb)"
      >
        <i v-if="idx === 0" class="pi pi-cloud" style="margin-right:4px;font-size:13px" />
        {{ crumb.name }}
      </span>
      <span v-if="idx < store.breadcrumbs.length - 1" class="breadcrumb-sep">
        <i class="pi pi-chevron-right" style="font-size:10px" />
      </span>
    </template>
  </nav>
</template>
