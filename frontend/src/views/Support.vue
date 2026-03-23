<template>
  <div class="sub-page">
    <header class="sub-header">
      <router-link to="/profile?from=support" class="back-btn">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="15 18 9 12 15 6"/>
        </svg>
      </router-link>
      <h1 class="sub-title">고객센터</h1>
      <div class="spacer"></div>
    </header>

    <main class="sub-content">
      <!-- FAQ 섹션 -->
      <div class="collapsible-section">
        <button class="section-toggle" @click="faqOpen = !faqOpen">
          <span class="section-toggle-label">자주 묻는 질문</span>
          <span class="section-toggle-icon" :class="{ open: faqOpen }">›</span>
        </button>
        <Transition name="section">
          <div v-if="faqOpen" class="section-body">
            <div class="faq-list">
              <div class="faq-item" v-for="(item, i) in faqItems" :key="i">
                <button class="faq-question" @click="toggleFaq(i)">
                  <span>{{ item.q }}</span>
                  <span class="faq-toggle" :class="{ open: openFaq === i }">›</span>
                </button>
                <Transition name="faq">
                  <div v-if="openFaq === i" class="faq-answer">
                    <p>{{ item.a }}</p>
                  </div>
                </Transition>
              </div>
            </div>
          </div>
        </Transition>
      </div>

      <!-- 고객 의견 섹션 -->
      <div class="collapsible-section">
        <button class="section-toggle" @click="feedbackOpen = !feedbackOpen">
          <span class="section-toggle-label">고객 의견</span>
          <span class="section-toggle-icon" :class="{ open: feedbackOpen }">›</span>
        </button>
        <Transition name="section">
          <div v-if="feedbackOpen" class="section-body">
            <div class="feedback-card">
              <div class="feedback-types">
                <button
                  v-for="option in feedbackTypes"
                  :key="option.value"
                  type="button"
                  class="feedback-type-chip"
                  :class="{ active: selectedType === option.value }"
                  @click="selectedType = option.value"
                >
                  {{ option.label }}
                </button>
              </div>

              <div class="feedback-grid">
                <label class="feedback-field">
                  <span class="feedback-label">이름</span>
                  <input v-model="form.name" class="feedback-input" type="text" placeholder="이름 또는 닉네임" />
                </label>
                <label class="feedback-field">
                  <span class="feedback-label">이메일</span>
                  <input v-model="form.email" class="feedback-input" type="email" placeholder="회신 받을 이메일" />
                </label>
              </div>

              <label class="feedback-field">
                <span class="feedback-label">내용</span>
                <textarea
                  v-model="form.message"
                  class="feedback-textarea"
                  placeholder="서비스를 사용하면서 느낀 점, 문의 사항, 불편했던 점, 개선 아이디어를 자유롭게 적어주세요."
                />
              </label>

              <p class="feedback-note">
                접수된 의견은 고객센터 메일로 전달되며, 필요한 경우 입력하신 이메일로 회신드립니다.
              </p>

              <div v-if="submitError" class="feedback-error">{{ submitError }}</div>
              <div v-if="submitSuccess" class="feedback-success">{{ submitSuccess }}</div>

              <div class="feedback-actions">
                <button class="feedback-submit" :disabled="submitting" @click="handleSubmit">
                  {{ submitting ? '접수 중...' : '고객 의견 보내기' }}
                </button>
              </div>
            </div>
          </div>
        </Transition>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { currentUser, getToken } from '../store/auth.js'
import { sendSupportFeedback } from '../api/support.js'

const faqOpen = ref(false)
const feedbackOpen = ref(false)
const openFaq = ref(null)
const submitting = ref(false)
const submitError = ref('')
const submitSuccess = ref('')
const selectedType = ref('inquiry')
const form = ref({
  name: currentUser.value?.nickname || currentUser.value?.name || '',
  email: currentUser.value?.email || '',
  message: '',
})

const feedbackTypes = [
  { value: 'inquiry', label: '문의하기' },
  { value: 'issue', label: '불편사항 접수' },
  { value: 'improvement', label: '서비스 개선 제안' },
]

