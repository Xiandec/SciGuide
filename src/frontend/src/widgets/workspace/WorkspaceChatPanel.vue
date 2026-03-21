<script setup>
import { ref, watch } from 'vue'

import {
  createChatMessage,
  createWorkspaceChat,
  deleteWorkspaceChat,
  listChatMessages,
  updateWorkspaceChat,
} from '@/shared/api/sciguide'
import {
  formatDateTime,
  messageRoleLabels,
  messageStatusLabels,
} from '@/shared/lib/format'
import RichTextMessage from '@/shared/ui/RichTextMessage.vue'
import StatusBadge from '@/shared/ui/StatusBadge.vue'

const props = defineProps({
  workspaceId: {
    type: String,
    required: true,
  },
  selectedChatId: {
    type: String,
    default: '',
  },
  selectedChat: {
    type: Object,
    default: null,
  },
})

const emit = defineEmits(['chat-created', 'chat-updated', 'chat-deleted'])

const messages = ref([])
const contextDocuments = ref([])
const chatTitle = ref('')
const renameTitle = ref('')
const messageDraft = ref('')

const isLoadingMessages = ref(false)
const isCreatingChat = ref(false)
const isRenamingChat = ref(false)
const isSendingMessage = ref(false)
const errorMessage = ref('')

watch(
  () => props.selectedChat,
  (chat) => {
    renameTitle.value = chat?.title || ''
  },
  { immediate: true },
)

watch(
  () => props.selectedChatId,
  async (chatId) => {
    contextDocuments.value = []

    if (!chatId) {
      messages.value = []
      errorMessage.value = ''
      return
    }

    await loadMessages(chatId)
  },
  { immediate: true },
)

async function loadMessages(chatId = props.selectedChatId) {
  if (!chatId) {
    messages.value = []
    return
  }

  isLoadingMessages.value = true
  errorMessage.value = ''

  try {
    const payload = await listChatMessages(props.workspaceId, chatId, {
      limit: 100,
    })

    messages.value = [...(payload.items || [])].sort(
      (left, right) => new Date(left.created_at) - new Date(right.created_at),
    )
  } catch (error) {
    errorMessage.value =
      error.message || 'Не удалось загрузить историю сообщений.'
  } finally {
    isLoadingMessages.value = false
  }
}

async function handleCreateChat() {
  if (!chatTitle.value.trim()) {
    return
  }

  errorMessage.value = ''
  isCreatingChat.value = true

  try {
    const chat = await createWorkspaceChat(props.workspaceId, {
      title: chatTitle.value.trim(),
    })

    chatTitle.value = ''
    emit('chat-created', chat)
  } catch (error) {
    errorMessage.value = error.message || 'Не удалось создать чат.'
  } finally {
    isCreatingChat.value = false
  }
}

async function handleRenameChat() {
  if (!props.selectedChat || !renameTitle.value.trim()) {
    return
  }

  errorMessage.value = ''
  isRenamingChat.value = true

  try {
    const updatedChat = await updateWorkspaceChat(
      props.workspaceId,
      props.selectedChat.id,
      {
        title: renameTitle.value.trim(),
      },
    )

    emit('chat-updated', updatedChat)
  } catch (error) {
    errorMessage.value =
      error.message || 'Не удалось переименовать чат.'
  } finally {
    isRenamingChat.value = false
  }
}

async function handleDeleteChat() {
  if (!props.selectedChat) {
    return
  }

  const confirmed = window.confirm('Удалить выбранный чат?')

  if (!confirmed) {
    return
  }

  errorMessage.value = ''

  try {
    await deleteWorkspaceChat(props.workspaceId, props.selectedChat.id)
    emit('chat-deleted', props.selectedChat.id)
  } catch (error) {
    errorMessage.value = error.message || 'Не удалось удалить чат.'
  }
}

async function handleSendMessage() {
  if (!props.selectedChat || !messageDraft.value.trim()) {
    return
  }

  errorMessage.value = ''
  isSendingMessage.value = true

  try {
    const payload = await createChatMessage(props.workspaceId, props.selectedChat.id, {
      content: messageDraft.value.trim(),
    })

    messageDraft.value = ''
    contextDocuments.value = payload.context?.documents_used || []
    messages.value = [...messages.value, payload.user_message, payload.assistant_message].sort(
      (left, right) => new Date(left.created_at) - new Date(right.created_at),
    )

    emit('chat-updated', {
      ...props.selectedChat,
      updated_at: payload.assistant_message.created_at,
      last_message_at: payload.assistant_message.created_at,
    })
  } catch (error) {
    errorMessage.value =
      error.message || 'Не удалось отправить сообщение.'
  } finally {
    isSendingMessage.value = false
  }
}
</script>

