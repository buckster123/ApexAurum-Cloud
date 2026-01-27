import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/chat'
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { requiresGuest: true }
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/RegisterView.vue'),
      meta: { requiresGuest: true }
    },
    {
      path: '/chat',
      name: 'chat',
      component: () => import('@/views/ChatView.vue'),
      meta: { requiresAuth: false }  // Allow unauthenticated for testing
    },
    {
      path: '/chat/:id',
      name: 'conversation',
      component: () => import('@/views/ChatView.vue'),
      meta: { requiresAuth: true }  // Saved conversations still require auth
    },
    {
      path: '/agents',
      name: 'agents',
      component: () => import('@/views/AgentsView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/village',
      name: 'village',
      component: () => import('@/views/VillageView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/music',
      name: 'music',
      component: () => import('@/views/MusicView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('@/views/SettingsView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/files',
      name: 'files',
      component: () => import('@/views/FilesView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/files/:folderId',
      name: 'folder',
      component: () => import('@/views/FilesView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/neural',
      name: 'neural',
      component: () => import('@/views/NeuralView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/village-gui',
      name: 'village-gui',
      component: () => import('@/views/VillageGUIView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/billing',
      name: 'billing',
      component: () => import('@/views/BillingView.vue'),
      meta: { requiresAuth: false }  // Allow viewing pricing without auth
    },
    {
      path: '/billing/success',
      name: 'billing-success',
      component: () => import('@/views/BillingView.vue'),
      meta: { requiresAuth: true }  // Need auth to verify purchase
    },
  ]
})

// Wait for auth initialization helper
function waitForAuth(auth) {
  return new Promise(resolve => {
    if (auth.initialized) {
      resolve()
      return
    }
    // Poll until initialized (init is fast, typically <100ms)
    const interval = setInterval(() => {
      if (auth.initialized) {
        clearInterval(interval)
        resolve()
      }
    }, 10)
  })
}

// Navigation guards
router.beforeEach(async (to, from, next) => {
  const auth = useAuthStore()

  // Wait for auth to initialize before checking
  await waitForAuth(auth)

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    next({ name: 'login', query: { redirect: to.fullPath } })
  } else if (to.meta.requiresGuest && auth.isAuthenticated) {
    next({ name: 'chat' })
  } else {
    next()
  }
})

export default router
