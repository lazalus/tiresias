<template>
  <div class="sub-page">
    <header class="sub-header">
      <router-link to="/profile" class="back-btn">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="15 18 9 12 15 6"/>
        </svg>
      </router-link>
      <h1 class="sub-title">고객센터</h1>
      <div class="spacer"></div>
    </header>

    <main class="sub-content">
      <!-- FAQ -->
      <div class="faq-header">자주 묻는 질문</div>

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
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const openFaq = ref(null)

const faqItems = [
  {
    q: '시뮬레이션은 얼마나 걸리나요?',
    a: '시뮬레이션은 데이터 크기와 설정에 따라 다르지만, 일반적으로 1~5분 이내에 완료됩니다. 복잡한 시뮬레이션의 경우 최대 10분까지 소요될 수 있습니다.'
  },
  {
    q: '이용권은 환불되나요?',
    a: '미사용 이용권에 한하여 구매일로부터 7일 이내에 환불 요청이 가능합니다. 환불은 고객센터 이메일을 통해 요청해주세요. 이미 사용된 이용권은 환불이 불가합니다.'
  },
  {
    q: '어떤 파일을 업로드할 수 있나요?',
    a: 'CSV, Excel(.xlsx) 형식의 데이터 파일을 업로드할 수 있습니다. 파일 크기는 최대 50MB까지 지원되며, 데이터는 암호화되어 안전하게 처리됩니다.'
  },
  {
    q: '시뮬레이션 결과는 얼마나 보관되나요?',
    a: '시뮬레이션 결과 및 보고서는 계정이 유지되는 동안 무기한 보관됩니다. 언제든지 보고서 탭에서 이전 결과를 확인하실 수 있습니다.'
  }
]

function toggleFaq(index) {
  openFaq.value = openFaq.value === index ? null : index
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

/* Contact Card */
.contact-card {
  display: flex;
  align-items: center;
  gap: 16px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 32px;
}

.contact-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: rgba(99, 102, 241, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #818cf8;
  flex-shrink: 0;
}

.contact-label {
  font-size: 0.8rem;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.contact-email {
  color: #818cf8;
  text-decoration: none;
  font-size: 0.92rem;
  font-weight: 500;
}

.contact-email:hover {
  text-decoration: underline;
}

/* FAQ */
.faq-header {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 12px;
}

.faq-list {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 16px;
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

/* FAQ transition */
.faq-enter-active,
.faq-leave-active {
  transition: all 0.2s ease;
}

.faq-enter-from,
.faq-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
