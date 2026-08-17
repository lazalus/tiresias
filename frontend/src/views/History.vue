<template>
  <div class="app-screen">
    <!-- App Header -->
    <header class="app-header">
      <div class="header-inner">
        <div class="header-left">
          <router-link to="/dashboard" class="header-home">
            <span class="app-name">TIRESIAS VIEW</span>
          </router-link>
        </div>
        <HeaderNav />
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
        <router-link to="/dashboard" class="empty-link">새 시뮬레이션 시작</router-link>
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
          <span class="col-action"></span>
        </div>

        <!-- Rows -->
        <div
          v-for="project in filteredProjects"
          :key="project.id"
          class="list-row"
          @click="goToProject(project)"
          @touchstart.passive="startLongPress(project, $event)"
          @touchend="cancelLongPress"
          @touchmove="cancelLongPress"
          @contextmenu.prevent="showContextMenu(project)"
        >
          <span class="col-name row-name">{{ project.name || project.title || '프로젝트' }}</span>
          <span class="col-status">
            <span class="status-badge" :class="statusClass(project)">
              {{ statusLabel(project) }}
            </span>
          </span>
          <span class="col-date row-date">{{ formatDate(project.created_at || project.createdAt) }}</span>
          <span class="col-action" v-if="isReportCompletedProject(project) && project.report_id" @click.stop="downloadReportPDF(project)">
            <span v-if="downloadingPDF === project.id" class="dl-spinner"></span>
            <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          </span>
        </div>
      </div>
    </main>

    <BottomNav />

    <!-- 컨텍스트 메뉴 -->
    <Teleport to="body">
      <div v-if="contextMenu.show" class="context-overlay" @click="closeContextMenu">
        <div class="context-menu" @click.stop>
          <div class="context-title">{{ contextMenu.project?.name || '프로젝트' }}</div>
          <button class="context-item" @click="viewProject">상세보기</button>
          <button class="context-item context-item--danger" @click="deleteFromMenu">삭제</button>
          <button class="context-item context-item--cancel" @click="closeContextMenu">취소</button>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { currentUser, buildAuthAxiosConfig } from '../store/auth.js'
import BottomNav from '../components/BottomNav.vue'
import HeaderNav from '../components/HeaderNav.vue'
import { tryDownloadReportPdf } from '../utils/pdfPayment.js'
import {
  getProjectFilterGroup,
  getProjectStatusLabel,
  isReportCompletedProject,
  isSimulationRunningProject,
  normalizeProjectRecord,
} from '../utils/projectStatus.js'

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
    list = list.filter((project) => {
      const group = getProjectFilterGroup(project.status, { reportId: project.report_id || null })
      if (activeFilter.value === 'running') return group === 'running'
      if (activeFilter.value === 'completed') return group === 'completed'
      if (activeFilter.value === 'failed') return group === 'failed'
      return true
    })
  }
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase()
    list = list.filter(p =>
      (p.name || p.title || '').toLowerCase().includes(q)
    )
  }
  return list
})

async function fetchProjects() {
  try {
    const res = await axios.get(`${API_BASE}/api/projects`, buildAuthAxiosConfig())
    projects.value = (res.data.projects || []).map(normalizeProjectRecord)
  } catch (e) {
    console.error('Failed to fetch projects:', e)
  } finally {
    loading.value = false
  }
}

const handleProjectsChanged = () => {
  fetchProjects()
}

const handleHistoryVisibilityChange = () => {
  if (document.visibilityState === 'visible') {
    fetchProjects()
  }
}

onMounted(async () => {
  await fetchProjects()
  window.addEventListener('focus', handleProjectsChanged)
  window.addEventListener('tiresias:projects-changed', handleProjectsChanged)
  document.addEventListener('visibilitychange', handleHistoryVisibilityChange)
})

onUnmounted(() => {
  window.removeEventListener('focus', handleProjectsChanged)
  window.removeEventListener('tiresias:projects-changed', handleProjectsChanged)
  document.removeEventListener('visibilitychange', handleHistoryVisibilityChange)
})

// 컨텍스트 메뉴
const contextMenu = ref({ show: false, project: null })
let longPressTimer = null

function goToProject(project) {
  if (contextMenu.value.show) return
  if (isReportCompletedProject(project)) {
    router.push({ name: 'Process', params: { projectId: project.id } })
  } else if (isSimulationRunningProject(project) && project.simulation_id) {
    router.push({ name: 'SimulationRun', params: { simulationId: project.simulation_id } })
  } else {
    // 진행 중/실패/준비 상태는 Process에서 백엔드 실제 상태를 다시 확인한다
    router.push({ name: 'Process', params: { projectId: project.id } })
  }
}

function startLongPress(project, e) {
  longPressTimer = setTimeout(() => {
    // 롱프레스 시 텍스트 선택/드래그 방지
    window.getSelection()?.removeAllRanges()
    showContextMenu(project)
  }, 500)
}

function cancelLongPress() {
  if (longPressTimer) { clearTimeout(longPressTimer); longPressTimer = null }
}

function showContextMenu(project) {
  cancelLongPress()
  contextMenu.value = { show: true, project }
}

function closeContextMenu() {
  contextMenu.value = { show: false, project: null }
}

function viewProject() {
  const project = contextMenu.value.project
  closeContextMenu()
  if (project) router.push({ name: 'Process', params: { projectId: project.id } })
}

async function deleteFromMenu() {
  const project = contextMenu.value.project
  if (!project) return
  closeContextMenu()
  if (!confirm(`"${project.name || '프로젝트'}"를 삭제하시겠습니까?`)) return
  try {
    await axios.delete(`${API_BASE}/api/projects/${project.id}`, buildAuthAxiosConfig())
    projects.value = projects.value.filter(p => p.id !== project.id)
    window.dispatchEvent(new CustomEvent('tiresias:projects-changed'))
  } catch (e) {
    alert('삭제 실패: ' + (e.response?.data?.error || e.message))
  }
}

