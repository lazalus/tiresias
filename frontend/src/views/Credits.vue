<template>
  <div v-if="isRedirectProcessing" class="redirect-screen">
    <div class="redirect-card">
      <div class="redirect-spinner"></div>
      <h1 class="redirect-title">{{ redirectTitle }}</h1>
      <p class="redirect-text">{{ redirectMessage }}</p>
    </div>
  </div>

  <div v-else class="sub-page">
    <!-- Sub Header -->
    <header class="sub-header">
      <router-link to="/profile" class="back-btn">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="15 18 9 12 15 6"/>
        </svg>
      </router-link>
      <h1 class="sub-title">결제 내역</h1>
      <div class="spacer"></div>
    </header>

    <main class="billing-main">
      <!-- Usage Summary -->
      <div class="usage-card">
        <div class="usage-row">
          <div class="usage-item">
            <div class="usage-label">총 결제 건수</div>
            <div class="usage-number">{{ totalPaymentCount }}</div>
          </div>
          <div class="usage-divider"></div>
          <div class="usage-item">
            <div class="usage-label">이번 달 결제 금액</div>
            <div class="usage-number usage-secondary">{{ monthlyPaymentAmount.toLocaleString() }}원</div>
          </div>
        </div>
      </div>

      <!-- Transaction History -->
      <section class="billing-section">
        <h2 class="billing-section-title">결제 내역</h2>
        <div v-if="history.length === 0" class="empty-state">
          결제 내역이 없습니다
        </div>
        <div v-else class="tx-table">
          <div class="tx-header">
            <span class="tx-col tx-col-date">날짜</span>
            <span class="tx-col tx-col-type">유형</span>
            <span class="tx-col tx-col-amount">금액</span>
            <span class="tx-col tx-col-desc">설명</span>
          </div>
          <div v-for="tx in history" :key="tx.id" class="tx-row">
            <span class="tx-col tx-col-date">{{ formatDate(tx.created_at || tx.createdAt) }}</span>
            <span class="tx-col tx-col-type">
              <span class="tx-badge" :class="tx.type">
                {{ formatType(tx.type) }}
              </span>
            </span>
            <span class="tx-col tx-col-amount">
              {{ formatAmount(tx.amount) }}
            </span>
            <span class="tx-col tx-col-desc">{{ tx.description }}</span>
          </div>
        </div>
      </section>
    </main>

    <BottomNav />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { buildAuthAxiosConfig } from '../store/auth.js'
import { getPendingUpload } from '../store/pendingUpload.js'
import axios from 'axios'
import BottomNav from '../components/BottomNav.vue'
import { clearPendingOrder, downloadConfirmedPdf, readPendingOrder } from '../utils/pdfPayment.js'
import { trackGoogleAdsConversionOnce, trackMarketingEvent } from '../utils/marketing.js'

const router = useRouter()
const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

const history = ref([])
const redirectHandled = ref(false)
const isRedirectProcessing = ref(false)
const redirectTitle = ref('결제를 확인하고 있습니다')
const redirectMessage = ref('잠시만 기다려주세요. 결제 완료 후 바로 시뮬레이션과 보고서 생성 흐름으로 이동합니다.')

const totalPaymentCount = computed(() => {
  return history.value.filter(tx =>
    tx.type === 'simulation_payment' ||
    tx.type === 'pdf_payment' ||
    tx.type === 'purchase'
  ).length
})

const monthlyPaymentAmount = computed(() => {
  const now = new Date()
  return history.value
    .filter(tx => {
      if (!['simulation_payment', 'pdf_payment', 'purchase', 'simulation_refund', 'pdf_refund'].includes(tx.type)) return false
      const d = new Date(tx.created_at || tx.createdAt)
      return d.getFullYear() === now.getFullYear() && d.getMonth() === now.getMonth()
    })
    .reduce((sum, tx) => sum + Number(tx.amount || 0), 0)
})

function authHeaders() {
  return buildAuthAxiosConfig()
}

onMounted(async () => {
  const params = new URLSearchParams(window.location.search)
  const hasRedirectPayload =
    Boolean(params.get('paymentKey') && params.get('orderId') && params.get('amount')) ||
    params.get('fail') === 'true' ||
    Boolean(params.get('code')) ||
    Boolean(params.get('message'))

  if (hasRedirectPayload) {
    isRedirectProcessing.value = true
    await checkRedirectResult()
    return
  }

  await fetchHistory()
})

async function fetchHistory() {
  try {
    const res = await axios.get(`${API_BASE}/api/payments/history`, authHeaders())
    history.value = res.data.transactions || res.data || []
  } catch (e) {
    console.error('Failed to fetch history:', e)
  }
}

async function confirmPayment(paymentKey, orderId, amount, simulationType) {
  try {
    const res = await axios.post(`${API_BASE}/api/payments/confirm`, {
      paymentKey,
      orderId,
      amount: Number(amount),
      simulationType
    }, authHeaders())
    await fetchHistory()
    return res.data || { success: true }
  } catch (e) {
    alert('결제 확인 실패: ' + (e.response?.data?.error || e.message))
    return null
  }
}

