<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { adminApi } from '@/api/admin'
import { useToastStore } from '@/stores/toast'
import { useThemeStore } from '@/stores/theme'
import type { StorageNode, AdminDashboardData } from '@/types'
import Sidebar from '@/components/Sidebar.vue'

const nodes = ref<StorageNode[]>([])
const dashData = ref<AdminDashboardData | null>(null)
const loading = ref(true)
const toast = useToastStore()
const theme = useThemeStore()
let interval: any

const chartData = ref()
const chartOptions = ref({})

// Функция для динамического обновления стилей графика
function updateChartOptions() {
  const docStyle = getComputedStyle(document.documentElement)
  const textColor = docStyle.getPropertyValue('--color-text-secondary').trim() || '#94a3b8'

  chartOptions.value = {
    // ВАЖНО: Отключаем стандартные пропорции Chart.js, чтобы он слушался CSS
    maintainAspectRatio: false, 
    responsive: true,
    plugins: { 
      legend: { 
        position: 'bottom', // Легенда снизу делает график визуально ровнее по центру
        labels: { 
          color: textColor,
          usePointStyle: true, // Круглые маркеры
          padding: 20,
          font: { family: "'Inter', sans-serif", size: 12 }
        } 
      } 
    },
    cutout: '75%', // Толщина кольца
    elements: {
      arc: { borderWidth: 0 } // Без обводки
    },
    layout: {
      padding: 0
    }
  }
}

watch(() => theme.isDark, () => {
  updateChartOptions()
})

async function fetchData() {
  try {
    const [nodesRes, dashRes] = await Promise.all([
      adminApi.getNodes(),
      adminApi.getDashboardData()
    ])
    nodes.value = nodesRes.data
    dashData.value = dashRes.data
    setupChart()
  } catch (e: any) {
    toast.error('Failed to load admin data')
  } finally {
    loading.value = false
  }
}

function setupChart() {
  if (!dashData.value) return
  const data = dashData.value.file_types
  
  const labels = Object.keys(data).filter(k => data[k] > 0)
  const values = labels.map(k => data[k])
  
  if (values.length === 0) return
  
  chartData.value = {
    labels: labels,
    datasets: [{
      data: values,
      backgroundColor: ['#6366f1', '#10b981', '#f59e0b', '#3b82f6', '#8b5cf6', '#64748b'],
      borderWidth: 0,
    }]
  }
}

onMounted(() => {
  updateChartOptions()
  fetchData()
  interval = setInterval(() => {
    adminApi.getNodes().then(res => { nodes.value = res.data }).catch(() => {})
  }, 5000)
})

onUnmounted(() => clearInterval(interval))

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

function isNodeOnline(lastHeartbeat: string): boolean {
  const diff = Date.now() - new Date(lastHeartbeat + 'Z').getTime()
  return diff < 45000
}

function getProgressColor(percent: number) {
  if (percent > 90) return 'var(--color-danger)'
  if (percent > 70) return 'var(--color-warning)'
  return 'var(--color-accent)'
}

async function deleteUser(user: any) {
  if (!confirm(`Delete user ${user.username}? All files will be lost!`)) return
  try {
    await adminApi.deleteUser(user.id)
    toast.success('User deleted')
    dashData.value!.users = dashData.value!.users.filter(u => u.id !== user.id)
  } catch (e: any) {
    toast.error('Failed to delete user')
  }
}
</script>

