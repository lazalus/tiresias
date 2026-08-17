<template>
  <div class="sub-page">
    <header class="sub-header">
      <button class="back-btn" @click="$router.back()">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="15 18 9 12 15 6"/>
        </svg>
      </button>
      <h1 class="sub-title">샘플 보고서</h1>
      <HeaderNav class="desktop-only" />
      <div class="spacer mobile-only"></div>
    </header>

    <main class="sub-content">
      <p class="page-desc">Tiresias View로 생성된 실제 시뮬레이션 보고서입니다.</p>

      <div v-if="loading" class="loading-state">불러오는 중...</div>
      <div v-else-if="sampleReports.length === 0" class="empty-state">아직 등록된 샘플 보고서가 없습니다.</div>
      <div v-else class="report-list">
        <div v-for="r in sampleReports" :key="r.id" class="report-item" @click="viewSample(r.id)">
          <div class="report-info">
            <span class="report-title">{{ r.title }}</span>
            <span v-if="r.requirement" class="report-requirement">{{ r.requirement }}</span>
            <div v-if="r.files && r.files.length" class="report-files">
              <span v-for="(f, i) in r.files" :key="i" class="file-chip">{{ f }}</span>
            </div>
            <span class="report-meta">{{ formatDate(r.created_at) }}</span>
          </div>
          <span class="report-arrow">&rsaquo;</span>
        </div>
      </div>

      <p class="page-note">보고서는 지속적으로 추가됩니다.</p>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import HeaderNav from '../components/HeaderNav.vue'
import { applySeoMeta, resetSeoMeta } from '../utils/seo.js'

const router = useRouter()
const API_BASE = import.meta.env.VITE_API_BASE_URL || ''
const sampleReports = ref([])
const loading = ref(true)

onMounted(async () => {
  applySeoMeta({
    title: '샘플 보고서 | 테이레시아스 뷰',
    description: '테이레시아스 뷰로 생성된 공개 샘플 보고서를 열람하고 PDF 형식까지 확인할 수 있습니다.',
    canonical: 'https://tiresiasview.com/samples',
    structuredData: [
      {
        id: 'sample-report-list',
        data: {
          '@context': 'https://schema.org',
          '@type': 'CollectionPage',
          name: '테이레시아스 뷰 샘플 보고서',
          url: 'https://tiresiasview.com/samples',
          description: '테이레시아스 뷰가 생성한 공개 시뮬레이션 보고서 모음',
        },
      },
    ],
  })

  try {
    const res = await axios.get(`${API_BASE}/api/reports/samples`)
    sampleReports.value = res.data.reports || []
    if (sampleReports.value.length > 0) {
      applySeoMeta({
        title: '샘플 보고서 | 테이레시아스 뷰',
        description: '테이레시아스 뷰로 생성된 공개 샘플 보고서를 열람하고 PDF 형식까지 확인할 수 있습니다.',
        canonical: 'https://tiresiasview.com/samples',
        structuredData: [
          {
            id: 'sample-report-list',
            data: {
              '@context': 'https://schema.org',
              '@type': 'CollectionPage',
              name: '테이레시아스 뷰 샘플 보고서',
              url: 'https://tiresiasview.com/samples',
              description: '테이레시아스 뷰가 생성한 공개 시뮬레이션 보고서 모음',
              mainEntity: {
                '@type': 'ItemList',
                itemListElement: sampleReports.value.slice(0, 10).map((item, index) => ({
                  '@type': 'ListItem',
                  position: index + 1,
                  url: `https://tiresiasview.com/samples/${encodeURIComponent(item.id)}`,
                  name: item.title || `샘플 보고서 ${index + 1}`,
                })),
              },
            },
          },
        ],
      })
    }
  } catch (e) {
    console.error('샘플 로드 실패:', e)
  } finally {
    loading.value = false
  }
})

onUnmounted(() => {
  resetSeoMeta(['sample-report-list'])
})

function viewSample(id) {
  router.push({ name: 'SampleReport', params: { reportId: id } })
}

function formatDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleDateString('ko-KR', { year: 'numeric', month: 'short', day: 'numeric' })
}
</script>

<style scoped>
.sub-page {
  min-height: 100vh;
  background: var(--bg-primary);
  color: var(--text-primary);
  font-family: 'Inter', 'Noto Sans KR', system-ui, -apple-system, sans-serif;
  -webkit-font-smoothing: antialiased;
}

.sub-header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: var(--header-bg);
  backdrop-filter: saturate(180%) blur(20px);
  -webkit-backdrop-filter: saturate(180%) blur(20px);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 56px;
  padding: 0 16px;
  max-width: 680px;
  margin: 0 auto;
}

.back-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  color: var(--text-primary);
  text-decoration: none;
  border-radius: 10px;
  transition: background 0.15s;
  background: none;
  border: none;
  cursor: pointer;
}

.back-btn:hover {
  background: var(--border-color);
}

.sub-title {
  font-size: 1rem;
  font-weight: 600;
  letter-spacing: -0.01em;
}

.spacer {
  width: 36px;
}

.sub-content {
  max-width: 680px;
  margin: 0 auto;
  padding: 24px 20px 64px;
}

.page-desc {
  font-size: 0.78rem;
  color: var(--text-secondary);
  margin: 0 0 20px;
}

.report-list {
  display: flex;
  flex-direction: column;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  overflow: hidden;
}

.report-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  cursor: pointer;
  transition: background 0.15s;
  border-bottom: 1px solid var(--border-color);
}

.report-item:last-child {
  border-bottom: none;
}

.report-item:hover {
  background: var(--surface-hover);
}

.report-info {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.report-title {
  font-size: 0.82rem;
  font-weight: 500;
  color: var(--text-primary);
}

.report-meta {
  font-size: 0.68rem;
  color: var(--text-secondary);
}

.report-requirement {
  font-size: 0.75rem;
  color: var(--text-muted);
  line-height: 1.4;
}

.report-files {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 2px;
}

.file-chip {
  font-size: 0.65rem;
  color: var(--text-muted);
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  padding: 1px 6px;
  font-family: 'JetBrains Mono', 'SF Mono', monospace;
}

.report-arrow {
  color: var(--text-secondary);
  font-size: 1.1rem;
  flex-shrink: 0;
}

.page-note {
  font-size: 0.7rem;
  color: var(--text-muted);
  margin: 16px 0 0;
  text-align: center;
}

.desktop-only { display: none; }

@media (min-width: 1024px) {
  .mobile-only { display: none; }
  .desktop-only { display: flex; }

  .sub-header {
    max-width: 1200px;
    height: 60px;
    padding: 0 40px;
  }

  .sub-content {
    max-width: 1080px;
    padding: 48px 40px 60px;
  }

  .sub-title {
    font-size: 1.4rem;
    font-weight: 700;
  }

  .page-desc {
    font-size: 0.88rem;
  }

  .report-list {
    border-radius: 12px;
  }

  .report-item {
    padding: 20px 24px;
  }

  .report-item:hover {
    background: var(--surface-hover);
  }

  .report-title {
    font-size: 0.9rem;
  }
}
</style>