async function checkRedirectResult() {
  if (redirectHandled.value) return

  const params = new URLSearchParams(window.location.search)
  const paymentKey = params.get('paymentKey')
  const orderId = params.get('orderId')
  const amount = params.get('amount')
  const simulationType = params.get('simulationType')
  const code = params.get('code')
  const message = params.get('message')

  if (!paymentKey && (params.get('fail') === 'true' || code || message)) {
    redirectHandled.value = true
    isRedirectProcessing.value = false
    if (code !== 'USER_CANCEL') {
      alert(`결제 실패: ${message || '알 수 없는 오류'}`)
    }
    window.history.replaceState({}, '', window.location.pathname)
    router.replace({ name: 'Home' })
    return
  }

  if (paymentKey && orderId && amount) {
    const pendingOrder = readPendingOrder()
    if (pendingOrder && pendingOrder.orderId === orderId && Number(pendingOrder.amount) !== Number(amount)) {
      alert('결제 검증에 실패했습니다. 주문 정보가 일치하지 않습니다.')
      return
    }

    redirectHandled.value = true
    redirectTitle.value = '결제 확인이 완료되었습니다'
    redirectMessage.value = '시뮬레이션과 보고서 생성 흐름으로 이동하고 있습니다.'
    const confirmed = await confirmPayment(paymentKey, orderId, amount, simulationType)
    if (confirmed) {
      await handleConfirmedRedirect(pendingOrder, confirmed)
      window.history.replaceState({}, '', window.location.pathname)
      return
    }
    isRedirectProcessing.value = false
  }
}

async function resolvePendingUploadWithRetry(retries = 3, delayMs = 450) {
  for (let attempt = 0; attempt < retries; attempt += 1) {
    const pending = await getPendingUpload()
    if (pending?.isPending) {
      return pending
    }

    if (attempt < retries - 1) {
      await new Promise((resolve) => setTimeout(resolve, delayMs))
    }
  }

  return null
}

async function handleConfirmedRedirect(pendingOrder, confirmedResponse) {
  const order = pendingOrder || readPendingOrder()

  if (order?.kind === 'simulation' && !confirmedResponse?.already_confirmed) {
    const amount = Number(order.amount || 0)
    trackMarketingEvent('purchase', {
      transaction_id: order.orderId,
      value: amount,
      currency: 'KRW',
    })
    trackGoogleAdsConversionOnce('purchase_completed', order.orderId, {
      transaction_id: order.orderId,
      value: amount,
      currency: 'KRW',
    })
  }

  if (order?.kind === 'pdf_download') {
    redirectTitle.value = 'PDF를 준비하고 있습니다'
    redirectMessage.value = '결제 확인 후 다운로드를 시작하는 중입니다.'
    try {
      await downloadConfirmedPdf({
        apiBase: API_BASE,
        reportId: order.reportId,
        title: order.title || '보고서',
      })
      clearPendingOrder()
      alert(confirmedResponse?.already_confirmed ? 'PDF 다운로드를 다시 시작했습니다.' : '결제가 완료되어 PDF 다운로드를 시작합니다.')
    } catch (error) {
      alert('결제는 완료되었지만 PDF 다운로드에 실패했습니다: ' + error.message)
      return
    }

    if (order.redirectPath) {
      router.replace(order.redirectPath)
      return
    }
    isRedirectProcessing.value = false
    return
  }

  const pending = await resolvePendingUploadWithRetry()
  if (pending?.isPending) {
    clearPendingOrder()
    redirectTitle.value = '보고서 생성으로 이동 중입니다'
    redirectMessage.value = '결제 완료가 확인되어 프로젝트와 보고서 생성 흐름을 이어갑니다.'
    router.replace({ name: 'Process', params: { projectId: 'new' } })
    return
  }

  isRedirectProcessing.value = false
  alert('결제는 완료되었지만 업로드 상태를 바로 복원하지 못했습니다. 홈에서 다시 시작하면 추가 결제 없이 그대로 이어집니다.')
  router.replace({ name: 'Home' })
}

function formatType(type) {
  const map = {
    'simulation_payment': '결제',
    'pdf_payment': 'PDF',
    'simulation_refund': '환불',
    'pdf_refund': 'PDF 환불',
    'purchase': '구매',
    'usage': '사용',
    'grant': '지급'
  }
  return map[type] || type
}

function formatAmount(amount) {
  if (typeof amount !== 'number') return amount
  const abs = Math.abs(amount).toLocaleString()
  return amount < 0 ? `-${abs}원` : `${abs}원`
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
.redirect-screen {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%);
  padding: 24px;
}

.redirect-card {
  width: min(100%, 420px);
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 22px;
  padding: 32px 28px;
  box-shadow: 0 24px 60px rgba(15, 23, 42, 0.12);
  text-align: center;
}

