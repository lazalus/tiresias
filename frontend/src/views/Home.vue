<template>
  <div class="app-screen">
    <header class="app-header">
      <div class="header-inner">
        <div class="header-left">
          <span class="app-name">TIRESIAS VIEW</span>
        </div>
        <HeaderNav />
      </div>
    </header>

    <main class="home-main">
      <!-- Welcome Banner -->
      <div class="welcome-banner">
        <div class="welcome-text">
          <h1 class="welcome-title">보고서 기반 예측 시뮬레이션</h1>
          <p class="welcome-desc">자료를 업로드하고 주제를 입력하면 AI 에이전트가 시나리오를 비교하고 분석 보고서를 생성합니다.</p>
          <div class="welcome-steps">
            <div class="welcome-step">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
              <span>자료 업로드</span>
            </div>
            <svg class="step-arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><polyline points="9 18 15 12 9 6"/></svg>
            <div class="welcome-step">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/></svg>
              <span>시나리오 비교</span>
            </div>
            <svg class="step-arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><polyline points="9 18 15 12 9 6"/></svg>
            <div class="welcome-step">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
              <span>분석 보고서</span>
            </div>
          </div>
        </div>
        <div class="welcome-visual">
          <img src="/dash-banner.png" alt="" class="welcome-img" />
        </div>
      </div>

      <!-- Left Column -->
      <div class="left-column">
        <!-- Use Cases (데스크탑) -->
        <div class="dash-card desktop-only">
          <div class="dash-card-header">
            <h2 class="dash-card-title">활용 사례</h2>
          </div>
          <div class="usecase-grid">
            <div class="usecase-item">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>
              <div>
                <span class="usecase-title">여론 예측</span>
                <span class="usecase-desc">이해관계자 반응을 시나리오로 검토</span>
              </div>
            </div>
            <div class="usecase-item">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/></svg>
              <div>
                <span class="usecase-title">시장 분석</span>
                <span class="usecase-desc">출시·가격 정책 반응 비교</span>
              </div>
            </div>
            <div class="usecase-item">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
              <div>
                <span class="usecase-title">위기 대응</span>
                <span class="usecase-desc">확산 경로와 반응 사전 검토</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Recent Projects -->
        <div v-if="recentProjects.length > 0" class="dash-card">
          <div class="dash-card-header">
            <h2 class="dash-card-title">최근 프로젝트</h2>
            <router-link to="/history" class="dash-card-link">전체 보기</router-link>
          </div>
          <div class="project-list">
            <div v-for="p in recentProjects" :key="p.id" class="project-item" @click="goToProject(p)">
              <div class="project-info">
                <span class="project-name">{{ p.name || '프로젝트' }}</span>
                <span class="project-date">{{ formatDate(p.created_at) }}</span>
              </div>
              <span class="project-status" :class="statusClass(p)">{{ statusLabel(p) }}</span>
            </div>
          </div>
        </div>

        <!-- Sample Reports (데스크탑) -->
        <div class="dash-card desktop-only">
          <div class="dash-card-header">
            <h2 class="dash-card-title">샘플 보고서</h2>
            <router-link to="/samples" class="dash-card-link">더 보기</router-link>
          </div>
          <div v-if="sampleReports.length === 0" class="dash-empty">아직 샘플이 없습니다</div>
          <div v-else class="sample-list">
            <router-link v-for="s in sampleReports" :key="s.id" :to="`/samples/${s.id}`" class="sample-item">
              <span class="sample-title">{{ s.title }}</span>
              <span class="sample-date">{{ formatDate(s.created_at) }}</span>
            </router-link>
          </div>
        </div>
      </div>

      <!-- Right: Action Area -->
      <div class="action-area">
        <!-- File Upload -->
        <div
          class="upload-zone"
          :class="{ 'drag-over': isDragOver, 'has-files': files.length > 0 }"
          @dragover.prevent="isDragOver = true"
          @dragleave.prevent="isDragOver = false"
          @drop.prevent="handleDrop"
          @click="triggerFileInput"
        >
          <input
            ref="fileInput"
            type="file"
            multiple
            accept=".pdf,.md,.markdown,.txt,.csv"
            @change="handleFileSelect"
            style="display: none"
          />
          <template v-if="files.length === 0">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
              <polyline points="17 8 12 3 7 8"/>
              <line x1="12" y1="3" x2="12" y2="15"/>
            </svg>
            <span class="upload-label">파일을 드래그하거나 클릭하여 업로드</span>
            <span class="upload-hint">PDF, Markdown, CSV, 텍스트 파일 지원</span>
          </template>
          <template v-else>
            <div class="file-list" @click.stop>
              <div v-for="(file, idx) in files" :key="idx" class="file-item">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                </svg>
                <span class="file-name">{{ file.name }}</span>
                <button class="file-remove" @click.stop="removeFile(idx)">
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                    <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                  </svg>
                </button>
              </div>
              <button class="add-more-btn" @click.stop="triggerFileInput">+ 파일 추가</button>
            </div>
          </template>
        </div>

        <div class="prompt-guide">
          <div class="prompt-guide-head">
            <div>
              <div class="prompt-guide-label">이런 식으로 요청하세요</div>
              <p class="prompt-guide-copy">자료를 올린 뒤, 그 자료를 바탕으로 앞으로 어떤 흐름이 전개될지 질문하면 됩니다.</p>
            </div>
          </div>

          <div class="prompt-guide-tabs">
            <button
              v-for="example in promptExamples"
              :key="example.id"
              type="button"
              class="prompt-guide-tab"
              :class="{ active: selectedPromptExampleId === example.id }"
              @click="selectedPromptExampleId = example.id"
            >
              {{ example.label }}
            </button>
          </div>

          <div class="prompt-guide-example">
            <div class="prompt-guide-example-title">{{ selectedPromptExample.headline }}</div>
            <p class="prompt-guide-example-text">{{ selectedPromptExample.prompt }}</p>
          </div>
        </div>

        <!-- Topic Input -->
        <textarea
          v-model="topic"
          class="topic-input"
          :placeholder="selectedPromptExample.placeholder"
          rows="3"
        ></textarea>

        <!-- Start Button -->
        <button
          class="start-btn"
          :disabled="!canStart || loading"
          @click="handleStart"
        >
          <span v-if="loading" class="spinner"></span>
          {{ loading ? '처리 중...' : '시뮬레이션 시작' }}
        </button>

        <!-- Estimate: 3-tier plan cards -->
        <div v-if="estimate" class="estimate-section">
          <!-- 자료 요약 -->
          <div class="estimate-summary">
            <span class="estimate-summary-label">등록 자료</span>
            <span class="estimate-summary-value">{{ estimate.fileCount }}건 · 약 {{ estimate.estimatedPages }}페이지</span>
          </div>

          <!-- 포함 항목 -->
          <div class="estimate-includes" v-if="estimate.plans && estimate.plans.length">
            <div class="includes-title">포함 작업</div>
            <div class="includes-list">
              <span v-for="b in estimate.plans[0].breakdown" :key="b.key" class="includes-item">{{ b.label }}</span>
            </div>
          </div>

          <!-- 플랜 카드 -->
          <div class="plan-cards">
            <div
              v-for="plan in estimate.plans"
              :key="plan.id"
              class="plan-card"
              :class="{ selected: selectedEstimatePlanId === plan.id, recommended: plan.id === estimate.recommendedPlanId }"
              @click="selectedEstimatePlanId = plan.id"
            >
              <div v-if="plan.id === estimate.recommendedPlanId" class="plan-badge">권장</div>
              <div class="plan-label">{{ plan.label }}</div>
              <div class="plan-desc">{{ plan.description }}</div>
              <div class="plan-specs">
                <span>에이전트 {{ plan.agents }}명</span>
                <span>{{ plan.rounds }}라운드</span>
              </div>
              <div class="plan-price">₩{{ plan.finalPrice.toLocaleString() }}</div>
            </div>
          </div>

          <!-- 안내 문구 -->
          <p class="estimate-note-text">
            외주 리서치나 수작업 시나리오 검토 전에, 초기 가설을 빠르게 비교·검토하기 위한 분석 옵션입니다.
          </p>

          <!-- 이전 결제 안내 -->
          <div v-if="!isAdmin && reusableSimulationOrder" class="estimate-reuse">
            이전 결제가 보관되어 있어 추가 결제 없이 바로 시작됩니다.
          </div>

          <!-- 결제 버튼 -->
          <button class="estimate-btn" @click="isAdmin ? startSimulation() : proceedToPayment()">
            {{ isAdmin ? '시뮬레이션 시작 (관리자)' : paymentButtonLabel }}
          </button>
        </div>
      </div>
    </main>

    <div class="help-link-area">
      <router-link to="/support" class="help-link">도움이 필요하신가요?</router-link>
    </div>

    <BottomNav />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import BottomNav from '../components/BottomNav.vue'
