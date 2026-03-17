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
          <span class="admin-badge">Admin</span>
        </div>
        <div class="header-right">
          <router-link to="/" class="header-link">홈</router-link>
        </div>
      </div>
    </header>

    <main class="admin-main">
      <!-- KPI Cards -->
      <div class="kpi-grid">
        <div class="kpi-card">
          <div class="kpi-icon kpi-icon--revenue">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
          </div>
          <div class="kpi-content">
            <span class="kpi-label">오늘 매출</span>
            <span class="kpi-value">{{ formatKRW(stats.todayRevenue) }}</span>
            <span v-if="stats.todayPurchases != null" class="kpi-sub">{{ stats.todayPurchases }}건 결제</span>
          </div>
        </div>

        <div class="kpi-card">
          <div class="kpi-icon kpi-icon--monthly">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
          </div>
          <div class="kpi-content">
            <span class="kpi-label">이번 달 매출</span>
            <span class="kpi-value">{{ formatKRW(stats.monthlyRevenue) }}</span>
            <span v-if="stats.monthlyPurchases != null" class="kpi-sub">{{ stats.monthlyPurchases }}건 결제</span>
          </div>
        </div>

        <div class="kpi-card">
          <div class="kpi-icon kpi-icon--signup">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="8.5" cy="7" r="4"/><line x1="20" y1="8" x2="20" y2="14"/><line x1="23" y1="11" x2="17" y2="11"/></svg>
          </div>
          <div class="kpi-content">
            <span class="kpi-label">오늘 신규 가입</span>
            <span class="kpi-value">{{ stats.todaySignups ?? clientTodaySignups }}</span>
            <span class="kpi-sub">전체 {{ stats.totalUsers ?? '-' }}명</span>
          </div>
        </div>

        <div class="kpi-card">
          <div class="kpi-icon kpi-icon--credits">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
          </div>
          <div class="kpi-content">
            <span class="kpi-label">총 크레딧 사용</span>
            <span class="kpi-value">{{ formatNumber(stats.monthlyCreditsUsed) }}</span>
            <span class="kpi-sub">이번 달</span>
          </div>
        </div>
      </div>

      <!-- Pending Users -->
      <section v-if="pendingUsers.length > 0" class="section-block">
        <h2 class="section-title">
          <span class="dot dot--warning"></span>
          승인 대기 ({{ pendingUsers.length }})
        </h2>
        <div class="user-cards">
          <div v-for="u in pendingUsers" :key="u.id" class="user-card user-card--pending">
            <div class="user-card-top">
              <div class="user-card-info">
                <div class="user-card-name-row">
                  <span class="user-card-name">{{ u.name }}</span>
                  <span class="role-badge role-badge--pending">대기</span>
                </div>
                <span class="user-card-email">{{ u.email }}</span>
              </div>
              <span class="user-card-date">{{ formatShortDate(u.created_at) }}</span>
            </div>
            <div class="user-card-actions">
              <button class="btn btn--approve" @click="approveUser(u.id)" :disabled="actionLoading[u.id]">승인</button>
              <button class="btn btn--reject" @click="rejectUser(u.id)" :disabled="actionLoading[u.id]">거절</button>
            </div>
          </div>
        </div>
      </section>

      <!-- All Users -->
      <section class="section-block">
        <h2 class="section-title">
          <span class="dot dot--primary"></span>
          유저 관리 ({{ activeUsers.length }})
        </h2>
        <div class="user-cards">
          <div v-for="u in activeUsers" :key="u.id" class="user-card" @click="toggleExpand(u.id)">
            <div class="user-card-top">
              <div class="user-card-info">
                <div class="user-card-name-row">
                  <span class="user-card-name">{{ u.name }}</span>
                  <span class="role-badge" :class="'role-badge--' + u.role">{{ u.role }}</span>
                </div>
                <span class="user-card-email">{{ u.email }}</span>
              </div>
              <div class="user-card-right">
                <div class="user-card-credits">
                  <span class="credits-value">{{ u.credits ?? 0 }}</span>
                  <span class="credits-label">크레딧</span>
                </div>
                <span class="user-card-date">{{ formatShortDate(u.created_at) }}</span>
              </div>
            </div>
            <transition name="expand">
              <div v-if="expandedUser === u.id" class="user-card-actions" @click.stop>
                <button class="btn btn--credit" @click="openCreditModal(u)">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                  크레딧 지급
                </button>
                <button
                  class="btn btn--role"
                  @click="toggleRole(u)"
                  :disabled="actionLoading[u.id]"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                  {{ u.role === 'admin' ? '유저로 변경' : '관리자 설정' }}
                </button>
              </div>
            </transition>
          </div>
        </div>
      </section>
    </main>

    <BottomNav />

    <!-- Grant Credits Modal -->
    <transition name="modal">
      <div v-if="creditModal.show" class="modal-overlay" @click.self="closeCreditModal">
        <div class="modal-card">
          <h3 class="modal-title">크레딧 지급</h3>
          <p class="modal-sub">{{ creditModal.user?.name }} &middot; {{ creditModal.user?.email }}</p>
          <div class="modal-field">
            <label>크레딧 수량</label>
            <input
              v-model.number="creditModal.amount"
              type="number"
              min="1"
              placeholder="지급할 크레딧 수"
              autofocus
            />
          </div>
          <div class="modal-field">
            <label>설명 (선택)</label>
            <input
              v-model="creditModal.description"
              type="text"
              placeholder="예: 프로모션 지급"
            />
          </div>
          <div class="modal-actions">
            <button class="btn btn--ghost" @click="closeCreditModal">취소</button>
            <button
              class="btn btn--primary"
              @click="grantCredits"
              :disabled="!creditModal.amount || creditModal.loading"
            >
              {{ creditModal.loading ? '처리 중...' : '지급 확인' }}
            </button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { currentUser, getToken } from '../store/auth.js'
