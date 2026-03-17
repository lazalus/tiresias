<template>
  <div class="sub-page">
    <!-- Sub Header -->
    <header class="sub-header">
      <router-link to="/profile" class="back-btn">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="15 18 9 12 15 6"/>
        </svg>
      </router-link>
      <h1 class="sub-title">이용권 관리</h1>
      <div class="spacer"></div>
    </header>

    <main class="billing-main">
      <!-- Usage Summary -->
      <div class="usage-card">
        <div class="usage-row">
          <div class="usage-item">
            <div class="usage-label">보유 크레딧</div>
            <div class="usage-number">{{ credits ?? '-' }}</div>
          </div>
          <div class="usage-divider"></div>
          <div class="usage-item">
            <div class="usage-label">이번 달 사용량</div>
            <div class="usage-number usage-secondary">{{ monthlyUsage }}</div>
          </div>
        </div>
        <div class="usage-note">시뮬레이션 1회 실행에 1 크레딧이 소모됩니다</div>
      </div>

      <!-- Value Info Box -->
      <div class="info-box">
        <div class="info-title">1회 시뮬레이션에 포함된 것</div>
        <div class="info-list">
          <div class="info-row">
            <span class="info-check">&#10003;</span>
            <span>수천 개 AI 에이전트가 가상 세계를 구축하고 상호작용</span>
          </div>
          <div class="info-row">
            <span class="info-check">&#10003;</span>
            <span>2개 병렬 세계 동시 비교 시뮬레이션</span>
          </div>
          <div class="info-row">
            <span class="info-check">&#10003;</span>
            <span>지식 그래프 자동 구축 + 시계열 분석</span>
          </div>
          <div class="info-row">
            <span class="info-check">&#10003;</span>
            <span>전문 분석 보고서 자동 생성</span>
          </div>
          <div class="info-row">
            <span class="info-check">&#10003;</span>
            <span>AI와 심층 대화로 추가 인사이트 획득</span>
          </div>
        </div>
      </div>

      <!-- Plans -->
      <section class="billing-section">
        <h2 class="billing-section-title">이용권 구매</h2>
        <div class="plans-row">
          <div
            v-for="plan in plans"
            :key="plan.id"
            class="plan-card"
            :class="{ featured: plan.featured }"
          >
            <div v-if="plan.featured" class="plan-badge">인기</div>
            <div class="plan-name">{{ plan.name }}</div>
            <div class="plan-credits">
              <span class="plan-credits-num">{{ plan.credits }}</span>
              <span class="plan-credits-unit">크레딧</span>
            </div>
            <div class="plan-price">{{ plan.price.toLocaleString() }}원</div>
            <div v-if="plan.savings" class="plan-savings">{{ plan.savings }}</div>
            <button class="plan-btn" :class="{ 'plan-btn-featured': plan.featured }" @click="handlePurchase(plan)" :disabled="purchaseLoading">
              구매
            </button>
          </div>
        </div>
      </section>

      <!-- Transaction History -->
      <section class="billing-section">
        <h2 class="billing-section-title">거래 내역</h2>
        <div v-if="history.length === 0" class="empty-state">
          거래 내역이 없습니다
        </div>
        <div v-else class="tx-table">
          <div class="tx-header">
            <span class="tx-col tx-col-date">날짜</span>
            <span class="tx-col tx-col-type">유형</span>
            <span class="tx-col tx-col-amount">수량</span>
            <span class="tx-col tx-col-desc">설명</span>
          </div>
          <div v-for="tx in history" :key="tx.id" class="tx-row">
            <span class="tx-col tx-col-date">{{ formatDate(tx.created_at) }}</span>
            <span class="tx-col tx-col-type">
              <span class="tx-badge" :class="tx.type">
                {{ tx.type === 'purchase' ? '구매' : tx.type === 'usage' ? '사용' : tx.type === 'grant' ? '지급' : tx.type }}
              </span>
            </span>
            <span class="tx-col tx-col-amount" :class="{ positive: tx.amount > 0, negative: tx.amount < 0 }">
              {{ tx.amount > 0 ? '+' : '' }}{{ tx.amount }}
            </span>
            <span class="tx-col tx-col-desc">{{ tx.description }}</span>
          </div>
        </div>
      </section>
    </main>

    <BottomNav />

    <!-- 결제 위젯 모달 -->
    <div v-if="showPaymentWidget" class="payment-overlay" @click.self="cancelPayment">
      <div class="payment-modal">
        <div class="payment-header">
          <h3>{{ selectedPlan?.name }} 결제</h3>
          <span class="payment-amount">{{ selectedPlan?.price?.toLocaleString() }}원</span>
          <button class="payment-close" @click="cancelPayment">&times;</button>
        </div>
        <div id="payment-method" class="payment-widget-area"></div>
        <div id="agreement" class="payment-agreement-area"></div>
        <button class="payment-submit" @click="submitPayment" :disabled="purchaseLoading">
          <span v-if="!purchaseLoading">결제하기</span>
          <span v-else>처리 중...</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { getToken, currentUser } from '../store/auth.js'
