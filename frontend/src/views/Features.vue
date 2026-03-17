<template>
  <div :class="fromProfile ? 'sub-page' : 'app-screen'">
    <!-- Sub Header (from profile) -->
    <header v-if="fromProfile" class="sub-header">
      <router-link to="/profile?from=support" class="back-btn">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="15 18 9 12 15 6"/>
        </svg>
      </router-link>
      <h1 class="sub-title">서비스 소개</h1>
      <div class="spacer"></div>
    </header>
    <!-- App Header (standalone) -->
    <header v-else class="app-header">
      <div class="header-inner">
        <div class="header-left">
          <img src="/logoss.png" alt="TIRESIAS VIEW" class="app-logo" />
          <span class="app-name">TIRESIAS VIEW</span>
        </div>
        <nav class="header-nav">
          <router-link to="/" class="header-link">홈으로</router-link>
        </nav>
      </div>
    </header>

    <main class="features-main">
      <!-- Hero -->
      <section class="hero">
        <h1 class="hero-title">
          AI 에이전트가 구축하는<br>병렬 세계 시뮬레이션
        </h1>
        <p class="hero-subtitle">
          비정형 데이터에서 현실 시드를 추출하고, 수천 개의 독립적인 AI 에이전트가
          상호작용하는 디지털 세계를 자동으로 생성합니다.<br>
          신의 시점에서 변수를 주입하여 미래의 궤적을 예측합니다.
        </p>
      </section>

      <!-- Divider -->
      <div class="section-divider"></div>

      <!-- Core Capabilities -->
      <section class="capabilities">
        <div class="section-label">CORE CAPABILITIES</div>
        <div class="cap-grid">
          <div class="cap-card">
            <div class="cap-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
              </svg>
            </div>
            <h3 class="cap-title">저비용 시뮬레이션</h3>
            <p class="cap-desc">일반 시뮬레이션 1회 9,900원으로 대규모 예측을 실행할 수 있습니다.</p>
          </div>
          <div class="cap-card">
            <div class="cap-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"/>
                <path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
              </svg>
            </div>
            <h3 class="cap-title">대규모 에이전트</h3>
            <p class="cap-desc">최대 백만 레벨 에이전트를 동시 운용하여 현실과 유사한 복잡계를 구현합니다.</p>
          </div>
          <div class="cap-card">
            <div class="cap-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"/>
                <path d="M9 12l2 2 4-4"/>
              </svg>
            </div>
            <h3 class="cap-title">완전 자동화</h3>
            <p class="cap-desc">데이터 업로드만으로 시뮬레이션 환경 구축부터 보고서 생성까지 완전 자동으로 처리됩니다.</p>
          </div>
        </div>
      </section>

      <!-- Divider -->
      <div class="section-divider"></div>

      <!-- Workflow Timeline -->
      <section class="workflow">
        <div class="section-label">WORKFLOW</div>
        <h2 class="section-heading">워크플로우</h2>
        <div class="timeline">
          <div class="timeline-line"></div>
          <div v-for="(step, i) in steps" :key="i" class="timeline-item">
            <div class="timeline-dot"></div>
            <div class="timeline-content">
              <div class="timeline-num">{{ String(i + 1).padStart(2, '0') }}</div>
              <h3 class="timeline-title">{{ step.name }}</h3>
              <p class="timeline-desc">{{ step.desc }}</p>
            </div>
          </div>
        </div>
      </section>

      <!-- Divider -->
      <div class="section-divider"></div>

      <!-- Use Cases -->
      <section class="use-cases">
        <div class="section-label">USE CASES</div>
        <h2 class="section-heading">활용 사례</h2>
        <div class="cases-list">
          <div class="case-card" style="--accent: #6366f1">
            <h3 class="case-title">여론 예측</h3>
            <p class="case-desc">정책 발표, 기업 PR 등의 여론 반응을 사전에 시뮬레이션하여 리스크를 최소화합니다.</p>
          </div>
          <div class="case-card" style="--accent: #818cf8">
            <h3 class="case-title">금융 시나리오</h3>
            <p class="case-desc">시장 변동, 정책 변화에 따른 투자자 행동 패턴을 다차원적으로 분석합니다.</p>
          </div>
          <div class="case-card" style="--accent: #a78bfa">
            <h3 class="case-title">정책 시뮬레이션</h3>
            <p class="case-desc">정책 시행 전 사회적 반응과 영향을 제로 리스크 환경에서 테스트합니다.</p>
          </div>
          <div class="case-card" style="--accent: #c4b5fd">
            <h3 class="case-title">창작 시뮬레이션</h3>
            <p class="case-desc">소설 결말 추론, 시나리오 분기점 탐색 등 창작 활동을 지원합니다.</p>
          </div>
        </div>
      </section>

      <!-- Divider -->
      <div class="section-divider"></div>

      <!-- CTA -->
      <section class="cta">
        <p class="cta-lead">미래를 시뮬레이션할 준비가 되셨나요?</p>
        <router-link to="/" class="cta-btn">
          <span>지금 시작하기</span>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M5 12h14M12 5l7 7-7 7"/>
          </svg>
        </router-link>
      </section>

      <!-- Footer -->
      <footer class="footer">
        <p class="footer-text">
          TIRESIAS VIEW is open source (AGPL-3.0) based on <a href="https://github.com/666ghj/MiroFish" target="_blank" class="footer-link">MiroFish</a>.
          <a href="https://github.com/lazalus/tiresias" target="_blank" class="footer-link">Source Code</a>
        </p>
      </footer>
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const fromProfile = computed(() => route.query.from === 'profile')

