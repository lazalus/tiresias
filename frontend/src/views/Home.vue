<template>
  <div class="app-screen">
    <!-- Header -->
    <header class="app-header">
      <div class="header-inner">
        <div class="header-left">
          <img src="/logoss.png" alt="TIRESIAS VIEW" class="app-logo" />
          <span class="app-name">TIRESIAS VIEW</span>
        </div>
        <div class="header-right">
          <span v-if="credits !== null" class="header-credits">
            크레딧: {{ credits }}
          </span>
          <span class="header-status-dot"></span>
        </div>
      </div>
    </header>

    <main class="app-main">
      <!-- KPI Strip -->
      <div class="kpi-strip">
        <div class="kpi-item">
          <span class="kpi-value">{{ credits ?? '—' }}</span>
          <span class="kpi-label">잔여 크레딧</span>
        </div>
        <div class="kpi-divider"></div>
        <div class="kpi-item">
          <span class="kpi-value">{{ totalCompleted }}</span>
          <span class="kpi-label">완료</span>
        </div>
        <div class="kpi-divider"></div>
        <div class="kpi-item">
          <span class="kpi-value">{{ totalInProgress }}</span>
          <span class="kpi-label">진행중</span>
        </div>
      </div>

      <!-- New Simulation Card -->
      <div class="section-label">새 시뮬레이션</div>
      <div class="sim-card">
        <!-- File Upload -->
        <div class="card-section">
          <div class="section-header">
            <span class="section-title">분석 자료</span>
            <span class="section-meta">PDF, MD, TXT</span>
          </div>
          <div
            class="upload-area"
            :class="{ 'drag-over': isDragOver, 'has-files': files.length > 0 }"
            @dragover.prevent="handleDragOver"
            @dragleave.prevent="handleDragLeave"
            @drop.prevent="handleDrop"
            @click="triggerFileInput"
          >
            <input
              ref="fileInput"
              type="file"
              multiple
              accept=".pdf,.md,.txt"
              @change="handleFileSelect"
              style="display: none"
              :disabled="loading"
            />
            <div v-if="files.length === 0" class="upload-empty">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
                <polyline points="17 8 12 3 7 8"/>
                <line x1="12" y1="3" x2="12" y2="15"/>
              </svg>
              <span>문서를 업로드하세요</span>
            </div>
            <div v-else class="file-chips">
              <div v-for="(file, index) in files" :key="index" class="file-chip">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                </svg>
                <span class="chip-name">{{ file.name }}</span>
                <button @click.stop="removeFile(index)" class="chip-remove">
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                    <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Prompt -->
        <div class="card-section">
          <div class="section-header">
            <span class="section-title">예측 질문</span>
          </div>
          <textarea
            v-model="formData.simulationRequirement"
            class="prompt-input"
            placeholder="어떤 상황을 예측하고 싶으신가요?"
            rows="3"
            :disabled="loading"
          ></textarea>
        </div>

        <!-- Submit -->
        <button
          class="start-btn"
          @click="startSimulation"
          :disabled="!canSubmit || loading"
        >
          <span v-if="!loading">시뮬레이션 시작</span>
          <span v-else class="loading-state">
            <span class="spinner"></span>
            초기화 중...
          </span>
          <svg v-if="!loading" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M5 12h14M12 5l7 7-7 7"/>
          </svg>
        </button>
      </div>

      <!-- Recent Simulations -->
      <div v-if="recentProjects.length > 0" class="recent-section">
        <div class="section-label">최근 시뮬레이션</div>
        <div class="recent-list">
          <div
            v-for="project in recentProjects"
            :key="project.id"
            class="recent-item"
            @click="goToProject(project)"
          >
            <div class="recent-item-left">
              <span class="recent-item-title">{{ project.title || project.simulation_requirement?.slice(0, 30) || '제목 없음' }}</span>
              <span class="recent-item-date">{{ formatDate(project.created_at) }}</span>
            </div>
            <span
              class="status-badge"
              :class="statusClass(project.status)"
            >{{ statusLabel(project.status) }}</span>
          </div>
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
import BottomNav from '../components/BottomNav.vue'
import { getToken } from '../store/auth.js'

