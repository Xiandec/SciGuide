<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import { createWorkspace, listWorkspaces } from '@/shared/api/sciguide'
import {
  formatDateTime,
  workspaceAccessLabels,
  workspaceRoleLabels,
  workspaceTypeLabels,
} from '@/shared/lib/format'
import StatusBadge from '@/shared/ui/StatusBadge.vue'

const router = useRouter()

const workspaces = ref([])
const isLoading = ref(true)
const isSubmitting = ref(false)
const isCreateModalOpen = ref(false)
const errorMessage = ref('')
const createError = ref('')

const form = reactive({
  name: '',
  description: '',
  type: 'shared',
  access_mode: 'by_membership',
})

const visibleAccessModes = computed(() =>
  form.type === 'private'
    ? [{ value: 'owner_only', label: workspaceAccessLabels.owner_only }]
    : [
        { value: 'by_membership', label: workspaceAccessLabels.by_membership },
        { value: 'global', label: workspaceAccessLabels.global },
      ],
)

watch(
  () => form.type,
  (type) => {
    if (type === 'private') {
      form.access_mode = 'owner_only'
      return
    }

    if (form.access_mode === 'owner_only') {
      form.access_mode = 'by_membership'
    }
  },
)

function resetForm() {
  form.name = ''
  form.description = ''
  form.type = 'shared'
  form.access_mode = 'by_membership'
  createError.value = ''
}

function openCreateModal() {
  resetForm()
  isCreateModalOpen.value = true
}

function closeCreateModal() {
  isCreateModalOpen.value = false
}

async function loadWorkspaces() {
  isLoading.value = true
  errorMessage.value = ''

  try {
    const payload = await listWorkspaces({
      limit: 100,
    })

    workspaces.value = [...(payload.items || [])].sort((left, right) =>
      new Date(right.updated_at) - new Date(left.updated_at),
    )
  } catch (error) {
    errorMessage.value =
      error.message || 'Не удалось загрузить список воркспейсов.'
  } finally {
    isLoading.value = false
  }
}

async function handleCreateWorkspace() {
  createError.value = ''
  isSubmitting.value = true

  try {
    const workspace = await createWorkspace({
      name: form.name.trim(),
      description: form.description.trim() || null,
      type: form.type,
      access_mode: form.type === 'private' ? 'owner_only' : form.access_mode,
    })

    closeCreateModal()
    await router.push(`/workspaces/${workspace.id}`)
  } catch (error) {
    createError.value =
      error.message || 'Не удалось создать воркспейс.'
  } finally {
    isSubmitting.value = false
  }
}

onMounted(loadWorkspaces)
</script>

<template>
  <main class="page-shell">
    <section class="page-header">
      <div>
        <p class="eyebrow">Главная</p>
        <h1>Доступные воркспейсы</h1>
        <p class="lead">
          Выбирай готовое пространство или создай новое через карточку с плюсом.
        </p>
      </div>

      <button class="button button--ghost" type="button" @click="loadWorkspaces">
        Обновить список
      </button>
    </section>

    <p v-if="errorMessage" class="notice notice--error">{{ errorMessage }}</p>

    <section class="workspace-gallery">
      <button class="workspace-create-card" type="button" @click="openCreateModal">
        <span class="workspace-create-card__icon">+</span>
        <strong>Новый воркспейс</strong>
        <span>Открыть модальное окно создания</span>
      </button>

      <template v-if="isLoading">
        <article v-for="index in 3" :key="index" class="workspace-card workspace-card--muted">
          <div class="workspace-card__header">
            <div>
              <h3>Загрузка…</h3>
              <p class="muted">Получаем список доступных воркспейсов.</p>
            </div>
          </div>
        </article>
      </template>

      <button
        v-for="workspace in workspaces"
        v-else
        :key="workspace.id"
        class="workspace-card"
        type="button"
        @click="router.push(`/workspaces/${workspace.id}`)"
      >
        <div class="workspace-card__header">
          <div>
            <h3>{{ workspace.name }}</h3>
            <p class="muted">
              {{ workspace.description || 'Описание пока не задано.' }}
            </p>
          </div>
          <StatusBadge
            :label="workspaceRoleLabels[workspace.my_role]"
            :tone="workspace.my_role === 'admin' ? 'accent' : 'neutral'"
          />
        </div>

        <div class="workspace-card__meta">
          <span>{{ workspaceTypeLabels[workspace.type] }}</span>
          <span>{{ workspaceAccessLabels[workspace.access_mode] }}</span>
          <span>Обновлён {{ formatDateTime(workspace.updated_at) }}</span>
        </div>
      </button>
    </section>

    <div
      v-if="isCreateModalOpen"
      class="modal-backdrop"
      role="dialog"
      aria-modal="true"
      aria-label="Создание воркспейса"
      @click.self="closeCreateModal"
    >
      <section class="modal-card panel">
        <div class="panel__header">
          <div>
            <p class="eyebrow">Создание</p>
            <h2>Новый воркспейс</h2>
          </div>
          <button class="button button--ghost" type="button" @click="closeCreateModal">
            Закрыть
          </button>
        </div>

        <form class="stack-md" @submit.prevent="handleCreateWorkspace">
          <label class="field">
            <span class="field__label">Название</span>
            <input
              v-model="form.name"
              class="field__control"
              type="text"
              maxlength="255"
              placeholder="Например, Graph Retrieval Lab"
              required
            />
          </label>

          <label class="field">
            <span class="field__label">Описание</span>
            <textarea
              v-model="form.description"
              class="field__control field__control--textarea"
              maxlength="4000"
              placeholder="Кратко опиши тематику, источник знаний и задачи воркспейса"
            />
          </label>

          <div class="form-row">
            <label class="field">
              <span class="field__label">Тип</span>
              <select v-model="form.type" class="field__control">
                <option value="shared">Общий</option>
                <option value="private">Приватный</option>
              </select>
            </label>

            <label class="field">
              <span class="field__label">Доступ</span>
              <select v-model="form.access_mode" class="field__control">
                <option
                  v-for="option in visibleAccessModes"
                  :key="option.value"
                  :value="option.value"
                >
                  {{ option.label }}
                </option>
              </select>
            </label>
          </div>

          <p v-if="createError" class="notice notice--error">{{ createError }}</p>

          <div class="actions-inline">
            <button class="button button--primary" :disabled="isSubmitting">
              {{ isSubmitting ? 'Создаём…' : 'Создать воркспейс' }}
            </button>
            <button class="button button--ghost" type="button" @click="closeCreateModal">
              Отмена
            </button>
          </div>
        </form>
      </section>
    </div>
  </main>
</template>
