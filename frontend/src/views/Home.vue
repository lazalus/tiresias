<template>
  <div class="app-screen">
    <!-- App Header -->
    <header class="app-header">
      <div class="header-inner">
        <div class="header-left">
          <img src="/logoss.png" alt="Tiresias View" class="app-logo" />
          <span class="app-name">Tiresias View</span>
        </div>
        <div class="header-right">
        </div>
      </div>
    </header>

    <main class="app-main">
      <!-- Greeting -->
      <div class="greeting">
        <h1 class="greeting-title">
          새로운 시뮬레이션
        </h1>
        <p class="greeting-sub">데이터를 업로드하고 예측 요구사항을 입력하면 AI 에이전트가 병렬 세계를 구축합니다.</p>
      </div>

      <!-- Input Card -->
      <div class="input-card">
        <!-- File Upload -->
        <div class="card-section">
          <div class="section-header">
            <span class="section-num">01</span>
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
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
                <polyline points="17 8 12 3 7 8"/>
                <line x1="12" y1="3" x2="12" y2="15"/>
              </svg>
              <span>보고서, 기사, 논문 등 분석할 문서를 업로드하세요</span>
            </div>
            <div v-else class="file-chips">
              <div v-for="(file, index) in files" :key="index" class="file-chip">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                </svg>
                <span class="chip-name">{{ file.name }}</span>
                <button @click.stop="removeFile(index)" class="chip-remove">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                    <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>

        <div class="card-divider"></div>

        <!-- Prompt -->
        <div class="card-section">
          <div class="section-header">
            <span class="section-num">02</span>
            <span class="section-title">예측 질문</span>
          </div>
          <textarea
            v-model="formData.simulationRequirement"
            class="prompt-input"
            placeholder="어떤 상황을 예측하고 싶으신가요? (예: A 기업이 신제품을 출시하면 시장 반응은 어떨까요?)"
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
          <svg v-if="!loading" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M5 12h14M12 5l7 7-7 7"/>
          </svg>
        </button>
      </div>

      <!-- History -->
      <HistoryDatabase />
    </main>

    <BottomNav />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import HistoryDatabase from '../components/HistoryDatabase.vue'
import BottomNav from '../components/BottomNav.vue'

const router = useRouter()

const formData = ref({ simulationRequirement: '' })
const files = ref([])
const loading = ref(false)
const isDragOver = ref(false)
const fileInput = ref(null)

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
</script>

<style scoped>
.app-screen {
  min-height: 100vh;
  background: #0c0a15;
  color: #fafafa;
  font-family: 'Inter', 'Noto Sans KR', system-ui, -apple-system, sans-serif;
  -webkit-font-smoothing: antialiased;
}

/* ── Header ── */
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

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* ── Main ── */
.app-main {
  max-width: 680px;
  margin: 0 auto;
  padding: 48px 24px 80px;
}

/* ── Greeting ── */
.greeting {
  margin-bottom: 32px;
}

.greeting-title {
  font-size: 1.5rem;
  font-weight: 700;
  letter-spacing: -0.025em;
  margin: 0 0 8px;
}

.greeting-sub {
  font-size: 0.88rem;
  color: rgba(255, 255, 255, 0.38);
  line-height: 1.6;
  margin: 0;
}

/* ── Input Card ── */
.input-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 16px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-bottom: 48px;
  transition: border-color 0.3s;
}

.input-card:hover {
  border-color: rgba(255, 255, 255, 0.1);
}

.card-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.section-num {
  font-family: 'JetBrains Mono', 'SF Mono', monospace;
  font-size: 0.68rem;
  font-weight: 600;
  color: #818cf8;
  letter-spacing: 0.02em;
}

.section-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.7);
  letter-spacing: -0.01em;
}

.section-meta {
  margin-left: auto;
  font-family: 'JetBrains Mono', 'SF Mono', monospace;
  font-size: 0.68rem;
  color: rgba(255, 255, 255, 0.2);
}

.card-divider {
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.06), transparent);
}

/* ── Upload ── */
.upload-area {
  border: 1px dashed rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  min-height: 96px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.25s ease;
  background: rgba(255, 255, 255, 0.015);
}

.upload-area.has-files {
  align-items: flex-start;
  padding: 12px;
}

.upload-area:hover {
  border-color: rgba(99, 102, 241, 0.3);
  background: rgba(99, 102, 241, 0.03);
}

.upload-area.drag-over {
  border-color: #6366f1;
  background: rgba(99, 102, 241, 0.06);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.upload-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  color: rgba(255, 255, 255, 0.22);
  font-size: 0.82rem;
  padding: 20px;
}

.file-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  width: 100%;
}

.file-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 0.78rem;
  color: rgba(255, 255, 255, 0.6);
  font-family: 'JetBrains Mono', monospace;
  transition: border-color 0.2s;
}

.file-chip:hover {
  border-color: rgba(255, 255, 255, 0.15);
}

.chip-name {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chip-remove {
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.25);
  cursor: pointer;
  padding: 2px;
  display: flex;
  align-items: center;
  border-radius: 4px;
  transition: all 0.15s;
}

.chip-remove:hover {
  color: #f87171;
  background: rgba(248, 113, 113, 0.1);
}

/* ── Prompt ── */
.prompt-input {
  width: 100%;
  background: rgba(255, 255, 255, 0.025);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 14px 16px;
  font-family: inherit;
  font-size: 0.88rem;
  line-height: 1.6;
  color: #fafafa;
  resize: vertical;
  outline: none;
  min-height: 88px;
  transition: border-color 0.25s, box-shadow 0.25s;
}

.prompt-input:focus {
  border-color: rgba(99, 102, 241, 0.4);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.08);
}

.prompt-input::placeholder {
  color: rgba(255, 255, 255, 0.18);
}

/* ── Start Button ── */
.start-btn {
  width: 100%;
  background: #6366f1;
  color: #fff;
  border: none;
  padding: 14px 20px;
  border-radius: 12px;
  font-weight: 600;
  font-size: 0.9rem;
  letter-spacing: -0.01em;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  cursor: pointer;
  transition: all 0.25s ease;
  position: relative;
  overflow: hidden;
}

.start-btn::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, transparent 50%);
  opacity: 0;
  transition: opacity 0.25s;
}

.start-btn:hover:not(:disabled) {
  background: #5558e6;
  transform: translateY(-1px);
  box-shadow: 0 8px 32px rgba(99, 102, 241, 0.25), 0 0 0 1px rgba(99, 102, 241, 0.3);
}

.start-btn:hover:not(:disabled)::before {
  opacity: 1;
}

.start-btn:active:not(:disabled) {
  transform: translateY(0);
}

.start-btn:disabled {
  background: rgba(255, 255, 255, 0.04);
  color: rgba(255, 255, 255, 0.18);
  cursor: not-allowed;
  box-shadow: none;
}

.loading-state {
  display: flex;
  align-items: center;
  gap: 8px;
}

.spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.25);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ── Responsive ── */
@media (max-width: 640px) {
  .app-main {
    padding: 32px 16px 80px;
  }

  .greeting-title {
    font-size: 1.3rem;
  }

  .header-inner {
    padding: 0 16px;
  }
}
</style>