function mdToHtml(text) {
  if (!text) return ''
  return text
    .replace(/### (.*)/g, '<h4 style="font-size:14px;font-weight:600;margin:12px 0 6px;color:#333;">$1</h4>')
    .replace(/## (.*)/g, '<h3 style="font-size:15px;font-weight:600;margin:14px 0 8px;color:#333;">$1</h3>')
    .replace(/# (.*)/g, '<h2 style="font-size:16px;font-weight:700;margin:16px 0 8px;color:#222;">$1</h2>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/^- (.*)/gm, '<li style="margin-bottom:4px;">$1</li>')
    .replace(/(<li[^>]*>.*<\/li>\n?)+/g, '<ul style="padding-left:20px;margin:8px 0;">$&</ul>')
    .replace(/\n\n/g, '<br/><br/>')
    .replace(/\n/g, '<br/>')
}

const downloadingPDF = ref(null)

async function downloadReportPDF(project) {
  if (downloadingPDF.value === project.id) return

  downloadingPDF.value = project.id
  try {
    const downloadResult = await tryDownloadReportPdf({
      apiBase: API_BASE,
      reportId: project.report_id,
      fileName: project.name || project.title || '보고서',
    })

    if (downloadResult.downloaded) {
      return
    }

    throw new Error(downloadResult.errorData?.error || 'PDF 다운로드에 실패했습니다.')
  } catch (e) {
    if (e?.code !== 'USER_CANCEL') {
      alert('PDF 다운로드 실패: ' + (e.response?.data?.error || e.message))
    }
  } finally {
    downloadingPDF.value = null
  }
}

function statusLabel(project) {
  return getProjectStatusLabel(project?.status, { reportId: project?.report_id || null })
}

function statusClass(project) {
  const group = getProjectFilterGroup(project?.status, { reportId: project?.report_id || null })
  if (group === 'completed') return 'badge-green'
  if (group === 'failed') return 'badge-red'
  if (group === 'running') return 'badge-indigo'
  return 'badge-gray'
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
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border-color);
}

.header-inner {
  max-width: 680px;
  margin: 0 auto;
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-home {
  display: flex;
  align-items: center;
  gap: 12px;
  text-decoration: none;
  color: inherit;
}

.app-logo {
  width: 26px;
  height: 26px;
  border-radius: 6px;
  object-fit: cover;
}

.app-name {
  font-family: 'Outfit', sans-serif;
  font-weight: 700;
  letter-spacing: 0.08em;
  font-size: 0.82rem;
  color: var(--text-primary);
}

/* Main */
.history-main {
  max-width: 680px;
  margin: 0 auto;
  padding: 48px 24px 80px;
}

.page-title {
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-secondary);
  margin: 0 0 16px;
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
.col-action {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  cursor: pointer;
  transition: color 0.15s;
}

.col-action:hover {
  color: #6366f1;
}

.list-header {
  display: grid;
  grid-template-columns: 1fr 72px 72px 36px;
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
  grid-template-columns: 1fr 72px 72px 36px;
  gap: 12px;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
  cursor: pointer;
  transition: background 0.12s;
  -webkit-user-select: none;
  user-select: none;
  -webkit-touch-callout: none;
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

/* Context Menu */
.context-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  z-index: 500;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.context-menu {
  width: 100%;
  max-width: 400px;
  background: var(--bg-secondary);
  border-radius: 14px 14px 0 0;
  padding: 8px 0 env(safe-area-inset-bottom, 8px);
  box-shadow: 0 -4px 24px rgba(0, 0, 0, 0.15);
}

.context-title {
  padding: 14px 20px 8px;
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--text-secondary);
  border-bottom: 1px solid var(--border-color);
}

.context-item {
  display: block;
  width: 100%;
  padding: 14px 20px;
  background: none;
  border: none;
  text-align: left;
  font-size: 0.85rem;
  font-family: inherit;
  color: var(--text-primary);
  cursor: pointer;
  transition: background 0.15s;
}

.context-item:hover {
  background: var(--surface-hover);
}

.context-item--danger {
  color: #ef4444;
}

.context-item--cancel {
  color: var(--text-muted);
  border-top: 1px solid var(--border-color);
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
    grid-template-columns: 1fr 60px 60px 32px;
    gap: 6px;
    padding: 0 12px 10px;
  }
  .list-row {
    grid-template-columns: 1fr 60px 60px 32px;
    gap: 8px;
    padding: 10px 12px;
  }
}

/* Desktop */
@media (min-width: 1024px) {
  .app-header {
    background: var(--header-bg);
    backdrop-filter: saturate(180%) blur(20px);
    -webkit-backdrop-filter: saturate(180%) blur(20px);
  }

  .header-inner {
    max-width: 1200px;
    height: 60px;
    padding: 0 40px;
  }

  .app-name {
    font-size: 0.9rem;
  }

  .history-main {
    max-width: 1080px;
    padding: 48px 40px 60px;
  }

  .page-title {
    font-size: 1.6rem;
  }

  .list-header,
  .list-row {
    padding-left: 20px;
    padding-right: 20px;
  }

  .list-row:hover {
    background: var(--surface-hover);
  }
}

.dl-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid var(--border-color);
  border-top-color: var(--accent-color, #6366f1);
  border-radius: 50%;
  animation: dlSpin 0.6s linear infinite;
  display: inline-block;
}

@keyframes dlSpin { to { transform: rotate(360deg); } }
</style>
