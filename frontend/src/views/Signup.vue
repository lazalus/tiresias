<template>
  <div class="signup-page">
    <div class="signup-container">
      <img src="/logoss.png" alt="Tiresias View" class="logo" />
      <h1>회원가입</h1>

      <form @submit.prevent="handleSignup">
        <p v-if="error" class="error">{{ error }}</p>

        <div class="field">
          <label for="name">이름</label>
          <input
            id="name"
            v-model="name"
            type="text"
            placeholder="홍길동"
            autocomplete="name"
            required
          />
        </div>

        <div class="field">
          <label for="email">이메일</label>
          <input
            id="email"
            v-model="email"
            type="email"
            placeholder="name@example.com"
            autocomplete="email"
            required
          />
        </div>

        <div class="field">
          <label for="password">비밀번호</label>
          <input
            id="password"
            v-model="password"
            type="password"
            placeholder="비밀번호를 입력하세요"
            autocomplete="new-password"
            required
            minlength="6"
          />
          <span class="hint">6자 이상</span>
        </div>

        <div class="field">
          <label for="passwordConfirm">비밀번호 확인</label>
          <input
            id="passwordConfirm"
            v-model="passwordConfirm"
            type="password"
            placeholder="비밀번호를 다시 입력하세요"
            autocomplete="new-password"
            required
            :class="{ 'input-error': passwordMismatch }"
          />
          <span v-if="passwordMismatch" class="field-error">비밀번호가 일치하지 않습니다</span>
        </div>

        <button type="submit" class="btn-primary" :disabled="loading">
          <svg v-if="loading" class="spinner" width="16" height="16" viewBox="0 0 16 16" fill="none">
            <circle cx="8" cy="8" r="6.5" stroke="rgba(255,255,255,0.3)" stroke-width="1.5"/>
            <path d="M14.5 8a6.5 6.5 0 0 0-6.5-6.5" stroke="white" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
          <span v-else>회원가입</span>
        </button>
      </form>

      <p class="footer-text">
        이미 계정이 있으신가요?
        <router-link to="/login">로그인</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { apiSignup } from '../api/auth.js'
import { login } from '../store/auth.js'

const router = useRouter()

const name = ref('')
const email = ref('')
const password = ref('')
const passwordConfirm = ref('')
const loading = ref(false)
const error = ref('')

const passwordMismatch = computed(() => {
  return passwordConfirm.value.length > 0 && password.value !== passwordConfirm.value
})

async function handleSignup() {
  error.value = ''

  if (password.value !== passwordConfirm.value) {
    error.value = '비밀번호가 일치하지 않습니다.'
    return
  }

  if (password.value.length < 6) {
    error.value = '비밀번호는 6자 이상이어야 합니다.'
    return
  }

  loading.value = true

  try {
    const { user, token } = await apiSignup(name.value, email.value, password.value)
    login(user, token)
    router.push('/')
  } catch (err) {
    error.value = err.response?.data?.error || '회원가입에 실패했습니다. 다시 시도해주세요.'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.signup-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-primary);
  padding: 24px;
}

.signup-container {
  width: 100%;
  max-width: 360px;
}

.logo {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  margin-bottom: 24px;
}

h1 {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: -0.02em;
  margin: 0 0 32px;
}

form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.error {
  font-size: 13px;
  color: #ef4444;
  margin: 0;
  line-height: 1.4;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
}

.hint {
  font-size: 12px;
  color: var(--text-muted);
}

.field input {
  width: 100%;
  height: 40px;
  padding: 0 12px;
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  color: var(--text-primary);
  font-size: 14px;
  font-family: inherit;
  outline: none;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.field input::placeholder {
  color: var(--text-muted);
}

.field input:focus {
  border-color: var(--accent-color);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.field input.input-error {
  border-color: #ef4444;
}

.field-error {
  font-size: 12px;
  color: #ef4444;
}

.btn-primary {
  width: 100%;
  height: 40px;
  background: var(--accent-color);
  border: none;
  border-radius: 8px;
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  font-family: inherit;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 4px;
  transition: background 0.15s ease;
}

.btn-primary:hover:not(:disabled) {
  background: var(--accent-hover);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.spinner {
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.footer-text {
  font-size: 13px;
  color: var(--text-muted);
  text-align: center;
  margin: 24px 0 0;
}

.footer-text a {
  color: var(--accent-color);
  text-decoration: none;
  font-weight: 500;
}

.footer-text a:hover {
  text-decoration: underline;
}
</style>