<template>
  <section class="stack-lg">
    <article v-if="!selectedChat" class="panel">
      <div class="panel__header">
        <div>
          <p class="eyebrow">Новый чат</p>
          <h2>Создай диалог в текущем воркспейсе</h2>
        </div>
      </div>

      <form class="stack-md" @submit.prevent="handleCreateChat">
        <label class="field">
          <span class="field__label">Название чата</span>
          <input
            v-model="chatTitle"
            class="field__control"
            type="text"
            maxlength="255"
            placeholder="Например, Обсуждение методов"
            required
          />
        </label>

        <p class="muted">
          После создания чат появится в меню слева, и можно будет сразу начать переписку.
        </p>

        <p v-if="errorMessage" class="notice notice--error">{{ errorMessage }}</p>

        <button class="button button--primary" :disabled="isCreatingChat">
          {{ isCreatingChat ? 'Создаём…' : 'Создать чат' }}
        </button>
      </form>
    </article>

    <article v-else class="panel panel--stretch">
      <div class="panel__header">
        <div>
          <p class="eyebrow">Чат</p>
          <h2>{{ selectedChat.title }}</h2>
        </div>

        <div class="actions-inline">
          <button class="button button--ghost" type="button" @click="loadMessages()">
            Обновить историю
          </button>
          <button class="button button--danger" type="button" @click="handleDeleteChat">
            Удалить чат
          </button>
        </div>
      </div>

      <form class="inline-form" @submit.prevent="handleRenameChat">
        <label class="field field--grow">
          <span class="field__label">Название чата</span>
          <input
            v-model="renameTitle"
            class="field__control"
            type="text"
            maxlength="255"
            required
          />
        </label>
        <button class="button button--ghost" :disabled="isRenamingChat">
          {{ isRenamingChat ? 'Сохраняем…' : 'Сохранить' }}
        </button>
      </form>

      <p v-if="errorMessage" class="notice notice--error">{{ errorMessage }}</p>

      <div v-if="isLoadingMessages" class="empty-state">
        <p>Загружаем историю сообщений…</p>
      </div>

      <div v-else-if="!messages.length" class="empty-state">
        <p>В этом чате пока нет сообщений. Отправь первый вопрос нейросети.</p>
      </div>

      <div v-else class="message-list">
        <article
          v-for="message in messages"
          :key="message.id"
          class="message-card"
          :class="{
            'message-card--user': message.role === 'user',
            'message-card--assistant': message.role === 'assistant',
          }"
        >
          <div class="message-card__meta">
            <strong>{{ messageRoleLabels[message.role] }}</strong>
            <div class="actions-inline">
              <StatusBadge
                :label="messageStatusLabels[message.status]"
                :tone="message.status === 'completed' ? 'success' : message.status === 'failed' ? 'danger' : 'neutral'"
              />
              <span>{{ formatDateTime(message.created_at) }}</span>
            </div>
          </div>

          <RichTextMessage
            v-if="message.role === 'assistant'"
            class="message-card__body"
            :content="message.content"
          />
          <p v-else class="message-card__body message-card__body--plain">{{ message.content }}</p>
        </article>
      </div>

      <div v-if="contextDocuments.length" class="context-box">
        <p class="eyebrow">Контекст ответа</p>
        <div class="context-tags">
          <span
            v-for="document in contextDocuments"
            :key="document.document_id"
            class="context-tag"
          >
            {{ document.filename }}
          </span>
        </div>
      </div>

      <form class="stack-sm" @submit.prevent="handleSendMessage">
        <label class="field">
          <span class="field__label">Сообщение нейросети</span>
          <textarea
            v-model="messageDraft"
            class="field__control field__control--textarea"
            maxlength="20000"
            placeholder="Например, Explain graph-guided retrieval."
            required
          />
        </label>
        <button class="button button--primary" :disabled="isSendingMessage">
          {{ isSendingMessage ? 'Отправляем…' : 'Отправить сообщение' }}
        </button>
      </form>
    </article>
  </section>
</template>
