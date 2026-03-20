function trimTrailingSlash(value) {
  return value.endsWith('/') ? value.slice(0, -1) : value
}

export const apiBaseUrl = trimTrailingSlash(
  import.meta.env.VITE_API_BASE_URL || '/api/v1',
)
