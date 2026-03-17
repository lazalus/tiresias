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

    <main class="history-main">
      <h1 class="page-title">보고서</h1>

      <!-- Search & Filter Bar -->
      <div class="toolbar">
        <div class="search-wrap">
          <svg class="search-icon" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/>
          </svg>
          <input
            v-model="searchQuery"
            type="text"
            class="search-input"
            placeholder="프로젝트 검색..."
          />
        </div>
        <div class="filter-pills">
          <button
            v-for="f in filters"
            :key="f.value"
            class="filter-pill"
            :class="{ active: activeFilter === f.value }"
            @click="activeFilter = f.value"
          >{{ f.label }}</button>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="loading-state">
        <span class="spinner"></span>
        <span>불러오는 중...</span>
      </div>

      <!-- Empty State -->
      <div v-else-if="filteredProjects.length === 0 && projects.length === 0" class="empty-state">
        <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
          <polyline points="14 2 14 8 20 8"/>
        </svg>
        <p>아직 시뮬레이션이 없습니다.</p>
        <p class="empty-sub">홈에서 새 시뮬레이션을 시작하세요.</p>
        <router-link to="/" class="empty-link">새 시뮬레이션 시작</router-link>
      </div>

      <!-- No Results for Filter -->
      <div v-else-if="filteredProjects.length === 0" class="empty-state">
        <p>검색 결과가 없습니다.</p>
      </div>

      <!-- Project List -->
      <div v-else class="project-list">
        <!-- Table Header -->
        <div class="list-header">
          <span class="col-name">프로젝트</span>
          <span class="col-status">상태</span>
          <span class="col-date">날짜</span>
          <span class="col-files">파일</span>
        </div>

        <!-- Rows -->
        <div
          v-for="project in filteredProjects"
          :key="project.id"
          class="list-row"
          @click="goToProject(project)"
        >
          <span class="col-name row-name">{{ project.name || project.title || '프로젝트' }}</span>
          <span class="col-status">
            <span class="status-badge" :class="statusClass(project.status)">
              {{ statusLabel(project.status) }}
            </span>
          </span>
          <span class="col-date row-date">{{ formatDate(project.created_at) }}</span>
          <span class="col-files row-files">{{ project.file_count || project.rounds || '-' }}</span>
        </div>
      </div>
    </main>

    <BottomNav />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { getToken } from '../store/auth.js'
import BottomNav from '../components/BottomNav.vue'

const router = useRouter()
const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

const projects = ref([])
const loading = ref(true)
const searchQuery = ref('')
const activeFilter = ref('all')

const filters = [
  { label: '전체', value: 'all' },
  { label: '진행중', value: 'running' },
  { label: '완료', value: 'completed' },
  { label: '에러', value: 'failed' }
]

const filteredProjects = computed(() => {
  let list = projects.value
  if (activeFilter.value !== 'all') {
    list = list.filter(p => p.status === activeFilter.value)
  }
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase()
    list = list.filter(p =>
      (p.name || p.title || '').toLowerCase().includes(q)
    )
  }
  return list
})

onMounted(async () => {
  try {
    const token = getToken()
    if (token) {
      const res = await axios.get(`${API_BASE}/api/projects`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      projects.value = res.data.projects || []
    }
  } catch (e) {
    console.error('Failed to fetch projects:', e)
  } finally {
    loading.value = false
  }
})

function goToProject(project) {
  router.push({ name: 'Process', params: { projectId: project.id } })
}

function statusLabel(status) {
  const labels = {
    pending: '생성됨',
    created: '생성됨',
    running: '진행중',
    completed: '완료',
    failed: '에러'
  }
  return labels[status] || status || '-'
}

function statusClass(status) {
  const map = {
    pending: 'badge-gray',
    created: 'badge-gray',
    running: 'badge-indigo',
    completed: 'badge-green',
    failed: 'badge-red'
  }
  return map[status] || 'badge-gray'
}

function formatDate(d) {
  if (!d) return '-'
  const date = new Date(d)
  const now = new Date()
  const diffMs = now - date
  const diffMin = Math.floor(diffMs / 60000)
  const diffHr = Math.floor(diffMs / 3600000)
  const diffDay = Math.floor(diffMs / 86400000)

  if (diffMin < 1) return '방금 전'
  if (diffMin < 60) return `${diffMin}분 전`
  if (diffHr < 24) return `${diffHr}시간 전`
  if (diffDay < 7) return `${diffDay}일 전`

  return date.toLocaleDateString('ko-KR', {
    month: 'short', day: 'numeric'
  })
}
</script>

<style scoped>
.app-screen {
  min-height: 100vh;
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
.history-main {
  max-width: 680px;
  margin: 0 auto;
  padding: 48px 24px 80px;
}

.page-title {
  font-size: 1.5rem;
  font-weight: 700;
  letter-spacing: -0.025em;
  margin: 0 0 24px;
}

/* Toolbar */
.toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
}

.search-wrap {
  position: relative;
  flex: 1;
}

.search-icon {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-muted);
  pointer-events: none;
}

