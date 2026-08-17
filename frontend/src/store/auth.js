import { reactive, computed } from 'vue'

function normalizeUser(user) {
  if (!user || typeof user !== 'object') {
    return user
  }

  const normalized = { ...user }

  if (normalized.profile_image && !normalized.profileImage) {
    normalized.profileImage = normalized.profile_image
  }

  if (normalized.created_at && !normalized.createdAt) {
    normalized.createdAt = normalized.created_at
  }

  if (normalized.must_change_password != null && normalized.mustChangePassword == null) {
    normalized.mustChangePassword = Boolean(normalized.must_change_password)
  }

  if (normalized.mustChangePassword != null && normalized.must_change_password == null) {
    normalized.must_change_password = normalized.mustChangePassword ? 1 : 0
  }

  return normalized
}

const state = reactive({
  user: normalizeUser(JSON.parse(localStorage.getItem('tiresias_user') || 'null')),
  token: null,
})

export const isAuthenticated = computed(() => !!state.user)
export const currentUser = computed(() => state.user)

export function login(user, token) {
  state.user = normalizeUser(user)
  state.token = token || null
  localStorage.setItem('tiresias_user', JSON.stringify(state.user))
}

function clearLocalAuthState() {
  state.user = null
  state.token = null
  localStorage.removeItem('tiresias_user')
  localStorage.removeItem('tiresias_token')
}

export function buildAuthHeaders(extraHeaders = {}) {
  const headers = { ...extraHeaders }
  if (state.token) {
    headers.Authorization = `Bearer ${state.token}`
  }
  return headers
}

export function buildAuthAxiosConfig(config = {}) {
  return {
    withCredentials: true,
    ...config,
    headers: buildAuthHeaders(config.headers || {}),
  }
}

export function buildAuthFetchOptions(options = {}) {
  return {
    ...options,
    credentials: 'include',
    headers: buildAuthHeaders(options.headers || {}),
  }
}

// 로그인 후 DB에서 최신 프로필 불러오기
export async function refreshProfile() {
  try {
    const res = await fetch(
      (import.meta.env.VITE_API_BASE_URL || '') + '/api/auth/me',
      buildAuthFetchOptions()
    )
    if (!res.ok) {
      clearLocalAuthState()
      return
    }
    const data = await res.json()
    if (data.user) {
      state.user = normalizeUser({ ...state.user, ...data.user })
      localStorage.setItem('tiresias_user', JSON.stringify(state.user))
      return
    }
    clearLocalAuthState()
  } catch (e) {}
}

export function logout() {
  clearLocalAuthState()
  fetch((import.meta.env.VITE_API_BASE_URL || '') + '/api/auth/logout', {
    method: 'POST',
    credentials: 'include',
  }).catch(() => {})
}

export function updateUser(updates) {
  if (state.user) {
    state.user = normalizeUser({ ...state.user, ...updates })
    localStorage.setItem('tiresias_user', JSON.stringify(state.user))
  }
}

export function getToken() {
  return state.token
}