import HeaderNav from '../components/HeaderNav.vue'
import { refreshProfile, currentUser, buildAuthAxiosConfig } from '../store/auth.js'
import { setPendingUpload } from '../store/pendingUpload.js'
import { trackGoogleAdsConversionOnce, trackMarketingEvent } from '../utils/marketing.js'
import {
  getProjectStatusClass,
  getProjectStatusLabel,
  isReportCompletedProject,
  isSimulationRunningProject,
  normalizeProjectRecord,
} from '../utils/projectStatus.js'

const router = useRouter()
const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

const files = ref([])
const topic = ref('')
const isDragOver = ref(false)
const fileInput = ref(null)
const loading = ref(false)
const estimate = ref(null)
const selectedEstimatePlanId = ref(null)
const promptExamples = [
  {
    id: 'policy',
    label: '정책 분석',
    headline: '정책 보고서, 조사자료, 보도자료를 넣고 이후 시장이나 여론 흐름을 묻는 방식입니다.',
    prompt: '예: 이 보고서를 바탕으로 2026년 서울 부동산 시장이 어떻게 전개될지 시뮬레이션해줘.',
    placeholder: '예: 이 보고서를 바탕으로 2026년 서울 부동산 시장이 어떻게 전개될지 시뮬레이션해줘',
  },
  {
    id: 'market',
    label: '시장 예측',
    headline: '시장 리포트, 경쟁사 자료, 기획 문서를 넣고 출시 이후 반응을 예측할 수 있습니다.',
    prompt: '예: 이 자료를 바탕으로 신제품 출시 후 소비자 반응과 시장 변화가 어떻게 전개될지 시뮬레이션해줘.',
    placeholder: '예: 이 자료를 바탕으로 신제품 출시 후 소비자 반응과 시장 변화가 어떻게 전개될지 시뮬레이션해줘',
  },
  {
    id: 'story',
    label: '스토리 전개',
    headline: '소설, 시나리오, 초고를 넣고 이후 결말이나 갈등 전개를 예측할 수도 있습니다.',
    prompt: '예: 이 소설 초안을 바탕으로 결말이 어떻게 전개될지 시뮬레이션해줘.',
    placeholder: '예: 이 소설 초안을 바탕으로 결말이 어떻게 전개될지 시뮬레이션해줘',
  },
  {
    id: 'response',
    label: '반응 검토',
    headline: '연설문, 입장문, 발표자료를 넣고 사람들의 반응과 쟁점을 미리 볼 수 있습니다.',
    prompt: '예: 이 발표자료를 공개했을 때 이해관계자들이 어떤 반응을 보일지 시뮬레이션해줘.',
    placeholder: '예: 이 발표자료를 공개했을 때 이해관계자들이 어떤 반응을 보일지 시뮬레이션해줘',
  },
]
const selectedPromptExampleId = ref(promptExamples[0].id)
const isAdmin = computed(() => currentUser.value?.role === 'admin')
const reusableSimulationOrder = ref(null)
const canStart = computed(() => files.value.length > 0 && topic.value.trim().length > 0)
const paymentButtonLabel = computed(() => {
  if (reusableSimulationOrder.value) return '추가 결제 없이 분석 시작'
  return '결제 후 분석 시작'
})