const faqItems = [
  {
    q: 'Tiresias View는 무엇을 하는 서비스인가요?',
    a: '업로드한 문서와 입력한 주제를 바탕으로 온톨로지와 지식 그래프를 만들고, AI 페르소나와 환경을 준비한 뒤, 다중 라운드 시뮬레이션과 보고서 생성을 이어서 수행하는 예측 시뮬레이션 서비스입니다.'
  },
  {
    q: '가격은 어떻게 결정되나요?',
    a: '가격은 업로드한 파일 수, 총 용량, 예상 페이지 수, 분석 깊이 등을 기준으로 실시간 견적이 계산됩니다. 결제 직전에 예상 비용이 표시되며, 승인된 금액과 주문 정보가 일치할 때만 결제가 확정됩니다.'
  },
  {
    q: '왜 이런 방식이 일반적인 조사나 외주 시뮬레이션보다 효율적인가요?',
    a: 'Tiresias View는 단일 응답형 AI가 아니라 자료 해석, 구조 분석, 행위자 모델 생성, 다중 라운드 시뮬레이션, 보고서 작성을 한 흐름으로 수행합니다. 전통적인 여론조사, 외부 리서치, 수작업 시나리오 분석처럼 일정과 인력비를 크게 들이지 않고도 초기 가설 검토와 시나리오 비교를 빠르게 반복할 수 있어, 탐색 단계에서는 더 낮은 비용과 짧은 리드타임으로 활용할 수 있습니다.'
  },
  {
    q: '결제했는데 대기열에 들어가면 추가로 돈이 빠지나요?',
    a: '아닙니다. 같은 프로젝트가 대기열에 들어가더라도 추가 과금은 되지 않습니다. 대기열은 순번에 따라 자동으로 다시 시도되며, 이미 결제된 주문은 해당 프로젝트에 묶여 유지됩니다.'
  },
  {
    q: '결제 후 오류가 나면 어떻게 처리되나요?',
    a: '프로젝트 생성 전 단계에서 회사 시스템 오류로 시작에 실패하면 주문은 확정 사용 처리되지 않도록 설계되어 있습니다. 프로젝트 생성 이후 회사 귀책으로 정상적인 이용이 불가능한 경우에는 재실행, 크레딧 복구 또는 환불 가능 여부를 개별 검토합니다.'
  },
  {
    q: '어떤 파일을 업로드할 수 있나요?',
    a: '현재 PDF, Markdown, TXT, CSV 파일을 지원합니다. 내부 보고서, 기사, 논문, 회의록, 리서치 메모처럼 텍스트 기반 자료가 적합합니다. 법령상 근거 없이 타인의 민감정보나 불법 자료를 업로드해서는 안 됩니다.'
  },
  {
    q: '시뮬레이션은 얼마나 걸리나요?',
    a: '문서 크기, 그래프 복잡도, 대기열 상황에 따라 달라집니다. 보통 문서 분석, 그래프 구축, 환경 준비, 시뮬레이션 실행, 보고서 생성이 순차 진행되며, 큰 프로젝트나 혼잡 시간대에는 더 오래 걸릴 수 있습니다.'
  },
  {
    q: '업로드한 데이터는 어디에 저장되고 누구에게 전달되나요?',
    a: '서비스 운영을 위해 Cloudflare 인프라(Workers, D1, R2)를 사용하며, AI 분석·보고서 생성을 위해 현재 OpenAI API를 사용합니다. 결제는 토스페이먼츠를 통해 처리됩니다. 자세한 내용은 개인정보처리방침에서 확인할 수 있습니다.'
  },
  {
    q: '시뮬레이션 결과를 그대로 의사결정에 써도 되나요?',
    a: '아니요. 결과물은 참고용 분석 자료이며 실제 시장·여론·정책 반응을 보장하지 않습니다. 투자, 법률, 의료, 정책, 사업 의사결정에는 반드시 추가 검토와 전문가 판단을 병행해야 합니다.'
  },
  {
    q: '프로젝트와 보고서는 직접 삭제할 수 있나요?',
    a: '네. 프로젝트와 보고서는 서비스 내에서 삭제할 수 있으며, 삭제 시 관련 저장 데이터도 함께 정리됩니다. 다만 결제기록, 접근기록 등은 관계 법령에 따라 일정 기간 보관될 수 있습니다.'
  }
]

function toggleFaq(index) {
  openFaq.value = openFaq.value === index ? null : index
}

async function handleSubmit() {
  submitError.value = ''
  submitSuccess.value = ''

  if (!form.value.name.trim() || !form.value.email.trim() || !form.value.message.trim()) {
    submitError.value = '이름, 이메일, 내용을 모두 입력해주세요.'
    return
  }

  submitting.value = true
  try {
    await sendSupportFeedback({
      category: selectedType.value,
      name: form.value.name,
      email: form.value.email,
      message: form.value.message,
    }, getToken())

    submitSuccess.value = '고객 의견이 접수되었습니다. 확인 후 필요한 경우 회신드리겠습니다.'
    form.value.message = ''
  } catch (error) {
    submitError.value = error?.response?.data?.error || '의견 접수 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.'
  } finally {
    submitting.value = false
  }
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
  padding: 32px 20px 64px;
}

