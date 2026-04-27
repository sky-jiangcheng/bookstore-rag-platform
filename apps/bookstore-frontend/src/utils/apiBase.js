export const getApiBaseUrl = () => {
  return import.meta.env.VITE_API_BASE_URL || '/api/v1'
}

export const getApiOrigin = () => {
  const configuredBase = import.meta.env.VITE_API_BASE_URL

  if (!configuredBase || configuredBase.startsWith('/')) {
    return window.location.origin
  }

  return configuredBase.replace(/\/api\/v1\/?$/, '').replace(/\/$/, '')
}
