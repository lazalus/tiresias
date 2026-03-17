<template>
  <div class="app-screen">
    <!-- App Header -->
    <header class="app-header">
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
        <div class="hero-pill">
          <span class="pill-dot"></span>
          집단 지능 예측 엔진
        </div>
        <h1 class="hero-title">
          AI 에이전트가 구축하는
          <span class="hero-gradient">병렬 세계 시뮬레이션</span>
        </h1>
        <p class="hero-subtitle">
          비정형 데이터에서 현실 시드를 추출하고, 수천 개의 독립적인 AI 에이전트가
          상호작용하는 디지털 세계를 자동으로 생성합니다.<br>
          신의 시점에서 변수를 주입하여 미래의 궤적을 예측합니다.
        </p>
      </section>

      <!-- Section Divider -->
      <div class="section-divider"></div>

      <!-- Core Capabilities -->
      <section class="capabilities">
        <div class="section-label">Core Capabilities</div>
        <div class="cap-grid">
          <div class="cap-card">
            <div class="cap-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
              </svg>
            </div>
            <h3 class="cap-title">저비용 시뮬레이션</h3>
            <p class="cap-desc">일반 시뮬레이션 평균 $5/회의 비용으로 대규모 예측을 실행할 수 있습니다.</p>
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

      <!-- Section Divider -->
      <div class="section-divider"></div>

      <!-- Workflow Timeline -->
      <section class="workflow">
        <div class="section-label">Workflow</div>
        <h2 class="section-heading">워크플로우</h2>
        <div class="timeline">
          <div class="timeline-line"></div>
          <div v-for="(step, i) in steps" :key="i" class="timeline-item">
            <div class="timeline-dot">
              <span class="dot-inner"></span>
            </div>
            <div class="timeline-content">
              <div class="timeline-num">{{ String(i + 1).padStart(2, '0') }}</div>
              <h3 class="timeline-title">{{ step.name }}</h3>
              <p class="timeline-desc">{{ step.desc }}</p>
            </div>
          </div>
        </div>
      </section>

      <!-- Section Divider -->
      <div class="section-divider"></div>

      <!-- Use Cases -->
      <section class="use-cases">
        <div class="section-label">Use Cases</div>
        <h2 class="section-heading">활용 사례</h2>
        <div class="cases-grid">
          <div class="case-card">
            <div class="case-dot" style="--dot-color: #6366f1"></div>
            <h3 class="case-title">여론 예측</h3>
            <p class="case-desc">정책 발표, 기업 PR 등의 여론 반응을 사전에 시뮬레이션하여 리스크를 최소화합니다.</p>
          </div>
          <div class="case-card">
            <div class="case-dot" style="--dot-color: #818cf8"></div>
            <h3 class="case-title">금융 시나리오</h3>
            <p class="case-desc">시장 변동, 정책 변화에 따른 투자자 행동 패턴을 다차원적으로 분석합니다.</p>
          </div>
          <div class="case-card">
            <div class="case-dot" style="--dot-color: #a78bfa"></div>
            <h3 class="case-title">정책 시뮬레이션</h3>
            <p class="case-desc">정책 시행 전 사회적 반응과 영향을 제로 리스크 환경에서 테스트합니다.</p>
          </div>
          <div class="case-card">
            <div class="case-dot" style="--dot-color: #c4b5fd"></div>
            <h3 class="case-title">창작 시뮬레이션</h3>
            <p class="case-desc">소설 결말 추론, 시나리오 분기점 탐색 등 창작 활동을 지원합니다.</p>
          </div>
        </div>
      </section>

      <!-- Section Divider -->
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
        <div class="footer-line"></div>
        <p class="footer-text">
          TIRESIAS VIEW is open source (AGPL-3.0) based on <a href="https://github.com/666ghj/MiroFish" target="_blank" class="footer-link">MiroFish</a>.
          <a href="https://github.com/lazalus/tiresias" target="_blank" class="footer-link">Source Code</a>
        </p>
      </footer>
    </main>
  </div>
</template>