import axios from 'axios'
import BottomNav from '../components/BottomNav.vue'

const router = useRouter()
const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

onMounted(() => {
  if (!currentUser.value || currentUser.value.role !== 'admin') {
    router.push('/')
    return
  }
  fetchStats()
  fetchUsers()
})

function authHeaders() {
  return { headers: { Authorization: `Bearer ${getToken()}` } }
}

// Stats
const stats = ref({})

async function fetchStats() {
  try {
    const res = await axios.get(`${API_BASE}/api/admin/stats`, authHeaders())
    stats.value = res.data
  } catch (e) {
    console.error('Failed to fetch stats:', e)
  }
}

// Users
const allUsers = ref([])
const actionLoading = reactive({})
const expandedUser = ref(null)

const pendingUsers = computed(() => allUsers.value.filter(u => u.status === 'pending' || u.role === 'pending'))
const activeUsers = computed(() => allUsers.value.filter(u => u.status !== 'pending' && u.role !== 'pending'))

// Client-side fallback: count today's signups from user list
const clientTodaySignups = computed(() => {
  const today = new Date().toISOString().slice(0, 10)
  return allUsers.value.filter(u => u.created_at && u.created_at.slice(0, 10) === today).length
})

function toggleExpand(id) {
  expandedUser.value = expandedUser.value === id ? null : id
}

async function fetchUsers() {
  try {
    const res = await axios.get(`${API_BASE}/api/admin/users`, authHeaders())
    allUsers.value = res.data.users || res.data
  } catch (e) {
    console.error('Failed to fetch users:', e)
  }
}

async function approveUser(id) {
  actionLoading[id] = true
  try {
    await axios.post(`${API_BASE}/api/admin/users/${id}/approve`, {}, authHeaders())
    await fetchUsers()
    await fetchStats()
  } catch (e) {
    alert('승인 실패: ' + (e.response?.data?.message || e.message))
  } finally {
    actionLoading[id] = false
  }
}

async function rejectUser(id) {
  if (!confirm('정말 거절하시겠습니까?')) return
  actionLoading[id] = true
  try {
    await axios.post(`${API_BASE}/api/admin/users/${id}/reject`, {}, authHeaders())
    await fetchUsers()
    await fetchStats()
  } catch (e) {
    alert('거절 실패: ' + (e.response?.data?.message || e.message))
  } finally {
    actionLoading[id] = false
  }
}

async function toggleRole(u) {
  const newRole = u.role === 'admin' ? 'user' : 'admin'
  const label = newRole === 'admin' ? '관리자로 설정' : '유저로 변경'
  if (!confirm(`${u.name}을(를) ${label}하시겠습니까?`)) return
  actionLoading[u.id] = true
  try {
    const endpoint = newRole === 'admin' ? 'set-admin' : 'set-user'
    await axios.post(`${API_BASE}/api/admin/users/${u.id}/${endpoint}`, {}, authHeaders())
    await fetchUsers()
  } catch (e) {
    alert('설정 실패: ' + (e.response?.data?.message || e.message))
  } finally {
    actionLoading[u.id] = false
  }
}

// Credit Modal
const creditModal = reactive({
  show: false,
  user: null,
  amount: null,
  description: '',
  loading: false
})

function openCreditModal(user) {
  creditModal.show = true
  creditModal.user = user
  creditModal.amount = null
  creditModal.description = ''
}

function closeCreditModal() {
  creditModal.show = false
  creditModal.user = null
}

