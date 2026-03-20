<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { getWorkspace, listWorkspaceChats } from '@/shared/api/sciguide'
import {
  formatCompactDate,
  formatDateTime,
  workspaceRoleLabels,
} from '@/shared/lib/format'
import StatusBadge from '@/shared/ui/StatusBadge.vue'
import WorkspaceChatPanel from '@/widgets/workspace/WorkspaceChatPanel.vue'
import WorkspaceMembersPanel from '@/widgets/workspace/WorkspaceMembersPanel.vue'
import WorkspaceSettingsPanel from '@/widgets/workspace/WorkspaceSettingsPanel.vue'

const route = useRoute()
const router = useRouter()

const workspace = ref(null)
const chats = ref([])
const isLoadingWorkspace = ref(true)
const isLoadingChats = ref(true)
const errorMessage = ref('')
const chatsError = ref('')

const workspaceId = computed(() => String(route.params.workspaceId || ''))
const isAdmin = computed(() => workspace.value?.my_role === 'admin')

const selectedChatId = computed(() =>
  typeof route.query.chat === 'string' ? route.query.chat : '',
)

const selectedView = computed(() => {
  const view = typeof route.query.view === 'string' ? route.query.view : ''

  if (view === 'members' && isAdmin.value) {
    return 'members'
  }

  if (view === 'settings' && isAdmin.value) {
    return 'settings'
  }

  if (selectedChatId.value) {
    return 'chat'
  }

  return 'new-chat'
})

const selectedChat = computed(() =>
  chats.value.find((chat) => chat.id === selectedChatId.value) || null,
)

const mainTitle = computed(() => {
  if (selectedView.value === 'members') {
    return 'Участники воркспейса'
  }

  if (selectedView.value === 'settings') {
    return 'Настройки воркспейса'
  }

  if (selectedView.value === 'chat') {
    return selectedChat.value?.title || 'Чат'
  }

  return 'Новый чат'
})

function navigateTo(view, chatId = '') {
  const query = {}

  if (view === 'members' || view === 'settings') {
    query.view = view
  }

  if (view === 'chat' && chatId) {
    query.chat = chatId
  }

  router.replace({
    name: 'workspace',
    params: {
      workspaceId: workspaceId.value,
    },
    query,
  })
}

function openNewChat() {
  navigateTo('new-chat')
}

function openChat(chatId) {
  navigateTo('chat', chatId)
}

function openMembers() {
  navigateTo('members')
}

function openSettings() {
  navigateTo('settings')
}

async function loadWorkspace() {
  if (!workspaceId.value) {
    return
  }

  isLoadingWorkspace.value = true
  errorMessage.value = ''

  try {
    workspace.value = await getWorkspace(workspaceId.value)
  } catch (error) {
    errorMessage.value =
      error.message || 'Не удалось загрузить воркспейс.'
  } finally {
    isLoadingWorkspace.value = false
  }
}

async function loadChats() {
  if (!workspaceId.value) {
    return
  }

  isLoadingChats.value = true
  chatsError.value = ''

  try {
    const payload = await listWorkspaceChats(workspaceId.value, {
      limit: 100,
    })

    chats.value = [...(payload.items || [])].sort(
      (left, right) =>
        new Date(right.last_message_at || right.updated_at) -
        new Date(left.last_message_at || left.updated_at),
    )

    if (selectedChatId.value && !chats.value.some((chat) => chat.id === selectedChatId.value)) {
      openNewChat()
    }
  } catch (error) {
    chatsError.value = error.message || 'Не удалось загрузить чаты.'
  } finally {
    isLoadingChats.value = false
  }
}

function handleWorkspaceUpdated(updatedWorkspace) {
  workspace.value = updatedWorkspace
}

async function handleWorkspaceDeleted() {
  await router.push('/workspaces')
}

function handleChatCreated(chat) {
  chats.value = [chat, ...chats.value.filter((item) => item.id !== chat.id)]
  openChat(chat.id)
}

function handleChatUpdated(chat) {
  chats.value = [chat, ...chats.value.filter((item) => item.id !== chat.id)].sort(
    (left, right) =>
      new Date(right.last_message_at || right.updated_at) -
      new Date(left.last_message_at || left.updated_at),
  )
}

function handleChatDeleted(chatId) {
  chats.value = chats.value.filter((chat) => chat.id !== chatId)
  openNewChat()
}