const selectedEstimatePlan = computed(() => {
  if (!estimate.value?.plans?.length) {
    return estimate.value || null
  }

  return (
    estimate.value.plans.find((plan) => plan.id === selectedEstimatePlanId.value) ||
    estimate.value.plans.find((plan) => plan.id === estimate.value.recommendedPlanId) ||
    estimate.value.plans[0]
  )
})

const selectedPromptExample = computed(
  () => promptExamples.find((example) => example.id === selectedPromptExampleId.value) || promptExamples[0]
)

function normalizeEstimatePayload(payload) {
  const plans = Array.isArray(payload?.plans) ? payload.plans : []
  const recommendedPlanId = payload?.recommendedPlanId || plans[0]?.id || null
  const recommendedPlan =
    plans.find((plan) => plan.id === recommendedPlanId) ||
    plans[0] ||
    null

  if (!recommendedPlan) {
    return payload
  }

  return {
    ...payload,
    recommendedPlanId,
    plans,
    agents: recommendedPlan.agents,
    rounds: recommendedPlan.rounds,
    depth: recommendedPlan.depth,
    costKRW: recommendedPlan.costKRW,
    finalPrice: recommendedPlan.finalPrice,
    quoteToken: recommendedPlan.quoteToken,
    breakdown: recommendedPlan.breakdown,
  }
}

const triggerFileInput = () => {
  const el = Array.isArray(fileInput.value) ? fileInput.value[0] : fileInput.value
  el?.click()
}

const handleFileSelect = (event) => {
  addFiles(Array.from(event.target.files))
  event.target.value = ''
}

const handleDrop = (e) => {
  isDragOver.value = false
  addFiles(Array.from(e.dataTransfer.files))
}

const pdfPageCounts = ref({})

async function getPdfPageCount(file) {
  try {
    if (!window.pdfjsLib) {
      const script = document.createElement('script')
      script.src = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.0.379/pdf.min.mjs'
      script.type = 'module'
      // Use legacy build instead for broader compat
      const s = document.createElement('script')
      s.src = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js'
      await new Promise((resolve, reject) => { s.onload = resolve; s.onerror = reject; document.head.appendChild(s) })
      window.pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js'
    }
    const arrayBuffer = await file.arrayBuffer()
    const pdf = await window.pdfjsLib.getDocument({ data: arrayBuffer }).promise
    return pdf.numPages
  } catch {
    return null
  }
}

