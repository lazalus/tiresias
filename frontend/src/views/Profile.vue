<template>
  <div class="app-screen">
    <!-- App Header -->
    <header class="app-header">
      <div class="header-inner">
        <div class="header-left">
          <router-link to="/" class="header-home">
            <img src="/logoss.png" alt="TIRESIAS VIEW" class="app-logo" />
            <span class="app-name">TIRESIAS VIEW</span>
          </router-link>
        </div>
      </div>
    </header>

    <main class="profile-main">
      <!-- Profile Card -->
      <div class="section-card profile-card">
        <div class="profile-row">
          <div class="info-avatar">{{ userInitial }}</div>
          <div class="info-details">
            <div class="info-name">{{ user?.name || '-' }}</div>
            <div class="info-email">{{ user?.email || '-' }}</div>
          </div>
        </div>
        <button class="edit-profile-btn" @click="showEditModal = true">프로필 수정</button>
      </div>

      <!-- Credits Card -->
      <div class="section-card credits-card">
        <div class="credits-left">
          <div class="credits-label">보유 크레딧</div>
          <div class="credits-value">{{ credits ?? '-' }}</div>
        </div>
        <router-link to="/credits" class="credits-link">이용권 구매</router-link>
      </div>

      <!-- Admin Menu -->
      <div v-if="isAdmin" class="section-card menu-group">
        <router-link to="/admin" class="menu-item">
          <span class="menu-label">관리자 대시보드</span>
          <span class="menu-arrow">›</span>
        </router-link>
      </div>

      <!-- Service Section -->
      <div class="section-card menu-group">
        <div class="menu-item" @click="toggleTheme">
          <span class="menu-label">화면 모드</span>
          <div class="theme-toggle">
            <span class="theme-label">{{ theme === 'dark' ? '다크' : '라이트' }}</span>
            <div class="toggle-switch" :class="{ light: theme === 'light' }">
              <div class="toggle-knob"></div>
            </div>
          </div>
        </div>
        <div class="menu-divider"></div>
        <router-link to="/features" class="menu-item">
          <span class="menu-label">서비스 소개</span>
          <span class="menu-arrow">›</span>
        </router-link>
        <div class="menu-divider"></div>
        <router-link to="/support" class="menu-item">
          <span class="menu-label">고객센터</span>
          <span class="menu-arrow">›</span>
        </router-link>
        <div class="menu-divider"></div>
        <router-link to="/terms" class="menu-item">
          <span class="menu-label">서비스 이용약관</span>
          <span class="menu-arrow">›</span>
        </router-link>
        <div class="menu-divider"></div>
        <router-link to="/privacy" class="menu-item">
          <span class="menu-label">개인정보 처리방침</span>
          <span class="menu-arrow">›</span>
        </router-link>
      </div>

      <!-- Footer -->
      <div class="profile-footer">
        <button class="logout-btn" @click="handleLogout">로그아웃</button>
        <div class="app-version">앱 버전 v1.0.0</div>
      </div>
    </main>

    <BottomNav />

    <!-- Edit Profile Modal -->
    <Teleport to="body">
      <div v-if="showEditModal" class="modal-overlay" @click.self="showEditModal = false">
        <div class="modal-content">
          <div class="modal-title">프로필 수정</div>
          <label class="modal-label">이름</label>
          <input
            v-model="editName"
            type="text"
            class="modal-input"
            placeholder="이름을 입력하세요"
          />
          <div class="modal-actions">
            <button class="modal-cancel" @click="showEditModal = false">취소</button>
            <button class="modal-save" @click="saveName">저장</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { currentUser, logout, getToken } from '../store/auth.js'
import { useTheme } from '../store/theme.js'
import BottomNav from '../components/BottomNav.vue'

const { theme, toggleTheme } = useTheme()

const router = useRouter()
const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

const user = currentUser
const credits = ref(null)
const showEditModal = ref(false)
const editName = ref('')

const isAdmin = computed(() => user.value?.role === 'admin')

const userInitial = computed(() => {
  const name = user.value?.name || user.value?.email || '?'
  return name.charAt(0).toUpperCase()
})

