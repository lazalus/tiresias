<template>
  <div class="verify-page">
    <div class="verify-card">
      <div class="brand">
        <span class="brand-name">TIRESIAS VIEW</span>
      </div>

      <h1>{{ title }}</h1>
      <p class="subtitle">{{ message }}</p>

      <div v-if="loading" class="loading-box">
        <svg class="spinner" width="18" height="18" viewBox="0 0 16 16" fill="none">
          <circle cx="8" cy="8" r="6.5" stroke="rgba(255,255,255,0.18)" stroke-width="1.5"/>
          <path d="M14.5 8a6.5 6.5 0 0 0-6.5-6.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
        <span>회원가입을 마무리하고 있습니다.</span>
      </div>

      <div v-else class="actions">
        <router-link v-if="success" to="/dashboard" class="btn-primary">대시보드로 이동</router-link>
        <router-link v-else to="/signup" class="btn-primary">회원가입 다시 시도</router-link>
        <router-link to="/login" class="btn-secondary">로그인</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { apiVerifySignup } from '../api/auth.js'
import { login } from '../store/auth.js'
import { trackGoogleAdsConversionOnce, trackMarketingEvent } from '../utils/marketing.js'
import { applySeoMeta, resetSeoMeta } from '../utils/seo.js'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const success = ref(false)
const message = ref('인증 링크를 확인하고 있습니다.')

const title = computed(() => {
  if (loading.value) return '이메일 인증 확인 중'
  return success.value ? '회원가입이 완료되었습니다' : '인증을 완료할 수 없습니다'
})

onMounted(async () => {
  applySeoMeta({
    title: '이메일 인증 | 테이레시아스 뷰',
    description: '테이레시아스 뷰 회원가입 이메일 인증 페이지',
    canonical: 'https://tiresiasview.com/signup/verify',
    robots: 'noindex,follow',
  })

  const token = String(route.query.token || '').trim()
  if (!token) {
    loading.value = false
    message.value = '인증 토큰이 없습니다. 메일의 링크를 다시 열어주세요.'
    return
  }

  try {
    const { user, token: authToken } = await apiVerifySignup(token)
    trackMarketingEvent('sign_up', {
      method: 'email_verification',
    })
    trackGoogleAdsConversionOnce('signup_complete', user?.id || user?.email, {
      value: 1,
      currency: 'KRW',
    })
    login(user, authToken)
    success.value = true
    message.value = '이메일 인증이 완료되어 계정이 생성되었습니다. 잠시 후 대시보드로 이동합니다.'
    setTimeout(() => {
      router.replace('/dashboard')
    }, 1200)
  } catch (error) {
    success.value = false
    message.value = error.response?.data?.error || '인증 링크가 유효하지 않거나 만료되었습니다.'
  } finally {
    loading.value = false
  }
})

onUnmounted(() => {
  resetSeoMeta()
})
</script>

<style scoped>
.verify-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-primary);
  padding: 24px;
}

.verify-card {
  width: 100%;
  max-width: 420px;
  padding: 24px;
  border: 1px solid var(--border-color);
  border-radius: 18px;
  background: var(--bg-secondary);
}

.brand {
  margin-bottom: 16px;
}

.brand-name {
  font-family: 'Outfit', sans-serif;
  font-weight: 700;
  font-size: 0.85rem;
  letter-spacing: 0.1em;
  color: var(--accent-color, #6366f1);
}

h1 {
  margin: 0 0 8px;
  font-size: 1.45rem;
  line-height: 1.3;
  color: var(--text-primary);
}

.subtitle {
  margin: 0;
  font-size: 14px;
  line-height: 1.7;
  color: var(--text-secondary);
}

.loading-box {
  margin-top: 18px;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: var(--text-secondary);
}

.spinner {
  color: var(--accent-color);
  animation: spin 0.7s linear infinite;
}

.actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 20px;
}

.btn-primary,
.btn-secondary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 42px;
  border-radius: 10px;
  text-decoration: none;
  font-size: 14px;
  font-weight: 600;
}

.btn-primary {
  background: var(--accent-color);
  color: #fff;
}

.btn-secondary {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