const addFiles = async (newFiles) => {
  const valid = newFiles.filter(f => {
    const ext = f.name.split('.').pop().toLowerCase()
    return ['pdf', 'md', 'markdown', 'txt', 'csv'].includes(ext)
  })
  files.value.push(...valid)
  estimate.value = null
  selectedEstimatePlanId.value = null

  for (const f of valid) {
    const ext = f.name.split('.').pop().toLowerCase()
    if (ext === 'pdf') {
      const pages = await getPdfPageCount(f)
      if (pages) pdfPageCounts.value[f.name] = pages
    } else {
      // 텍스트 파일: 글자 수 기반 페이지 추정 (약 1500자/페이지)
      try {
        const text = await f.text()
        const chars = text.replace(/\s/g, '').length
        pdfPageCounts.value[f.name] = Math.max(1, Math.ceil(chars / 1500))
      } catch {
        pdfPageCounts.value[f.name] = Math.max(1, Math.ceil(f.size / 3000))
      }
    }
  }
}

const removeFile = (index) => {
  const removed = files.value[index]
  if (removed && pdfPageCounts.value[removed.name]) {
    delete pdfPageCounts.value[removed.name]
  }
  files.value.splice(index, 1)
  estimate.value = null
  selectedEstimatePlanId.value = null
}

async function handleStart() {
  if (loading.value || !canStart.value) return
  loading.value = true

  const fileCount = files.value.length
  const totalSize = files.value.reduce((sum, f) => sum + f.size, 0)
  const hasPdf = files.value.some(f => f.name.toLowerCase().endsWith('.pdf'))

  // 실제 PDF 페이지 수 합산
  const actualPdfPages = Object.values(pdfPageCounts.value).reduce((sum, p) => sum + p, 0)

  try {
    const pendingState = await setPendingUpload(files.value, topic.value.trim())
    const res = await axios.post(`${API_BASE}/api/estimate`, {
      fileCount,
      totalSize,
      requirement: topic.value.trim(),
      hasPdf,
      actualPages: actualPdfPages || undefined,
      pendingToken: pendingState?.remoteToken || undefined,
    }, buildAuthAxiosConfig())

    estimate.value = normalizeEstimatePayload(res.data)
    selectedEstimatePlanId.value =
      reusableSimulationOrder.value?.planId ||
      estimate.value?.recommendedPlanId ||
      null

    const recommendedPlan = estimate.value?.plans?.find((plan) => plan.id === estimate.value?.recommendedPlanId) || selectedEstimatePlan.value
    const quoteDedupeKey = estimate.value?.quoteToken || `${fileCount}:${topic.value.trim()}`
    trackMarketingEvent('generate_lead', {
      currency: 'KRW',
      value: Number(recommendedPlan?.finalPrice || 0),
      lead_type: 'simulation_quote',
    })
    trackGoogleAdsConversionOnce('quote_requested', quoteDedupeKey, {
      value: Number(recommendedPlan?.finalPrice || 0),
      currency: 'KRW',
    })
  } catch (error) {
    alert('견적 계산 실패: ' + (error.response?.data?.error || error.message))
  } finally {
    loading.value = false
  }
}

async function proceedToPayment() {
  if (loading.value || !selectedEstimatePlan.value?.quoteToken) return
  loading.value = true

  try {
    const pendingState = await setPendingUpload(files.value, topic.value.trim())
    const pendingSaved = Boolean(pendingState?.saved)
    if (!pendingSaved) {
      console.warn('Pending upload durable save unavailable, proceeding without pre-saved files.')
    }

    if (reusableSimulationOrder.value?.orderId) {
      localStorage.setItem('pending_order', JSON.stringify({
        kind: 'simulation',
        orderId: reusableSimulationOrder.value.orderId,
        amount: reusableSimulationOrder.value.amount,
        reusable: true,
        pendingUploadSaved: pendingSaved,
      }))
      await fetchReusableSimulationOrder(pendingState?.remoteToken || null)
      router.push({ name: 'Process', params: { projectId: 'new' } })
      return
    }

    if (!window.TossPayments) {
      await new Promise((resolve, reject) => {
        const script = document.createElement('script')
        script.src = 'https://js.tosspayments.com/v1/payment'
        script.onload = resolve
        script.onerror = reject
        document.head.appendChild(script)
      })
    }

    const toss = new TossPayments('test_ck_Z1aOwX7K8mE1NNDJmzam8yQxzvNP')
    const amount = selectedEstimatePlan.value.finalPrice

    const orderRes = await axios.post(`${API_BASE}/api/payments/create-order`, {
      amount,
      quoteToken: selectedEstimatePlan.value.quoteToken
    }, buildAuthAxiosConfig())

    const orderId = orderRes.data?.order?.orderId
    if (!orderId) {
      throw new Error('결제 주문 생성에 실패했습니다.')
    }

    if (orderRes.data?.already_confirmed && orderRes.data?.reusable) {
      localStorage.setItem('pending_order', JSON.stringify({
        kind: 'simulation',
        orderId,
        amount: orderRes.data?.order?.amount ?? amount,
        reusable: true,
        pendingUploadSaved: pendingSaved,
      }))
      await fetchReusableSimulationOrder(pendingState?.remoteToken || null)
      router.push({ name: 'Process', params: { projectId: 'new' } })
      return
    }

    if (!pendingSaved) {
      alert('결제 전 업로드 상태를 안전하게 저장하지 못했습니다. 브라우저 권한 또는 네트워크 상태를 확인한 뒤 다시 시도해주세요.')
      return
    }

    localStorage.setItem('pending_order', JSON.stringify({
      kind: 'simulation',
      orderId,
      amount,
      pendingUploadSaved: pendingSaved,
    }))

    await toss.requestPayment('카드', {
      amount,
      orderId,
      orderName: 'Tiresias 시뮬레이션',
      successUrl: `${window.location.origin}/credits`,
      failUrl: `${window.location.origin}/credits`
    })
  } catch (e) {
    if (e.code !== 'USER_CANCEL') {
      alert('결제 중 오류가 발생했습니다: ' + (e.message || '다시 시도해주세요.'))
    }
  } finally {
    loading.value = false
  }
}