import axios from 'axios'
import BottomNav from '../components/BottomNav.vue'

const TOSS_CLIENT_KEY = 'live_gck_LlDJaYngroy4XnkKKwGK3ezGdRpX'
const TOSS_CUSTOMER_KEY = 'tiresias'
const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

const credits = ref(null)
const plans = ref([])
const history = ref([])
const purchaseLoading = ref(false)
const showPaymentWidget = ref(false)
const selectedPlan = ref(null)
let paymentWidget = null
let paymentMethodsWidget = null
let agreementWidget = null

const monthlyUsage = computed(() => {
  const now = new Date()
  const thisMonth = history.value.filter(tx => {
    if (tx.type !== 'usage') return false
    const d = new Date(tx.created_at)
    return d.getFullYear() === now.getFullYear() && d.getMonth() === now.getMonth()
  })
  return thisMonth.reduce((sum, tx) => sum + Math.abs(tx.amount), 0)
})

function authHeaders() {
  return { headers: { Authorization: `Bearer ${getToken()}` } }
}

onMounted(async () => {
  await Promise.all([fetchCredits(), fetchPlans(), fetchHistory()])
  await loadTossSDK()
  checkRedirectResult()
})

onUnmounted(() => {
  showPaymentWidget.value = false
  paymentWidget = null
})

// 토스 결제위젯 SDK 로드
async function loadTossSDK() {
  if (window.TossPayments) return
  return new Promise((resolve, reject) => {
    const script = document.createElement('script')
    script.src = 'https://js.tosspayments.com/v2/standard'
    script.onload = resolve
    script.onerror = reject
    document.head.appendChild(script)
  })
}

async function fetchCredits() {
  try {
    const res = await axios.get(`${API_BASE}/api/payments/credits`, authHeaders())
    credits.value = res.data.credits ?? res.data
  } catch (e) {
    console.error('Failed to fetch credits:', e)
  }
}

async function fetchPlans() {
  try {
    const res = await axios.get(`${API_BASE}/api/payments/plans`, authHeaders())
    plans.value = res.data.plans || res.data || defaultPlans()
  } catch (e) {
    plans.value = defaultPlans()
  }
}

function defaultPlans() {
  return [
    { id: 'plan_1', name: '기본', credits: 1, price: 9900, savings: null, featured: false },
    { id: 'plan_5', name: '스탠다드', credits: 5, price: 44000, savings: '11% 할인', featured: true },
    { id: 'plan_10', name: '프로', credits: 10, price: 79000, savings: '20% 할인', featured: false }
  ]
}

