<template>
  <div class="landing">
    <!-- Header -->
    <header class="landing-header">
      <div class="header-container">
        <span class="logo">TIRESIAS VIEW</span>
        <nav class="header-nav">
          <a href="#features">기능</a>
          <a href="#process">작동 방식</a>
          <router-link to="/pricing">가격</router-link>
          <router-link to="/samples">샘플 보고서</router-link>
        </nav>
        <div class="header-actions">
          <router-link to="/login" class="btn-start">로그인</router-link>
        </div>
        <button class="mobile-menu-btn" @click="mobileMenuOpen = !mobileMenuOpen">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
        </button>
      </div>
      <Transition name="menu">
        <div v-if="mobileMenuOpen" class="mobile-menu">
          <a href="#features" @click="mobileMenuOpen = false">기능</a>
          <a href="#process" @click="mobileMenuOpen = false">작동 방식</a>
          <router-link to="/pricing" @click="mobileMenuOpen = false">가격</router-link>
          <router-link to="/samples" @click="mobileMenuOpen = false">샘플 보고서</router-link>
          <div class="mobile-menu-actions">
            <router-link to="/login" class="btn-start">로그인</router-link>
          </div>
        </div>
      </Transition>
    </header>

    <!-- Hero -->
    <section class="hero-section">
      <div class="hero-container">
        <div class="hero-text">
          <div class="hero-badge">AI 시나리오 분석 플랫폼</div>
          <h1 class="hero-title">자료를 업로드하면<br/>시나리오를 비교합니다</h1>
          <p class="hero-desc">정책 문서, 시장 자료, 보도자료를 업로드하면 AI 에이전트가 이해관계자 반응을 시뮬레이션하고, 시나리오별 분석 보고서를 생성합니다.</p>
          <div class="hero-cta">
            <router-link to="/signup" class="btn-primary">무료로 시작하기</router-link>
            <router-link to="/samples" class="btn-ghost">샘플 보고서 보기</router-link>
          </div>
        </div>
        <div class="hero-visual">
          <img src="/landing-hero.png" alt="AI 시뮬레이션 보고서 미리보기" class="hero-img" />
        </div>
      </div>
    </section>

    <!-- Pain Points -->
    <section class="pain-section">
      <div class="section-container">
        <div class="section-header">
          <span class="section-label">이런 고민, 익숙하시죠?</span>
          <h2 class="section-title">기존 방식의 한계를<br class="desktop-br"/>매번 느끼고 있다면</h2>
        </div>
        <div class="pain-grid">
          <div class="pain-card">
            <div class="pain-icon pain-icon--red">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
            </div>
            <h3>시나리오 분석을 수작업으로 하고 계신가요?</h3>
            <p>엑셀과 문서를 오가며 이해관계자별 반응을 수동으로 정리하면, 시간과 정확성 모두 놓치게 됩니다.</p>
          </div>
          <div class="pain-card">
            <div class="pain-icon pain-icon--orange">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
            </div>
            <h3>외주 리서치에 몇 주씩 기다리고 계신가요?</h3>
            <p>전통적인 여론조사나 리서치 외주는 비용도 높고, 결과를 받기까지 수주가 걸립니다.</p>
          </div>
          <div class="pain-card">
            <div class="pain-icon pain-icon--blue">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>
            </div>
            <h3>ChatGPT 한 줄 답변으론 부족하셨나요?</h3>
            <p>단일 AI 응답은 다수 이해관계자의 입장 차이와 시나리오 분기를 반영하지 못합니다.</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Features (alternating left-right) -->
    <section id="features" class="features-section">
      <div class="section-container">
        <div class="section-header">
          <span class="section-label">주요 기능</span>
          <h2 class="section-title">자료에서 보고서까지<br class="desktop-br"/>하나의 워크플로우</h2>
          <p class="section-subtitle">업로드한 자료의 구조를 분석하고, 다수 에이전트가 시나리오를 비교해 보고서를 만듭니다.</p>
        </div>

        <!-- Feature 1 -->
        <div class="feature-row">
          <div class="feature-content">
            <span class="feature-label feature-label--purple">구조 분석</span>
            <h3 class="feature-title">지식 그래프 자동 구축</h3>
            <p class="feature-desc">업로드한 자료에서 이해관계자, 이슈, 변수를 자동 추출하여 관계 구조를 시각화합니다.</p>
            <ul class="feature-checks">
              <li>이해관계자 · 변수 자동 식별</li>
              <li>관계 그래프 시각화</li>
              <li>PDF, Markdown, CSV 등 다양한 포맷 지원</li>
            </ul>
          </div>
          <div class="feature-visual">
            <img src="/landing-graph.png" alt="지식 그래프" class="feature-img" />
          </div>
        </div>

        <!-- Feature 2 (reversed) -->
        <div class="feature-row feature-row--reversed">
          <div class="feature-content">
            <span class="feature-label feature-label--blue">시뮬레이션</span>
            <h3 class="feature-title">다수 에이전트 시나리오 비교</h3>
            <p class="feature-desc">각 이해관계자의 입장을 가진 AI 에이전트들이 다중 라운드로 반응하며 시나리오를 비교합니다.</p>
            <ul class="feature-checks">
              <li>이해관계자별 AI 페르소나 자동 생성</li>
              <li>다중 라운드 상호작용 시뮬레이션</li>
              <li>시나리오별 반응 경로 추적</li>
            </ul>
          </div>
          <div class="feature-visual">
            <img src="/landing-agents.png" alt="에이전트 시뮬레이션" class="feature-img" />
          </div>
        </div>

        <!-- Feature 3 -->
        <div class="feature-row">
          <div class="feature-content">
            <span class="feature-label feature-label--green">보고서</span>
            <h3 class="feature-title">심층 분석 보고서 자동 생성</h3>
            <p class="feature-desc">시뮬레이션 결과를 정리한 구조화된 분석 보고서를 자동으로 생성하고 PDF로 내려받을 수 있습니다.</p>
            <ul class="feature-checks">
              <li>시나리오 비교 · 핵심 인사이트 요약</li>
              <li>웹 보고서 + PDF 다운로드</li>
              <li>보고서 기반 추가 질의 가능</li>
            </ul>
          </div>
          <div class="feature-visual">
            <img src="/landing-report.png" alt="분석 보고서" class="feature-img" />
          </div>
        </div>
      </div>
    </section>

    <!-- Mid CTA -->
    <section class="mid-cta-section">
      <div class="section-container mid-cta-container">
        <h2 class="mid-cta-title">새로운 시나리오 분석,<br class="desktop-br"/> 시작할 준비 되셨나요?</h2>
      </div>
    </section>

    <!-- Process -->
    <section id="process" class="process-section">
      <div class="section-container">
        <div class="section-header">
          <span class="section-label">작동 방식</span>
          <h2 class="section-title">자료 업로드부터 보고서까지<br class="desktop-br"/>3단계 분석 흐름</h2>
        </div>
        <div class="process-steps">
          <div class="process-step">
            <div class="step-number">01</div>
            <h3 class="step-title">자료 업로드</h3>
            <p class="step-desc">정책 문서, 보도자료, 조사 자료 등을 업로드하고 검토할 주제를 입력합니다.</p>
          </div>
          <div class="process-connector"><svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><polyline points="9 18 15 12 9 6"/></svg></div>
          <div class="process-step">
            <div class="step-number">02</div>
            <h3 class="step-title">AI 시뮬레이션</h3>
            <p class="step-desc">에이전트들이 각자의 입장에서 반응하며, 여론 확산과 시나리오를 비교합니다.</p>
          </div>
          <div class="process-connector"><svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><polyline points="9 18 15 12 9 6"/></svg></div>
          <div class="process-step">
            <div class="step-number">03</div>
            <h3 class="step-title">보고서 생성</h3>
            <p class="step-desc">시나리오 비교 결과를 요약한 분석 보고서를 생성하고 PDF로 내려받습니다.</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Use Cases -->
    <section class="usecases-section">
      <div class="section-container">
        <div class="section-header">
          <span class="section-label">활용 사례</span>
          <h2 class="section-title">다양한 분야에서 활용됩니다</h2>
        </div>
        <div class="usecases-grid">
          <div class="usecase-card usecase-card--purple">
            <div class="usecase-icon"><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg></div>
            <h3>여론 예측</h3>
            <p>정책 시행 전 국민 반응을 사전 시뮬레이션하여 여론 리스크를 최소화합니다.</p>
          </div>
          <div class="usecase-card usecase-card--blue">
            <div class="usecase-icon"><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/></svg></div>
            <h3>시장 분석</h3>
            <p>신제품 출시, 가격 정책 변경 등에 대한 소비자 반응을 예측합니다.</p>
          </div>
          <div class="usecase-card usecase-card--green">
            <div class="usecase-icon"><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg></div>
            <h3>정책 영향 평가</h3>
            <p>규제, 법안, 제도 변경이 이해관계자에게 미치는 영향을 사전 분석합니다.</p>
          </div>
          <div class="usecase-card usecase-card--red">
            <div class="usecase-icon"><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg></div>
            <h3>위기 대응 훈련</h3>
            <p>위기 상황에서의 이해관계자 반응을 시뮬레이션하여 대응 전략을 수립합니다.</p>
          </div>
        </div>
      </div>
    </section>

    <!-- FAQ -->
    <section class="faq-section">
      <div class="section-container">
        <div class="section-header">
          <span class="section-label">자주 묻는 질문</span>
          <h2 class="section-title">궁금한 점을 미리 정리했습니다</h2>
        </div>
        <div class="faq-list">
          <div v-for="(item, i) in faqItems" :key="i" class="faq-item" @click="toggleFaq(i)">
            <button class="faq-question">
              <span>{{ item.q }}</span>
              <span class="faq-chevron" :class="{ open: openFaq === i }">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
              </span>
            </button>
            <Transition name="faq">
              <div v-if="openFaq === i" class="faq-answer">
                <p>{{ item.a }}</p>
              </div>
            </Transition>
          </div>
        </div>
      </div>
    </section>

    <!-- Final CTA -->
    <section class="cta-section">
      <div class="section-container cta-container">
        <h2 class="cta-title">의사결정 전 가설 검토를<br class="desktop-br"/> 지금 시작하세요</h2>
        <p class="cta-desc">자료를 업로드하면 시나리오를 비교하고 분석 보고서를 받을 수 있습니다.</p>
        <div class="cta-actions">
          <router-link to="/signup" class="btn-primary btn-large">무료로 시작하기</router-link>
          <router-link to="/samples" class="btn-ghost btn-large">샘플 보고서 보기</router-link>
        </div>
      </div>
    </section>

    <!-- Footer -->
    <footer class="landing-footer">
      <div class="footer-container">
        <div class="footer-top">
          <div class="footer-brand">
            <span class="footer-logo">TIRESIAS VIEW</span>
            <p class="footer-copy">AI 기반 시나리오 분석 플랫폼</p>
          </div>
          <div class="footer-nav">
            <div class="footer-col">
              <span class="footer-col-title">서비스</span>
              <router-link to="/features">기능 소개</router-link>
              <router-link to="/pricing">가격 안내</router-link>
              <router-link to="/samples">샘플 보고서</router-link>
            </div>
            <div class="footer-col">
              <span class="footer-col-title">지원</span>
              <router-link to="/support">자주 묻는 질문</router-link>
              <router-link to="/support?tab=feedback">고객 의견</router-link>
              <a href="mailto:support@TIRESIAS VIEWview.com">문의하기</a>
            </div>
            <div class="footer-col">
              <span class="footer-col-title">법적 고지</span>
              <router-link to="/terms">이용약관</router-link>
              <router-link to="/privacy">개인정보처리방침</router-link>
              <router-link to="/open-source">오픈소스 고지</router-link>
            </div>
          </div>
        </div>
        <div class="footer-bottom">
          에스아이 | 대표 정희수 | 사업자등록번호 111-63-00101 | 통신판매업신고번호 2024-안양동안-0010 | support@TIRESIAS VIEWview.com
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { applySeoMeta, resetSeoMeta } from '../utils/seo.js'