const startSimulation = async () => {
  if (loading.value) return
  try {
    const pendingState = await setPendingUpload(files.value, topic.value.trim())
    const pendingSaved = Boolean(pendingState?.saved)
    if (!pendingSaved) {
      console.warn('Pending upload durable save unavailable, proceeding with in-memory fallback for admin flow.')
    }
    router.push({ name: 'Process', params: { projectId: 'new' } })
  } catch (error) {
    alert('시뮬레이션을 시작하지 못했습니다: ' + (error.message || '업로드 상태 저장 실패'))
  }
}

const recentProjects = ref([])
const sampleReports = ref([])

async function fetchRecentProjects() {
  try {
    const res = await axios.get(`${API_BASE}/api/projects`, buildAuthAxiosConfig())
    recentProjects.value = (res.data.projects || []).map(normalizeProjectRecord).slice(0, 5)
  } catch {}
}

const refreshHomeProjects = () => {
  fetchRecentProjects()
}

const handleHomeVisibilityChange = () => {
  if (document.visibilityState === 'visible') {
    fetchRecentProjects()
  }
}

function goToProject(p) {
  if (isReportCompletedProject(p)) {
    router.push({ name: 'Process', params: { projectId: p.id } })
  } else if (isSimulationRunningProject(p) && p.simulation_id) {
    router.push({ name: 'SimulationRun', params: { simulationId: p.simulation_id } })
  } else {
    router.push({ name: 'Process', params: { projectId: p.id } })
  }
}

function statusLabel(project) {
  return getProjectStatusLabel(project?.status, { reportId: project?.report_id || null })
}

function statusClass(project) {
  return getProjectStatusClass(project?.status, { reportId: project?.report_id || null })
}

function formatDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' })
}

async function fetchSampleReports() {
  try {
    const res = await axios.get(`${API_BASE}/api/reports/samples`)
    sampleReports.value = (res.data.reports || []).slice(0, 3)
  } catch {}
}

async function fetchReusableSimulationOrder(pendingToken = null) {
  if (isAdmin.value) {
    reusableSimulationOrder.value = null
    return
  }

  try {
    const res = await axios.get(`${API_BASE}/api/payments/status`, {
      params: pendingToken ? { pending_token: pendingToken } : undefined,
      ...buildAuthAxiosConfig()
    })
    reusableSimulationOrder.value = res.data?.reusableSimulationOrder || null
  } catch {
    reusableSimulationOrder.value = null
  }
}

onMounted(async () => {
  await refreshProfile()
  fetchRecentProjects()
  fetchSampleReports()
  fetchReusableSimulationOrder()
  window.addEventListener('focus', refreshHomeProjects)
  window.addEventListener('tiresias:projects-changed', refreshHomeProjects)
  document.addEventListener('visibilitychange', handleHomeVisibilityChange)
})

onUnmounted(() => {
  window.removeEventListener('focus', refreshHomeProjects)
  window.removeEventListener('tiresias:projects-changed', refreshHomeProjects)
  document.removeEventListener('visibilitychange', handleHomeVisibilityChange)
})

watch(topic, () => {
  estimate.value = null
  selectedEstimatePlanId.value = null
})
</script>

<style scoped>
.app-screen {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
  color: var(--text-primary);
  font-family: 'Inter', 'Noto Sans KR', system-ui, -apple-system, sans-serif;
  -webkit-font-smoothing: antialiased;
  font-size: 0.82rem;
}

.app-header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border-color);
  backdrop-filter: saturate(180%) blur(20px);
  -webkit-backdrop-filter: saturate(180%) blur(20px);
  flex-shrink: 0;
}

.header-inner {
  max-width: 1200px;
  margin: 0 auto;
  min-height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}

.header-left {
  display: flex;
  align-items: center;
}

.app-name {
  font-family: 'Outfit', sans-serif;
  font-weight: 700;
  letter-spacing: 0.08em;
  font-size: 0.86rem;
  color: var(--text-primary);
}

