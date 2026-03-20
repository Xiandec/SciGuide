import { computed, readonly, reactive } from 'vue'

import { configureHttpClient } from '@/shared/api/http'
import {
  fetchCurrentUser,
  loginUser,
  logoutUser,
  registerUser,
  refreshTokens,
} from '@/shared/api/sciguide'

const STORAGE_KEY = 'sciguide.session'

const state = reactive({
  accessToken: '',
  refreshToken: '',
  expiresIn: 3600,
  user: null,
  initialized: false,
  initializingPromise: null,
  refreshingPromise: null,
})

function readStoredSession() {
  if (typeof window === 'undefined') {
    return null
  }

  try {
    const rawValue = window.localStorage.getItem(STORAGE_KEY)

    if (!rawValue) {
      return null
    }

    return JSON.parse(rawValue)
  } catch (error) {
    console.warn('Failed to read stored session', error)
    return null
  }
}

function persistSession() {
  if (typeof window === 'undefined') {
    return
  }

  if (!state.accessToken || !state.refreshToken) {
    window.localStorage.removeItem(STORAGE_KEY)
    return
  }

  window.localStorage.setItem(
    STORAGE_KEY,
    JSON.stringify({
      accessToken: state.accessToken,
      refreshToken: state.refreshToken,
      expiresIn: state.expiresIn,
    }),
  )
}

function applyTokens(payload) {
  state.accessToken = payload.access_token
  state.refreshToken = payload.refresh_token
  state.expiresIn = payload.expires_in ?? 3600
  persistSession()
}

function clearSessionState() {
  state.accessToken = ''
  state.refreshToken = ''
  state.expiresIn = 3600
  state.user = null
  persistSession()
}

async function refreshSessionToken() {
  if (!state.refreshToken) {
    clearSessionState()
    return false
  }

  if (state.refreshingPromise) {
    return state.refreshingPromise
  }

  state.refreshingPromise = (async () => {
    try {
      const payload = await refreshTokens({
        refresh_token: state.refreshToken,
      })

      applyTokens(payload)
      return true
    } catch (error) {
      clearSessionState()
      return false
    } finally {
      state.refreshingPromise = null
    }
  })()

  return state.refreshingPromise
}

async function hydrateCurrentUser() {
  state.user = await fetchCurrentUser()
  return state.user
}

export async function initializeSessionStore() {
  if (state.initialized) {
    return
  }

  if (state.initializingPromise) {
    return state.initializingPromise
  }

  state.initializingPromise = (async () => {
    const storedSession = readStoredSession()

    if (storedSession?.accessToken && storedSession?.refreshToken) {
      state.accessToken = storedSession.accessToken
      state.refreshToken = storedSession.refreshToken
      state.expiresIn = storedSession.expiresIn ?? 3600
    }

    if (!state.accessToken && !state.refreshToken) {
      state.initialized = true
      state.initializingPromise = null
      return
    }

    try {
      await hydrateCurrentUser()
    } catch (error) {
      const refreshed = await refreshSessionToken()

      if (refreshed) {
        try {
          await hydrateCurrentUser()
        } catch (retryError) {
          clearSessionState()
        }
      } else {
        clearSessionState()
      }
    } finally {
      state.initialized = true
      state.initializingPromise = null
    }
  })()

  return state.initializingPromise
}

async function login(credentials) {
  const payload = await loginUser(credentials)

  applyTokens(payload)
  state.user = payload.user

  return payload.user
}

async function register(payload) {
  const response = await registerUser(payload)

  applyTokens(response)
  state.user = response.user

  return response.user
}

async function logout() {
  try {
    if (state.refreshToken) {
      await logoutUser({
        refresh_token: state.refreshToken,
      })
    }
  } catch (error) {
    console.warn('Logout request failed', error)
  } finally {
    clearSessionState()
  }
}

configureHttpClient({
  getAccessToken: () => state.accessToken,
  refreshAuth: refreshSessionToken,
  onUnauthorized: clearSessionState,
})

const isAuthenticated = computed(() => Boolean(state.accessToken))

export function useSessionStore() {
  return {
    state: readonly(state),
    isAuthenticated,
    login,
    register,
    logout,
    clearSessionState,
    initializeSessionStore,
  }
}
