<template>
  <div class="app-screen">
    <!-- App Header -->
    <header class="app-header">
      <div class="header-inner">
        <div class="header-left">
          <router-link to="/" class="header-home">
            <img src="/logoss.png" alt="Tiresias View" class="app-logo" />
            <span class="app-name">Tiresias View</span>
          </router-link>
        </div>
        <div class="header-right">
          <router-link to="/" class="header-link">홈</router-link>
        </div>
      </div>
    </header>

    <main class="credits-main">
      <!-- Current Credits -->
      <div class="credits-hero">
        <div class="credits-label">보유 크레딧</div>
        <div class="credits-number">{{ credits ?? '-' }}</div>
        <div class="credits-sub">시뮬레이션 1회 실행에 1 크레딧이 소모됩니다</div>
      </div>

      <!-- Plans Grid -->
      <section class="section-block">
        <h2 class="section-title">이용권 구매</h2>
        <div class="plans-grid">
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
              <span class="plan-credits-label">크레딧</span>
            </div>
            <div class="plan-price">{{ plan.price.toLocaleString() }}원</div>
            <div v-if="plan.savings" class="plan-savings">{{ plan.savings }}</div>
            <button class="plan-btn" @click="handlePurchase(plan)" :disabled="purchaseLoading">
              구매
            </button>
          </div>
        </div>
      </section>

      <!-- Transaction History -->
      <section class="section-block">
        <h2 class="section-title">거래 내역</h2>
        <div v-if="history.length === 0" class="empty-state">
          거래 내역이 없습니다
        </div>
        <div v-else class="history-list">
          <div v-for="tx in history" :key="tx.id" class="history-item">
            <div class="history-left">
              <span class="history-type" :class="tx.type">
                {{ tx.type === 'purchase' ? '구매' : tx.type === 'usage' ? '사용' : tx.type === 'grant' ? '지급' : tx.type }}
              </span>
              <span class="history-desc">{{ tx.description }}</span>
            </div>
            <div class="history-right">
              <span class="history-amount" :class="{ positive: tx.amount > 0, negative: tx.amount < 0 }">
                {{ tx.amount > 0 ? '+' : '' }}{{ tx.amount }}
              </span>
              <span class="history-date">{{ formatDate(tx.created_at) }}</span>
            </div>
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
          <button class="payment-close" @click="cancelPayment">×</button>
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
import { ref, onMounted, onUnmounted } from 'vue'
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
    { id: 'plan_1', name: '기본', credits: 1, price: 10000, savings: null, featured: false },
    { id: 'plan_5', name: '스탠다드', credits: 5, price: 45000, savings: '10% 할인', featured: true },
    { id: 'plan_10', name: '프로', credits: 10, price: 80000, savings: '20% 할인', featured: false }
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
  max-width: 780px;
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
  font-weight: 600;
  font-size: 0.95rem;
  letter-spacing: -0.01em;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-link {
  color: rgba(255, 255, 255, 0.4);
  text-decoration: none;
  font-size: 0.82rem;
  font-weight: 500;
  padding: 6px 14px;
  border-radius: 8px;
  transition: color 0.2s, background 0.2s;
}

.header-link:hover {
  color: rgba(255, 255, 255, 0.9);
  background: rgba(255, 255, 255, 0.06);
}

/* Main */
.credits-main {
  max-width: 780px;
  margin: 0 auto;
  padding: 48px 24px 80px;
}

/* Credits Hero */
.credits-hero {
  text-align: center;
  margin-bottom: 48px;
  padding: 40px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 20px;
  position: relative;
  overflow: hidden;
}

.credits-hero::before {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse 300px 200px at 50% 0%, rgba(99, 102, 241, 0.08), transparent);
  pointer-events: none;
}

.credits-label {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.4);
  font-weight: 500;
  margin-bottom: 8px;
  position: relative;
}

.credits-number {
  font-size: 3.5rem;
  font-weight: 800;
  letter-spacing: -0.04em;
  background: linear-gradient(135deg, #818cf8, #6366f1);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  position: relative;
}

.credits-sub {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.3);
  margin-top: 8px;
  position: relative;
}

/* Section */
.section-block {
  margin-bottom: 48px;
}

.section-title {
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 20px;
  letter-spacing: -0.01em;
}

