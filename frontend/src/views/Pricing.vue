<template>
  <div class="pricing-page">
    <header class="page-header">
      <div class="header-container">
        <router-link to="/" class="logo-link">
          <span class="logo">TIRESIAS VIEW</span>
        </router-link>
        <nav class="header-nav">
          <router-link to="/features">기능</router-link>
          <router-link to="/samples">샘플 보고서</router-link>
          <router-link to="/support">FAQ</router-link>
        </nav>
        <div class="header-actions">
          <router-link to="/login" class="btn-header">로그인</router-link>
        </div>
      </div>
    </header>

    <main class="page-main">
      <!-- Hero -->
      <section class="hero">
        <span class="eyebrow">가격 안내</span>
        <h1>파일 규모에 맞춰 견적을 먼저 확인하고 결제합니다</h1>
        <p class="hero-desc">
          테이레시아스 뷰는 고정 요금제가 아니라 업로드한 파일 수, 총 용량, 예상 페이지 수, 분석 깊이를 바탕으로
          프로젝트별 견적을 먼저 보여준 뒤 결제를 진행합니다.
        </p>
        <div class="hero-actions">
          <router-link to="/signup" class="btn-primary">견적 확인하기</router-link>
          <router-link to="/samples" class="btn-ghost">샘플 보고서 보기</router-link>
        </div>
      </section>

      <!-- Cost Structure -->
      <section class="section section--alt">
        <div class="section-head">
          <span class="eyebrow">비용 구조</span>
          <h2>견적은 이렇게 계산됩니다</h2>
        </div>
        <div class="grid three">
          <article class="card">
            <h3>업로드 자료 규모</h3>
            <p>파일 수, 페이지 수, 추출 텍스트 양이 클수록 그래프 구축과 보고서 생성 비용이 함께 올라갑니다.</p>
          </article>
          <article class="card">
            <h3>분석 깊이</h3>
            <p>시뮬레이션 범위, 고려할 이해관계자, 비교할 시나리오 수가 많을수록 더 정교한 분석이 들어갑니다.</p>
          </article>
          <article class="card">
            <h3>프로젝트 단위 결제</h3>
            <p>정기 구독보다 프로젝트 단위 결제에 가깝습니다. 결제 전에 먼저 예상 비용을 보고 시작할 수 있습니다.</p>
          </article>
        </div>
      </section>

      <!-- Flow -->
      <section class="section">
        <div class="section-head">
          <span class="eyebrow">이용 흐름</span>
          <h2>결제 전에 반드시 확인하는 단계</h2>
        </div>
        <div class="steps">
          <div class="step">
            <div class="num">01</div>
            <div>
              <h3>자료 업로드</h3>
              <p>정책 문서, 시장 자료, 보도자료, 조사자료 등을 업로드하고 분석 주제를 입력합니다.</p>
            </div>
          </div>
          <div class="step">
            <div class="num">02</div>
            <div>
              <h3>실시간 견적 확인</h3>
              <p>업로드 규모와 분석 계획을 바탕으로 예상 금액을 먼저 표시합니다.</p>
            </div>
          </div>
          <div class="step">
            <div class="num">03</div>
            <div>
              <h3>결제 후 시뮬레이션 시작</h3>
              <p>결제 승인 후 그래프 구축, 시뮬레이션 실행, 보고서 생성이 순차적으로 진행됩니다.</p>
            </div>
          </div>
        </div>
      </section>

      <!-- FAQ -->
      <section class="section section--alt">
        <div class="section-head">
          <span class="eyebrow">환불과 대기열</span>
          <h2>비용 관련 자주 묻는 내용</h2>
        </div>
        <div class="grid two">
          <article class="card">
            <h3>대기열에 들어가도 추가 과금되나요?</h3>
            <p>아닙니다. 같은 프로젝트가 순번 대기 상태로 들어가도 동일 프로젝트에 대해 추가 결제되지 않습니다.</p>
          </article>
          <article class="card">
            <h3>오류가 나면 어떻게 되나요?</h3>
            <p>프로젝트 시작 전 단계 오류는 결제 확정 전 검증에서 막고, 시작 이후 회사 귀책 장애는 재실행이나 복구 가능 여부를 검토합니다.</p>
          </article>
          <article class="card">
            <h3>환불은 가능한가요?</h3>
            <p>관계 법령과 실제 사용 개시 여부에 따라 환불 또는 결제 복구 가능 여부를 판단합니다. 미사용 결제분은 별도 검토 대상입니다.</p>
          </article>
          <article class="card">
            <h3>정기 결제 서비스인가요?</h3>
            <p>현재는 프로젝트 기반 이용에 가깝습니다. 분석 주제와 자료 규모에 맞춰 건별로 시작하는 흐름입니다.</p>
          </article>
        </div>
      </section>

      <!-- CTA -->
      <section class="cta">
        <h2>가격은 먼저 확인하고, 결제는 그다음에 진행합니다</h2>
        <p>자료를 올려보고 실제 견적을 확인한 뒤 시작하세요.</p>
        <router-link to="/signup" class="btn-primary">지금 견적 확인하기</router-link>
      </section>
    </main>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'
