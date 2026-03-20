import { apiBaseUrl } from '@/shared/config/env'

const authHandlers = {
  getAccessToken: () => '',
  refreshAuth: async () => false,
  onUnauthorized: () => {},
}

export function configureHttpClient(handlers) {
  authHandlers.getAccessToken = handlers.getAccessToken || authHandlers.getAccessToken
  authHandlers.refreshAuth = handlers.refreshAuth || authHandlers.refreshAuth
  authHandlers.onUnauthorized = handlers.onUnauthorized || authHandlers.onUnauthorized
}

function toQueryString(params) {
  const searchParams = new URLSearchParams()

  Object.entries(params || {}).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') {
      return
    }

    searchParams.set(key, String(value))
  })

  const query = searchParams.toString()
  return query ? `?${query}` : ''
}

function extractErrorMessage(payload, fallbackStatus) {
  if (!payload) {
    return `Request failed with status ${fallbackStatus}`
  }

  if (typeof payload === 'string') {
    return payload
  }

  if (payload.error?.message) {
    return payload.error.message
  }

  if (typeof payload.detail === 'string') {
    return payload.detail
  }

  if (Array.isArray(payload.detail)) {
    return payload.detail
      .map((entry) => entry.msg || JSON.stringify(entry))
      .join(', ')
  }

  return `Request failed with status ${fallbackStatus}`
}

function createApiError(status, payload) {
  const error = new Error(extractErrorMessage(payload, status))
  error.status = status
  error.payload = payload
  return error
}

export async function request(
  path,
  {
    method = 'GET',
    params,
    data,
    headers = {},
    auth = true,
    retryOnUnauthorized = true,
    signal,
  } = {},
) {
  const requestHeaders = new Headers(headers)
  const isFormData = data instanceof FormData

  if (!isFormData && data !== undefined && !requestHeaders.has('Content-Type')) {
    requestHeaders.set('Content-Type', 'application/json')
  }

  if (auth) {
    const accessToken = authHandlers.getAccessToken()

    if (accessToken) {
      requestHeaders.set('Authorization', `Bearer ${accessToken}`)
    }
  }

  const response = await fetch(`${apiBaseUrl}${path}${toQueryString(params)}`, {
    method,
    headers: requestHeaders,
    body:
      data === undefined
        ? undefined
        : isFormData
          ? data
          : JSON.stringify(data),
    signal,
  })

  if (response.status === 401 && auth && retryOnUnauthorized) {
    const refreshed = await authHandlers.refreshAuth()

    if (refreshed) {
      return request(path, {
        method,
        params,
        data,
        headers,
        auth,
        retryOnUnauthorized: false,
        signal,
      })
    }

    authHandlers.onUnauthorized()
  }

  if (response.status === 204) {
    return null
  }

  const contentType = response.headers.get('content-type') || ''
  const payload = contentType.includes('application/json')
    ? await response.json()
    : await response.text()

  if (!response.ok) {
    throw createApiError(response.status, payload)
  }

  return payload
}