<template>
  <div class="app-layout">
    <Sidebar />

    <div class="main-content" style="padding: 32px">
      <div style="margin-bottom: 24px;">
        <h1 style="font-size:24px; font-weight:700">System Dashboard</h1>
        <p style="color:var(--color-text-muted); font-size:14px">Real-time overview & analytics</p>
      </div>

      <div v-if="loading" class="skeleton" style="height:60px; border-radius:var(--radius-md)" />

      <template v-else-if="dashData">
        
        <!-- 1. OVERVIEW CARDS -->
        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; margin-bottom: 32px;">
          <div class="glass-card stat-card">
            <div class="stat-icon" style="background: rgba(99,102,241,0.15); color: var(--color-accent)"><i class="pi pi-database"></i></div>
            <div>
              <div class="stat-label">Total Storage Used</div>
              <div class="stat-value">{{ formatBytes(dashData.global.total_size_bytes) }}</div>
            </div>
          </div>
          <div class="glass-card stat-card">
            <div class="stat-icon" style="background: rgba(16,185,129,0.15); color: #10b981"><i class="pi pi-file"></i></div>
            <div>
              <div class="stat-label">Total Files</div>
              <div class="stat-value">{{ dashData.global.total_files }}</div>
            </div>
          </div>
          <div class="glass-card stat-card">
            <div class="stat-icon" style="background: rgba(245,158,11,0.15); color: #f59e0b"><i class="pi pi-share-alt"></i></div>
            <div>
              <div class="stat-label">Public Links</div>
              <div class="stat-value">{{ dashData.global.total_public_links }}</div>
            </div>
          </div>
        </div>

        <div style="display:flex; gap: 32px; margin-bottom:32px; align-items: stretch; flex-wrap: wrap;">
          
          <!-- 2. NODE HEALTH -->
          <div style="flex: 2; min-width: 300px; display: flex; flex-direction: column;">
            <h2 class="section-title">Node Health</h2>
            <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px;">
              <div v-for="node in nodes" :key="node.id" class="glass-card" style="padding: 20px;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
                  <strong style="font-size:16px"><i class="pi pi-server" style="margin-right:8px; color:var(--color-text-muted)"></i>{{ node.name }}</strong>
                  <span :class="['badge', isNodeOnline(node.last_heartbeat) ? 'badge-public' : 'badge-private']">
                    {{ isNodeOnline(node.last_heartbeat) ? 'Online' : 'Offline' }}
                  </span>
                </div>

                <!-- Disk Bar -->
                <div class="bar-group">
                  <div class="bar-header"><span>Storage</span><span>{{ formatBytes(node.total_space_bytes - node.free_space_bytes) }} / {{ formatBytes(node.total_space_bytes) }}</span></div>
                  <div class="bar-track"><div class="bar-fill" :style="{ width: `${((node.total_space_bytes - node.free_space_bytes) / node.total_space_bytes) * 100}%`, background: getProgressColor(((node.total_space_bytes - node.free_space_bytes) / node.total_space_bytes) * 100) }"></div></div>
                </div>
                
                <!-- CPU Bar -->
                <div class="bar-group">
                  <div class="bar-header"><span>CPU Usage</span><span>{{ node.cpu_percent }}%</span></div>
                  <div class="bar-track"><div class="bar-fill" :style="{ width: `${node.cpu_percent}%`, background: getProgressColor(node.cpu_percent) }"></div></div>
                </div>

                <!-- RAM Bar -->
                <div class="bar-group">
                  <div class="bar-header"><span>RAM Usage</span><span>{{ node.ram_percent }}%</span></div>
                  <div class="bar-track"><div class="bar-fill" :style="{ width: `${node.ram_percent}%`, background: getProgressColor(node.ram_percent) }"></div></div>
                </div>

                <!-- Network -->
                <div style="display:flex; gap:16px; background:var(--color-bg-primary); padding:10px; border-radius:var(--radius-sm); border:1px solid var(--color-border); margin-top:16px">
                  <div style="flex:1"><span class="net-lbl">RX </span> <span class="net-val">{{ formatBytes(node.rx_bytes_per_sec) }}/s</span></div>
                  <div style="width:1px; background:var(--color-border)"></div>
                  <div style="flex:1"><span class="net-lbl">TX </span> <span class="net-val">{{ formatBytes(node.tx_bytes_per_sec) }}/s</span></div>
                </div>
              </div>
            </div>
          </div>

          <!-- 3. DATA ANALYTICS -->
          <div style="flex: 1; min-width: 300px; max-width: 400px; display: flex; flex-direction: column;">
            <h2 class="section-title">Data Analytics</h2>
            
            <div class="glass-card" style="flex: 1; padding: 24px; display: flex; align-items: center; justify-content: center; min-height: 280px;">
              
              <!-- ЖЕСТКИЙ КВАДРАТ: 100% высота и ширина от этого квадрата заставит график идеально отцентрироваться -->
              <div v-if="chartData" style="position: relative; width: 100%; max-width: 260px; height: 260px;">
                <Chart type="doughnut" :data="chartData" :options="chartOptions" style="width: 100%; height: 100%; display: block;" />
              </div>

              <div v-else style="color:var(--color-text-muted); text-align:center;">
                <i class="pi pi-box" style="font-size:32px; margin-bottom:12px; opacity:0.5"></i>
                <p>No files uploaded yet</p>
              </div>

            </div>
          </div>

        </div>

        <!-- 4. USERS QUOTAS -->
        <h2 class="section-title">Users Storage Usage</h2>
        <div class="glass-card" style="overflow: hidden;">
          <table class="admin-table">
            <thead>
              <tr>
                <th>User</th>
                <th>Role</th>
                <th>Storage Used</th>
                <th style="text-align:right">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="user in dashData.users" :key="user.id">
                <td>
                  <div style="font-weight:600; color:var(--color-text-primary)">{{ user.username }}</div>
                  <div style="font-size:12px; color:var(--color-text-muted)">{{ user.email }}</div>
                </td>
                <td>
                  <span :class="['badge', user.role === 'admin' ? 'badge-admin' : 'badge-user']">
                    {{ user.role.toUpperCase() }}
                  </span>
                </td>
                
                <td style="width: 40%">
                  <div style="display:flex; align-items:center; gap:12px">
                    <span style="font-size:13px; font-weight:600; min-width: 60px">{{ formatBytes(user.used_bytes) }}</span>
                    <div style="flex:1; height:6px; background:var(--color-bg-primary); border-radius:99px; border:1px solid var(--color-border); overflow:hidden">
                      <div :style="{ 
                        width: `${Math.min((user.used_bytes / (Math.max(...dashData.users.map(u => u.used_bytes)) || 1)) * 100, 100)}%`, 
                        height: '100%', 
                        background: 'var(--color-accent)' 
                      }"></div>
                    </div>
                  </div>
                </td>

                <td style="text-align:right">
                  <button v-if="user.role !== 'admin'" class="btn btn-sm btn-danger" @click="deleteUser(user)">
                    <i class="pi pi-trash" /> Delete
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

      </template>
    </div>
  </div>
