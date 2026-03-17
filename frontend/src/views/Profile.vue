<template>
  <div class="app-screen">
    <!-- App Header -->
    <header class="app-header">
      <div class="header-inner">
        <div class="header-left">
          <router-link to="/" class="header-home">
            <img src="/logoss.png" alt="Tiresias View" class="app-logo" />
            <span class="app-name">Tiresias View</span>
          </router-link>
        </div>
      </div>
    </header>

    <main class="profile-main">
      <h1 class="page-title">내 정보</h1>

      <!-- User Info Card -->
      <div class="info-card">
        <div class="info-avatar">{{ userInitial }}</div>
        <div class="info-details">
          <div class="info-name">{{ user?.name || '-' }}</div>
          <div class="info-email">{{ user?.email || '-' }}</div>
          <div class="info-joined" v-if="user?.created_at">
            가입일: {{ formatDate(user.created_at) }}
          </div>
        </div>
      </div>

      <!-- Credits Card -->
      <div class="credits-card">
        <div class="credits-left">
          <div class="credits-label">보유 크레딧</div>
          <div class="credits-value">{{ credits ?? '-' }}</div>
        </div>
        <router-link to="/credits" class="credits-link">이용권 구매</router-link>
      </div>

      <!-- Logout -->
      <button class="logout-btn" @click="handleLogout">로그아웃</button>
    </main>

    <BottomNav />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { currentUser, logout, getToken } from '../store/auth.js'
import BottomNav from '../components/BottomNav.vue'

const router = useRouter()
const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

const user = currentUser
const credits = ref(null)

const userInitial = computed(() => {
  const name = user.value?.name || user.value?.email || '?'
  return name.charAt(0).toUpperCase()
})

onMounted(async () => {
  try {
    const res = await axios.get(`${API_BASE}/api/payments/credits`, {
      headers: { Authorization: `Bearer ${getToken()}` }
    })
    credits.value = res.data.credits ?? res.data
  } catch (e) {
    // Credits fetch failed silently
  }
})

function handleLogout() {
  logout()
  router.push({ name: 'Login' })
}

function formatDate(d) {
  if (!d) return '-'
  return new Date(d).toLocaleDateString('ko-KR', {
    year: 'numeric', month: '2-digit', day: '2-digit'
  })
}
</script>

<style scoped>
.app-screen {
  min-height: 100vh;
  background: #0c0a15;
  color: #fafafa;
  font-family: 'Inter', 'Noto Sans KR', system-ui, -apple-system, sans-serif;
  -webkit-font-smoothing: antialiased;
}

/* Header */
.app-header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(9, 9, 11, 0.72);
  backdrop-filter: saturate(180%) blur(20px);
  -webkit-backdrop-filter: saturate(180%) blur(20px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.header-inner {
  max-width: 680px;
  margin: 0 auto;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-home {
  display: flex;
  align-items: center;
  gap: 12px;
  text-decoration: none;
  color: inherit;
}

.app-logo {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  object-fit: cover;
}

.app-name {
  font-weight: 600;
  font-size: 0.95rem;
  letter-spacing: -0.01em;
}

/* Main */
.profile-main {
  max-width: 680px;
  margin: 0 auto;
  padding: 48px 24px 80px;
}

.page-title {
  font-size: 1.5rem;
  font-weight: 700;
  letter-spacing: -0.025em;
  margin: 0 0 32px;
}

/* Info Card */
.info-card {
  display: flex;
  align-items: center;
  gap: 20px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 20px;
}

.info-avatar {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6366f1, #818cf8);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  font-weight: 700;
  color: #fff;
  flex-shrink: 0;
}

.info-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-name {
  font-size: 1.05rem;
  font-weight: 600;
}

.info-email {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.4);
}

.info-joined {
  font-size: 0.78rem;
  color: rgba(255, 255, 255, 0.25);
  font-family: 'JetBrains Mono', monospace;
  margin-top: 4px;
}

/* Credits Card */
.credits-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 32px;
}

.credits-label {
  font-size: 0.82rem;
  color: rgba(255, 255, 255, 0.4);
  font-weight: 500;
  margin-bottom: 6px;
}

.credits-value {
  font-size: 2rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  background: linear-gradient(135deg, #818cf8, #6366f1);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.credits-link {
  color: #818cf8;
  text-decoration: none;
  font-size: 0.85rem;
  font-weight: 500;
  padding: 8px 20px;
  border: 1px solid rgba(99, 102, 241, 0.3);
  border-radius: 10px;
  transition: all 0.2s;
}

.credits-link:hover {
  background: rgba(99, 102, 241, 0.1);
  border-color: rgba(99, 102, 241, 0.5);
}

/* Logout */
.logout-btn {
  width: 100%;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: #f87171;
  padding: 14px 20px;
  border-radius: 12px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.logout-btn:hover {
  background: rgba(248, 113, 113, 0.08);
  border-color: rgba(248, 113, 113, 0.2);
}

/* Responsive */
@media (max-width: 640px) {
  .profile-main {
    padding: 32px 16px 80px;
  }
  .page-title {
    font-size: 1.3rem;
  }
}
</style>
