<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { useSessionStore } from '@/app/session-store'
import { getInitials } from '@/shared/lib/format'

const router = useRouter()
const session = useSessionStore()

const isMenuOpen = ref(false)
const menuRef = ref(null)

const userName = computed(
  () => session.state.user?.display_name || session.state.user?.email || 'Гость',
)

const userEmail = computed(() => session.state.user?.email || '')

const isAuthenticated = computed(() => session.isAuthenticated.value)

function toggleMenu() {
  if (!isAuthenticated.value) {
    return
  }

  isMenuOpen.value = !isMenuOpen.value
}

async function handleLogout() {
  isMenuOpen.value = false
  await session.logout()
  await router.replace('/login')
}

function handleDocumentClick(event) {
  if (!menuRef.value?.contains(event.target)) {
    isMenuOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleDocumentClick)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleDocumentClick)
})
</script>

<template>
  <header class="app-header">
    <div class="app-header__inner">
      <button class="brand-mark" type="button" @click="router.push('/workspaces')">
        <span class="brand-mark__dot" />
        <span class="brand-mark__text">SciGuide</span>
      </button>

      <div v-if="isAuthenticated" ref="menuRef" class="account-menu">
        <div class="account-menu__summary">
          <div class="avatar">
            {{ getInitials(userName) }}
          </div>
          <div class="account-menu__meta">
            <strong>{{ userName }}</strong>
            <span>{{ userEmail }}</span>
          </div>
          <button class="account-menu__toggle" type="button" @click.stop="toggleMenu">
            <span />
            <span />
            <span />
          </button>
        </div>

        <div v-if="isMenuOpen" class="account-menu__dropdown">
          <button class="account-menu__action" type="button" @click="handleLogout">
            Выйти из аккаунта
          </button>
        </div>
      </div>
    </div>
  </header>
</template>
