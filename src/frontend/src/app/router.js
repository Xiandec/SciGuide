import { createRouter, createWebHistory } from 'vue-router'

import { initializeSessionStore, useSessionStore } from '@/app/session-store'
import LoginPage from '@/pages/LoginPage.vue'
import WorkspacePage from '@/pages/WorkspacePage.vue'
import WorkspacesPage from '@/pages/WorkspacesPage.vue'

const routes = [
  {
    path: '/',
    redirect: '/workspaces',
  },
  {
    path: '/login',
    name: 'login',
    component: LoginPage,
    meta: {
      public: true,
    },
  },
  {
    path: '/workspaces',
    name: 'workspaces',
    component: WorkspacesPage,
    meta: {
      requiresAuth: true,
    },
  },
  {
    path: '/workspaces/:workspaceId',
    name: 'workspace',
    component: WorkspacePage,
    meta: {
      requiresAuth: true,
    },
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/workspaces',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  await initializeSessionStore()

  const session = useSessionStore()

  if (to.meta.requiresAuth && !session.isAuthenticated.value) {
    return {
      name: 'login',
      query: {
        redirect: to.fullPath,
      },
    }
  }

  if (to.name === 'login' && session.isAuthenticated.value) {
    return {
      name: 'workspaces',
    }
  }

  return true
})

export default router