watch(
  workspaceId,
  async () => {
    chats.value = []
    await Promise.all([loadWorkspace(), loadChats()])
  },
  { immediate: true },
)
</script>

<template>
  <main class="page-shell">
    <section class="page-header">
      <div>
        <button class="back-link" type="button" @click="router.push('/workspaces')">
          ← Ко всем воркспейсам
        </button>
        <p class="eyebrow">Workspace</p>
        <h1>{{ workspace?.name || 'Загрузка воркспейса…' }}</h1>
        <p class="lead">
          {{ workspace?.description || 'Здесь живут личные чаты и контекст выбранного воркспейса.' }}
        </p>
      </div>

      <div v-if="workspace" class="actions-inline">
        <StatusBadge
          :label="workspaceRoleLabels[workspace.my_role]"
          :tone="isAdmin ? 'accent' : 'neutral'"
        />
        <button class="button button--ghost" type="button" @click="loadWorkspace">
          Обновить
        </button>
      </div>
    </section>

    <p v-if="errorMessage" class="notice notice--error">{{ errorMessage }}</p>

    <section v-if="workspace" class="workspace-board">
      <aside class="workspace-menu panel panel--ghost">
        <div class="workspace-menu__head">
          <div>
            <p class="eyebrow">Навигация</p>
            <h2>{{ workspace.name }}</h2>
          </div>
          <p class="muted">Обновлён {{ formatDateTime(workspace.updated_at) }}</p>
        </div>

        <button
          class="menu-action"
          :class="{ 'menu-action--active': selectedView === 'new-chat' }"
          type="button"
          @click="openNewChat"
        >
          + Новый чат
        </button>

        <div class="workspace-menu__section">
          <div class="workspace-menu__section-title">
            <span>Чаты</span>
            <button class="button button--ghost button--compact" type="button" @click="loadChats">
              Обновить
            </button>
          </div>

          <p v-if="chatsError" class="notice notice--error">{{ chatsError }}</p>

          <div v-if="isLoadingChats" class="empty-state empty-state--compact">
            <p>Загружаем чаты…</p>
          </div>

          <div v-else-if="!chats.length" class="empty-state empty-state--compact">
            <p>Здесь пока нет ни одного чата.</p>
          </div>

          <div v-else class="menu-list">
            <button
              v-for="chat in chats"
              :key="chat.id"
              class="menu-list__item"
              :class="{ 'menu-list__item--active': selectedChatId === chat.id }"
              type="button"
              @click="openChat(chat.id)"
            >
              <strong>{{ chat.title }}</strong>
              <span>{{ formatCompactDate(chat.last_message_at || chat.updated_at) }}</span>
            </button>
          </div>
        </div>

        <div v-if="isAdmin" class="workspace-menu__section">
          <div class="workspace-menu__section-title">
            <span>Управление</span>
          </div>

          <div class="menu-list">
            <button
              class="menu-list__item"
              :class="{ 'menu-list__item--active': selectedView === 'members' }"
              type="button"
              @click="openMembers"
            >
              <strong>Пользователи</strong>
              <span>Роли и доступ</span>
            </button>
            <button
              class="menu-list__item"
              :class="{ 'menu-list__item--active': selectedView === 'settings' }"
              type="button"
              @click="openSettings"
            >
              <strong>Настройки воркспейса</strong>
              <span>Название, описание, документы, промпт</span>
            </button>
          </div>
        </div>
      </aside>

      <section class="workspace-main">
        <div class="workspace-main__header">
          <div>
            <p class="eyebrow">Рабочая область</p>
            <h2>{{ mainTitle }}</h2>
          </div>
        </div>

        <WorkspaceMembersPanel
          v-if="selectedView === 'members' && isAdmin"
          :workspace-id="workspace.id"
          :can-manage="isAdmin"
        />

        <WorkspaceSettingsPanel
          v-else-if="selectedView === 'settings' && isAdmin"
          :workspace="workspace"
          :workspace-id="workspace.id"
          :can-manage="isAdmin"
          @workspace-updated="handleWorkspaceUpdated"
          @workspace-deleted="handleWorkspaceDeleted"
        />

        <WorkspaceChatPanel
          v-else
          :workspace-id="workspace.id"
          :selected-chat="selectedChat"
          :selected-chat-id="selectedChatId"
          @chat-created="handleChatCreated"
          @chat-updated="handleChatUpdated"
          @chat-deleted="handleChatDeleted"
        />
      </section>
    </section>
  </main>
</template>