const router = useRouter()

const formData = ref({ simulationRequirement: '' })
const files = ref([])
const loading = ref(false)
const isDragOver = ref(false)
const fileInput = ref(null)
const credits = ref(null)
const recentProjects = ref([])

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

const totalCompleted = computed(() =>
  recentProjects.value.filter(p => p.status === 'completed' || p.status === 'done').length
)

const totalInProgress = computed(() =>
  recentProjects.value.filter(p => p.status === 'processing' || p.status === 'in_progress' || p.status === 'pending').length
)

const canSubmit = computed(() => {
  return formData.value.simulationRequirement.trim() !== '' && files.value.length > 0
})

const triggerFileInput = () => {
  if (!loading.value) fileInput.value?.click()
}

const handleFileSelect = (event) => {
  addFiles(Array.from(event.target.files))
}

const handleDragOver = () => {
  if (!loading.value) isDragOver.value = true
}

const handleDragLeave = () => {
  isDragOver.value = false
}

const handleDrop = (e) => {
  isDragOver.value = false
  if (loading.value) return
  addFiles(Array.from(e.dataTransfer.files))
}

const addFiles = (newFiles) => {
  const valid = newFiles.filter(f => ['pdf', 'md', 'txt'].includes(f.name.split('.').pop().toLowerCase()))
  files.value.push(...valid)
}

const removeFile = (index) => {
  files.value.splice(index, 1)
}