const steps = [
  {
    name: '그래프 구축',
    desc: '업로드된 데이터에서 현실 시드를 추출하고, 개체 및 집단 기억을 주입하여 GraphRAG 지식 그래프를 자동 구축합니다.'
  },
  {
    name: '환경 설정',
    desc: '엔티티 관계를 추출하고 페르소나를 생성한 후, 시뮬레이션 환경에 에이전트 파라미터를 주입합니다.'
  },
  {
    name: '시뮬레이션 실행',
    desc: '이중 플랫폼에서 병렬 시뮬레이션을 수행하며, 예측 요구사항을 자동 분석하고 시계열 기억을 동적으로 업데이트합니다.'
  },
  {
    name: '보고서 생성',
    desc: 'ReportAgent가 풍부한 도구 세트를 활용하여 시뮬레이션 결과를 분석하고 상세한 예측 보고서를 생성합니다.'
  },
  {
    name: '심층 상호작용',
    desc: '시뮬레이션 세계의 에이전트와 자유롭게 대화하거나 ReportAgent에게 추가 질문을 할 수 있습니다.'
  }
]
</script>

<style scoped>
/* ── Sub Page (from profile) ── */
.sub-page {
  min-height: 100vh;
  background: var(--bg-primary);
  color: var(--text-primary);
  font-family: 'Inter', 'Noto Sans KR', system-ui, -apple-system, sans-serif;
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
.back-btn:hover { background: var(--border-color); }
.sub-title { font-size: 1rem; font-weight: 600; letter-spacing: -0.01em; }
.spacer { width: 36px; }

/* ── Base ── */
.app-screen {
  min-height: 100vh;
  background: var(--bg-primary);
  color: var(--text-primary);
  font-family: 'Inter', 'Noto Sans KR', system-ui, -apple-system, sans-serif;
  -webkit-font-smoothing: antialiased;
}

/* ── Header ── */
.app-header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: var(--header-bg);
  backdrop-filter: saturate(180%) blur(20px);
  -webkit-backdrop-filter: saturate(180%) blur(20px);
  border-bottom: 1px solid var(--border-color);
}

.header-inner {
  max-width: 680px;
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

.app-logo {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  object-fit: cover;
}

.app-name {
  font-family: 'Outfit', sans-serif;
  font-weight: 700;
  letter-spacing: 0.08em;
  font-size: 0.9rem;
  color: var(--text-primary);
}

.header-nav {
  display: flex;
  align-items: center;
}

.header-link {
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 0.82rem;
  font-weight: 500;
  letter-spacing: 0.01em;
  padding: 6px 14px;
  border-radius: 8px;
  transition: color 0.15s, background 0.15s;
}

.header-link:hover {
  color: var(--text-primary);
  background: var(--border-color);
}

/* ── Main ── */
.features-main {
  max-width: 680px;
  margin: 0 auto;
  padding: 0 24px 120px;
}

/* ── Hero ── */
.hero {
  text-align: center;
  padding: 80px 0 64px;
}

.hero-title {
  font-size: 2.2rem;
  font-weight: 700;
  line-height: 1.3;
  letter-spacing: -0.03em;
  margin: 0 0 20px;
  color: var(--text-primary);
}

.hero-subtitle {
  font-size: 0.88rem;
  color: var(--text-secondary);
  line-height: 1.8;
  margin: 0 auto;
  max-width: 520px;
  font-weight: 400;
}

/* ── Section Divider ── */
.section-divider {
  height: 1px;
  background: var(--border-color);
  margin: 0;
}

/* ── Section Labels ── */
.section-label {
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--text-tertiary, var(--text-muted));
  margin-bottom: 12px;
}

