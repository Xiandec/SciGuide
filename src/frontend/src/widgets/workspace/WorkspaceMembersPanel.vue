<script setup>
import { reactive, ref, watch } from 'vue'

import {
  addWorkspaceMember,
  listWorkspaceMembers,
  removeWorkspaceMember,
  updateWorkspaceMember,
} from '@/shared/api/sciguide'
import { formatDateTime, workspaceRoleLabels } from '@/shared/lib/format'

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

const members = ref([])
const roleDrafts = reactive({})
const addForm = reactive({
  user_id: '',
  role: 'user',
})

const isLoading = ref(false)
const isSubmitting = ref(false)
const errorMessage = ref('')

watch(
  () => props.workspaceId,
  () => {
    loadMembers()
  },
  { immediate: true },
)

async function loadMembers() {
  isLoading.value = true
  errorMessage.value = ''

  try {
    const payload = await listWorkspaceMembers(props.workspaceId)
    members.value = payload.items || []

    members.value.forEach((member) => {
      roleDrafts[member.user_id] = member.role
    })
  } catch (error) {
    errorMessage.value =
      error.message || 'Не удалось загрузить участников.'
  } finally {
    isLoading.value = false
  }
}

async function handleAddMember() {
  errorMessage.value = ''
  isSubmitting.value = true

  try {
    await addWorkspaceMember(props.workspaceId, {
      user_id: addForm.user_id.trim(),
      role: addForm.role,
    })

    addForm.user_id = ''
    addForm.role = 'user'
    await loadMembers()
  } catch (error) {
    errorMessage.value =
      error.message || 'Не удалось добавить участника.'
  } finally {
    isSubmitting.value = false
  }
}

async function handleUpdateRole(member) {
  errorMessage.value = ''

  try {
    await updateWorkspaceMember(props.workspaceId, member.user_id, {
      role: roleDrafts[member.user_id],
    })

    await loadMembers()
  } catch (error) {
    errorMessage.value =
      error.message || 'Не удалось обновить роль участника.'
  }
}

async function handleRemoveMember(member) {
  const confirmed = window.confirm('Удалить участника из воркспейса?')

  if (!confirmed) {
    return
  }

  errorMessage.value = ''

  try {
    await removeWorkspaceMember(props.workspaceId, member.user_id)
    await loadMembers()
  } catch (error) {
    errorMessage.value =
      error.message || 'Не удалось удалить участника.'
  }
}
</script>

<template>
  <section class="stack-lg">
    <article class="panel">
      <div class="panel__header">
        <div>
          <p class="eyebrow">Участники</p>
          <h2>Состав общего воркспейса и роли пользователей</h2>
        </div>
        <button class="button button--ghost" type="button" @click="loadMembers">
          Обновить
        </button>
      </div>

      <form class="inline-form" @submit.prevent="handleAddMember">
        <label class="field field--grow">
          <span class="field__label">User ID</span>
          <input
            v-model="addForm.user_id"
            class="field__control"
            type="text"
            placeholder="UUID пользователя"
            :disabled="!canManage"
            required
          />
        </label>

        <label class="field">
          <span class="field__label">Роль</span>
          <select v-model="addForm.role" class="field__control" :disabled="!canManage">
            <option value="user">Пользователь</option>
            <option value="admin">Администратор</option>
          </select>
        </label>

        <button class="button button--primary" :disabled="!canManage || isSubmitting">
          {{ isSubmitting ? 'Добавляем…' : 'Добавить' }}
        </button>
      </form>

      <p class="muted">
        {{ canManage ? 'Из Swagger видно, что добавление идёт по user_id и role.' : 'У тебя только режим просмотра списка участников.' }}
      </p>

      <p v-if="errorMessage" class="notice notice--error">{{ errorMessage }}</p>
    </article>

    <article class="panel">
      <div v-if="isLoading" class="empty-state">
        <p>Загружаем участников…</p>
      </div>

      <div v-else-if="!members.length" class="empty-state">
        <p>Воркспейс пока не содержит участников.</p>
      </div>

      <div v-else class="stack-md">
        <article v-for="member in members" :key="member.user_id" class="resource-card">
          <div class="resource-card__header">
            <div>
              <h3>{{ member.display_name || 'Без имени' }}</h3>
              <p class="muted">{{ member.email || member.user_id }}</p>
            </div>
            <span class="muted">Вступил {{ formatDateTime(member.joined_at) }}</span>
          </div>

          <div class="inline-form">
            <label class="field">
              <span class="field__label">Роль</span>
              <select
                v-model="roleDrafts[member.user_id]"
                class="field__control"
                :disabled="!canManage"
              >
                <option value="user">{{ workspaceRoleLabels.user }}</option>
                <option value="admin">{{ workspaceRoleLabels.admin }}</option>
              </select>
            </label>

            <div class="actions-inline">
              <button
                class="button button--ghost"
                type="button"
                :disabled="!canManage"
                @click="handleUpdateRole(member)"
              >
                Сохранить роль
              </button>
              <button
                class="button button--danger"
                type="button"
                :disabled="!canManage"
                @click="handleRemoveMember(member)"
              >
                Удалить
              </button>
            </div>
          </div>
        </article>
      </div>
    </article>
  </section>
</template>