async function fetchHistory() {
  try {
    const res = await axios.get(`${API_BASE}/api/payments/history`, authHeaders())
    history.value = res.data.transactions || res.data || []
  } catch (e) {
    console.error('Failed to fetch history:', e)
  }
}

async function handlePurchase(plan) {
  selectedPlan.value = plan
  showPaymentWidget.value = true
  purchaseLoading.value = true

  try {
    await loadTossSDK()

    const customerKey = `${TOSS_CUSTOMER_KEY}_${currentUser.value?.id || 'guest'}`
    const tossPayments = window.TossPayments(TOSS_CLIENT_KEY)
    paymentWidget = tossPayments.widgets({ customerKey })

    await paymentWidget.setAmount({ currency: 'KRW', value: plan.price })

    // 위젯 렌더링 대기
    await new Promise(resolve => setTimeout(resolve, 100))

    await paymentWidget.renderPaymentMethods({
      selector: '#payment-method',
      variantKey: 'tiresias'
    })

    await paymentWidget.renderAgreement({
      selector: '#agreement',
      variantKey: 'tiresias'
    })
  } catch (e) {
    showPaymentWidget.value = false
    alert('결제 위젯 로드 실패: ' + (e.message || e))
  } finally {
    purchaseLoading.value = false
  }
}

async function submitPayment() {
  if (!paymentWidget || !selectedPlan.value) return
  purchaseLoading.value = true

  try {
    const orderId = `tiresias_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`

    await paymentWidget.requestPayment({
      orderId,
      orderName: `Tiresias ${selectedPlan.value.name} (${selectedPlan.value.credits} 크레딧)`,
      successUrl: `${window.location.origin}/credits?planId=${selectedPlan.value.id}`,
      failUrl: `${window.location.origin}/credits?fail=true`,
    })
  } catch (e) {
    if (e.code === 'USER_CANCEL') {
      showPaymentWidget.value = false
    } else {
      alert('결제 요청 실패: ' + (e.message || e))
    }
  } finally {
    purchaseLoading.value = false
  }
}

function cancelPayment() {
  showPaymentWidget.value = false
  selectedPlan.value = null
}

async function confirmPayment(paymentKey, orderId, amount, planId) {
  purchaseLoading.value = true
  try {
    await axios.post(`${API_BASE}/api/payments/confirm`, {
      paymentKey,
      orderId,
      amount: Number(amount),
      planId
    }, authHeaders())
    await fetchCredits()
    await fetchHistory()
    alert('결제가 완료되었습니다!')
  } catch (e) {
    alert('결제 확인 실패: ' + (e.response?.data?.error || e.message))
  } finally {
    purchaseLoading.value = false
  }
}

function checkRedirectResult() {
  const params = new URLSearchParams(window.location.search)
  const paymentKey = params.get('paymentKey')
  const orderId = params.get('orderId')
  const amount = params.get('amount')
  const planId = params.get('planId')

  if (params.get('fail') === 'true') {
    const code = params.get('code')
    const message = params.get('message')
    if (code !== 'USER_CANCEL') {
      alert(`결제 실패: ${message || '알 수 없는 오류'}`)
    }
    window.history.replaceState({}, '', window.location.pathname)
    return
  }

  if (paymentKey && orderId && amount) {
    confirmPayment(paymentKey, orderId, amount, planId)
    window.history.replaceState({}, '', window.location.pathname)
  }
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
  font-size: 1.8rem;
}

.usage-note {
  font-size: 0.72rem;
  color: var(--text-muted);
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid var(--border-color);
}

/* Info Box */
.info-box {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 14px 16px;
}

.info-title {
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 10px;
}

.info-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.info-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 0.75rem;
  color: var(--text-secondary);
  line-height: 1.4;
}

