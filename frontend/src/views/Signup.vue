<template>
  <div class="signup-page">
    <div class="signup-bg"></div>
    <div class="signup-card">
      <div class="card-header">
        <img src="/logoss.png" alt="TIRESIAS VIEW" class="logo" />
        <h1 class="title">회원가입</h1>
        <p class="tagline">TIRESIAS VIEW에 오신 것을 환영합니다</p>
      </div>

      <!-- Success state after signup -->
      <div v-if="signupSuccess" class="card-body">
        <div class="success-message">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#4ade80" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
            <polyline points="22 4 12 14.01 9 11.01"/>
          </svg>
          <p class="success-title">회원가입이 완료되었습니다</p>
          <p class="success-sub">관리자 승인 후 로그인할 수 있습니다.</p>
          <router-link to="/login" class="back-to-login">로그인으로 돌아가기</router-link>
        </div>
      </div>

      <form v-else class="card-body" @submit.prevent="handleSignup">
        <div v-if="error" class="error-message">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <circle cx="8" cy="8" r="7" stroke="currentColor" stroke-width="1.5"/>
            <path d="M8 4.5V9" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            <circle cx="8" cy="11.5" r="0.75" fill="currentColor"/>
          </svg>
          <span>{{ error }}</span>
        </div>

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
          <label for="password">
            비밀번호
            <span class="hint">6자 이상</span>
          </label>
          <input
            id="password"
            v-model="password"
            type="password"
            placeholder="비밀번호를 입력하세요"
            autocomplete="new-password"
            required
            minlength="6"
          />
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
          <span v-else>회원가입</span>
        </button>
      </form>

      <div v-if="!signupSuccess" class="card-footer">
        <span class="footer-text">이미 계정이 있으신가요?</span>
        <router-link to="/login" class="footer-link">로그인</router-link>
      </div>
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
const signupSuccess = ref(false)

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
  position: relative;
  overflow: hidden;
  padding: 24px;
}

.signup-bg {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse 600px 400px at 50% 0%, rgba(99, 102, 241, 0.12), transparent),
    radial-gradient(ellipse 400px 300px at 80% 80%, rgba(129, 140, 248, 0.06), transparent),
    radial-gradient(ellipse 400px 300px at 20% 60%, rgba(99, 102, 241, 0.04), transparent);
  pointer-events: none;
}

.signup-card {
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
  color: var(--text-primary);
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
  gap: 18px;
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
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.hint {
  font-size: 11px;
  font-weight: 400;
  color: var(--text-muted);
}

.field input {
  width: 100%;
  padding: 11px 14px;
  background: var(--bg-surface);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  color: var(--text-primary);
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

.field input.input-error {
  border-color: rgba(239, 68, 68, 0.5);
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.08);
}

.field-error {
  font-size: 12px;
  color: #f87171;
  padding-left: 2px;
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

.success-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 12px 0;
  gap: 12px;
}

.success-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.success-sub {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 0;
  line-height: 1.5;
}

.back-to-login {
  display: inline-block;
  margin-top: 8px;
  padding: 10px 24px;
  background: #6366f1;
  color: #fff;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  text-decoration: none;
  transition: all 0.2s;
}

.back-to-login:hover {
  background: #5558e6;
  box-shadow: 0 0 24px -4px rgba(99, 102, 241, 0.4);
}
</style>
