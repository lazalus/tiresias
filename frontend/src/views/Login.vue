<template>
  <div class="login-page">
    <div class="login-container">
      <img src="/logoss.png" alt="Tiresias View" class="logo" />
      <h1>Tiresias View에 로그인</h1>

      <form @submit.prevent="handleLogin">
        <p v-if="error" class="error">{{ error }}</p>

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
            autocomplete="current-password"
            required
          />
        </div>

        <button type="submit" class="btn-primary" :disabled="loading">
          <svg v-if="loading" class="spinner" width="16" height="16" viewBox="0 0 16 16" fill="none">
            <circle cx="8" cy="8" r="6.5" stroke="rgba(255,255,255,0.3)" stroke-width="1.5"/>
            <path d="M14.5 8a6.5 6.5 0 0 0-6.5-6.5" stroke="white" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
          <span v-else>로그인</span>
        </button>
      </form>

      <p class="footer-text">
        계정이 없으신가요?
        <router-link to="/signup">회원가입</router-link>
      </p>
      <router-link to="/features" class="features-link">서비스 소개 &rarr;</router-link>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { apiLogin } from '../api/auth.js'
import { login } from '../store/auth.js'

const router = useRouter()

const email = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

async function handleLogin() {
  error.value = ''
  loading.value = true

  try {
    const { user, token } = await apiLogin(email.value, password.value)
    login(user, token)
    router.push('/')
  } catch (err) {
    error.value = err.response?.data?.error || err.message || '로그인에 실패했습니다. 다시 시도해주세요.'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-primary);
  padding: 24px;
}

.login-container {
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

.features-link {
  display: block;
  text-align: center;
  margin-top: 12px;
  font-size: 13px;
  color: var(--text-muted);
  text-decoration: none;
}

.features-link:hover {
  color: var(--text-secondary);
}
</style>