.info-check {
  color: #6366f1;
  font-weight: 600;
  flex-shrink: 0;
  font-size: 0.7rem;
  margin-top: 1px;
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

/* Plans Row */
.plans-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.plan-card {
  position: relative;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 16px 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  transition: border-color 0.2s;
}

.plan-card.featured {
  border-color: #6366f1;
}

.plan-badge {
  position: absolute;
  top: -1px;
  right: 12px;
  background: #6366f1;
  color: #fff;
  font-size: 0.62rem;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 0 0 6px 6px;
  letter-spacing: 0.02em;
}

.plan-name {
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.plan-credits {
  display: flex;
  align-items: baseline;
  gap: 3px;
  margin-bottom: 4px;
}

.plan-credits-num {
  font-size: 1.5rem;
  font-weight: 700;
  letter-spacing: -0.03em;
}

.plan-credits-unit {
  font-size: 0.7rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.plan-price {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 2px;
}

.plan-savings {
  font-size: 0.68rem;
  color: #22c55e;
  font-weight: 500;
}

.plan-btn {
  width: 100%;
  margin-top: 12px;
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  padding: 7px 14px;
  border-radius: 8px;
  font-size: 0.78rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.plan-btn:hover:not(:disabled) {
  background: var(--border-color);
}

.plan-btn-featured {
  background: #6366f1;
  border-color: #6366f1;
  color: #fff;
}

.plan-btn-featured:hover:not(:disabled) {
  background: #5558e6;
}

.plan-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
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
  width: 60px;
  flex-shrink: 0;
  font-family: 'JetBrains Mono', monospace;
  font-weight: 600;
  font-size: 0.78rem;
  text-align: right;
}

.tx-col-amount.positive {
  color: #22c55e;
}

.tx-col-amount.negative {
  color: var(--text-muted);
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

.tx-badge.purchase {
  background: rgba(99, 102, 241, 0.1);
  color: #818cf8;
}

.tx-badge.usage {
  background: rgba(156, 163, 175, 0.15);
  color: var(--text-muted);
}

.tx-badge.grant {
  background: rgba(34, 197, 94, 0.1);
  color: #22c55e;
}

/* Payment Modal */
.payment-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.payment-modal {
  background: #fff;
  border-radius: 12px;
  width: 100%;
  max-width: 540px;
  max-height: 90vh;
  overflow-y: auto;
  color: #111;
}

.payment-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  border-bottom: 1px solid #eee;
  position: relative;
}

.payment-header h3 {
  font-size: 0.9rem;
  font-weight: 600;
  margin: 0;
}

.payment-amount {
  font-size: 0.85rem;
  font-weight: 700;
  color: #6366f1;
}

.payment-close {
  position: absolute;
  right: 14px;
  top: 14px;
  background: none;
  border: none;
  font-size: 1.4rem;
  color: #999;
  cursor: pointer;
  line-height: 1;
}

.payment-close:hover {
  color: #333;
}

.payment-widget-area {
  padding: 0 20px;
  min-height: 200px;
}

.payment-agreement-area {
  padding: 0 20px;
}

.payment-submit {
  width: calc(100% - 40px);
  margin: 14px 20px 20px;
  background: #6366f1;
  color: #fff;
  border: none;
  padding: 12px;
  border-radius: 8px;
  font-size: 0.88rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.payment-submit:hover:not(:disabled) {
  background: #4f46e5;
}

.payment-submit:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Responsive */
@media (max-width: 640px) {
  .plans-row {
    grid-template-columns: 1fr;
    gap: 8px;
  }
  .plan-card {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
    text-align: left;
    padding: 14px 16px;
    gap: 12px;
  }
  .plan-card.featured {
    border-color: #6366f1;
  }
  .plan-badge {
    top: -1px;
    right: 10px;
  }
  .plan-credits {
    margin-bottom: 0;
  }
  .plan-btn {
    width: auto;
    margin-top: 0;
    padding: 7px 18px;
  }
  .tx-col-date {
    width: 90px;
    font-size: 0.65rem;
  }
  .tx-col-desc {
    display: none;
  }
}
</style>
