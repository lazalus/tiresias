<template>
  <div class="login-page">
    <div class="login-bg"></div>
    <div class="login-card">
      <div class="card-header">
        <img src="/logoss.png" alt="TIRESIAS VIEW" class="logo" />
        <h1 class="title">TIRESIAS VIEW</h1>
        <p class="tagline">집단 지능 예측 엔진</p>
      </div>

      <form class="card-body" @submit.prevent="handleLogin">
        <div v-if="error" class="error-message">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <circle cx="8" cy="8" r="7" stroke="currentColor" stroke-width="1.5"/>
            <path d="M8 4.5V9" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            <circle cx="8" cy="11.5" r="0.75" fill="currentColor"/>
          </svg>
          <span>{{ error }}</span>
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
            autocomplete="current-password"
            required
          />
        </div>

        <button type="submit" class="submit-btn" :disabled="loading">
          <svg
            v-if="loading"
            class="spinner"
            width="18"
            height="18"
            viewBox="0 0 18 18"
            fill="none"
          >
            <circle cx="9" cy="9" r="7.5" stroke="rgba(255,255,255,0.25)" stroke-width="2"/>
            <path
              d="M16.5 9a7.5 7.5 0 0 0-7.5-7.5"
              stroke="white"
              stroke-width="2"
              stroke-linecap="round"
            />
          </svg>
          <span v-else>로그인</span>
        </button>
      </form>

      <div class="card-footer">
        <span class="footer-text">계정이 없으신가요?</span>
        <router-link to="/signup" class="footer-link">회원가입</router-link>
      </div>
      <router-link to="/features" class="features-link">서비스 소개 →</router-link>
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
  position: relative;
  overflow: hidden;
  padding: 24px;
}

.login-bg {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse 600px 400px at 50% 0%, rgba(99, 102, 241, 0.12), transparent),
    radial-gradient(ellipse 400px 300px at 20% 80%, rgba(129, 140, 248, 0.06), transparent),
    radial-gradient(ellipse 400px 300px at 80% 60%, rgba(99, 102, 241, 0.04), transparent);
  pointer-events: none;
}

.login-card {
  position: relative;
  width: 100%;
  max-width: 400px;
  background: var(--bg-secondary);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 20px;
  backdrop-filter: blur(40px);
  -webkit-backdrop-filter: blur(40px);
  box-shadow:
    0 0 0 1px rgba(255, 255, 255, 0.03) inset,
    0 20px 50px -12px rgba(0, 0, 0, 0.5),
    0 0 80px -20px rgba(99, 102, 241, 0.1);
  overflow: hidden;
}

.card-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 40px 0;
}

.logo {
  width: 48px;
  height: 48px;
  margin-bottom: 16px;
  border-radius: 12px;
}

.title {
  font-size: 22px;
  font-weight: 600;
  color: #f4f4f5;
  letter-spacing: -0.02em;
  margin: 0;
}

.tagline {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 6px 0 0;
  letter-spacing: 0.02em;
}

.card-body {
  padding: 32px 40px 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.error-message {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: rgba(239, 68, 68, 0.08);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: 10px;
  color: #fca5a5;
  font-size: 13px;
  line-height: 1.4;
}

.error-message svg {
  flex-shrink: 0;
  color: #f87171;
}

.pending-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 12px 0;
  gap: 12px;
}

.pending-title {
  font-size: 15px;
  font-weight: 600;
  color: #f4f4f5;
  margin: 0;
}

.pending-sub {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 0;
  line-height: 1.5;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field label {
  font-size: 13px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.55);
  padding-left: 2px;
}

.field input {
  width: 100%;
  padding: 11px 14px;
  background: var(--bg-surface);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  color: #f4f4f5;
  font-size: 14px;
  outline: none;
  transition: all 0.2s ease;
  box-sizing: border-box;
}

.field input::placeholder {
  color: rgba(255, 255, 255, 0.2);
}

.field input:focus {
  border-color: rgba(99, 102, 241, 0.5);
  background: var(--border-color);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1), 0 0 20px -4px rgba(99, 102, 241, 0.15);
}

.submit-btn {
  width: 100%;
  padding: 12px;
  background: #6366f1;
  border: none;
  border-radius: 10px;
  color: white;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 44px;
  margin-top: 4px;
}

.submit-btn:hover:not(:disabled) {
  background: #5558e6;
  box-shadow: 0 0 24px -4px rgba(99, 102, 241, 0.4);
}

.submit-btn:active:not(:disabled) {
  transform: scale(0.98);
}

.submit-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.spinner {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 20px 40px 32px;
}

.footer-text {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.35);
}

.footer-link {
  font-size: 13px;
  color: #818cf8;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.15s ease;
}

.footer-link:hover {
  color: #a5b4fc;
}

.features-link {
  display: block;
  text-align: center;
  padding: 0 0 28px;
  font-size: 12px;
  color: var(--text-muted);
  text-decoration: none;
  transition: color 0.15s;
}

.features-link:hover {
  color: #818cf8;
}
</style>