.home-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
  box-sizing: border-box;
  gap: 18px;
  padding: 24px 16px 20px;
}

.left-column,
.action-area {
  width: 100%;
}

.left-column {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.desktop-only { display: none; }

/* Welcome Banner */
.welcome-banner {
  grid-column: 1 / -1;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  align-items: center;
}

.welcome-text {
  flex: 1;
  padding: 20px 28px;
}

.welcome-title {
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 6px;
  letter-spacing: -0.01em;
}

.welcome-desc {
  font-size: 0.78rem;
  color: var(--text-secondary);
  line-height: 1.5;
  margin: 0 0 14px;
  max-width: 400px;
}

.welcome-steps {
  display: flex;
  align-items: center;
  gap: 8px;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  padding-bottom: 2px;
}

.welcome-step {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--text-secondary);
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  padding: 6px 12px;
  border-radius: 6px;
  white-space: nowrap;
  flex-shrink: 0;
}

.welcome-step svg { color: var(--accent-color, #6366f1); flex-shrink: 0; }
.step-arrow { color: var(--text-muted); flex-shrink: 0; }

.welcome-visual {
  width: 260px;
  flex-shrink: 0;
  height: 120px;
  overflow: hidden;
}

.welcome-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: 0.85;
}

/* Use Case Grid */
.usecase-grid {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.usecase-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid var(--border-color);
}

.usecase-item:last-child { border-bottom: none; }

.usecase-item svg {
  color: var(--accent-color, #6366f1);
  flex-shrink: 0;
  margin-top: 2px;
}

.usecase-item > div { display: flex; flex-direction: column; gap: 2px; }

.usecase-title {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--text-primary);
}

.usecase-desc {
  font-size: 0.72rem;
  color: var(--text-muted);
}

.dash-card,
.action-area {
  border: 1px solid var(--border-color);
  background: var(--bg-secondary);
  ;
}

.dash-card {
  border-radius: 12px;
  padding: 18px;
}

.intro-card {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.94) 0%, rgba(248, 250, 252, 0.96) 100%);
}

.intro-eyebrow,
.action-kicker {
  display: inline-flex;
  align-items: center;
  min-height: 30px;
  padding: 0 12px;
  border-radius: 999px;
  background: rgba(99, 102, 241, 0.1);
  color: var(--accent-color, #6366f1);
  font-size: 0.74rem;
  font-weight: 700;
}

.intro-title {
  margin: 16px 0 10px;
  font-size: 1.4rem;
  line-height: 1.28;
  letter-spacing: -0.03em;
}

.intro-desc,
.guide-desc,
.sample-date,
.project-date,
.action-desc,
.field-meta,
.upload-hint,
.estimate-subtitle,
.summary-desc,
.help-link {
  color: var(--text-muted);
}

.intro-desc,
.action-desc,
.upload-hint,
.estimate-subtitle,
.summary-desc {
  line-height: 1.65;
}

.intro-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
}

.intro-pill {
  padding: 7px 10px;
  border-radius: 999px;
  font-size: 0.76rem;
  font-weight: 600;
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
}

