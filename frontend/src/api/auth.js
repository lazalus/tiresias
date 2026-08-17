import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

const api = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
  withCredentials: true,
})

export async function apiLogin(email, password) {
  const res = await api.post('/api/auth/login', { email, password })
  return res.data
}

export async function apiSignup(name, email, password) {
  const res = await api.post('/api/auth/signup', { name, email, password })
  return res.data
}

export async function apiVerifySignup(token) {
  const res = await api.post('/api/auth/signup/verify', { token })
  return res.data
}

export async function apiChangePassword(currentPassword, newPassword) {
  const res = await api.post('/api/auth/change-password', { currentPassword, newPassword })
  return res.data
}

export async function apiGetMe(token) {
  const res = await api.get('/api/auth/me')
  return res.data
}
