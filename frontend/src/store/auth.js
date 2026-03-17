import { reactive, computed } from 'vue'

const state = reactive({
  user: JSON.parse(localStorage.getItem('tiresias_user') || 'null'),
  token: localStorage.getItem('tiresias_token') || null,
})

export const isAuthenticated = computed(() => !!state.token)
export const currentUser = computed(() => state.user)

export function login(user, token) {
  state.user = user
  state.token = token
  localStorage.setItem('tiresias_user', JSON.stringify(user))
  localStorage.setItem('tiresias_token', token)
}

export function logout() {
  state.user = null
  state.token = null
  localStorage.removeItem('tiresias_user')
  localStorage.removeItem('tiresias_token')
}

export function getToken() {
  return state.token
}