.dash-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.dash-card-title {
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.dash-card-link {
  font-size: 0.76rem;
  color: var(--accent-color, #6366f1);
  text-decoration: none;
  font-weight: 600;
}

.dash-empty {
  font-size: 0.84rem;
  color: var(--text-muted);
  padding: 12px 0;
  text-align: center;
}

.project-list,
.sample-list,
.summary-list,
.guide-steps {
  display: flex;
  flex-direction: column;
}

.project-item,
.sample-item,
.guide-step,
.summary-item {
  border-bottom: 1px solid rgba(226, 232, 240, 0.9);
}

.project-item:last-child,
.sample-item:last-child,
.guide-step:last-child,
.summary-item:last-child {
  border-bottom: none;
}

.project-item,
.sample-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
  cursor: pointer;
}

.project-info {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
  flex: 1;
}

.project-name,
.sample-title,
.summary-title,
.guide-label {
  color: var(--text-primary);
}

.project-name,
.sample-title {
  font-size: 0.84rem;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.project-date,
.sample-date {
  font-size: 0.72rem;
}

.project-status {
  font-size: 0.7rem;
  font-weight: 700;
  padding: 5px 9px;
  border-radius: 999px;
  flex-shrink: 0;
  color: var(--text-secondary);
  background: var(--bg-surface);
}

.status--done { color: #1A936F; background: rgba(26, 147, 111, 0.1); }
.status--running { color: var(--accent-color, #6366f1); background: rgba(99, 102, 241, 0.1); }
.status--fail { color: #ef4444; background: rgba(239, 68, 68, 0.1); }

.guide-step,
.summary-item {
  display: flex;
  gap: 14px;
  padding: 14px 0;
}

.guide-num {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: rgba(99, 102, 241, 0.1);
  color: var(--accent-color, #6366f1);
  font-size: 0.76rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.guide-body {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.guide-label,
.summary-title {
  font-size: 0.84rem;
  font-weight: 700;
}

.guide-desc,
.summary-desc {
  font-size: 0.76rem;
}

.sample-item {
  text-decoration: none;
}

.summary-item {
  flex-direction: column;
  gap: 6px;
}

.action-area {
  display: flex;
  flex-direction: column;
  gap: 16px;
  border-radius: 12px;
  padding: 20px;
}

.action-guide-card {
  padding: 16px 18px;
}

.action-guide-card .guide-step {
  padding: 12px 0;
}

.action-head {
  display: grid;
  gap: 10px;
}

.action-title {
  margin: 0;
  font-size: 1.2rem;
  line-height: 1.28;
}

.action-desc {
  margin: 0;
  font-size: 0.9rem;
}

.field-block {
  display: grid;
  gap: 10px;
}

.field-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.field-label {
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--text-primary);
}

.field-meta {
  font-size: 0.74rem;
}

.upload-zone {
  border: 1.5px dashed var(--border-color);
  border-radius: 10px;
  padding: 28px 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: var(--text-muted);
  transition: border-color 0.18s ease, background 0.18s ease;
  min-height: 110px;
  background: var(--bg-surface);
}

.upload-zone:hover,
.upload-zone.drag-over {
  border-color: var(--accent-color, #6366f1);
  background: rgba(99, 102, 241, 0.04);
}

.upload-zone.has-files {
  padding: 14px 16px;
  align-items: stretch;
  cursor: default;
}

.prompt-guide {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px 16px 14px;
  border: 1px solid var(--border-color);
  border-radius: 12px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.92) 0%, rgba(248, 250, 252, 0.96) 100%);
}

.prompt-guide-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.prompt-guide-label {
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.02em;
  color: var(--text-primary);
}

.prompt-guide-copy {
  margin: 6px 0 0;
  font-size: 0.75rem;
  line-height: 1.6;
  color: var(--text-muted);
}

.prompt-guide-tabs {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 2px;
}

.prompt-guide-tab {
  border: 1px solid var(--border-color);
  background: var(--bg-surface);
  color: var(--text-secondary);
  min-height: 34px;
  padding: 0 12px;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 700;
  white-space: nowrap;
  cursor: pointer;
  font-family: inherit;
  transition: border-color 0.18s ease, background 0.18s ease, color 0.18s ease;
}

.prompt-guide-tab.active {
  border-color: rgba(99, 102, 241, 0.3);
  background: rgba(99, 102, 241, 0.08);
  color: var(--accent-color, #6366f1);
}

.prompt-guide-example {
  padding-top: 2px;
}

.prompt-guide-example-title {
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.5;
}

.prompt-guide-example-text {
  margin: 6px 0 0;
  font-size: 0.8rem;
  line-height: 1.65;
  color: var(--text-secondary);
}

.upload-label {
  font-size: 0.88rem;
  font-weight: 600;
  color: #1e293b;
}

.upload-hint {
  font-size: 0.76rem;
  text-align: center;
}

.file-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 9px 12px;
  font-size: 0.76rem;
  color: var(--text-secondary);
  font-family: 'JetBrains Mono', 'SF Mono', monospace;
}

.file-name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-remove,
.add-more-btn {
  background: none;
  border: none;
  font-family: inherit;
  cursor: pointer;
}

.file-remove {
  color: var(--text-muted);
  padding: 2px;
}

.file-remove:hover {
  color: #ef4444;
}

.add-more-btn {
  align-self: flex-start;
  color: var(--accent-color, #6366f1);
  font-size: 0.74rem;
  font-weight: 600;
  padding: 2px 0;
}

.topic-input {
  width: 100%;
  min-height: 112px;
  padding: 14px 16px;
  box-sizing: border-box;
  border-radius: 10px;
  border: 1px solid var(--border-color);
  background: var(--bg-secondary);
  color: var(--text-primary);
  font: inherit;
  line-height: 1.65;
  resize: vertical;
  outline: none;
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
}

.topic-input:focus {
  border-color: var(--accent-color, #6366f1);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.topic-input::placeholder {
  color: var(--text-muted);
}

.start-btn,
.estimate-btn {
  min-height: 48px;
  border: none;
  border-radius: 8px;
  color: #fff;
  background: var(--accent-color, #6366f1);
  font-size: 0.9rem;
  font-weight: 700;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-family: inherit;
  transition: transform 0.18s ease, box-shadow 0.18s ease, opacity 0.18s ease;
  box-shadow: 0 14px 28px rgba(15, 95, 219, 0.18);
}

.start-btn:hover:not(:disabled),
.estimate-btn:hover {
  transform: translateY(-1px);
}

.start-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
  box-shadow: none;
}

.estimate-card {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 18px;
  border-radius: 12px;
  border: 1px solid var(--border-color);
  background: var(--bg-surface);
}

.estimate-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.estimate-title {
  font-size: 0.92rem;
  font-weight: 700;
  color: var(--text-primary);
}

.estimate-subtitle {
  margin-top: 4px;
  font-size: 0.76rem;
}

.estimate-badge {
  white-space: nowrap;
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--accent-color, #6366f1);
  background: rgba(99, 102, 241, 0.1);
  border-radius: 999px;
  padding: 6px 10px;
}

.estimate-rows {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.estimate-row,
.estimate-price {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  font-size: 0.82rem;
}

.estimate-row span:first-child,
.estimate-price span:first-child {
  color: var(--text-secondary);
}

.estimate-row span:last-child,
.estimate-price span:last-child {
  text-align: right;
  color: var(--text-primary);
  font-weight: 600;
}

.estimate-divider {
  height: 1px;
  background: var(--border-color);
}

.estimate-note {
  padding: 11px 12px;
  border-radius: 12px;
  background: rgba(15, 118, 110, 0.1);
  color: #1A936F;
  font-size: 0.78rem;
  line-height: 1.55;
}

.price-value {
  font-size: 1.16rem;
  font-weight: 800;
  color: var(--accent-color, #6366f1) !important;
}

.help-link-area {
  text-align: center;
  padding: 8px 0 14px;
  flex-shrink: 0;
}

.help-link {
  font-size: 0.78rem;
  text-decoration: none;
}

.help-link:hover {
  color: var(--accent-color, #6366f1);
}

.spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.34);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 640px) {
  .header-inner {
    padding: 0 16px;
  }

  .home-main {
    padding: 20px 16px 16px;
  }

  .estimate-head,
  .field-head,
  .prompt-guide-head {
    align-items: flex-start;
    flex-direction: column;
  }

  .welcome-visual {
    display: none;
  }

  .welcome-text {
    padding: 16px 18px;
  }

  .welcome-steps {
    overflow-x: visible;
    padding-bottom: 0;
    gap: 4px;
  }

  .welcome-step {
    background: none;
    border: none;
    padding: 2px 0;
    font-size: 0.74rem;
    gap: 4px;
  }

  .step-arrow {
    width: 12px;
    height: 12px;
  }
}

@media (min-width: 1024px) {
  .header-inner {
    padding: 0 40px;
  }

  .home-main {
    display: grid;
    grid-template-columns: minmax(360px, 420px) minmax(420px, 520px);
    align-items: start;
    padding: 40px;
    gap: 28px;
  }

  .desktop-only {
    display: block !important;
  }

  .welcome-banner {
    display: flex !important;
  }

  .welcome-visual {
    display: block;
  }

  .action-area {
    position: sticky;
    top: 92px;
    padding: 24px;
  }

  .left-column {
    gap: 16px;
  }
}

/* -- Estimate Section (3-tier) -- */
.estimate-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-top: 4px;
}

.estimate-summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 14px;
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  font-size: 0.82rem;
}

.estimate-summary-label { color: var(--text-secondary); }
.estimate-summary-value { font-weight: 600; color: var(--text-primary); }

.estimate-includes {
  padding: 14px;
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: 8px;
}

.includes-title {
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--text-muted);
  margin-bottom: 8px;
}

.includes-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.includes-item {
  font-size: 0.72rem;
  color: var(--text-secondary);
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  padding: 3px 8px;
}

.plan-cards {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.plan-card {
  position: relative;
  border: 1.5px solid var(--border-color);
  border-radius: 10px;
  padding: 16px;
  cursor: pointer;
  transition: border-color 0.15s;
}

.plan-card:hover {
  border-color: var(--text-muted);
}

.plan-card.selected {
  border-color: var(--accent-color, #6366f1);
  background: rgba(99, 102, 241, 0.04);
}

.plan-card.recommended {
  border-color: var(--accent-color, #6366f1);
}

.plan-badge {
  position: absolute;
  top: -8px;
  right: 14px;
  font-size: 0.65rem;
  font-weight: 700;
  color: #fff;
  background: var(--accent-color, #6366f1);
  padding: 2px 8px;
  border-radius: 4px;
}

.plan-label {
  font-size: 0.88rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.plan-desc {
  font-size: 0.75rem;
  color: var(--text-muted);
  line-height: 1.4;
  margin-bottom: 8px;
}

.plan-specs {
  display: flex;
  gap: 12px;
  font-size: 0.72rem;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.plan-price {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--accent-color, #6366f1);
}

.estimate-note-text {
  font-size: 0.72rem;
  color: var(--text-muted);
  line-height: 1.5;
  margin: 0;
}

.estimate-reuse {
  font-size: 0.78rem;
  color: var(--accent-color, #6366f1);
  background: rgba(99, 102, 241, 0.06);
  border-radius: 6px;
  padding: 10px 12px;
  line-height: 1.4;
}

@media (min-width: 1024px) {
  .plan-cards {
    flex-direction: row;
    gap: 12px;
  }

  .plan-card {
    flex: 1;
  }
}
</style>