<script setup>
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
/* ── Base ── */
.app-screen {
  min-height: 100vh;
  background: var(--bg-primary);
  color: var(--text-primary);
  font-family: 'Inter', 'Noto Sans KR', system-ui, -apple-system, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
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
  max-width: 1080px;
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
  transition: color 0.2s, background 0.2s;
}

.header-link:hover {
  color: rgba(255, 255, 255, 0.9);
  background: var(--border-color);
}

/* ── Main ── */
.features-main {
  max-width: 800px;
  margin: 0 auto;
  padding: 0 24px 120px;
}

/* ── Hero ── */
.hero {
  text-align: center;
  padding: 100px 0 80px;
  position: relative;
}

.hero::before {
  content: '';
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 600px;
  height: 400px;
  background: radial-gradient(ellipse at center, rgba(99, 102, 241, 0.08) 0%, transparent 70%);
  pointer-events: none;
}

.hero-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: #818cf8;
  background: rgba(129, 140, 248, 0.08);
  border: 1px solid rgba(129, 140, 248, 0.15);
  border-radius: 100px;
  padding: 6px 18px 6px 14px;
  margin-bottom: 32px;
}

.pill-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #818cf8;
  box-shadow: 0 0 8px rgba(129, 140, 248, 0.6);
  animation: pulse-dot 2s ease-in-out infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.hero-title {
  font-size: 3rem;
  font-weight: 700;
  line-height: 1.2;
  letter-spacing: -0.035em;
  margin: 0 0 24px;
  color: var(--text-primary);
}

.hero-gradient {
  display: block;
  background: linear-gradient(135deg, #6366f1 0%, #818cf8 40%, #a78bfa 60%, #6366f1 100%);
  background-size: 200% 200%;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: gradient-shift 6s ease infinite;
}

@keyframes gradient-shift {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

.hero-subtitle {
  font-size: 1rem;
  color: var(--text-secondary);
  line-height: 1.8;
  margin: 0 auto;
  max-width: 560px;
  font-weight: 400;
}

/* ── Section Divider ── */
.section-divider {
  height: 1px;
  background: linear-gradient(90deg, transparent 0%, rgba(99, 102, 241, 0.2) 50%, transparent 100%);
  margin: 0 auto;
  max-width: 400px;
}

/* ── Section Labels ── */
.section-label {
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #6366f1;
  margin-bottom: 12px;
}

.section-heading {
  font-size: 1.6rem;
  font-weight: 700;
  letter-spacing: -0.025em;
  margin: 0 0 40px;
  color: var(--text-primary);
}

/* ── Capabilities ── */
.capabilities {
  padding: 80px 0;
}

.cap-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.cap-card {
  position: relative;
  padding: 32px 24px;
  border-radius: 16px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  transition: transform 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease;
}

.cap-card::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 16px;
  background: linear-gradient(180deg, rgba(99, 102, 241, 0.04) 0%, transparent 60%);
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: none;
}

.cap-card:hover {
  transform: translateY(-4px);
  border-color: rgba(99, 102, 241, 0.2);
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(99, 102, 241, 0.1);
}

.cap-card:hover::before {
  opacity: 1;
}

.cap-icon {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: rgba(99, 102, 241, 0.1);
  color: #818cf8;
  margin-bottom: 20px;
}

.cap-title {
  font-size: 0.95rem;
  font-weight: 600;
  letter-spacing: -0.01em;
  margin: 0 0 8px;
  color: var(--text-primary);
}

.cap-desc {
  font-size: 0.84rem;
  color: var(--text-secondary);
  line-height: 1.65;
  margin: 0;
}

/* ── Workflow Timeline ── */
.workflow {
  padding: 80px 0;
}

.timeline {
  position: relative;
  padding-left: 32px;
}

.timeline-line {
  position: absolute;
  left: 7px;
  top: 8px;
  bottom: 8px;
  width: 1px;
  background: linear-gradient(180deg, #6366f1 0%, rgba(99, 102, 241, 0.15) 100%);
}

.timeline-item {
  position: relative;
  padding-bottom: 40px;
  display: flex;
  align-items: flex-start;
}

.timeline-item:last-child {
  padding-bottom: 0;
}

.timeline-dot {
  position: absolute;
  left: -32px;
  top: 4px;
  width: 15px;
  height: 15px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.dot-inner {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15);
  transition: box-shadow 0.2s ease;
}

.timeline-item:hover .dot-inner {
  box-shadow: 0 0 0 5px rgba(99, 102, 241, 0.2), 0 0 12px rgba(99, 102, 241, 0.3);
}

.timeline-content {
  flex: 1;
}

.timeline-num {
  font-family: 'JetBrains Mono', 'SF Mono', monospace;
  font-size: 0.68rem;
  font-weight: 500;
  color: rgba(99, 102, 241, 0.6);
  letter-spacing: 0.05em;
  margin-bottom: 4px;
}

.timeline-title {
  font-size: 1rem;
  font-weight: 600;
  letter-spacing: -0.01em;
  margin: 0 0 8px;
  color: var(--text-primary);
}

.timeline-desc {
  font-size: 0.84rem;
  color: rgba(255, 255, 255, 0.38);
  line-height: 1.7;
  margin: 0;
}

/* ── Use Cases ── */
.use-cases {
  padding: 80px 0;
}

.cases-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.case-card {
  position: relative;
  padding: 28px 24px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--border-color);
  transition: border-color 0.3s ease, background 0.3s ease;
}

.case-card:hover {
  border-color: rgba(99, 102, 241, 0.25);
  background: var(--bg-surface);
}

.case-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--dot-color, #6366f1);
  margin-bottom: 16px;
  opacity: 0.8;
}

