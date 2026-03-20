<script setup>
import { computed, reactive, ref, watch } from 'vue'

import { deleteWorkspace, updateWorkspace } from '@/shared/api/sciguide'
import {
  formatDateTime,
  workspaceAccessLabels,
  workspaceRoleLabels,
  workspaceTypeLabels,
} from '@/shared/lib/format'

const props = defineProps({
  workspace: {
    type: Object,
    required: true,
  },
  canManage: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['workspace-updated', 'workspace-deleted'])

const form = reactive({
  name: '',
  description: '',
})

const isSaving = ref(false)
const isDeleting = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

const metaItems = computed(() => [
  {
    label: 'Тип',
    value: workspaceTypeLabels[props.workspace.type],
  },
  {
    label: 'Доступ',
    value: workspaceAccessLabels[props.workspace.access_mode],
  },
  {
    label: 'Роль',
    value: workspaceRoleLabels[props.workspace.my_role],
  },
  {
    label: 'Создан',
    value: formatDateTime(props.workspace.created_at),
  },
  {
    label: 'Обновлён',
    value: formatDateTime(props.workspace.updated_at),
  },
])

watch(
  () => props.workspace,
  (workspace) => {
    form.name = workspace.name || ''
    form.description = workspace.description || ''
  },
  { immediate: true },
)

async function handleSave() {
  errorMessage.value = ''
  successMessage.value = ''
  isSaving.value = true

  try {
    const updatedWorkspace = await updateWorkspace(props.workspace.id, {
      name: form.name.trim(),
      description: form.description.trim() || null,
    })

    emit('workspace-updated', updatedWorkspace)
    successMessage.value = 'Изменения сохранены.'
  } catch (error) {
    errorMessage.value =
      error.message || 'Не удалось обновить воркспейс.'
  } finally {
    isSaving.value = false
  }
}

async function handleDelete() {
  const confirmed = window.confirm(
    'Удалить воркспейс? Это действие нельзя отменить.',
  )

  if (!confirmed) {
    return
  }

  errorMessage.value = ''
  successMessage.value = ''
  isDeleting.value = true

  try {
    await deleteWorkspace(props.workspace.id)
    emit('workspace-deleted')
  } catch (error) {
    errorMessage.value =
      error.message || 'Не удалось удалить воркспейс.'
  } finally {
    isDeleting.value = false
  }
}
</script>

<template>
  <section class="stack-lg">
    <article class="panel">
      <div class="panel__header">
        <div>
          <p class="eyebrow">Обзор</p>
          <h2>Сводка по воркспейсу</h2>
        </div>
      </div>

      <div class="summary-grid">
        <div v-for="item in metaItems" :key="item.label" class="summary-card">
          <span class="summary-card__label">{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
        </div>
      </div>

      <div class="stack-sm">
        <h3>Описание</h3>
        <p class="muted">
          {{ props.workspace.description || 'Описание ещё не заполнено.' }}
        </p>
      </div>
    </article>

    <article class="panel">
      <div class="panel__header">
        <div>
          <p class="eyebrow">Настройки</p>
          <h2>Редактирование воркспейса</h2>
        </div>
        <p class="muted">
          {{ canManage ? 'Доступно администратору.' : 'Только чтение.' }}
        </p>
      </div>

      <form class="stack-md" @submit.prevent="handleSave">
        <label class="field">
          <span class="field__label">Название</span>
          <input
            v-model="form.name"
            class="field__control"
            type="text"
            maxlength="255"
            :disabled="!canManage"
            required
          />
        </label>

        <label class="field">
          <span class="field__label">Описание</span>
          <textarea
            v-model="form.description"
            class="field__control field__control--textarea"
            maxlength="4000"
            :disabled="!canManage"
          />
        </label>

        <p v-if="errorMessage" class="notice notice--error">{{ errorMessage }}</p>
        <p v-if="successMessage" class="notice notice--success">{{ successMessage }}</p>

        <div class="actions-inline">
          <button
            class="button button--primary"
            type="submit"
            :disabled="!canManage || isSaving"
          >
            {{ isSaving ? 'Сохраняем…' : 'Сохранить изменения' }}
          </button>

          <button
            class="button button--danger"
            type="button"
            :disabled="!canManage || isDeleting"
            @click="handleDelete"
          >
            {{ isDeleting ? 'Удаляем…' : 'Удалить воркспейс' }}
          </button>
        </div>
      </form>
    </article>
  </section>
</template>