const mobileMenuOpen = ref(false)
const openFaq = ref(null)

function toggleFaq(i) {
  openFaq.value = openFaq.value === i ? null : i
}

const faqItems = [
  {
    q: '테이레시아스 뷰는 무엇을 하나요?',
    a: '보고서와 정책 문서, 시장 자료를 업로드하면 AI 에이전트가 반응 시나리오를 비교하고 분석 보고서를 만듭니다.',
  },
  {
    q: '정책 시뮬레이션은 어떻게 진행되나요?',
    a: '문서 구조를 분석해 이해관계자와 이슈를 정리한 뒤, 다수 에이전트가 반응과 확산 경로를 여러 라운드로 시뮬레이션합니다.',
  },
  {
    q: '시장 반응 예측에도 쓸 수 있나요?',
    a: '신제품 출시, 가격 변경, 메시지 전략, 브랜드 이슈 같은 주제에 대해 소비자와 커뮤니티 반응 시나리오를 점검할 수 있습니다.',
  },
  {
    q: '결과물은 어떤 형태로 받나요?',
    a: '웹 보고서와 PDF 보고서로 결과를 확인할 수 있고, 생성된 보고서를 바탕으로 추가 질문도 이어갈 수 있습니다.',
  },
]

onMounted(() => {
  applySeoMeta({
    title: '테이레시아스 뷰 | 정책·시장·여론 시나리오 분석 AI',
    description: '보고서·정책 문서·시장 자료를 업로드하면 AI 에이전트가 정책 시뮬레이션, 시장 반응 예측, 여론 시나리오 분석 보고서를 생성합니다.',
    canonical: 'https://TIRESIAS VIEWview.com',
    structuredData: [
      {
        id: 'landing-software',
        data: {
          '@context': 'https://schema.org',
          '@type': 'SoftwareApplication',
          name: '테이레시아스 뷰',
          applicationCategory: 'BusinessApplication',
          operatingSystem: 'Web',
          url: 'https://TIRESIAS VIEWview.com',
          description: '보고서·정책 문서·시장 자료를 업로드하면 AI 에이전트가 정책·시장·여론 반응을 시나리오로 비교하고 분석 보고서를 생성하는 서비스입니다.',
          offers: {
            '@type': 'Offer',
            price: '9900',
            priceCurrency: 'KRW',
          },
        },
      },
      {
        id: 'landing-organization',
        data: {
          '@context': 'https://schema.org',
          '@type': 'Organization',
          name: 'Tiresias View',
          url: 'https://TIRESIAS VIEWview.com',
          logo: 'https://TIRESIAS VIEWview.com/logos1.png',
          contactPoint: {
            '@type': 'ContactPoint',
            contactType: 'customer support',
            email: 'support@TIRESIAS VIEWview.com',
            availableLanguage: ['Korean', 'English'],
          },
        },
      },
      {
        id: 'landing-faq',
        data: {
          '@context': 'https://schema.org',
          '@type': 'FAQPage',
          mainEntity: faqItems.map((item) => ({
            '@type': 'Question',
            name: item.q,
            acceptedAnswer: {
              '@type': 'Answer',
              text: item.a,
            },
          })),
        },
      },
    ],
  })
})

