<template>
  <div class="app-screen">
    <!-- App Header -->
    <header class="app-header">
      <div class="header-inner">
        <div class="header-left">
          <router-link to="/" class="header-home">
            <img src="/logoss.png" alt="Tiresias" class="app-logo" />
            <span class="app-name">Tiresias</span>
          </router-link>
          <span class="admin-badge">Admin</span>
        </div>
        <div class="header-right">
          <router-link to="/" class="header-link">홈</router-link>
        </div>
      </div>
    </header>

    <main class="admin-main">
      <!-- Stats Cards -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">총 유저</div>
          <div class="stat-value">{{ stats.totalUsers ?? '-' }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">승인 대기</div>
          <div class="stat-value stat-pending">{{ stats.pendingUsers ?? '-' }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">총 프로젝트</div>
          <div class="stat-value">{{ stats.totalProjects ?? '-' }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">총 매출</div>
          <div class="stat-value">{{ stats.totalRevenue != null ? `₩${stats.totalRevenue.toLocaleString()}` : '-' }}</div>
        </div>
      </div>

      <!-- Pending Users -->
      <section v-if="pendingUsers.length > 0" class="section-block">
        <h2 class="section-title">승인 대기 유저</h2>
        <div class="pending-list">
          <div v-for="u in pendingUsers" :key="u.id" class="pending-item">
            <div class="pending-info">
              <span class="pending-name">{{ u.name }}</span>
              <span class="pending-email">{{ u.email }}</span>
              <span class="pending-date">{{ formatDate(u.created_at) }}</span>
            </div>
            <div class="pending-actions">
              <button class="btn-approve" @click="approveUser(u.id)" :disabled="actionLoading[u.id]">승인</button>
              <button class="btn-reject" @click="rejectUser(u.id)" :disabled="actionLoading[u.id]">거절</button>
            </div>
          </div>
        </div>
      </section>

      <!-- All Users Table -->
      <section class="section-block">
        <h2 class="section-title">전체 유저</h2>
        <div class="table-wrap">
          <table class="users-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>이름</th>
                <th>이메일</th>
                <th>역할</th>
                <th>크레딧</th>
                <th>가입일</th>
                <th>액션</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="u in allUsers" :key="u.id">
                <td class="td-id">{{ u.id }}</td>
                <td>{{ u.name }}</td>
                <td class="td-email">{{ u.email }}</td>
                <td>
                  <span class="role-badge" :class="u.role">{{ u.role }}</span>
                </td>
                <td class="td-credits">{{ u.credits ?? 0 }}</td>
                <td class="td-date">{{ formatDate(u.created_at) }}</td>
                <td class="td-actions">
                  <button v-if="u.status === 'pending'" class="btn-sm btn-approve" @click="approveUser(u.id)" :disabled="actionLoading[u.id]">승인</button>
                  <button class="btn-sm btn-credit" @click="openCreditModal(u)">크레딧 부여</button>
                  <button v-if="u.role !== 'admin'" class="btn-sm btn-admin" @click="setAdmin(u.id)" :disabled="actionLoading[u.id]">관리자 설정</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </main>

    <!-- Grant Credits Modal -->
    <div v-if="creditModal.show" class="modal-overlay" @click.self="closeCreditModal">
      <div class="modal-card">
        <h3 class="modal-title">크레딧 부여</h3>
        <p class="modal-sub">{{ creditModal.user?.name }} ({{ creditModal.user?.email }})</p>
        <div class="modal-field">
          <label>크레딧 수량</label>
          <input v-model.number="creditModal.amount" type="number" min="1" placeholder="부여할 크레딧 수" />
        </div>
        <div class="modal-field">
          <label>설명</label>
          <input v-model="creditModal.description" type="text" placeholder="예: 프로모션 지급" />
        </div>
        <div class="modal-actions">
          <button class="btn-cancel" @click="closeCreditModal">취소</button>
          <button class="btn-confirm" @click="grantCredits" :disabled="!creditModal.amount || creditModal.loading">
            {{ creditModal.loading ? '처리 중...' : '부여' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { currentUser, getToken } from '../store/auth.js'
import axios from 'axios'

const router = useRouter()
const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

// Auth check
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

const pendingUsers = computed(() => allUsers.value.filter(u => u.status === 'pending'))

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

async function setAdmin(id) {
  if (!confirm('이 유저를 관리자로 설정하시겠습니까?')) return
  actionLoading[id] = true
  try {
    await axios.post(`${API_BASE}/api/admin/users/${id}/set-admin`, {}, authHeaders())
    await fetchUsers()
  } catch (e) {
    alert('설정 실패: ' + (e.response?.data?.message || e.message))
  } finally {
    actionLoading[id] = false
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
    alert('크레딧 부여 실패: ' + (e.response?.data?.message || e.message))
  } finally {
    creditModal.loading = false
  }
}

function formatDate(d) {
  if (!d) return '-'
  return new Date(d).toLocaleDateString('ko-KR', { year: 'numeric', month: '2-digit', day: '2-digit' })
}
</script>

<style scoped>
.app-screen {
  min-height: 100vh;
  background: #09090b;
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
  max-width: 1100px;
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

.admin-badge {
  font-size: 0.68rem;
  font-weight: 600;
  color: #818cf8;
  background: rgba(99, 102, 241, 0.12);
  border: 1px solid rgba(99, 102, 241, 0.2);
  padding: 2px 10px;
  border-radius: 20px;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-link {
  color: rgba(255, 255, 255, 0.4);
  text-decoration: none;
  font-size: 0.82rem;
  font-weight: 500;
  padding: 6px 14px;
  border-radius: 8px;
  transition: color 0.2s, background 0.2s;
}

.header-link:hover {
  color: rgba(255, 255, 255, 0.9);
  background: rgba(255, 255, 255, 0.06);
}

/* Main */
.admin-main {
  max-width: 1100px;
  margin: 0 auto;
  padding: 32px 24px 100px;
}

/* Stats */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 40px;
}

.stat-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 14px;
  padding: 20px;
  transition: border-color 0.3s;
}

.stat-card:hover {
  border-color: rgba(255, 255, 255, 0.1);
}

.stat-label {
  font-size: 0.78rem;
  color: rgba(255, 255, 255, 0.4);
  margin-bottom: 8px;
  font-weight: 500;
}

.stat-value {
  font-size: 1.6rem;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.stat-pending {
  color: #f59e0b;
}

/* Section */
.section-block {
  margin-bottom: 40px;
}

.section-title {
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 16px;
  letter-spacing: -0.01em;
}

/* Pending List */
.pending-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.pending-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  padding: 14px 18px;
  transition: border-color 0.2s;
}

.pending-item:hover {
  border-color: rgba(255, 255, 255, 0.1);
}

.pending-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.pending-name {
  font-size: 0.88rem;
  font-weight: 600;
}

.pending-email {
  font-size: 0.82rem;
  color: rgba(255, 255, 255, 0.4);
}

.pending-date {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.25);
  font-family: 'JetBrains Mono', monospace;
}

.pending-actions {
  display: flex;
  gap: 8px;
}

.btn-approve {
  background: rgba(34, 197, 94, 0.12);
  border: 1px solid rgba(34, 197, 94, 0.25);
  color: #4ade80;
  padding: 6px 16px;
  border-radius: 8px;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-approve:hover:not(:disabled) {
  background: rgba(34, 197, 94, 0.2);
}

.btn-reject {
  background: rgba(239, 68, 68, 0.08);
  border: 1px solid rgba(239, 68, 68, 0.2);
  color: #f87171;
  padding: 6px 16px;
  border-radius: 8px;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-reject:hover:not(:disabled) {
  background: rgba(239, 68, 68, 0.15);
}

/* Users Table */
.table-wrap {
  overflow-x: auto;
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(255, 255, 255, 0.02);
}

.users-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.82rem;
}

.users-table th {
  text-align: left;
  padding: 12px 16px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.4);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.users-table td {
  padding: 12px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.03);
  vertical-align: middle;
}

.users-table tr:last-child td {
  border-bottom: none;
}

.users-table tr:hover td {
  background: rgba(255, 255, 255, 0.02);
}

.td-id {
  font-family: 'JetBrains Mono', monospace;
  color: rgba(255, 255, 255, 0.3);
  font-size: 0.75rem;
}

.td-email {
  color: rgba(255, 255, 255, 0.5);
}

.td-credits {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 600;
  color: #818cf8;
}

.td-date {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.3);
}

.td-actions {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.role-badge {
  font-size: 0.72rem;
  font-weight: 500;
  padding: 3px 10px;
  border-radius: 20px;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.role-badge.admin {
  background: rgba(99, 102, 241, 0.12);
  color: #818cf8;
  border: 1px solid rgba(99, 102, 241, 0.2);
}

.role-badge.user {
  background: rgba(255, 255, 255, 0.04);
  color: rgba(255, 255, 255, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.btn-sm {
  padding: 4px 12px;
  border-radius: 6px;
  font-size: 0.72rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.btn-sm.btn-approve {
  padding: 4px 12px;
}

.btn-credit {
  background: rgba(99, 102, 241, 0.1);
  border: 1px solid rgba(99, 102, 241, 0.2);
  color: #818cf8;
}

.btn-credit:hover {
  background: rgba(99, 102, 241, 0.18);
}

.btn-admin {
  background: rgba(245, 158, 11, 0.08);
  border: 1px solid rgba(245, 158, 11, 0.2);
  color: #fbbf24;
}

.btn-admin:hover:not(:disabled) {
  background: rgba(245, 158, 11, 0.15);
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 500;
  padding: 24px;
}

.modal-card {
  background: #18181b;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 28px;
  width: 100%;
  max-width: 420px;
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.5);
}

.modal-title {
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0 0 4px;
}

.modal-sub {
  font-size: 0.82rem;
  color: rgba(255, 255, 255, 0.4);
  margin: 0 0 20px;
}

.modal-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 16px;
}

.modal-field label {
  font-size: 0.8rem;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.55);
}

.modal-field input {
  width: 100%;
  padding: 10px 14px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  color: #f4f4f5;
  font-size: 0.88rem;
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
  justify-content: flex-end;
  margin-top: 24px;
}

.btn-cancel {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.6);
  padding: 8px 20px;
  border-radius: 10px;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel:hover {
  background: rgba(255, 255, 255, 0.08);
}

.btn-confirm {
  background: #6366f1;
  border: none;
  color: #fff;
  padding: 8px 24px;
  border-radius: 10px;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-confirm:hover:not(:disabled) {
  background: #5558e6;
  box-shadow: 0 0 20px rgba(99, 102, 241, 0.3);
}

.btn-confirm:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Responsive */
@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .admin-main {
    padding: 24px 16px 80px;
  }
  .header-inner {
    padding: 0 16px;
  }
}

@media (max-width: 480px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