/* Plans Grid */
.plans-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.plan-card {
  position: relative;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 16px;
  padding: 28px 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  transition: all 0.3s;
}

.plan-card:hover {
  border-color: rgba(255, 255, 255, 0.12);
  transform: translateY(-2px);
}

.plan-card.featured {
  border-color: rgba(99, 102, 241, 0.3);
  background: rgba(99, 102, 241, 0.04);
  box-shadow: 0 0 40px -10px rgba(99, 102, 241, 0.15);
}

.plan-badge {
  position: absolute;
  top: -1px;
  right: 20px;
  background: #6366f1;
  color: #fff;
  font-size: 0.68rem;
  font-weight: 600;
  padding: 4px 12px;
  border-radius: 0 0 8px 8px;
  letter-spacing: 0.02em;
}

.plan-name {
  font-size: 0.85rem;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.5);
  margin-bottom: 16px;
}

.plan-credits {
  display: flex;
  align-items: baseline;
  gap: 6px;
  margin-bottom: 8px;
}

.plan-credits-num {
  font-size: 2.2rem;
  font-weight: 800;
  letter-spacing: -0.03em;
}

.plan-credits-label {
  font-size: 0.82rem;
  color: rgba(255, 255, 255, 0.4);
  font-weight: 500;
}

.plan-price {
  font-size: 1rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 4px;
}

.plan-savings {
  font-size: 0.75rem;
  color: #4ade80;
  font-weight: 500;
  margin-bottom: 4px;
}

.plan-btn {
  width: 100%;
  margin-top: 20px;
  background: #6366f1;
  border: none;
  color: #fff;
  padding: 10px 20px;
  border-radius: 10px;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.plan-btn:hover:not(:disabled) {
  background: #5558e6;
  box-shadow: 0 0 20px rgba(99, 102, 241, 0.3);
  transform: translateY(-1px);
}

.plan-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* History */
.empty-state {
  text-align: center;
  padding: 40px;
  color: rgba(255, 255, 255, 0.25);
  font-size: 0.88rem;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.04);
  border-radius: 14px;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 14px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.02);
}

.history-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.03);
  transition: background 0.15s;
}

.history-item:last-child {
  border-bottom: none;
}

.history-item:hover {
  background: rgba(255, 255, 255, 0.02);
}

.history-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.history-type {
  font-size: 0.72rem;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 20px;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.history-type.purchase {
  background: rgba(99, 102, 241, 0.1);
  color: #818cf8;
}

.history-type.usage {
  background: rgba(245, 158, 11, 0.1);
  color: #fbbf24;
}

.history-type.grant {
  background: rgba(34, 197, 94, 0.1);
  color: #4ade80;
}

.history-desc {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.6);
}

.history-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.history-amount {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.88rem;
  font-weight: 600;
}

.history-amount.positive {
  color: #4ade80;
}

.history-amount.negative {
  color: #f87171;
}

.history-date {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.72rem;
  color: rgba(255, 255, 255, 0.25);
  min-width: 120px;
  text-align: right;
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
  border-radius: 16px;
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
  padding: 20px 24px;
  border-bottom: 1px solid #eee;
  position: relative;
}

.payment-header h3 {
  font-size: 1rem;
  font-weight: 600;
  margin: 0;
}

.payment-amount {
  font-size: 0.9rem;
  font-weight: 700;
  color: #6366f1;
}

.payment-close {
  position: absolute;
  right: 16px;
  top: 16px;
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #999;
  cursor: pointer;
  line-height: 1;
}

.payment-close:hover {
  color: #333;
}

.payment-widget-area {
  padding: 0 24px;
  min-height: 200px;
}

.payment-agreement-area {
  padding: 0 24px;
}

.payment-submit {
  width: calc(100% - 48px);
  margin: 16px 24px 24px;
  background: #6366f1;
  color: #fff;
  border: none;
  padding: 14px;
  border-radius: 10px;
  font-size: 0.95rem;
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
  .credits-main {
    padding: 32px 16px 80px;
  }
  .plans-grid {
    grid-template-columns: 1fr;
  }
  .credits-number {
    font-size: 2.5rem;
  }
  .history-left {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
  .history-right {
    flex-direction: column;
    align-items: flex-end;
    gap: 4px;
  }
}
</style>
