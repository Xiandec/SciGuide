<script setup>
import { ref, watch } from 'vue'

import { getWorkspacePrompt, updateWorkspacePrompt } from '@/shared/api/sciguide'
import { formatDateTime } from '@/shared/lib/format'

const props = defineProps({
  workspaceId: {
    type: String,
    required: true,
  },
  canManage: {
    type: Boolean,
    default: false,
  },
})

const prompt = ref(null)
const draft = ref('')
const isLoading = ref(false)
const isSaving = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

watch(
  () => props.workspaceId,
  () => {
    loadPrompt()
  },
  { immediate: true },
)

async function loadPrompt() {
  isLoading.value = true
  errorMessage.value = ''
  successMessage.value = ''

  try {
    const payload = await getWorkspacePrompt(props.workspaceId)
    prompt.value = payload
    draft.value = payload.content
  } catch (error) {
    errorMessage.value =
      error.message || 'Не удалось загрузить системный промпт.'
  } finally {
    isLoading.value = false
  }
}

async function handleSavePrompt() {
  errorMessage.value = ''
  successMessage.value = ''
  isSaving.value = true

  try {
    const payload = await updateWorkspacePrompt(props.workspaceId, {
      content: draft.value.trim(),
    })

    prompt.value = payload
    draft.value = payload.content
    successMessage.value = 'Промпт обновлён.'
  } catch (error) {
    errorMessage.value =
      error.message || 'Не удалось сохранить системный промпт.'
  } finally {
    isSaving.value = false
  }
}
</script>

<template>
  <section class="panel">
    <div class="panel__header">
      <div>
        <p class="eyebrow">Системный промпт</p>
        <h2>Инструкции, общие для всех запросов внутри воркспейса</h2>
      </div>
      <button class="button button--ghost" type="button" @click="loadPrompt">
        Обновить
      </button>
    </div>

    <div v-if="isLoading" class="empty-state">
      <p>Загружаем системный промпт…</p>
    </div>

    <form v-else class="stack-md" @submit.prevent="handleSavePrompt">
      <p class="muted">
        {{ canManage ? 'Редактирование доступно администратору.' : 'У тебя только режим просмотра.' }}
      </p>

      <label class="field">
        <span class="field__label">Содержимое промпта</span>
        <textarea
          v-model="draft"
          class="field__control field__control--textarea field__control--xl"
          maxlength="20000"
          :disabled="!canManage"
          required
        />
      </label>

      <div class="summary-grid">
        <div class="summary-card">
          <span class="summary-card__label">Обновлён</span>
          <strong>{{ prompt ? formatDateTime(prompt.updated_at) : '—' }}</strong>
        </div>
        <div class="summary-card">
          <span class="summary-card__label">Updated by</span>
          <strong>{{ prompt?.updated_by || '—' }}</strong>
        </div>
      </div>

      <p v-if="errorMessage" class="notice notice--error">{{ errorMessage }}</p>
      <p v-if="successMessage" class="notice notice--success">{{ successMessage }}</p>

      <button class="button button--primary" :disabled="!canManage || isSaving">
        {{ isSaving ? 'Сохраняем…' : 'Сохранить промпт' }}
      </button>
    </form>
  </section>
</template>