</template>

<style scoped>
.section-title { font-size:16px; font-weight:600; margin-bottom: 16px; color:var(--color-text-secondary); }

.stat-card { display: flex; align-items: center; gap: 16px; padding: 24px; }
.stat-icon { width: 54px; height: 54px; border-radius: var(--radius-md); display: flex; align-items: center; justify-content: center; font-size: 24px; }
.stat-label { font-size: 13px; color: var(--color-text-muted); font-weight: 500; margin-bottom: 4px; }
.stat-value { font-size: 24px; font-weight: 800; color: var(--color-text-primary); line-height: 1; }

.bar-group { margin-bottom: 12px; }
.bar-header { display: flex; justify-content: space-between; font-size: 12px; color: var(--color-text-muted); margin-bottom: 4px; }
.bar-track { width: 100%; height: 6px; background: var(--color-border); border-radius: 99px; overflow: hidden; }
.bar-fill { height: 100%; transition: width 0.5s ease, background-color 0.3s ease; }

.net-lbl { font-size: 11px; color: var(--color-text-muted); font-weight: 600; }
.net-val { font-size: 13px; font-weight: 700; color: var(--color-text-primary); }

.admin-table { width: 100%; border-collapse: collapse; text-align: left; }
.admin-table th { padding: 16px; font-size: 13px; text-transform: uppercase; color: var(--color-text-muted); border-bottom: 1px solid var(--color-border); background: var(--color-bg-secondary); }
.admin-table td { padding: 16px; font-size: 14px; border-bottom: 1px solid var(--color-border); }
.admin-table tbody tr:hover { background: var(--color-bg-hover); }

.badge-admin { background: rgba(245, 158, 11, 0.2); color: var(--color-warning); }
.badge-user { background: rgba(99, 102, 241, 0.15); color: var(--color-accent); }
</style>