.collapsible-section {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  overflow: hidden;
  margin-bottom: 16px;
}

.section-toggle {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 20px;
  background: none;
  border: none;
  color: var(--text-primary);
  font-size: 0.95rem;
  font-weight: 600;
  text-align: left;
  cursor: pointer;
  font-family: inherit;
  transition: background 0.15s;
}

.section-toggle:hover {
  background: var(--bg-tertiary, var(--border-color));
}

.section-toggle-label {
  letter-spacing: -0.01em;
}

.section-toggle-icon {
  color: var(--text-muted);
  font-size: 1.4rem;
  font-weight: 300;
  transition: transform 0.2s;
  flex-shrink: 0;
  margin-left: 12px;
}

.section-toggle-icon.open {
  transform: rotate(90deg);
}

.section-body {
  padding: 0 20px 20px;
}

.section-enter-active,
.section-leave-active {
  transition: all 0.2s ease;
}

.section-enter-from,
.section-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

.feedback-card {
  padding: 0;
}

.feedback-types {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 18px;
}

.feedback-type-chip {
  border: 1px solid var(--border-color);
  background: transparent;
  color: var(--text-secondary);
  border-radius: 999px;
  padding: 9px 14px;
  font-size: 0.82rem;
  font-weight: 500;
  cursor: pointer;
  font-family: inherit;
}

.feedback-type-chip.active {
  background: rgba(99, 102, 241, 0.12);
  border-color: rgba(99, 102, 241, 0.3);
  color: #818cf8;
}

.feedback-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 12px;
}

.feedback-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}

.feedback-label {
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--text-secondary);
}

.feedback-input,
.feedback-textarea {
  width: 100%;
  border: 1px solid var(--border-color);
  background: var(--bg-primary);
  color: var(--text-primary);
  border-radius: 12px;
  padding: 12px 14px;
  font-family: inherit;
  font-size: 0.88rem;
  outline: none;
}

.feedback-input:focus,
.feedback-textarea:focus {
  border-color: rgba(99, 102, 241, 0.45);
}

.feedback-textarea {
  min-height: 148px;
  resize: vertical;
  line-height: 1.65;
}

.feedback-note {
  font-size: 0.78rem;
  line-height: 1.6;
  color: var(--text-muted);
  margin: 2px 0 0;
}

.feedback-error,
.feedback-success {
  margin-top: 12px;
  border-radius: 12px;
  padding: 12px 14px;
  font-size: 0.82rem;
  line-height: 1.6;
}

.feedback-error {
  background: rgba(239, 68, 68, 0.08);
  border: 1px solid rgba(239, 68, 68, 0.18);
  color: #ef9a9a;
}

.feedback-success {
  background: rgba(34, 197, 94, 0.08);
  border: 1px solid rgba(34, 197, 94, 0.18);
  color: #86efac;
}

.feedback-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.feedback-submit {
  border: none;
  background: #6366f1;
  color: #fff;
  border-radius: 12px;
  padding: 12px 18px;
  font-size: 0.88rem;
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
}

.feedback-submit:disabled {
  opacity: 0.6;
  cursor: default;
}

.faq-list {
  overflow: hidden;
}

.faq-item + .faq-item {
  border-top: 1px solid var(--border-color);
}

.faq-question {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 20px;
  background: none;
  border: none;
  color: var(--text-primary);
  font-size: 0.9rem;
  font-weight: 500;
  text-align: left;
  cursor: pointer;
  transition: background 0.15s;
  font-family: inherit;
}

.faq-question:hover {
  background: var(--bg-secondary);
}

.faq-toggle {
  color: var(--text-muted);
  font-size: 1.4rem;
  font-weight: 300;
  transition: transform 0.2s;
  flex-shrink: 0;
  margin-left: 12px;
}

.faq-toggle.open {
  transform: rotate(90deg);
}

.faq-answer {
  padding: 0 20px 18px;
  overflow: hidden;
}

.faq-answer p {
  font-size: 0.85rem;
  color: var(--text-secondary);
  line-height: 1.7;
  margin: 0;
}

.faq-enter-active,
.faq-leave-active {
  transition: all 0.2s ease;
}

.faq-enter-from,
.faq-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

@media (max-width: 720px) {
  .feedback-grid {
    grid-template-columns: 1fr;
    gap: 0;
  }

  .feedback-card {
    padding: 18px;
  }

  .feedback-actions {
    justify-content: stretch;
  }

  .feedback-submit {
    width: 100%;
  }
}
</style>
