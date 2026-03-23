<template>
  <div class="sample-page">
    <header class="sample-header">
      <button class="back-btn" @click="goBack">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="15 18 9 12 15 6" />
        </svg>
      </button>
      <div class="header-copy">
        <span class="header-kicker">샘플 보고서</span>
        <h1 class="header-title">공개 샘플 보고서</h1>
      </div>
    </header>

    <main class="sample-main">
      <div v-if="loading" class="state-card">불러오는 중...</div>
      <div v-else-if="error" class="state-card state-card--error">{{ error }}</div>
      <article v-else-if="report" class="report-card">
        <!-- 입력 정보 -->
        <div v-if="report.requirement || (report.files && report.files.length)" class="input-info">
          <div class="input-label">시뮬레이션 입력</div>
          <div v-if="report.requirement" class="input-requirement">
            <span class="input-key">주제</span>
            <span class="input-value">{{ report.requirement }}</span>
          </div>
          <div v-if="report.files && report.files.length" class="input-files">
            <span class="input-key">자료</span>
            <div class="input-file-chips">
              <span v-for="(f, i) in report.files" :key="i" class="input-file-chip">{{ f }}</span>
            </div>
          </div>
        </div>

        <div class="report-actions">
          <button class="download-btn" @click="downloadSamplePdf">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            PDF 다운로드
          </button>
        </div>
        <ReportReader
          :title="report.title || '샘플 보고서'"
          :summary="report.summary || ''"
          :report-id="report.id"
          :sections="report.sections || []"
        />
      </article>
      <div v-else class="state-card">보고서를 찾을 수 없습니다.</div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import ReportReader from '../components/ReportReader.vue'

const route = useRoute()
const router = useRouter()
const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

const loading = ref(true)
const error = ref('')
const report = ref(null)

function ensureMeta(selector, attrs) {
  let el = document.head.querySelector(selector)
  if (!el) {
    el = document.createElement('meta')
    Object.entries(attrs).forEach(([key, value]) => el.setAttribute(key, value))
    document.head.appendChild(el)
  }
  return el
}

function ensureCanonicalLink() {
  let link = document.head.querySelector('link[rel="canonical"]')
  if (!link) {
    link = document.createElement('link')
    link.setAttribute('rel', 'canonical')
    document.head.appendChild(link)
  }
  return link
}

onMounted(async () => {
  try {
    const res = await axios.get(`${API_BASE}/api/reports/samples/${route.params.reportId}`)
    report.value = res.data.report || null
    if (report.value) {
      const title = `${report.value.title || '공개 샘플 보고서'} | Tiresias View`
      const description = report.value.summary || report.value.requirement || 'Tiresias View 공개 샘플 보고서'
      document.title = title
      ensureMeta('meta[name="description"]', { name: 'description' }).setAttribute('content', description)
      ensureMeta('meta[property="og:title"]', { property: 'og:title' }).setAttribute('content', title)
      ensureMeta('meta[property="og:description"]', { property: 'og:description' }).setAttribute('content', description)
      ensureMeta('meta[property="og:url"]', { property: 'og:url' }).setAttribute('content', `https://tiresiasview.com/samples/${encodeURIComponent(route.params.reportId)}`)
      ensureMeta('meta[name="robots"]', { name: 'robots' }).setAttribute('content', 'index,follow')
      ensureCanonicalLink().setAttribute('href', `https://tiresiasview.com/samples/${encodeURIComponent(route.params.reportId)}`)
    }
  } catch (err) {
    error.value = err.response?.data?.error || err.message || '보고서를 불러오지 못했습니다.'
  } finally {
    loading.value = false
  }
})

onUnmounted(() => {
  document.title = '테이레시아스 뷰 - 보고서 기반 예측 시뮬레이션'
})

function goBack() {
  if (window.history.length > 1) {
    router.back()
    return
  }
  router.push('/samples')
}

function downloadSamplePdf() {
  window.location.assign(`${API_BASE}/api/reports/samples/${encodeURIComponent(route.params.reportId)}/pdf`)
}

</script>

<style scoped>
.sample-page {
  min-height: 100vh;
  background: var(--bg-primary);
  color: var(--text-primary);
}

.sample-header {
  max-width: 760px;
  margin: 0 auto;
  padding: 20px 20px 0;
  display: flex;
  gap: 14px;
  align-items: flex-start;
}

.back-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  border-radius: 10px;
  color: var(--text-primary);
  text-decoration: none;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
}

.header-copy {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.header-kicker {
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-secondary);
}

.header-title {
  margin: 0;
  font-size: 1.4rem;
}

.sample-main {
  max-width: 760px;
  margin: 0 auto;
  padding: 20px 20px 56px;
}

.state-card,
.report-card {
  border: 1px solid var(--border-color);
  border-radius: 18px;
  background: var(--bg-secondary);
}

.state-card {
  padding: 24px;
  color: var(--text-secondary);
}

.state-card--error {
  color: #dc2626;
}

.report-card {
  padding: 28px 24px;
}

.report-meta {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.report-actions {
  margin-top: 12px;
  margin-bottom: 8px;
}

.download-btn {
  appearance: none;
  border: 1px solid var(--border-color);
  background: var(--bg-surface);
  color: var(--text-primary);
  font-size: 0.82rem;
  font-weight: 600;
  font-family: inherit;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 8px;
  transition: background 0.15s, border-color 0.15s;
}

.download-btn:hover {
  background: var(--bg-tertiary, var(--bg-secondary));
  border-color: var(--text-secondary);
}

.report-tag {
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.report-title {
  margin: 16px 0 10px;
  font-size: 1.8rem;
  line-height: 1.15;
}

.report-summary {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.7;
}

.report-divider {
  height: 1px;
  background: var(--border-color);
  margin: 24px 0;
}

.report-section + .report-section {
  margin-top: 28px;
}

.section-index {
  display: inline-block;
  margin-bottom: 8px;
  font-size: 0.72rem;
  letter-spacing: 0.08em;
  color: var(--text-secondary);
}

.section-title {
  margin: 0 0 12px;
  font-size: 1.08rem;
}

.section-content {
  line-height: 1.8;
  color: var(--text-secondary);
}

.section-content :deep(p) {
  margin: 0 0 12px;
}

.section-content :deep(ul) {
  padding-left: 18px;
  margin: 0 0 12px;
}

/* Input Info */
.input-info {
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 16px;
  margin-bottom: 24px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.input-label {
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-muted);
}

.input-requirement,
.input-files {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}

.input-key {
  font-size: 0.75rem;
  color: var(--text-muted);
  min-width: 32px;
  flex-shrink: 0;
}

.input-value {
  font-size: 0.82rem;
  color: var(--text-primary);
  line-height: 1.5;
}

.input-file-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.input-file-chip {
  font-size: 0.68rem;
  color: var(--text-secondary);
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  padding: 2px 8px;
  font-family: 'JetBrains Mono', 'SF Mono', monospace;
}

/* Desktop */
@media (min-width: 1024px) {
  .sample-header {
    max-width: 1080px;
    padding: 32px 40px 0;
  }

  .sample-main {
    max-width: 1080px;
    padding: 24px 40px 60px;
  }

  .header-title {
    font-size: 1.6rem;
  }

  .report-card {
    padding: 40px 36px;
  }
}

@media (max-width: 640px) {
  .sample-header,
  .sample-main {
    padding-left: 16px;
    padding-right: 16px;
  }

  .report-card {
    padding: 22px 18px;
  }

  .report-title {
    font-size: 1.5rem;
  }
}
</style>
