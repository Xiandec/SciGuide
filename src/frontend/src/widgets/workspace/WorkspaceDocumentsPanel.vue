<script setup>
import { ref, watch } from 'vue'

import {
  deleteWorkspaceDocument,
  getDocumentProcessingStatus,
  listWorkspaceDocuments,
  uploadWorkspaceDocument,
} from '@/shared/api/sciguide'
import {
  documentStageLabels,
  documentStatusLabels,
  formatBytes,
  formatDateTime,
} from '@/shared/lib/format'
import StatusBadge from '@/shared/ui/StatusBadge.vue'

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

const documents = ref([])
const processingById = ref({})
const uploadTitle = ref('')
const selectedFile = ref(null)
const fileInput = ref(null)

const isLoading = ref(false)
const isUploading = ref(false)
const errorMessage = ref('')

watch(
  () => props.workspaceId,
  () => {
    loadDocuments()
  },
  { immediate: true },
)

function onFileChange(event) {
  selectedFile.value = event.target.files?.[0] || null
}

async function hydrateProcessing() {
  const nextProcessing = {}

  await Promise.all(
    documents.value
      .filter((document) => document.status === 'uploaded' || document.status === 'processing')
      .map(async (document) => {
        try {
          nextProcessing[document.id] = await getDocumentProcessingStatus(
            props.workspaceId,
            document.id,
          )
        } catch (error) {
          nextProcessing[document.id] = null
        }
      }),
  )

  processingById.value = nextProcessing
}

async function loadDocuments() {
  isLoading.value = true
  errorMessage.value = ''

  try {
    const payload = await listWorkspaceDocuments(props.workspaceId, {
      limit: 100,
    })

    documents.value = payload.items || []
    await hydrateProcessing()
  } catch (error) {
    errorMessage.value =
      error.message || 'Не удалось загрузить документы.'
  } finally {
    isLoading.value = false
  }
}

async function handleUpload() {
  if (!selectedFile.value) {
    return
  }

  errorMessage.value = ''
  isUploading.value = true

  try {
    await uploadWorkspaceDocument(props.workspaceId, {
      file: selectedFile.value,
      title: uploadTitle.value.trim() || null,
    })

    selectedFile.value = null
    uploadTitle.value = ''

    if (fileInput.value) {
      fileInput.value.value = ''
    }

    await loadDocuments()
  } catch (error) {
    errorMessage.value =
      error.message || 'Не удалось загрузить документ.'
  } finally {
    isUploading.value = false
  }
}

async function handleDeleteDocument(documentId) {
  const confirmed = window.confirm('Удалить документ из воркспейса?')

  if (!confirmed) {
    return
  }

  errorMessage.value = ''

  try {
    await deleteWorkspaceDocument(props.workspaceId, documentId)
    await loadDocuments()
  } catch (error) {
    errorMessage.value =
      error.message || 'Не удалось удалить документ.'
  }
}
</script>

<template>
  <section class="stack-lg">
    <article class="panel">
      <div class="panel__header">
        <div>
          <p class="eyebrow">Документы</p>
          <h2>Контекстная база знаний воркспейса</h2>
        </div>
        <button class="button button--ghost" type="button" @click="loadDocuments">
          Обновить
        </button>
      </div>

      <form class="stack-md" @submit.prevent="handleUpload">
        <label class="field">
          <span class="field__label">Заголовок файла</span>
          <input
            v-model="uploadTitle"
            class="field__control"
            type="text"
            placeholder="Необязательное имя документа"
            :disabled="!canManage"
          />
        </label>

        <label class="field">
          <span class="field__label">Файл</span>
          <input
            ref="fileInput"
            class="field__control"
            type="file"
            :disabled="!canManage"
            @change="onFileChange"
          />
        </label>

        <p class="muted">
          {{ canManage ? 'Администратор может загружать и удалять документы.' : 'У тебя только режим просмотра.' }}
        </p>

        <p v-if="errorMessage" class="notice notice--error">{{ errorMessage }}</p>

        <button class="button button--primary" :disabled="!canManage || isUploading">
          {{ isUploading ? 'Загружаем…' : 'Загрузить документ' }}
        </button>
      </form>
    </article>

    <article class="panel">
      <div v-if="isLoading" class="empty-state">
        <p>Загружаем список документов…</p>
      </div>

      <div v-else-if="!documents.length" class="empty-state">
        <p>В этом воркспейсе пока нет документов.</p>
      </div>

      <div v-else class="stack-md">
        <article v-for="document in documents" :key="document.id" class="resource-card">
          <div class="resource-card__header">
            <div>
              <h3>{{ document.filename }}</h3>
              <p class="muted">
                {{ formatBytes(document.size_bytes) }} · {{ document.content_type }}
              </p>
            </div>

            <div class="actions-inline">
              <StatusBadge
                :label="documentStatusLabels[document.status]"
                :tone="document.status === 'processed' ? 'success' : document.status === 'failed' ? 'danger' : 'neutral'"
              />
              <button
                v-if="canManage"
                class="button button--danger"
                type="button"
                @click="handleDeleteDocument(document.id)"
              >
                Удалить
              </button>
            </div>
          </div>

          <div class="resource-card__meta">
            <span>Загружен {{ formatDateTime(document.created_at) }}</span>
            <span>ID: {{ document.id }}</span>
          </div>

          <p v-if="processingById[document.id]" class="muted">
            Этап обработки:
            {{ documentStageLabels[processingById[document.id].stage] }}
            <template v-if="processingById[document.id].error">
              · {{ processingById[document.id].error }}
            </template>
          </p>
        </article>
      </div>
    </article>
  </section>
</template>