async function grantCredits() {
  if (!creditModal.amount || !creditModal.user) return
  creditModal.loading = true
  try {
    await axios.post(
      `${API_BASE}/api/admin/users/${creditModal.user.id}/credits`,
      { amount: creditModal.amount, description: creditModal.description },
      authHeaders()
    )
    closeCreditModal()
    await fetchUsers()
    await fetchStats()
  } catch (e) {
    alert('크레딧 지급 실패: ' + (e.response?.data?.message || e.message))
  } finally {
    creditModal.loading = false
  }
}

function formatKRW(val) {
  if (val == null) return '-'
  return `₩${Number(val).toLocaleString('ko-KR')}`
}

function formatNumber(val) {
  if (val == null) return '-'
  return Number(val).toLocaleString('ko-KR')
}

function formatShortDate(d) {
  if (!d) return '-'
  const dt = new Date(d)
  const m = String(dt.getMonth() + 1).padStart(2, '0')
  const day = String(dt.getDate()).padStart(2, '0')
  return `${m}.${day}`
}
</script>

<style scoped>
.app-screen {
  min-height: 100vh;
  min-height: 100dvh;
  background: var(--bg-primary);
  color: var(--text-primary);
  font-family: 'Inter', 'Noto Sans KR', system-ui, -apple-system, sans-serif;
  -webkit-font-smoothing: antialiased;
}

/* Header */
.app-header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: var(--header-bg);
  backdrop-filter: saturate(180%) blur(20px);
  -webkit-backdrop-filter: saturate(180%) blur(20px);
  border-bottom: 1px solid var(--border-color);
}