const startSimulation = () => {
  if (!canSubmit.value || loading.value) return
  import('../store/pendingUpload.js').then(({ setPendingUpload }) => {
    setPendingUpload(files.value, formData.value.simulationRequirement)
    router.push({ name: 'Process', params: { projectId: 'new' } })
  })
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getMonth() + 1}/${d.getDate()}`
}

const statusClass = (status) => {
  if (status === 'completed' || status === 'done') return 'badge-done'
  if (status === 'processing' || status === 'in_progress' || status === 'pending') return 'badge-progress'
  if (status === 'error' || status === 'failed') return 'badge-error'
  return 'badge-progress'
}

const statusLabel = (status) => {
  if (status === 'completed' || status === 'done') return '완료'
  if (status === 'processing' || status === 'in_progress' || status === 'pending') return '진행중'
  if (status === 'error' || status === 'failed') return '에러'
  return status || '—'
}

const goToProject = (project) => {
  if (project.id) {
    router.push({ name: 'Process', params: { projectId: project.id } })
  }
}

onMounted(async () => {
  const token = getToken()
  if (token) {
    try {
      const res = await axios.get(`${API_BASE}/api/payments/credits`, { headers: { Authorization: `Bearer ${token}` } })
      credits.value = res.data.credits
    } catch(e) {}

    try {
      const res = await axios.get(`${API_BASE}/api/projects`, { headers: { Authorization: `Bearer ${token}` } })
      recentProjects.value = (res.data.projects || []).slice(0, 5)
    } catch(e) {}
  }
})
</script>

<style scoped>
.app-screen {
  min-height: 100vh;
  background: var(--bg-primary);
  color: var(--text-primary);
  font-family: 'Inter', 'Noto Sans KR', system-ui, -apple-system, sans-serif;
  -webkit-font-smoothing: antialiased;
}

/* ── Header ── */
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

.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-credits {
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--text-secondary);
}

.header-status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #22c55e;
}

/* ── Main ── */
.app-main {
  max-width: 680px;
  margin: 0 auto;
  padding: 24px 24px 100px;
}

/* ── Section Label ── */
.section-label {
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-tertiary, var(--text-muted));
  margin-bottom: 10px;
}

/* ── KPI Strip ── */
.kpi-strip {
  display: flex;
  align-items: center;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 14px 0;
  margin-bottom: 28px;
}

.kpi-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.kpi-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1;
}

.kpi-label {
  font-size: 0.7rem;
  font-weight: 500;
  color: var(--text-muted);
  letter-spacing: 0.01em;
}

.kpi-divider {
  width: 1px;
  height: 28px;
  background: var(--border-color);
}

/* ── Simulation Card ── */
.sim-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 32px;
}

.card-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-title {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-secondary);
}

.section-meta {
  margin-left: auto;
  font-family: 'JetBrains Mono', 'SF Mono', monospace;
  font-size: 0.65rem;
  color: var(--text-muted);
}

/* ── Upload ── */
.upload-area {
  border: 1px dashed var(--border-color);
  border-radius: 10px;
  min-height: 72px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: border-color 0.2s;
  background: transparent;
}

.upload-area.has-files {
  align-items: flex-start;
  padding: 10px;
}

.upload-area:hover {
  border-color: var(--accent-color, #6366f1);
}

.upload-area.drag-over {
  border-color: var(--accent-color, #6366f1);
  background: rgba(99, 102, 241, 0.04);
}

.upload-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  color: var(--text-muted);
  font-size: 0.78rem;
  padding: 16px;
}

.file-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  width: 100%;
}

.file-chip {
  display: flex;
  align-items: center;
  gap: 6px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  padding: 5px 10px;
  font-size: 0.72rem;
  color: var(--text-secondary);
  font-family: 'JetBrains Mono', monospace;
  max-width: 100%;
  overflow: hidden;
  min-width: 0;
}

.chip-name {
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chip-remove {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 1px;
  display: flex;
  align-items: center;
  border-radius: 3px;
  transition: color 0.15s;
}

.chip-remove:hover {
  color: #ef4444;
}

/* ── Prompt ── */
.prompt-input {
  width: 100%;
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 10px 12px;
  font-family: inherit;
  font-size: 0.85rem;
  line-height: 1.5;
  color: var(--text-primary);
  resize: vertical;
  outline: none;
  min-height: 72px;
  transition: border-color 0.2s;
}

.prompt-input:focus {
  border-color: var(--accent-color, #6366f1);
}

.prompt-input::placeholder {
  color: var(--text-muted);
}

/* ── Start Button ── */
.start-btn {
  width: 100%;
  height: 40px;
  background: var(--accent-color, #6366f1);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.85rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  cursor: pointer;
  transition: opacity 0.15s;
}

.start-btn:hover:not(:disabled) {
  opacity: 0.9;
}

.start-btn:disabled {
  background: var(--bg-surface, var(--bg-secondary));
  color: var(--text-muted);
  cursor: not-allowed;
}

.loading-state {
  display: flex;
  align-items: center;
  gap: 6px;
}

.spinner {
  width: 13px;
  height: 13px;
  border: 2px solid rgba(255, 255, 255, 0.25);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ── Recent Simulations ── */
.recent-section {
  margin-top: 4px;
}

.recent-list {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  overflow: hidden;
}

.recent-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  cursor: pointer;
  transition: background 0.15s;
}

.recent-item:not(:last-child) {
  border-bottom: 1px solid var(--border-color);
}

.recent-item:hover {
  background: var(--bg-surface, rgba(0,0,0,0.02));
}

.recent-item-left {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.recent-item-title {
  font-size: 0.84rem;
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.recent-item-date {
  font-size: 0.7rem;
  color: var(--text-muted);
}

/* ── Status Badges ── */
.status-badge {
  font-size: 0.68rem;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 4px;
  white-space: nowrap;
  flex-shrink: 0;
}

.badge-done {
  color: #16a34a;
  background: rgba(22, 163, 74, 0.1);
}

.badge-progress {
  color: #6366f1;
  background: rgba(99, 102, 241, 0.1);
}

.badge-error {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
}

/* ── Responsive ── */
@media (max-width: 640px) {
  .app-main {
    padding: 20px 16px 100px;
  }

  .header-inner {
    padding: 0 16px;
  }
}
</style>
