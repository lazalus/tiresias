import { reactive, computed } from 'vue'

const state = reactive({
  user: JSON.parse(localStorage.getItem('tiresias_user') || 'null'),
  token: localStorage.getItem('tiresias_token') || null,
})

export const isAuthenticated = computed(() => !!state.token)
export const currentUser = computed(() => state.user)

export function login(user, token) {
  // DB에서 온 nickname/profile_image를 profileImage로 매핑
  if (user.profile_image && !user.profileImage) {
    user.profileImage = user.profile_image
  }
  state.user = user
  state.token = token
  localStorage.setItem('tiresias_user', JSON.stringify(user))
  localStorage.setItem('tiresias_token', token)
}

// 로그인 후 DB에서 최신 프로필 불러오기
export async function refreshProfile() {
  if (!state.token) return
  try {
    const res = await fetch(
      (import.meta.env.VITE_API_BASE_URL || '') + '/api/auth/me',
      { headers: { Authorization: `Bearer ${state.token}` } }
    )
    const data = await res.json()
    if (data.user) {
      data.user.profileImage = data.user.profile_image || null
      state.user = { ...state.user, ...data.user }
      localStorage.setItem('tiresias_user', JSON.stringify(state.user))
    }
  } catch (e) {}
}

export function logout() {
  state.user = null
  state.token = null
  localStorage.removeItem('tiresias_user')
  localStorage.removeItem('tiresias_token')
}

export function updateUser(updates) {
  if (state.user) {
    state.user = { ...state.user, ...updates }
    localStorage.setItem('tiresias_user', JSON.stringify(state.user))
  }
}

export function getToken() {
  return state.token
}