.section-heading {
  font-size: 1.4rem;
  font-weight: 700;
  letter-spacing: -0.025em;
  margin: 0 0 32px;
  color: var(--text-primary);
}

/* ── Capabilities ── */
.capabilities {
  padding: 64px 0;
}

.cap-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
}

.cap-card {
  padding: 28px 22px;
  border-radius: 10px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  transition: border-color 0.15s;
}

.cap-card:hover {
  border-color: rgba(99, 102, 241, 0.25);
}

.cap-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  background: rgba(99, 102, 241, 0.08);
  color: #6366f1;
  margin-bottom: 16px;
}

.cap-title {
  font-size: 0.85rem;
  font-weight: 600;
  letter-spacing: -0.01em;
  margin: 0 0 6px;
  color: var(--text-primary);
}

.cap-desc {
  font-size: 0.8rem;
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 0;
}

/* ── Workflow Timeline ── */
.workflow {
  padding: 64px 0;
}

.timeline {
  position: relative;
  padding-left: 24px;
}

.timeline-line {
  position: absolute;
  left: 4px;
  top: 6px;
  bottom: 6px;
  width: 1px;
  background: var(--border-color);
}

.timeline-item {
  position: relative;
  padding-bottom: 32px;
  display: flex;
  align-items: flex-start;
}

.timeline-item:last-child {
  padding-bottom: 0;
}

.timeline-dot {
  position: absolute;
  left: -24px;
  top: 6px;
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: #6366f1;
  border: 2px solid var(--bg-primary);
  box-shadow: 0 0 0 1px var(--border-color);
}

.timeline-content {
  flex: 1;
}

.timeline-num {
  font-family: 'JetBrains Mono', 'SF Mono', monospace;
  font-size: 0.68rem;
  font-weight: 500;
  color: var(--text-muted);
  letter-spacing: 0.05em;
  margin-bottom: 4px;
}

.timeline-title {
  font-size: 0.88rem;
  font-weight: 600;
  letter-spacing: -0.01em;
  margin: 0 0 6px;
  color: var(--text-primary);
}

.timeline-desc {
  font-size: 0.8rem;
  color: var(--text-muted);
  line-height: 1.65;
  margin: 0;
}

/* ── Use Cases ── */
.use-cases {
  padding: 64px 0;
}

.cases-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.case-card {
  padding: 22px 22px 22px 26px;
  border-radius: 10px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-left: 3px solid var(--accent, #6366f1);
  transition: border-color 0.15s;
}

.case-card:hover {
  border-color: var(--border-color);
  border-left-color: var(--accent, #6366f1);
}

.case-title {
  font-size: 0.85rem;
  font-weight: 600;
  letter-spacing: -0.01em;
  margin: 0 0 6px;
  color: var(--text-primary);
}

.case-desc {
  font-size: 0.8rem;
  color: var(--text-muted);
  line-height: 1.6;
  margin: 0;
}

/* ── CTA ── */
.cta {
  text-align: center;
  padding: 64px 0 0;
}

.cta-lead {
  font-size: 0.88rem;
  color: var(--text-secondary);
  margin: 0 0 20px;
  font-weight: 400;
}

.cta-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: #6366f1;
  color: #fff;
  text-decoration: none;
  font-weight: 600;
  font-size: 0.85rem;
  letter-spacing: -0.01em;
  padding: 12px 28px;
  border-radius: 10px;
  transition: background 0.15s;
}

.cta-btn:hover {
  background: #5558e6;
}

/* ── Footer ── */
.footer {
  padding-top: 48px;
  text-align: center;
}

.footer-text {
  font-size: 0.72rem;
  color: var(--text-muted);
  margin: 0;
}

.footer-link {
  color: var(--text-secondary);
  text-decoration: none;
  transition: color 0.15s;
}

.footer-link:hover {
  color: #6366f1;
}

/* ── Responsive ── */
@media (max-width: 768px) {
  .hero-title {
    font-size: 1.7rem;
  }

  .cap-grid {
    grid-template-columns: 1fr;
    gap: 10px;
  }

  .features-main {
    padding: 0 20px 80px;
  }

  .hero {
    padding: 56px 0 48px;
  }

  .capabilities,
  .workflow,
  .use-cases {
    padding: 48px 0;
  }

  .cta {
    padding: 48px 0 0;
  }
}

@media (max-width: 480px) {
  .hero-title {
    font-size: 1.5rem;
  }

  .section-heading {
    font-size: 1.2rem;
  }

  .hero-subtitle {
    font-size: 0.82rem;
  }
}
</style>