.redirect-spinner {
  width: 42px;
  height: 42px;
  margin: 0 auto 18px;
  border-radius: 999px;
  border: 3px solid rgba(99, 102, 241, 0.18);
  border-top-color: #4f46e5;
  animation: redirect-spin 0.7s linear infinite;
}

.redirect-title {
  margin: 0;
  font-size: 1.08rem;
  font-weight: 800;
  color: #111827;
}

.redirect-text {
  margin: 10px 0 0;
  font-size: 0.9rem;
  line-height: 1.65;
  color: #475569;
}

@keyframes redirect-spin {
  to { transform: rotate(360deg); }
}

.sub-page {
  min-height: 100vh;
  background: var(--bg-primary);
  color: var(--text-primary);
  font-family: 'Inter', 'Noto Sans KR', system-ui, -apple-system, sans-serif;
  -webkit-font-smoothing: antialiased;
}

/* Sub Header */
.sub-header {
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 52px;
  padding: 0 16px;
  background: var(--header-bg);
  backdrop-filter: saturate(180%) blur(20px);
  -webkit-backdrop-filter: saturate(180%) blur(20px);
  border-bottom: 1px solid var(--border-color);
}

.back-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  color: var(--text-primary);
  text-decoration: none;
  transition: background 0.15s;
}

.back-btn:hover {
  background: var(--bg-secondary);
}

.sub-title {
  font-size: 0.95rem;
  font-weight: 600;
  margin: 0;
}

.spacer {
  width: 36px;
}

/* Main */
.billing-main {
  max-width: 680px;
  margin: 0 auto;
  padding: 20px 16px 100px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* Usage Summary Card */
.usage-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 16px;
}

.usage-row {
  display: flex;
  align-items: center;
  gap: 16px;
}

.usage-item {
  flex: 1;
}

.usage-divider {
  width: 1px;
  height: 36px;
  background: var(--border-color);
  flex-shrink: 0;
}

.usage-label {
  font-size: 0.75rem;
  color: var(--text-secondary);
  font-weight: 500;
  margin-bottom: 4px;
}

.usage-number {
  font-size: 1.8rem;
  font-weight: 700;
  letter-spacing: -0.03em;
  color: #6366f1;
}

.usage-number.usage-secondary {
  color: var(--text-primary);
  font-size: 1.4rem;
}

/* Billing Section */
.billing-section {
  margin-top: 8px;
}

.billing-section-title {
  font-size: 0.85rem;
  font-weight: 600;
  margin: 0 0 12px;
  letter-spacing: -0.01em;
}

/* Transaction Table */
.empty-state {
  text-align: center;
  padding: 32px 16px;
  color: var(--text-muted);
  font-size: 0.8rem;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 10px;
}

.tx-table {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  overflow: hidden;
}

.tx-header {
  display: flex;
  align-items: center;
  padding: 10px 16px;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-surface);
}

.tx-header .tx-col {
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.tx-row {
  display: flex;
  align-items: center;
  padding: 10px 16px;
  border-bottom: 1px solid var(--border-color);
  transition: background 0.1s;
}

.tx-row:last-child {
  border-bottom: none;
}

.tx-row:hover {
  background: var(--bg-surface);
}

.tx-col {
  font-size: 0.78rem;
}

.tx-col-date {
  width: 130px;
  flex-shrink: 0;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.72rem;
  color: var(--text-muted);
}

.tx-col-type {
  width: 60px;
  flex-shrink: 0;
}

.tx-col-amount {
  width: 80px;
  flex-shrink: 0;
  font-family: 'JetBrains Mono', monospace;
  font-weight: 600;
  font-size: 0.78rem;
  text-align: right;
}

.tx-col-desc {
  flex: 1;
  min-width: 0;
  color: var(--text-secondary);
  font-size: 0.75rem;
  padding-left: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tx-badge {
  display: inline-block;
  font-size: 0.65rem;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
  letter-spacing: 0.02em;
}

.tx-badge.simulation_payment {
  background: rgba(99, 102, 241, 0.1);
  color: #818cf8;
}

.tx-badge.pdf_payment,
.tx-badge.purchase {
  background: rgba(99, 102, 241, 0.1);
  color: #818cf8;
}

.tx-badge.simulation_refund,
.tx-badge.pdf_refund {
  background: rgba(239, 68, 68, 0.12);
  color: #ef4444;
}

.tx-badge.usage {
  background: rgba(156, 163, 175, 0.15);
  color: var(--text-muted);
}

.tx-badge.grant {
  background: rgba(34, 197, 94, 0.1);
  color: #22c55e;
}

/* Responsive */
@media (max-width: 640px) {
  .tx-col-date {
    width: 90px;
    font-size: 0.65rem;
  }
  .tx-col-desc {
    display: none;
  }
  .usage-number.usage-secondary {
    font-size: 1.2rem;
  }
}
</style>