.search-input {
  width: 100%;
  height: 36px;
  background: var(--surface, var(--bg-secondary));
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 0 12px 0 32px;
  font-family: inherit;
  font-size: 0.8rem;
  color: var(--text-primary);
  outline: none;
  transition: border-color 0.15s;
}

.search-input::placeholder {
  color: var(--text-muted);
}

.search-input:focus {
  border-color: rgba(99, 102, 241, 0.4);
}

.filter-pills {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

.filter-pill {
  background: none;
  border: 1px solid var(--border-color);
  border-radius: 100px;
  padding: 5px 12px;
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s;
  font-family: inherit;
  white-space: nowrap;
}

.filter-pill:hover {
  background: var(--bg-secondary);
}

.filter-pill.active {
  background: var(--text-primary);
  color: var(--bg-primary);
  border-color: var(--text-primary);
}

/* Loading */
.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 60px 0;
  color: var(--text-secondary);
  font-size: 0.85rem;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid var(--border-color);
  border-top-color: #818cf8;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-muted);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.empty-state p {
  font-size: 0.85rem;
  margin: 0;
}

.empty-sub {
  font-size: 0.8rem !important;
  color: var(--text-muted);
}

.empty-link {
  margin-top: 8px;
  color: #6366f1;
  text-decoration: none;
  font-size: 0.8rem;
  font-weight: 500;
  padding: 6px 16px;
  border: 1px solid rgba(99, 102, 241, 0.25);
  border-radius: 8px;
  transition: all 0.15s;
}

.empty-link:hover {
  background: rgba(99, 102, 241, 0.08);
  border-color: rgba(99, 102, 241, 0.4);
}

/* List Header */
.list-header {
  display: grid;
  grid-template-columns: 1fr 80px 80px 48px;
  gap: 12px;
  padding: 0 16px 10px;
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
  border-bottom: 1px solid var(--border-color);
}

/* List Rows */
.project-list {
  display: flex;
  flex-direction: column;
}

.list-row {
  display: grid;
  grid-template-columns: 1fr 80px 80px 48px;
  gap: 12px;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
  cursor: pointer;
  transition: background 0.12s;
}

.list-row:hover {
  background: var(--bg-secondary);
}

.list-row:last-child {
  border-bottom: none;
}

.row-name {
  font-size: 0.85rem;
  font-weight: 500;
  letter-spacing: -0.01em;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Status Badges */
.status-badge {
  display: inline-block;
  font-size: 0.7rem;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
  letter-spacing: 0.01em;
  white-space: nowrap;
}

.badge-indigo {
  background: rgba(99, 102, 241, 0.12);
  color: #6366f1;
}

.badge-green {
  background: rgba(34, 197, 94, 0.12);
  color: #16a34a;
}

.badge-red {
  background: rgba(239, 68, 68, 0.12);
  color: #dc2626;
}

.badge-gray {
  background: var(--bg-surface, var(--bg-secondary));
  color: var(--text-muted);
}

.row-date {
  font-size: 0.8rem;
  color: var(--text-muted);
  white-space: nowrap;
}

.row-files {
  font-size: 0.8rem;
  color: var(--text-muted);
  text-align: center;
  font-family: 'JetBrains Mono', monospace;
}

/* Responsive */
@media (max-width: 640px) {
  .history-main {
    padding: 32px 16px 80px;
  }
  .page-title {
    font-size: 1.3rem;
  }
  .toolbar {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }
  .filter-pills {
    overflow-x: auto;
  }
  .list-header {
    grid-template-columns: 1fr 72px 72px 40px;
    gap: 8px;
    padding: 0 12px 10px;
  }
  .list-row {
    grid-template-columns: 1fr 72px 72px 40px;
    gap: 8px;
    padding: 10px 12px;
  }
}
</style>
