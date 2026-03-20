<script setup>
import { computed, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useSessionStore } from '@/app/session-store'

const route = useRoute()
const router = useRouter()
const session = useSessionStore()

const mode = ref('login')
const form = reactive({
  email: 'user@example.com',
  display_name: 'Ivan Petrov',
  password: 'secret',
})

const isSubmitting = ref(false)
const errorMessage = ref('')

const redirectTarget = computed(() =>
  typeof route.query.redirect === 'string' ? route.query.redirect : '/workspaces',
)

const isRegisterMode = computed(() => mode.value === 'register')

const panelTitle = computed(() =>
  isRegisterMode.value ? 'Создание аккаунта SciGuide' : 'Подключение к API SciGuide',
)

const panelEyebrow = computed(() =>
  isRegisterMode.value ? 'Регистрация' : 'Вход',
)

const panelDescription = computed(() =>
  isRegisterMode.value
    ? 'Используется контракт из документации: `POST /api/v1/auth/register`.'
    : 'Используется контракт из Swagger: `POST /api/v1/auth/login`.',
)

const submitLabel = computed(() => {
  if (isSubmitting.value && isRegisterMode.value) {
    return 'Создаём аккаунт…'
  }

  if (isSubmitting.value) {
    return 'Входим…'
  }

  return isRegisterMode.value ? 'Зарегистрироваться' : 'Войти в систему'
})

function switchMode(nextMode) {
  mode.value = nextMode
  errorMessage.value = ''
}

async function handleSubmit() {
  errorMessage.value = ''
  isSubmitting.value = true

  try {
    if (isRegisterMode.value) {
      await session.register({
        email: form.email.trim(),
        display_name: form.display_name.trim(),
        password: form.password,
      })
    } else {
      await session.login({
        email: form.email.trim(),
        password: form.password,
      })
    }

    await router.replace(redirectTarget.value)
  } catch (error) {
    errorMessage.value =
      error.message ||
      (isRegisterMode.value
        ? 'Не удалось зарегистрировать пользователя.'
        : 'Не удалось выполнить вход.')
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <main class="auth-shell">
    <section class="auth-hero panel panel--ghost">
      <p class="eyebrow">SciGuide</p>
      <h1>Научный ассистент с изолированными воркспейсами и персональными чатами.</h1>
      <p class="lead">
        Интерфейс покрывает сценарии из функциональных требований: вход по JWT,
        список доступных воркспейсов, отдельные чаты, документы, системный
        промпт и управление участниками.
      </p>

      <div class="auth-highlights">
        <article class="metric-card">
          <span class="metric-card__value">JWT</span>
          <span class="metric-card__label">Аутентификация и защита доступа</span>
        </article>
        <article class="metric-card">
          <span class="metric-card__value">Workspace</span>
          <span class="metric-card__label">Изоляция документов, ролей и промпта</span>
        </article>
        <article class="metric-card">
          <span class="metric-card__value">Chat</span>
          <span class="metric-card__label">Личная история сообщений внутри контекста</span>
        </article>
      </div>
    </section>

    <section class="auth-panel panel">
      <div class="auth-panel__header">
        <div class="auth-mode-switch" role="tablist" aria-label="Auth mode">
          <button
            class="auth-mode-switch__item"
            :class="{ 'auth-mode-switch__item--active': !isRegisterMode }"
            type="button"
            @click="switchMode('login')"
          >
            Вход
          </button>
          <button
            class="auth-mode-switch__item"
            :class="{ 'auth-mode-switch__item--active': isRegisterMode }"
            type="button"
            @click="switchMode('register')"
          >
            Регистрация
          </button>
        </div>

        <p class="eyebrow">{{ panelEyebrow }}</p>
        <h2>{{ panelTitle }}</h2>
        <p class="muted">
          {{ panelDescription }}
        </p>
      </div>

      <form class="auth-form" @submit.prevent="handleSubmit">
        <label class="field">
          <span class="field__label">Email</span>
          <input
            v-model="form.email"
            class="field__control"
            type="email"
            autocomplete="username"
            placeholder="user@example.com"
            required
          />
        </label>

        <label v-if="isRegisterMode" class="field">
          <span class="field__label">Отображаемое имя</span>
          <input
            v-model="form.display_name"
            class="field__control"
            type="text"
            autocomplete="name"
            maxlength="255"
            placeholder="Ivan Petrov"
            required
          />
        </label>

        <label class="field">
          <span class="field__label">Пароль</span>
          <input
            v-model="form.password"
            class="field__control"
            type="password"
            :autocomplete="isRegisterMode ? 'new-password' : 'current-password'"
            :minlength="isRegisterMode ? 8 : 1"
            placeholder="Введите пароль"
            required
          />
        </label>

        <p v-if="isRegisterMode" class="muted">
          Пароль должен содержать минимум 8 символов.
        </p>

        <p v-if="errorMessage" class="notice notice--error">
          {{ errorMessage }}
        </p>

        <button class="button button--primary button--block" :disabled="isSubmitting">
          {{ submitLabel }}
        </button>
      </form>

      <div class="auth-footnote">
        <span>
          По умолчанию фронт ходит в `VITE_API_BASE_URL` или `/api/v1` и после
          логина или регистрации сразу сохраняет JWT-сессию.
        </span>
      </div>
    </section>
  </main>
</template>