.case-title {
  font-size: 0.95rem;
  font-weight: 600;
  letter-spacing: -0.01em;
  margin: 0 0 8px;
  color: var(--text-primary);
}

.case-desc {
  font-size: 0.82rem;
  color: rgba(255, 255, 255, 0.38);
  line-height: 1.65;
  margin: 0;
}

/* ── CTA ── */
.cta {
  text-align: center;
  padding: 80px 0 0;
  position: relative;
}

.cta::before {
  content: '';
  position: absolute;
  bottom: -40px;
  left: 50%;
  transform: translateX(-50%);
  width: 500px;
  height: 300px;
  background: radial-gradient(ellipse at center, rgba(99, 102, 241, 0.06) 0%, transparent 70%);
  pointer-events: none;
}

.cta-lead {
  font-size: 1rem;
  color: var(--text-secondary);
  margin: 0 0 28px;
  font-weight: 400;
}

.cta-btn {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  background: #6366f1;
  color: #fff;
  text-decoration: none;
  font-weight: 600;
  font-size: 0.9rem;
  letter-spacing: -0.01em;
  padding: 14px 32px;
  border-radius: 12px;
  transition: all 0.25s ease;
  position: relative;
  overflow: hidden;
}

.cta-btn::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, transparent 50%);
  opacity: 0;
  transition: opacity 0.25s ease;
}

.cta-btn:hover {
  background: #5558e6;
  transform: translateY(-2px);
  box-shadow: 0 8px 32px rgba(99, 102, 241, 0.3), 0 0 0 1px rgba(99, 102, 241, 0.3);
}

.cta-btn:hover::before {
  opacity: 1;
}

/* ── Footer ── */
.footer {
  padding-top: 60px;
  text-align: center;
}

.footer-line {
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--border-color), transparent);
  margin-bottom: 24px;
}

.footer-text {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin: 0;
}

.footer-link {
  color: var(--text-secondary);
  text-decoration: none;
  transition: color 0.2s;
}

.footer-link:hover {
  color: #818cf8;
}

/* ── Responsive ── */
@media (max-width: 768px) {
  .hero-title {
    font-size: 2.2rem;
  }

  .cap-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .cases-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .features-main {
    padding: 0 20px 80px;
  }

  .hero {
    padding: 72px 0 60px;
  }

  .capabilities,
  .workflow,
  .use-cases {
    padding: 60px 0;
  }

  .cta {
    padding: 60px 0 0;
  }
}

@media (max-width: 480px) {
  .hero-title {
    font-size: 1.75rem;
  }

  .section-heading {
    font-size: 1.35rem;
  }

  .hero-subtitle {
    font-size: 0.9rem;
  }
}
</style>
