import axios from 'axios'

// Discard pre-session tokens; never persist bearer credentials in browser storage.
localStorage.removeItem('simulator_token')
const options = {
  baseURL: import.meta.env.VITE_API_URL || window.location.origin,
  withCredentials: true,
  headers: { 'X-Requested-With': 'XMLHttpRequest' },
}
const apiClient = axios.create(options)
const sessionClient = axios.create(options)
let accessToken = null
let refreshPromise = null
let onUnauthorized = () => {}
let onToken = () => {}
let sessionVersion = 0

export function setAccessToken(token) {
  accessToken = token
}
export function setOnToken(handler) { onToken = handler }
export function setOnUnauthorized(handler) { onUnauthorized = handler }

export function clearAccessToken() {
  sessionVersion += 1
  accessToken = null
}

export function refreshSession() {
  if (!refreshPromise) {
    const version = sessionVersion
    const refresh = () => sessionClient.post('/api/auth/refresh')
    const request = navigator.locks ? navigator.locks.request('startup-session-refresh', refresh) : refresh()
    refreshPromise = request.then(({ data }) => {
      if (version !== sessionVersion) throw new Error('Session changed')
      setAccessToken(data.access_token)
      onToken(data.access_token)
      return data
    }).finally(() => { refreshPromise = null })
  }
  return refreshPromise
}

export async function endSession() {
  // Stop an already-running refresh from restoring a token during logout.
  const token = accessToken
  clearAccessToken()
  await sessionClient.post('/api/auth/logout', {}, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
}

apiClient.interceptors.request.use((config) => {
  if (accessToken && !config.url.startsWith('/api/auth/')) config.headers.Authorization = `Bearer ${accessToken}`
  return config
})

apiClient.interceptors.response.use((response) => response, async (error) => {
  const config = error.config
  if (error.response?.status === 401 && config && !config.url.startsWith('/api/auth/')) {
    if (!config._retried) {
      config._retried = true
      try {
        const data = await refreshSession()
        config.headers.Authorization = `Bearer ${data.access_token}`
        return await apiClient(config)
      } catch {
        // Fall through to the signed-out state once, without a refresh loop.
      }
    }
    clearAccessToken()
    onUnauthorized()
  }
  return Promise.reject(error)
})

export default apiClient
