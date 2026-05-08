import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/LoginView.vue'),
      meta: { guest: true },
    },
    {
      path: '/register',
      name: 'Register',
      component: () => import('@/views/RegisterView.vue'),
      meta: { guest: true },
    },
    {
      path: '/',
      name: 'Dashboard',
      component: () => import('@/views/DashboardView.vue'),
      meta: { requiresAuth: true },
    },
    // НОВЫЙ МАРШРУТ
    {
      path: '/admin',
      name: 'Admin',
      component: () => import('@/views/AdminView.vue'),
      meta: { requiresAuth: true, requiresAdmin: true },
    },
    {
      path: '/share/file/:uid',
      name: 'PublicFile',
      component: () => import('@/views/PublicFileView.vue'),
      meta: { public: true },
    },
    {
      path: '/share/folder/:public_link',
      name: 'PublicFolder',
      component: () => import('@/views/PublicFolderView.vue'),
      meta: { public: true },
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/',
    },
  ],
})

router.beforeEach((to, _from, next) => {
  const auth = useAuthStore()

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return next({ name: 'Login' })
  }
  
  // ЗАЩИТА АДМИНКИ
  if (to.meta.requiresAdmin && !auth.isAdmin) {
    return next({ name: 'Dashboard' })
  }

  if (to.meta.guest && auth.isAuthenticated) {
    return next({ name: 'Dashboard' })
  }
  next()
})

export default router