import { applySeoMeta, resetSeoMeta } from '../utils/seo.js'

const faqItems = [
  {
    q: '테이레시아스 뷰 가격은 어떻게 정해지나요?',
    a: '업로드 파일 수, 총 용량, 예상 페이지 수, 분석 깊이를 바탕으로 프로젝트별 견적이 계산됩니다.',
  },
  {
    q: '결제 전에 비용을 확인할 수 있나요?',
    a: '가능합니다. 자료 업로드와 분석 조건 입력 후 실제 결제 전 예상 비용을 먼저 확인할 수 있습니다.',
  },
  {
    q: '대기열에 들어가면 추가 결제가 발생하나요?',
    a: '아닙니다. 같은 프로젝트 기준으로 대기열 진입만으로 추가 과금되지 않습니다.',
  },
]

onMounted(() => {
  applySeoMeta({
    title: '가격 안내 | 테이레시아스 뷰',
    description: '테이레시아스 뷰는 업로드 파일 수, 용량, 페이지 수, 분석 깊이를 기준으로 프로젝트별 견적을 먼저 계산하고 결제를 진행합니다.',
    canonical: 'https://tiresiasview.com/pricing',
    structuredData: [
      {
        id: 'pricing-faq',
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
  resetSeoMeta(['pricing-faq'])
})
</script>

<style scoped>
.pricing-page {
  min-height: 100vh;
  background: #ffffff;
  color: #1a1a2e;
  font-family: 'Inter', 'Noto Sans KR', system-ui, -apple-system, sans-serif;
  -webkit-font-smoothing: antialiased;
}

/* ── Header ── */
.page-header {
  position: sticky; top: 0; z-index: 100;
  background: rgba(255,255,255,0.92);
  backdrop-filter: saturate(180%) blur(20px);
  -webkit-backdrop-filter: saturate(180%) blur(20px);
  border-bottom: 1px solid #f0f0f5;
}
.header-container {
  max-width: 1160px; margin: 0 auto; padding: 0 32px;
  height: 64px; display: flex; align-items: center; gap: 18px;
}
.logo-link { text-decoration: none; }
.logo {
  font-family: 'Outfit', 'Inter', sans-serif;
  font-weight: 800; font-size: 1.25rem; letter-spacing: -0.03em; color: #1a1a2e;
}
.header-nav {
  display: flex; align-items: center; gap: 24px; margin-left: auto; margin-right: 24px;
}
.header-nav a {
  color: #64648a; text-decoration: none; font-size: 0.88rem; font-weight: 500;
  transition: color 0.15s;
}
.header-nav a:hover { color: #1a1a2e; }
.header-actions { display: flex; align-items: center; }
.btn-header {
  background: #6366f1; color: #fff; text-decoration: none;
  font-size: 0.88rem; font-weight: 600; padding: 9px 22px; border-radius: 10px;
  transition: background 0.15s;
}
.btn-header:hover { background: #5558e6; }

/* ── Main ── */
.page-main {
  max-width: 1160px; margin: 0 auto; padding: 88px 32px 0;
}

/* ── Hero ── */
.hero { padding: 40px 0 64px; }
.eyebrow {
  display: inline-block; font-size: 0.78rem; font-weight: 700;
  letter-spacing: 0.04em; color: #6366f1; text-transform: uppercase;
}
.hero h1 {
  margin: 14px 0 0; line-height: 1.2; letter-spacing: -0.03em;
  font-size: clamp(2rem, 4vw, 3.2rem); max-width: 820px; color: #1a1a2e;
}
.hero-desc {
  margin: 18px 0 0; max-width: 760px; color: #64648a; line-height: 1.8; font-size: 1rem;
}
.hero-actions { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 28px; }
.btn-primary {
  display: inline-block; background: #6366f1; color: #fff; text-decoration: none;
  font-size: 0.95rem; font-weight: 600; padding: 14px 32px; border-radius: 12px;
  transition: background 0.15s;
}
.btn-primary:hover { background: #5558e6; }
.btn-ghost {
  display: inline-block; color: #64648a; text-decoration: none; font-size: 0.95rem; font-weight: 500;
  padding: 14px 32px; border-radius: 12px; border: 1px solid #e0e0ea;
  transition: border-color 0.15s, color 0.15s;
}
.btn-ghost:hover { border-color: #c0c0d0; color: #1a1a2e; }

/* ── Sections ── */
.section { padding: 56px 0; }
.section--alt { background: #f8f8fc; margin: 0 -32px; padding: 56px 32px; }
.section-head { margin-bottom: 28px; }
.section-head h2 {
  margin: 14px 0 0; line-height: 1.2; letter-spacing: -0.02em;
  font-size: clamp(1.5rem, 3vw, 2.2rem); color: #1a1a2e;
}

/* ── Grid / Cards ── */
.grid { display: grid; gap: 16px; }
.grid.three { grid-template-columns: repeat(3, minmax(0,1fr)); }
.grid.two { grid-template-columns: repeat(2, minmax(0,1fr)); }
.card {
  background: #fff; border: 1px solid #ededf5; border-radius: 16px; padding: 28px 24px;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.card:hover { border-color: #d0d0e0; box-shadow: 0 8px 28px rgba(0,0,0,0.04); }
.card h3 { margin: 0 0 10px; font-size: 1rem; font-weight: 700; color: #1a1a2e; }
.card p { margin: 0; color: #64648a; line-height: 1.75; font-size: 0.88rem; }

/* ── Steps ── */
.steps { display: grid; gap: 14px; }
.step {
  background: #fff; border: 1px solid #ededf5; border-radius: 16px; padding: 24px;
  display: grid; grid-template-columns: 64px 1fr; gap: 18px; align-items: start;
  transition: border-color 0.2s;
}
.step:hover { border-color: #d0d0e0; }
.step h3 { margin: 0 0 8px; font-size: 1rem; font-weight: 700; color: #1a1a2e; }
.step p { margin: 0; color: #64648a; line-height: 1.75; font-size: 0.88rem; }
.num {
  display: inline-flex; align-items: center; justify-content: center;
  width: 48px; height: 48px; border-radius: 999px;
  background: rgba(99,102,241,0.08); color: #6366f1; font-weight: 700; font-size: 0.9rem;
}

/* ── CTA ── */
.cta {
  background: #f8f8fc; border: 1px solid #ededf5; border-radius: 20px;
  margin: 40px 0 64px; padding: 48px 36px; text-align: center;
}
.cta h2 {
  font-size: 1.5rem; font-weight: 800; color: #1a1a2e; margin: 0 0 12px;
  letter-spacing: -0.02em; line-height: 1.35;
}
.cta p { color: #64648a; margin: 0 0 28px; font-size: 0.95rem; }

/* ── Mobile ── */
@media (max-width: 900px) {
  .header-nav { display: none; }
  .grid.three, .grid.two { grid-template-columns: 1fr; }
  .section--alt { margin: 0 -20px; padding: 48px 20px; }
}
@media (max-width: 640px) {
  .header-container { padding: 0 20px; height: 56px; }
  .page-main { padding: 72px 20px 0; }
  .hero h1 { font-size: 1.8rem; }
  .hero-actions { flex-direction: column; }
  .btn-primary, .btn-ghost { text-align: center; }
  .step { grid-template-columns: 1fr; }
  .cta { padding: 36px 24px; margin: 32px 0 48px; }
  .cta h2 { font-size: 1.3rem; }
}
</style>
