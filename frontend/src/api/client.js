import axios from 'axios'

const TOKEN_STORAGE_KEY = 'simulator_token'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
})

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_STORAGE_KEY)
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Set from App.jsx (a component, so it can navigate) rather than imported here,
// since this module has no access to the router outside a component tree.
let onUnauthorized = () => {}
export function setOnUnauthorized(handler) {
  onUnauthorized = handler
}

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem(TOKEN_STORAGE_KEY)
      onUnauthorized()
    }
    return Promise.reject(error)
  },
)

export { TOKEN_STORAGE_KEY }
export default apiClient
