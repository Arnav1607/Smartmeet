import axios from 'axios'

const API = axios.create({ baseURL: import.meta.env.VITE_API_URL || 'https://your-api.railway.app' })

API.interceptors.request.use((cfg) => {
  const t = localStorage.getItem('jwt_token')
  if (t) cfg.headers.Authorization = `Bearer ${t}`
  return cfg
})

API.interceptors.response.use(
  (r) => r,
  (e) => {
    if (e.response?.status === 401) { localStorage.removeItem('jwt_token'); window.location.href = '/login' }
    return Promise.reject(e)
  }
)

export default API