.header-inner {
  max-width: 640px;
  margin: 0 auto;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-home {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  color: inherit;
}

.app-logo {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  object-fit: cover;
}

.app-name {
  font-family: 'Outfit', sans-serif;
  font-weight: 700;
  letter-spacing: 0.08em;
  font-size: 0.85rem;
}

.admin-badge {
  font-size: 0.65rem;
  font-weight: 600;
  color: #818cf8;
  background: rgba(99, 102, 241, 0.12);
  border: 1px solid rgba(99, 102, 241, 0.2);
  padding: 2px 8px;
  border-radius: 20px;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.header-right {
  display: flex;
  align-items: center;
}

.header-link {
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 0.8rem;
  font-weight: 500;
  padding: 6px 12px;
  border-radius: 8px;
  transition: color 0.2s, background 0.2s;
}

.header-link:hover {
  color: var(--text-primary);
  background: var(--border-color);
}

/* Main */
.admin-main {
  max-width: 640px;
  margin: 0 auto;
  padding: 20px 16px 100px;
}

/* KPI Grid */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 32px;
}

.kpi-card {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 16px;
  transition: border-color 0.3s;
}

.kpi-card:hover {
  border-color: var(--border-color);
}

.kpi-icon {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.kpi-icon--revenue {
  background: rgba(34, 197, 94, 0.12);
  color: #4ade80;
}

.kpi-icon--monthly {
  background: rgba(59, 130, 246, 0.12);
  color: #60a5fa;
}

.kpi-icon--signup {
  background: rgba(168, 85, 247, 0.12);
  color: #c084fc;
}

.kpi-icon--credits {
  background: rgba(245, 158, 11, 0.12);
  color: #fbbf24;
}

.kpi-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.kpi-label {
  font-size: 0.7rem;
  font-weight: 500;
  color: var(--text-secondary);
  letter-spacing: 0.01em;
}

.kpi-value {
  font-size: 1.15rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.kpi-sub {
  font-size: 0.68rem;
  color: var(--text-muted);
}

/* Section */
.section-block {
  margin-bottom: 28px;
}

.section-title {
  font-size: 0.88rem;
  font-weight: 600;
  margin: 0 0 14px;
  letter-spacing: -0.01em;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* Dots */
.dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.dot--primary {
  background: #6366f1;
}

.dot--warning {
  background: #f59e0b;
}

/* User Cards */
.user-cards {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.user-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 16px;
  transition: border-color 0.2s, background 0.2s;
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
}

.user-card:active {
  background: var(--bg-surface);
}

.user-card--pending {
  border-color: rgba(245, 158, 11, 0.15);
  cursor: default;
}

.user-card-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.user-card-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.user-card-name-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-card-name {
  font-size: 0.88rem;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-card-email {
  font-size: 0.75rem;
  color: var(--text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-card-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  flex-shrink: 0;
}

.user-card-credits {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.credits-value {
  font-size: 1rem;
  font-weight: 700;
  color: #818cf8;
  letter-spacing: -0.01em;
}

.credits-label {
  font-size: 0.65rem;
  color: var(--text-muted);
  font-weight: 500;
}

.user-card-date {
  font-size: 0.68rem;
  color: var(--text-muted);
  font-variant-numeric: tabular-nums;
}

/* Role Badges */
.role-badge {
  font-size: 0.62rem;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 20px;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  flex-shrink: 0;
}

.role-badge--admin {
  background: rgba(99, 102, 241, 0.12);
  color: #818cf8;
  border: 1px solid rgba(99, 102, 241, 0.2);
}

.role-badge--user {
  background: var(--bg-surface);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
}

.role-badge--pending {
  background: rgba(245, 158, 11, 0.1);
  color: #fbbf24;
  border: 1px solid rgba(245, 158, 11, 0.2);
}

/* Card Actions */
.user-card-actions {
  display: flex;
  gap: 8px;
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid var(--border-color);
  overflow: hidden;
}

/* Expand transition */
.expand-enter-active,
.expand-leave-active {
  transition: all 0.2s ease;
  max-height: 80px;
}

.expand-enter-from,
.expand-leave-to {
  opacity: 0;
  max-height: 0;
  margin-top: 0;
  padding-top: 0;
}

/* Buttons */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: 10px;
  font-size: 0.78rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
  white-space: nowrap;
  flex: 1;
  font-family: inherit;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn--approve {
  background: rgba(34, 197, 94, 0.12);
  border-color: rgba(34, 197, 94, 0.25);
  color: #4ade80;
}

.btn--approve:hover:not(:disabled) {
  background: rgba(34, 197, 94, 0.2);
}

.btn--reject {
  background: rgba(239, 68, 68, 0.08);
  border-color: rgba(239, 68, 68, 0.2);
  color: #f87171;
}

.btn--reject:hover:not(:disabled) {
  background: rgba(239, 68, 68, 0.15);
}

.btn--credit {
  background: rgba(99, 102, 241, 0.1);
  border-color: rgba(99, 102, 241, 0.2);
  color: #818cf8;
}

.btn--credit:hover:not(:disabled) {
  background: rgba(99, 102, 241, 0.18);
}

.btn--role {
  background: rgba(245, 158, 11, 0.08);
  border-color: rgba(245, 158, 11, 0.2);
  color: #fbbf24;
}

.btn--role:hover:not(:disabled) {
  background: rgba(245, 158, 11, 0.15);
}

.btn--ghost {
  background: var(--bg-surface);
  border-color: var(--border-color);
  color: var(--text-secondary);
}

.btn--ghost:hover {
  background: var(--bg-surface);
  opacity: 0.8;
}

.btn--primary {
  background: #6366f1;
  border: none;
  color: #fff;
  font-weight: 600;
}

.btn--primary:hover:not(:disabled) {
  background: #5558e6;
  box-shadow: 0 0 20px rgba(99, 102, 241, 0.3);
}

.btn--primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  z-index: 500;
  padding: 0;
}

.modal-card {
  background: #151419;
  border: 1px solid var(--border-color);
  border-radius: 20px 20px 0 0;
  padding: 28px 20px 32px;
  width: 100%;
  max-width: 480px;
  box-shadow: 0 -8px 48px rgba(0, 0, 0, 0.5);
}

.modal-title {
  font-size: 1.05rem;
  font-weight: 600;
  margin: 0 0 4px;
}

.modal-sub {
  font-size: 0.8rem;
  color: var(--text-secondary);
  margin: 0 0 22px;
}

.modal-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 16px;
}

.modal-field label {
  font-size: 0.78rem;
  font-weight: 500;
  color: var(--text-secondary);
}

.modal-field input {
  width: 100%;
  padding: 12px 14px;
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  color: var(--text-primary);
  font-size: 0.9rem;
  font-family: inherit;
  outline: none;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.modal-field input:focus {
  border-color: rgba(99, 102, 241, 0.5);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.modal-actions {
  display: flex;
  gap: 10px;
  margin-top: 24px;
}

.modal-actions .btn {
  flex: 1;
  padding: 12px 20px;
  font-size: 0.88rem;
}

/* Modal transition */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}

.modal-enter-active .modal-card,
.modal-leave-active .modal-card {
  transition: transform 0.25s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .modal-card {
  transform: translateY(100%);
}

.modal-leave-to .modal-card {
  transform: translateY(100%);
}

/* Desktop adjustments */
@media (min-width: 480px) {
  .modal-overlay {
    align-items: center;
    padding: 24px;
  }

  .modal-card {
    border-radius: 20px;
  }
}

@media (min-width: 768px) {
  .admin-main {
    padding: 28px 24px 100px;
  }

  .header-inner {
    max-width: 720px;
    padding: 0 24px;
  }

  .admin-main {
    max-width: 720px;
  }

  .kpi-card {
    padding: 20px;
  }

  .kpi-value {
    font-size: 1.3rem;
  }
}
</style>
