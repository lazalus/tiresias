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
      <h1 class="page-title">히스토리</h1>

      <!-- Loading -->
      <div v-if="loading" class="loading-state">
        <span class="spinner"></span>
        <span>불러오는 중...</span>
      </div>

      <!-- Empty State -->
      <div v-else-if="projects.length === 0" class="empty-state">
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"/>
          <polyline points="12 6 12 12 16 14"/>
        </svg>
        <p>아직 시뮬레이션 기록이 없습니다.</p>
        <router-link to="/" class="empty-link">새 시뮬레이션 시작하기</router-link>
      </div>

      <!-- Project List -->
      <div v-else class="project-list">
        <div
          v-for="project in projects"
          :key="project.id"
          class="project-item"
          @click="goToProject(project)"
        >
          <div class="project-top">
            <span class="project-name">{{ project.name || project.title || '프로젝트' }}</span>
            <span class="project-status" :class="project.status || 'unknown'">
              {{ statusLabel(project.status) }}
            </span>
          </div>
          <div class="project-bottom">
            <span class="project-date">{{ formatDate(project.created_at) }}</span>
            <span v-if="project.rounds" class="project-rounds">{{ project.rounds }} 라운드</span>
          </div>
        </div>
      </div>
    </main>

    <BottomNav />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { getToken } from '../store/auth.js'
import BottomNav from '../components/BottomNav.vue'

const router = useRouter()
const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

const projects = ref([])
const loading = ref(true)

onMounted(async () => {
  try {
    const res = await axios.get(`${API_BASE}/api/projects`, {
      headers: { Authorization: `Bearer ${getToken()}` }
    })
    projects.value = res.data.projects || res.data || []
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
    pending: '대기',
    running: '진행 중',
    completed: '완료',
    failed: '실패'
  }
  return labels[status] || status || '-'
}

function formatDate(d) {
  if (!d) return '-'
  return new Date(d).toLocaleDateString('ko-KR', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit'
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
  margin: 0 0 32px;
}

/* Loading */
.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 60px 0;
  color: rgba(255, 255, 255, 0.4);
  font-size: 0.88rem;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.15);
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
  color: rgba(255, 255, 255, 0.25);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.empty-state p {
  font-size: 0.9rem;
  margin: 0;
}

.empty-link {
  color: #818cf8;
  text-decoration: none;
  font-size: 0.85rem;
  font-weight: 500;
  padding: 8px 20px;
  border: 1px solid rgba(99, 102, 241, 0.3);
  border-radius: 10px;
  transition: all 0.2s;
}

.empty-link:hover {
  background: rgba(99, 102, 241, 0.1);
  border-color: rgba(99, 102, 241, 0.5);
}

/* Project List */
.project-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.project-item {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 14px;
  padding: 18px 20px;
  cursor: pointer;
  transition: all 0.2s;
}

.project-item:hover {
  border-color: rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.05);
}

.project-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.project-name {
  font-size: 0.92rem;
  font-weight: 600;
  letter-spacing: -0.01em;
}

.project-status {
  font-size: 0.72rem;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 20px;
  letter-spacing: 0.02em;
}

.project-status.completed {
  background: rgba(34, 197, 94, 0.1);
  color: #4ade80;
}

.project-status.running {
  background: rgba(99, 102, 241, 0.1);
  color: #818cf8;
}

.project-status.pending {
  background: rgba(245, 158, 11, 0.1);
  color: #fbbf24;
}

.project-status.failed {
  background: rgba(239, 68, 68, 0.1);
  color: #f87171;
}

.project-status.unknown {
  background: rgba(255, 255, 255, 0.04);
  color: rgba(255, 255, 255, 0.3);
}

.project-bottom {
  display: flex;
  align-items: center;
  gap: 16px;
}

.project-date {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.25);
}

.project-rounds {
  font-size: 0.78rem;
  color: rgba(255, 255, 255, 0.35);
  font-weight: 500;
}

/* Responsive */
@media (max-width: 640px) {
  .history-main {
    padding: 32px 16px 80px;
  }
  .page-title {
    font-size: 1.3rem;
  }
}
</style>