onUnmounted(() => {
  resetSeoMeta(['landing-software', 'landing-organization', 'landing-faq'])
})
</script>

<style scoped>
/* ── Base ── */
.landing {
  background: #ffffff;
  color: #1a1a2e;
  font-family: 'Inter', 'Noto Sans KR', system-ui, -apple-system, sans-serif;
  -webkit-font-smoothing: antialiased;
  overflow-x: hidden;
}

/* ── Header ── */
.landing-header {
  position: fixed; top: 0; left: 0; right: 0; z-index: 200;
  background: rgba(255,255,255,0.92);
  backdrop-filter: saturate(180%) blur(20px);
  -webkit-backdrop-filter: saturate(180%) blur(20px);
  border-bottom: 1px solid #f0f0f5;
}
.header-container {
  max-width: 1160px; margin: 0 auto; height: 64px;
  display: flex; align-items: center; padding: 0 32px;
}
.logo {
  font-family: 'Outfit', 'Inter', sans-serif;
  font-weight: 800; font-size: 1.25rem; letter-spacing: -0.03em;
  color: #1a1a2e;
}
.header-nav {
  display: flex; align-items: center; gap: 24px; margin-left: auto; margin-right: 24px;
}
.header-nav a {
  color: #64648a; text-decoration: none; font-size: 0.88rem; font-weight: 500;
  transition: color 0.15s;
}
.header-nav a:hover { color: #1a1a2e; }
.header-actions { display: flex; align-items: center; gap: 10px; }
.btn-login {
  color: #64648a; text-decoration: none; font-size: 0.88rem; font-weight: 500;
  padding: 8px 16px; border-radius: 8px; transition: color 0.15s;
}
.btn-login:hover { color: #1a1a2e; }
.btn-start {
  background: #6366f1; color: #fff; text-decoration: none;
  font-size: 0.88rem; font-weight: 600; padding: 9px 22px; border-radius: 10px;
  transition: background 0.15s;
}
.btn-start:hover { background: #5558e6; }
.mobile-menu-btn {
  display: none; background: none; border: none; color: #1a1a2e; cursor: pointer; padding: 4px;
}
.mobile-menu {
  display: none; flex-direction: column; padding: 12px 32px 20px; gap: 4px;
  border-top: 1px solid #f0f0f5;
}
.mobile-menu a {
  color: #64648a; text-decoration: none; font-size: 0.92rem; font-weight: 500;
  padding: 10px 0; border-bottom: 1px solid #f5f5fa;
}
.mobile-menu-actions { display: flex; gap: 10px; padding-top: 12px; }

/* ── Hero ── */
.hero-section {
  padding-top: 64px; background: linear-gradient(180deg, #f8f8fc 0%, #ffffff 100%);
}
.hero-container {
  max-width: 1160px; margin: 0 auto; padding: 80px 32px 60px;
  display: flex; align-items: center; gap: 56px;
}
.hero-text { flex: 1; max-width: 520px; }
.hero-badge {
  display: inline-block; font-size: 0.78rem; font-weight: 600; letter-spacing: 0.02em;
  color: #6366f1; background: rgba(99,102,241,0.08); padding: 6px 16px;
  border-radius: 20px; margin-bottom: 20px;
}
.hero-title {
  font-size: 2.8rem; font-weight: 800; line-height: 1.25; color: #1a1a2e;
  margin: 0 0 20px; letter-spacing: -0.03em;
}
.hero-desc {
  font-size: 1.05rem; line-height: 1.7; color: #64648a; margin: 0 0 32px;
}
.hero-cta { display: flex; gap: 12px; flex-wrap: wrap; }
.btn-primary {
  background: #6366f1; color: #fff; text-decoration: none;
  font-size: 0.95rem; font-weight: 600; padding: 14px 32px; border-radius: 12px;
  border: none; cursor: pointer; transition: background 0.15s;
}
.btn-primary:hover { background: #5558e6; }
.btn-ghost {
  color: #64648a; text-decoration: none; font-size: 0.95rem; font-weight: 500;
  padding: 14px 32px; border-radius: 12px; border: 1px solid #e0e0ea;
  transition: border-color 0.15s, color 0.15s;
}
.btn-ghost:hover { border-color: #c0c0d0; color: #1a1a2e; }
.btn-outline {
  color: #6366f1; text-decoration: none; font-size: 0.95rem; font-weight: 600;
  padding: 14px 32px; border-radius: 12px; border: 2px solid #6366f1;
  transition: background 0.15s;
}
.btn-outline:hover { background: rgba(99,102,241,0.06); }
.hero-visual {
  flex: 1; max-width: 540px; border-radius: 20px; overflow: hidden;
  border: 1px solid #e8e8f0; box-shadow: 0 20px 60px rgba(0,0,0,0.08);
}
.hero-img { display: block; width: 100%; height: auto; }

/* ── Sections common ── */
.section-container { max-width: 1160px; margin: 0 auto; padding: 100px 32px; }
.section-header { text-align: center; margin-bottom: 56px; }
.section-label {
  display: inline-block; font-size: 0.78rem; font-weight: 700; letter-spacing: 0.04em;
  color: #6366f1; margin-bottom: 12px; text-transform: uppercase;
}
.section-title {
  font-size: 2rem; font-weight: 800; line-height: 1.35; color: #1a1a2e;
  margin: 0 0 14px; letter-spacing: -0.02em;
}
.section-subtitle { font-size: 1rem; color: #64648a; line-height: 1.65; max-width: 560px; margin: 0 auto; }

/* ── Pain Points ── */
.pain-section { background: #ffffff; }
.pain-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; }
.pain-card {
  background: #fafafe; border: 1px solid #ededf5; border-radius: 16px; padding: 32px 28px;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.pain-card:hover { border-color: #d0d0e0; box-shadow: 0 8px 32px rgba(0,0,0,0.04); }
.pain-icon {
  width: 48px; height: 48px; border-radius: 12px; display: flex;
  align-items: center; justify-content: center; margin-bottom: 20px;
}
.pain-icon--red { background: rgba(239,68,68,0.08); color: #ef4444; }
.pain-icon--orange { background: rgba(245,158,11,0.08); color: #f59e0b; }
.pain-icon--blue { background: rgba(59,130,246,0.08); color: #3b82f6; }
.pain-card h3 { font-size: 1rem; font-weight: 700; color: #1a1a2e; margin: 0 0 10px; line-height: 1.5; }
.pain-card p { font-size: 0.88rem; color: #64648a; line-height: 1.65; margin: 0; }

/* ── Features (alternating) ── */
.features-section { background: #f8f8fc; }
.feature-row {
  display: flex; align-items: center; gap: 56px; margin-bottom: 80px;
}
.feature-row:last-child { margin-bottom: 0; }
.feature-row--reversed { flex-direction: row-reverse; }
.feature-content { flex: 1; }
.feature-visual {
  flex: 1; border-radius: 20px; overflow: hidden;
  border: 1px solid #e8e8f0; box-shadow: 0 12px 40px rgba(0,0,0,0.06);
}
.feature-img { display: block; width: 100%; height: auto; }
.feature-label {
  display: inline-block; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.04em;
  padding: 4px 12px; border-radius: 6px; margin-bottom: 14px; text-transform: uppercase;
}
.feature-label--purple { background: rgba(99,102,241,0.08); color: #6366f1; }
.feature-label--blue { background: rgba(59,130,246,0.08); color: #3b82f6; }
.feature-label--green { background: rgba(34,197,94,0.08); color: #16a34a; }
.feature-title {
  font-size: 1.5rem; font-weight: 800; color: #1a1a2e; margin: 0 0 12px;
  letter-spacing: -0.01em; line-height: 1.35;
}
.feature-desc { font-size: 0.95rem; color: #64648a; line-height: 1.7; margin: 0 0 20px; }
.feature-checks { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 10px; }
.feature-checks li {
  font-size: 0.88rem; color: #3a3a5c; padding-left: 24px; position: relative; line-height: 1.5;
}
.feature-checks li::before {
  content: ''; position: absolute; left: 0; top: 5px;
  width: 16px; height: 16px; border-radius: 50%;
  background: rgba(99,102,241,0.1);
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='10' viewBox='0 0 24 24' fill='none' stroke='%236366f1' stroke-width='3'%3E%3Cpolyline points='20 6 9 17 4 12'/%3E%3C/svg%3E");
  background-repeat: no-repeat; background-position: center; background-size: 10px;
}

/* ── Mid CTA ── */
.mid-cta-section { background: #6366f1; }
.mid-cta-container { text-align: center; padding-top: 72px; padding-bottom: 72px; }
.mid-cta-title {
  font-size: 2rem; font-weight: 800; color: #fff; margin: 0 0 14px;
  letter-spacing: -0.02em; line-height: 1.35;
}
.mid-cta-desc { font-size: 1rem; color: rgba(255,255,255,0.75); margin: 0; }

/* ── Process ── */
.process-section { background: #ffffff; }
.process-steps { display: flex; align-items: flex-start; justify-content: center; }
.process-step { flex: 1; text-align: center; padding: 0 24px; max-width: 280px; }
.step-number {
  font-size: 2.8rem; font-weight: 800; color: rgba(99,102,241,0.15);
  margin-bottom: 14px; font-family: 'Outfit', 'Inter', sans-serif;
}
.step-title { font-size: 1.08rem; font-weight: 700; color: #1a1a2e; margin: 0 0 10px; }
.step-desc { font-size: 0.88rem; color: #64648a; line-height: 1.65; margin: 0; }
.process-connector {
  display: flex; align-items: center; color: #d0d0e0; flex-shrink: 0; padding-top: 24px;
}

/* ── Use Cases ── */
.usecases-section { background: #f8f8fc; }
.usecases-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; }
.usecase-card {
  background: #fff; border: 1px solid #ededf5; border-radius: 16px; padding: 28px 24px;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.usecase-card:hover { box-shadow: 0 8px 28px rgba(0,0,0,0.05); }
.usecase-icon { margin-bottom: 16px; }
.usecase-card--purple .usecase-icon { color: #6366f1; }
.usecase-card--blue .usecase-icon { color: #3b82f6; }
.usecase-card--green .usecase-icon { color: #16a34a; }
.usecase-card--red .usecase-icon { color: #ef4444; }
.usecase-card--purple:hover { border-color: rgba(99,102,241,0.3); }
.usecase-card--blue:hover { border-color: rgba(59,130,246,0.3); }
.usecase-card--green:hover { border-color: rgba(34,197,94,0.3); }
.usecase-card--red:hover { border-color: rgba(239,68,68,0.3); }
.usecase-card h3 { font-size: 1rem; font-weight: 700; color: #1a1a2e; margin: 0 0 8px; }
.usecase-card p { font-size: 0.85rem; color: #64648a; line-height: 1.65; margin: 0; }

/* ── FAQ ── */
.faq-section { background: #ffffff; }
.faq-list { max-width: 720px; margin: 0 auto; }
.faq-item {
  border-bottom: 1px solid #ededf5; cursor: pointer;
}
.faq-question {
  width: 100%; display: flex; align-items: center; justify-content: space-between;
  padding: 22px 0; background: none; border: none; cursor: pointer;
  font-size: 1rem; font-weight: 600; color: #1a1a2e; text-align: left;
  font-family: inherit; gap: 16px;
}
.faq-chevron { flex-shrink: 0; color: #a0a0b8; transition: transform 0.25s; }
.faq-chevron.open { transform: rotate(180deg); }
.faq-answer { padding: 0 0 22px; }
.faq-answer p { font-size: 0.92rem; color: #64648a; line-height: 1.75; margin: 0; }
.faq-enter-active, .faq-leave-active { transition: all 0.2s ease; }
.faq-enter-from, .faq-leave-to { opacity: 0; transform: translateY(-4px); }

/* ── Final CTA ── */
.cta-section { background: linear-gradient(180deg, #f8f8fc 0%, #eeeef8 100%); }
.cta-container { text-align: center; padding-top: 80px; padding-bottom: 80px; }
.cta-title {
  font-size: 2.2rem; font-weight: 800; color: #1a1a2e; margin: 0 0 14px;
  letter-spacing: -0.02em; line-height: 1.35;
}
.cta-desc { font-size: 1rem; color: #64648a; margin: 0 0 32px; }
.cta-actions { display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; }
.btn-large { padding: 16px 40px; font-size: 1rem; }

/* ── Footer ── */
.landing-footer { background: #1a1a2e; color: #a0a0b8; }
.footer-container { max-width: 1160px; margin: 0 auto; padding: 48px 32px 32px; }
.footer-top { display: flex; justify-content: space-between; gap: 40px; margin-bottom: 40px; }
.footer-brand { max-width: 240px; }
.footer-logo {
  font-family: 'Outfit', 'Inter', sans-serif; font-weight: 800;
  font-size: 1.2rem; letter-spacing: -0.03em; color: #fff;
}
.footer-copy { font-size: 0.82rem; color: #6a6a88; margin: 8px 0 0; line-height: 1.5; }
.footer-nav { display: flex; gap: 56px; }
.footer-col { display: flex; flex-direction: column; gap: 8px; }
.footer-col-title {
  font-size: 0.75rem; font-weight: 700; color: #fff; text-transform: uppercase;
  letter-spacing: 0.06em; margin-bottom: 4px;
}
.footer-col a { font-size: 0.82rem; color: #6a6a88; text-decoration: none; transition: color 0.15s; }
.footer-col a:hover { color: #a0a0b8; }
.footer-bottom {
  border-top: 1px solid rgba(255,255,255,0.06); padding-top: 24px;
  font-size: 0.75rem; color: #44445a; text-align: center;
}

/* ── Helpers ── */
.desktop-br { display: none; }
@media (min-width: 1024px) { .desktop-br { display: inline; } }

/* ── Menu transitions ── */
.menu-enter-active, .menu-leave-active { transition: all 0.2s ease; }
.menu-enter-from, .menu-leave-to { opacity: 0; transform: translateY(-4px); }

/* ── Mobile ── */
@media (max-width: 1023px) {
  .header-container { height: 56px; padding: 0 20px; }
  .header-nav { display: none; }
  .header-actions { display: none; }
  .mobile-menu-btn { display: block; margin-left: auto; }
  .mobile-menu { display: flex; }

  .hero-container { flex-direction: column-reverse; padding: 0; gap: 0; }
  .hero-visual { width: 100%; max-width: 100%; border-radius: 0; border: none; box-shadow: none; }
  .hero-img { border-radius: 0; }
  .hero-text { max-width: 100%; padding: 28px 24px 40px; }
  .hero-badge { font-size: 0.72rem; margin-bottom: 14px; }
  .hero-title { font-size: 1.8rem; margin-bottom: 14px; }
  .hero-desc { font-size: 0.9rem; margin-bottom: 24px; }
  .hero-cta { flex-direction: column; gap: 10px; }
  .btn-primary, .btn-ghost, .btn-outline { text-align: center; padding: 14px 24px; font-size: 0.9rem; }

  .section-container { padding: 64px 20px; }
  .section-header { margin-bottom: 36px; }
  .section-title { font-size: 1.5rem; }

  .pain-grid { grid-template-columns: 1fr; gap: 14px; }
  .pain-card { padding: 24px 20px; }

  .feature-row, .feature-row--reversed { flex-direction: column; gap: 28px; margin-bottom: 56px; }
  .feature-visual { width: 100%; }
  .feature-title { font-size: 1.25rem; }

  .mid-cta-title { font-size: 1.5rem; }

  .process-steps { flex-direction: column; gap: 0; align-items: stretch; }
  .process-step { text-align: left; padding: 20px 0; display: flex; gap: 16px; align-items: flex-start; max-width: 100%; }
  .step-number { font-size: 1.8rem; margin-bottom: 0; min-width: 44px; flex-shrink: 0; }
  .process-connector { display: none; }

  .usecases-grid { grid-template-columns: 1fr; gap: 12px; }
  .usecase-card { display: flex; gap: 16px; align-items: flex-start; padding: 22px 20px; }
  .usecase-icon { margin-bottom: 0; flex-shrink: 0; padding-top: 2px; }

  .cta-title { font-size: 1.5rem; }
  .btn-large { padding: 14px 32px; display: block; }
  .cta-actions { flex-direction: column; }

  .footer-top { flex-direction: column; gap: 32px; }
  .footer-nav { gap: 32px; flex-wrap: wrap; }
  .footer-container { padding: 32px 20px 24px; }
}
</style>