onMounted(async () => {
  editName.value = user.value?.name || ''
  try {
    const res = await axios.get(`${API_BASE}/api/payments/credits`, {
      headers: { Authorization: `Bearer ${getToken()}` }
    })
    credits.value = res.data.credits ?? res.data
  } catch (e) {
    // Credits fetch failed silently
  }
})

function saveName() {
  if (!editName.value.trim()) return
  // Update localStorage for now (API endpoint /api/auth/me to be added later)
  if (user.value) {
    user.value = { ...user.value, name: editName.value.trim() }
    const stored = localStorage.getItem('user')
    if (stored) {
      const parsed = JSON.parse(stored)
      parsed.name = editName.value.trim()
      localStorage.setItem('user', JSON.stringify(parsed))
    }
  }
  showEditModal.value = false
}

function handleLogout() {
  logout()
  router.push({ name: 'Login' })
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
  font-family: 'Outfit', sans-serif;
  font-weight: 700;
  letter-spacing: 0.08em;
  font-size: 0.9rem;
}

/* Main */
.profile-main {
  max-width: 680px;
  margin: 0 auto;
  padding: 24px 16px 100px;
}

/* Section Card */
.section-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 16px;
  margin-bottom: 16px;
}

/* Profile Card */
.profile-card {
  padding: 24px;
}

.profile-row {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
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

.edit-profile-btn {
  width: 100%;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.7);
  padding: 10px;
  border-radius: 10px;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.edit-profile-btn:hover {
  background: rgba(255, 255, 255, 0.08);
}

/* Credits Card */
.credits-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px;
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

/* Menu Group */
.menu-group {
  overflow: hidden;
}

.menu-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  text-decoration: none;
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.92rem;
  transition: background 0.15s;
  cursor: pointer;
}

.menu-item:hover {
  background: rgba(255, 255, 255, 0.04);
}

.menu-label {
  font-weight: 450;
}

.menu-arrow {
  color: rgba(255, 255, 255, 0.2);
  font-size: 1.3rem;
  font-weight: 300;
}

.menu-divider {
  height: 1px;
  background: rgba(255, 255, 255, 0.04);
  margin: 0 20px;
}

/* Theme Toggle */
.theme-toggle {
  display: flex;
  align-items: center;
  gap: 10px;
}
.theme-label {
  font-size: 0.8rem;
  color: var(--text-secondary);
}
.toggle-switch {
  width: 44px;
  height: 24px;
  border-radius: 12px;
  background: #6366f1;
  position: relative;
  cursor: pointer;
  transition: background 0.2s;
}
.toggle-switch.light {
  background: #d1d5db;
}
.toggle-knob {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #fff;
  position: absolute;
  top: 2px;
  left: 2px;
  transition: transform 0.2s;
}
.toggle-switch.light .toggle-knob {
  transform: translateX(20px);
}

/* Footer */
.profile-footer {
  margin-top: 32px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.logout-btn {
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.35);
  font-size: 0.85rem;
  font-weight: 450;
  cursor: pointer;
  padding: 8px 16px;
  transition: color 0.2s;
}

.logout-btn:hover {
  color: rgba(255, 255, 255, 0.55);
}

.app-version {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.15);
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 500;
  padding: 24px;
}

.modal-content {
  background: #1a1828;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 20px;
  padding: 28px 24px;
  width: 100%;
  max-width: 360px;
}

.modal-title {
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 20px;
}

.modal-label {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.4);
  font-weight: 500;
  margin-bottom: 8px;
  display: block;
}

.modal-input {
  width: 100%;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  padding: 12px 14px;
  color: #fafafa;
  font-size: 0.92rem;
  outline: none;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.modal-input:focus {
  border-color: rgba(99, 102, 241, 0.5);
}

.modal-actions {
  display: flex;
  gap: 10px;
  margin-top: 20px;
}

.modal-cancel {
  flex: 1;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.6);
  padding: 12px;
  border-radius: 10px;
  font-size: 0.88rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.modal-cancel:hover {
  background: rgba(255, 255, 255, 0.08);
}

.modal-save {
  flex: 1;
  background: #6366f1;
  border: none;
  color: #fff;
  padding: 12px;
  border-radius: 10px;
  font-size: 0.88rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.modal-save:hover {
  background: #5558e6;
}

/* Responsive */
@media (max-width: 640px) {
  .profile-main {
    padding: 20px 16px 100px;
  }
}
</style>
