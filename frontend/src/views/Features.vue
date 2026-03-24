<template>
  <div :class="fromProfile ? 'sub-page' : 'features-page'">
    <!-- Sub Header (앱 내부에서 접근 시) -->
    <header v-if="fromProfile" class="sub-header">
      <router-link to="/profile?from=support" class="back-btn">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="15 18 9 12 15 6"/>
        </svg>
      </router-link>
      <h1 class="sub-title">서비스 소개</h1>
      <div class="spacer"></div>
    </header>

    <!-- 독립 페이지 헤더 -->
    <header v-else class="page-header">
      <div class="header-container">
        <router-link to="/" class="logo-link">
          <span class="logo">TIRESIAS VIEW</span>
        </router-link>
        <nav class="header-nav">
          <router-link to="/features" class="nav-active">기능 소개</router-link>
          <router-link to="/pricing">요금 안내</router-link>
          <router-link to="/samples">샘플 보고서</router-link>
        </nav>
        <div class="header-actions">
          <router-link to="/login" class="btn-header">로그인</router-link>
        </div>
      </div>
    </header>

    <main :class="fromProfile ? 'sub-content' : 'page-main'">
      <!-- Hero -->
      <section class="f-hero">
        <span class="f-badge">AI 시나리오 분석 플랫폼</span>
        <h1 class="f-hero-title">자료를 업로드하면<br class="desktop-br"/>시나리오를 비교합니다</h1>
        <p class="f-hero-desc">정책 문서, 시장 자료, 보도자료를 업로드하면 AI 에이전트가 이해관계자 반응을 시뮬레이션하고, 시나리오별 분석 보고서를 생성합니다.</p>
        <div class="f-hero-cta">
          <router-link to="/signup" class="btn-primary">무료로 시작하기</router-link>
          <router-link to="/samples" class="btn-ghost">샘플 보고서 보기</router-link>
        </div>
      </section>

      <!-- Overview Video -->
      <section class="f-video-section">
        <div class="video-placeholder">
          <div class="video-inner">
            <svg width="56" height="56" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2"><circle cx="12" cy="12" r="10"/><polygon points="10 8 16 12 10 16" fill="currentColor" stroke="none"/></svg>
            <p>서비스 소개 영상</p>
            <span>준비 중입니다</span>
          </div>
        </div>
      </section>

      <!-- Pain Points -->
      <section class="f-section">
        <div class="f-section-header">
          <span class="f-label">이런 고민, 익숙하시죠?</span>
          <h2 class="f-section-title">기존 방식의 한계를 매번 느끼고 있다면</h2>
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
      </section>

      <!-- ═══ 주요 기능 ═══ -->
      <section id="features" class="f-section f-section--alt">
        <div class="f-section-header">
          <span class="f-label">주요 기능</span>
          <h2 class="f-section-title">자료에서 보고서까지 하나의 워크플로우</h2>
          <p class="f-section-subtitle">업로드한 자료의 구조를 분석하고, 다수 에이전트가 시나리오를 비교해 보고서를 만듭니다.</p>
        </div>

        <!-- Feature 1: 지식 그래프 -->
        <div class="feature-block">
          <div class="feature-row">
            <div class="feature-content">
              <span class="feature-tag feature-tag--purple">구조 분석</span>
              <h3 class="feature-title">지식 그래프 자동 구축</h3>
              <p class="feature-desc">업로드한 자료에서 이해관계자, 이슈, 변수를 자동 추출하여 관계 구조를 시각화합니다. 수작업으로 며칠 걸리던 구조 분석을 몇 분 만에 완료합니다.</p>
              <ul class="feature-checks">
                <li>이해관계자 · 변수 · 이슈 자동 식별 및 관계 매핑</li>
                <li>인터랙티브 그래프 시각화로 구조 한눈에 파악</li>
                <li>PDF, Markdown, TXT, CSV 등 다양한 포맷 지원</li>
                <li>추출된 온톨로지를 시뮬레이션 환경에 자동 연결</li>
              </ul>
            </div>
            <div class="feature-visual">
              <div class="feature-media">
                <img src="/landing-graph.png" alt="지식 그래프 자동 구축" class="feature-img" />
                <div class="feature-video-overlay" title="데모 영상 준비 중">
                  <svg width="40" height="40" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="11" stroke="currentColor" stroke-width="1"/><polygon points="10 8 16 12 10 16" fill="currentColor"/></svg>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Feature 2: 시뮬레이션 -->
        <div class="feature-block">
          <div class="feature-row feature-row--reversed">
            <div class="feature-content">
              <span class="feature-tag feature-tag--blue">시뮬레이션</span>
              <h3 class="feature-title">다수 에이전트 시나리오 비교</h3>
              <p class="feature-desc">각 이해관계자의 입장을 가진 AI 에이전트들이 다중 라운드로 반응합니다. 정책 지지자, 반대 세력, 언론, 소비자 등 다양한 관점에서 시나리오가 어떻게 분기하는지 추적합니다.</p>
              <ul class="feature-checks">
                <li>이해관계자별 AI 페르소나 자동 생성 (성향·배경·이해관계 반영)</li>
                <li>다중 라운드 상호작용으로 반응 변화 추적</li>
                <li>시나리오별 반응 경로 비교 및 분기점 식별</li>
                <li>플랫폼(SNS, 커뮤니티, 언론) 환경 시뮬레이션</li>
              </ul>
            </div>
            <div class="feature-visual">
              <div class="feature-media">
                <img src="/landing-agents.png" alt="다수 에이전트 시뮬레이션" class="feature-img" />
                <div class="feature-video-overlay" title="데모 영상 준비 중">
                  <svg width="40" height="40" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="11" stroke="currentColor" stroke-width="1"/><polygon points="10 8 16 12 10 16" fill="currentColor"/></svg>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Feature 3: 보고서 -->
        <div class="feature-block">
          <div class="feature-row">
            <div class="feature-content">
              <span class="feature-tag feature-tag--green">보고서</span>
              <h3 class="feature-title">심층 분석 보고서 자동 생성</h3>
              <p class="feature-desc">시뮬레이션 결과를 구조화된 분석 보고서로 자동 정리합니다. 핵심 인사이트, 시나리오 비교, 리스크 요인을 한눈에 파악할 수 있고, PDF 다운로드와 후속 질의까지 이어집니다.</p>
              <ul class="feature-checks">
                <li>시나리오 비교표 · 핵심 인사이트 · 리스크 요인 자동 요약</li>
                <li>웹 보고서 + PDF 다운로드</li>
                <li>보고서 기반 추가 질의 (심층 대화)</li>
                <li>팀 공유 및 의사결정 참고자료로 활용</li>
              </ul>
            </div>
            <div class="feature-visual">
              <div class="feature-media">
                <img src="/landing-report.png" alt="심층 분석 보고서" class="feature-img" />
                <div class="feature-video-overlay" title="데모 영상 준비 중">
                  <svg width="40" height="40" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="11" stroke="currentColor" stroke-width="1"/><polygon points="10 8 16 12 10 16" fill="currentColor"/></svg>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- ═══ 작동 방식 ═══ -->
      <section id="process" class="f-section">
        <div class="f-section-header">
          <span class="f-label">작동 방식</span>
          <h2 class="f-section-title">5단계 시뮬레이션 파이프라인</h2>
          <p class="f-section-subtitle">자료 업로드부터 보고서 생성까지, 모든 과정이 하나의 흐름으로 자동 연결됩니다.</p>
        </div>
        <div class="workflow-list">
          <div v-for="(step, i) in steps" :key="i" class="workflow-item">
            <div class="workflow-num-wrap">
              <div class="workflow-num">{{ String(i + 1).padStart(2, '0') }}</div>
              <div v-if="i < steps.length - 1" class="workflow-line"></div>
            </div>
            <div class="workflow-body">
              <h3>{{ step.name }}</h3>
              <p>{{ step.desc }}</p>
              <div v-if="step.details" class="workflow-details">
                <span v-for="(d, j) in step.details" :key="j" class="workflow-detail-chip">{{ d }}</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- 활용 사례 -->
      <section class="f-section f-section--alt">
        <div class="f-section-header">
          <span class="f-label">활용 사례</span>
          <h2 class="f-section-title">다양한 분야에서 활용됩니다</h2>
          <p class="f-section-subtitle">정책, 시장, 위기관리, 커뮤니케이션 등 의사결정 전 가설 검토가 필요한 모든 영역에서 쓸 수 있습니다.</p>
        </div>
        <div class="usecases-grid">
          <div class="usecase-card usecase-card--purple">
            <div class="usecase-icon"><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg></div>
            <div>
              <h3>여론 예측</h3>
              <p>정책 발표, 기업 PR, 사회적 이슈에 대한 여론 반응을 사전 시뮬레이션하여 리스크를 최소화합니다.</p>
            </div>
          </div>
          <div class="usecase-card usecase-card--blue">
            <div class="usecase-icon"><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/></svg></div>
            <div>
              <h3>시장 분석</h3>
              <p>신제품 출시, 가격 변경, 브랜드 전략이 소비자와 커뮤니티에 미치는 영향을 다각도로 점검합니다.</p>
            </div>
          </div>
          <div class="usecase-card usecase-card--green">
            <div class="usecase-icon"><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg></div>
            <div>
              <h3>정책 영향 평가</h3>
              <p>규제, 법안, 제도 변경이 이해관계자별 반응과 온라인 여론에 어떤 영향을 주는지 사전 검토합니다.</p>
            </div>
          </div>
          <div class="usecase-card usecase-card--red">
            <div class="usecase-icon"><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg></div>
            <div>
              <h3>위기 대응 · 캠페인 테스트</h3>
              <p>위기 상황 대응 전략, 브랜드 메시지, 보도자료가 불러올 반응을 미리 시뮬레이션합니다.</p>
            </div>
          </div>
        </div>
      </section>

      <!-- 운영 원칙 -->
      <section class="f-section">
        <div class="f-section-header">
          <span class="f-label">운영 원칙</span>
          <h2 class="f-section-title">투명하고 안정적인 서비스 운영</h2>
        </div>
        <div class="principle-grid">
          <div class="principle-card">
            <h3>대기열과 순번 안내</h3>
            <p>동시에 무거운 작업이 몰리면 순번을 부여하고, 차례가 오면 자동으로 다시 시도합니다.</p>
          </div>
          <div class="principle-card">
            <h3>보고서와 후속 상호작용</h3>
            <p>시뮬레이션이 끝나면 보고서를 생성하고, 결과를 바탕으로 후속 질문과 탐색을 이어갈 수 있습니다.</p>
          </div>
          <div class="principle-card">
            <h3>문서·프로젝트 삭제 지원</h3>
            <p>프로젝트와 보고서를 삭제하면 관련 저장 데이터도 함께 정리됩니다.</p>
          </div>
          <div class="principle-card">
            <h3>참고용 결과물</h3>
            <p>결과물은 의사결정을 돕는 참고 자료입니다. 투자, 법률, 의료, 정책 판단은 별도 검토가 필요합니다.</p>
          </div>
        </div>
      </section>

      <!-- CTA -->
      <section class="f-cta-section">
        <h2 class="f-cta-title">의사결정 전 가설 검토를<br class="desktop-br"/> 지금 시작하세요</h2>
        <p class="f-cta-desc">자료를 업로드하면 시나리오를 비교하고 분석 보고서를 받을 수 있습니다.</p>
        <div class="f-cta-actions">
          <router-link to="/signup" class="btn-primary">무료로 시작하기</router-link>
          <router-link to="/samples" class="btn-ghost">샘플 보고서 보기</router-link>
        </div>
      </section>

      <!-- Footer -->
      <footer class="f-footer">
        <div class="f-footer-links">
          <router-link to="/pricing">요금 안내</router-link>
          <router-link to="/samples">샘플 보고서</router-link>
          <router-link to="/terms">이용약관</router-link>
          <router-link to="/privacy">개인정보처리방침</router-link>
        </div>
        <p class="f-footer-biz">에스아이 | 대표 정희수 | 사업자등록번호 111-63-00101 | 통신판매업신고번호 2024-안양동안-0010 | support@tiresiasview.com</p>
      </footer>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { applySeoMeta, resetSeoMeta } from '../utils/seo.js'

const route = useRoute()
const fromProfile = computed(() => route.query.from === 'profile')

const steps = [
  {
    name: '자료 업로드 및 견적 확인',
    desc: 'PDF, Markdown, TXT, CSV 자료를 올리고 예상 페이지 수와 분석 깊이에 따른 견적을 먼저 확인합니다.',
    details: ['PDF', 'Markdown', 'TXT', 'CSV'],
  },
  {
    name: '온톨로지·지식 그래프 구축',
    desc: '문서에서 핵심 엔티티와 관계를 추출해 그래프를 만들고, 이후 단계에서 재사용할 수 있는 구조화된 지식을 준비합니다.',
    details: ['엔티티 추출', '관계 매핑', '그래프 시각화'],
  },
  {
    name: '페르소나·환경 준비',
    desc: '그래프를 바탕으로 에이전트 프로필, 환경 설정, 라운드 구성 등 시뮬레이션 실행 조건을 자동 생성합니다.',
    details: ['AI 페르소나', '환경 설정', '라운드 구성'],
  },
  {
    name: '다중 라운드 시뮬레이션',
    desc: '플랫폼별 행동과 상호작용을 여러 라운드로 실행해 변화 흐름과 반응 패턴을 수집합니다.',
    details: ['SNS', '커뮤니티', '언론', '다중 라운드'],
  },
  {
    name: '보고서 생성 및 후속 질의',
    desc: '결과를 요약한 보고서를 만들고, 이후 추가 질문과 세부 분석을 이어서 확인할 수 있습니다.',
    details: ['웹 보고서', 'PDF 다운로드', '심층 대화'],
  }
]

onMounted(() => {
  if (fromProfile.value) return
  applySeoMeta({
    title: '서비스 소개 | 테이레시아스 뷰 – AI 시나리오 분석 플랫폼',
    description: '보고서를 업로드하면 AI 에이전트가 이해관계자 반응을 시뮬레이션하고 시나리오별 분석 보고서를 생성합니다. 지식 그래프 구축, 다중 에이전트 시뮬레이션, 보고서 자동 생성까지 하나의 흐름으로.',
    canonical: 'https://tiresiasview.com/features',
  })
})

onUnmounted(() => {
  if (fromProfile.value) return
  resetSeoMeta()
})
</script>

<style scoped>
/* ── Sub Page (앱 내부) ── */
.sub-page { min-height: 100vh; background: var(--bg-primary); color: var(--text-primary); font-family: 'Inter', 'Noto Sans KR', system-ui, -apple-system, sans-serif; }
.sub-header { position: sticky; top: 0; z-index: 100; background: var(--header-bg); backdrop-filter: saturate(180%) blur(20px); border-bottom: 1px solid var(--border-color); display: flex; align-items: center; justify-content: space-between; height: 56px; padding: 0 16px; max-width: 680px; margin: 0 auto; }
.back-btn { display: flex; align-items: center; justify-content: center; width: 36px; height: 36px; color: var(--text-primary); text-decoration: none; border-radius: 10px; }
.sub-title { font-size: 1rem; font-weight: 600; }
.spacer { width: 36px; }
.sub-content { max-width: 680px; margin: 0 auto; padding: 24px 20px 80px; }

/* ── Standalone ── */
.features-page { min-height: 100vh; background: #ffffff; color: #1a1a2e; font-family: 'Inter', 'Noto Sans KR', system-ui, -apple-system, sans-serif; -webkit-font-smoothing: antialiased; }

/* ── Header ── */
.page-header { position: fixed; top: 0; left: 0; right: 0; z-index: 100; background: rgba(255,255,255,0.92); backdrop-filter: saturate(180%) blur(20px); -webkit-backdrop-filter: saturate(180%) blur(20px); border-bottom: 1px solid #f0f0f5; }
.header-container { max-width: 1160px; margin: 0 auto; height: 64px; display: flex; align-items: center; padding: 0 32px; }
.logo-link { text-decoration: none; }
.logo { font-family: 'Outfit', 'Inter', sans-serif; font-weight: 800; font-size: 1.25rem; letter-spacing: -0.03em; color: #1a1a2e; }
.header-nav { display: flex; align-items: center; gap: 24px; margin-left: auto; margin-right: 24px; }
.header-nav a { color: #64648a; text-decoration: none; font-size: 0.88rem; font-weight: 500; transition: color 0.15s; }
.header-nav a:hover, .header-nav .nav-active { color: #1a1a2e; }
.header-actions { display: flex; align-items: center; }
.btn-header { background: #6366f1; color: #fff; text-decoration: none; font-size: 0.88rem; font-weight: 600; padding: 9px 22px; border-radius: 10px; transition: background 0.15s; }
.btn-header:hover { background: #5558e6; }

.page-main { max-width: 1160px; margin: 0 auto; padding: 100px 32px 0; }

/* ── Shared ── */
.f-label { display: inline-block; font-size: 0.78rem; font-weight: 700; letter-spacing: 0.04em; color: #6366f1; margin-bottom: 12px; text-transform: uppercase; }
.f-badge { display: inline-block; font-size: 0.78rem; font-weight: 600; letter-spacing: 0.02em; color: #6366f1; background: rgba(99,102,241,0.08); padding: 6px 16px; border-radius: 20px; margin-bottom: 20px; }
.btn-primary { display: inline-block; background: #6366f1; color: #fff; text-decoration: none; font-size: 0.95rem; font-weight: 600; padding: 14px 32px; border-radius: 12px; transition: background 0.15s; }
.btn-primary:hover { background: #5558e6; }
.btn-ghost { display: inline-block; color: #64648a; text-decoration: none; font-size: 0.95rem; font-weight: 500; padding: 14px 32px; border-radius: 12px; border: 1px solid #e0e0ea; transition: border-color 0.15s, color 0.15s; }
.btn-ghost:hover { border-color: #c0c0d0; color: #1a1a2e; }

/* ── Hero ── */
.f-hero { text-align: center; padding: 60px 0 48px; }
.f-hero-title { font-size: 2.8rem; font-weight: 800; line-height: 1.25; color: #1a1a2e; margin: 0 0 20px; letter-spacing: -0.03em; }
.f-hero-desc { font-size: 1.05rem; color: #64648a; line-height: 1.7; max-width: 600px; margin: 0 auto 32px; }
.f-hero-cta { display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; }

/* ── Video ── */
.f-video-section { padding: 0 0 40px; }
.video-placeholder { background: #f4f4fa; border: 2px dashed #d8d8e8; border-radius: 20px; aspect-ratio: 16/9; max-width: 800px; margin: 0 auto; display: flex; align-items: center; justify-content: center; }
.video-inner { text-align: center; color: #a0a0b8; }
.video-inner svg { margin-bottom: 12px; }
.video-inner p { font-size: 1rem; font-weight: 600; margin: 0 0 4px; color: #64648a; }
.video-inner span { font-size: 0.82rem; }

/* ── Sections ── */
.f-section { padding: 80px 0; }
.f-section--alt { background: #f8f8fc; margin: 0 -32px; padding: 80px 32px; }
.f-section-header { text-align: center; margin-bottom: 48px; }
.f-section-title { font-size: 2rem; font-weight: 800; line-height: 1.35; color: #1a1a2e; margin: 0 0 14px; letter-spacing: -0.02em; }
.f-section-subtitle { font-size: 1rem; color: #64648a; line-height: 1.65; max-width: 580px; margin: 0 auto; }

/* ── Pain ── */
.pain-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; }
.pain-card { background: #fafafe; border: 1px solid #ededf5; border-radius: 16px; padding: 32px 28px; transition: border-color 0.2s, box-shadow 0.2s; }
.pain-card:hover { border-color: #d0d0e0; box-shadow: 0 8px 32px rgba(0,0,0,0.04); }
.pain-icon { width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center; margin-bottom: 20px; }
.pain-icon--red { background: rgba(239,68,68,0.08); color: #ef4444; }
.pain-icon--orange { background: rgba(245,158,11,0.08); color: #f59e0b; }
.pain-icon--blue { background: rgba(59,130,246,0.08); color: #3b82f6; }
.pain-card h3 { font-size: 1rem; font-weight: 700; color: #1a1a2e; margin: 0 0 10px; line-height: 1.5; }
.pain-card p { font-size: 0.88rem; color: #64648a; line-height: 1.65; margin: 0; }

/* ── Feature rows ── */
.feature-block { margin-bottom: 72px; }
.feature-block:last-child { margin-bottom: 0; }
.feature-row { display: flex; align-items: center; gap: 56px; }
.feature-row--reversed { flex-direction: row-reverse; }
.feature-content { flex: 1; }
.feature-visual { flex: 1; }
.feature-media { position: relative; border-radius: 20px; overflow: hidden; border: 1px solid #e8e8f0; box-shadow: 0 12px 40px rgba(0,0,0,0.06); }
.feature-img { display: block; width: 100%; height: auto; }
.feature-video-overlay { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; background: rgba(0,0,0,0.15); color: #fff; opacity: 0; transition: opacity 0.25s; cursor: pointer; }
.feature-media:hover .feature-video-overlay { opacity: 1; }
.feature-tag { display: inline-block; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.04em; padding: 4px 12px; border-radius: 6px; margin-bottom: 14px; text-transform: uppercase; }
.feature-tag--purple { background: rgba(99,102,241,0.08); color: #6366f1; }
.feature-tag--blue { background: rgba(59,130,246,0.08); color: #3b82f6; }
.feature-tag--green { background: rgba(34,197,94,0.08); color: #16a34a; }
.feature-title { font-size: 1.5rem; font-weight: 800; color: #1a1a2e; margin: 0 0 12px; letter-spacing: -0.01em; line-height: 1.35; }
.feature-desc { font-size: 0.95rem; color: #64648a; line-height: 1.7; margin: 0 0 20px; }
.feature-checks { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 10px; }
.feature-checks li { font-size: 0.88rem; color: #3a3a5c; padding-left: 24px; position: relative; line-height: 1.5; }
.feature-checks li::before { content: ''; position: absolute; left: 0; top: 5px; width: 16px; height: 16px; border-radius: 50%; background: rgba(99,102,241,0.1); background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='10' viewBox='0 0 24 24' fill='none' stroke='%236366f1' stroke-width='3'%3E%3Cpolyline points='20 6 9 17 4 12'/%3E%3C/svg%3E"); background-repeat: no-repeat; background-position: center; background-size: 10px; }

/* ── Workflow ── */
.workflow-list { max-width: 640px; margin: 0 auto; display: flex; flex-direction: column; }
.workflow-item { display: flex; gap: 20px; }
.workflow-num-wrap { display: flex; flex-direction: column; align-items: center; flex-shrink: 0; width: 48px; }
.workflow-num { width: 48px; height: 48px; border-radius: 50%; background: rgba(99,102,241,0.08); color: #6366f1; font-family: 'Outfit', 'Inter', sans-serif; font-size: 0.9rem; font-weight: 700; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.workflow-line { width: 2px; flex: 1; background: #ededf5; min-height: 20px; }
.workflow-body { padding-bottom: 32px; }
.workflow-body h3 { font-size: 1rem; font-weight: 700; color: #1a1a2e; margin: 12px 0 6px; }
.workflow-body p { font-size: 0.88rem; color: #64648a; line-height: 1.65; margin: 0; }
.workflow-details { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 12px; }
.workflow-detail-chip { font-size: 0.72rem; font-weight: 600; color: #6366f1; background: rgba(99,102,241,0.06); border: 1px solid rgba(99,102,241,0.12); padding: 3px 10px; border-radius: 6px; }

/* ── Use Cases ── */
.usecases-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }
.usecase-card { background: #fff; border: 1px solid #ededf5; border-radius: 16px; padding: 28px 24px; display: flex; gap: 18px; align-items: flex-start; transition: border-color 0.2s, box-shadow 0.2s; }
.usecase-card:hover { box-shadow: 0 8px 28px rgba(0,0,0,0.05); }
.usecase-icon { flex-shrink: 0; padding-top: 2px; }
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

/* ── Principles ── */
.principle-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; }
.principle-card { background: #fafafe; border: 1px solid #ededf5; border-left: 3px solid #6366f1; border-radius: 12px; padding: 24px; transition: border-color 0.2s; }
.principle-card:hover { border-color: #d0d0e0; border-left-color: #818cf8; }
.principle-card h3 { font-size: 0.95rem; font-weight: 700; color: #1a1a2e; margin: 0 0 6px; }
.principle-card p { font-size: 0.82rem; color: #64648a; line-height: 1.65; margin: 0; }

/* ── CTA ── */
.f-cta-section { text-align: center; padding: 80px 0; background: linear-gradient(180deg, #f8f8fc 0%, #eeeef8 100%); margin: 0 -32px; }
.f-cta-title { font-size: 2.2rem; font-weight: 800; color: #1a1a2e; margin: 0 0 14px; letter-spacing: -0.02em; line-height: 1.35; }
.f-cta-desc { font-size: 1rem; color: #64648a; margin: 0 0 32px; }
.f-cta-actions { display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; }

/* ── Footer ── */
.f-footer { border-top: 1px solid #ededf5; text-align: center; padding: 32px 0 48px; }
.f-footer-links { display: flex; gap: 20px; justify-content: center; margin-bottom: 16px; }
.f-footer-links a { font-size: 0.82rem; color: #64648a; text-decoration: none; }
.f-footer-links a:hover { color: #1a1a2e; }
.f-footer-biz { font-size: 0.72rem; color: #a0a0b8; margin: 0; }

.desktop-br { display: none; }
@media (min-width: 1024px) { .desktop-br { display: inline; } }

/* ── Mobile ── */
@media (max-width: 1023px) {
  .header-container { height: 56px; padding: 0 20px; }
  .header-nav { display: none; }
  .page-main { padding: 80px 20px 0; }
  .f-hero { padding: 32px 0 40px; }
  .f-hero-title { font-size: 1.8rem; }
  .f-hero-desc { font-size: 0.9rem; }
  .f-hero-cta { flex-direction: column; gap: 10px; }
  .btn-primary, .btn-ghost { text-align: center; padding: 14px 24px; font-size: 0.9rem; }
  .video-placeholder { max-width: 100%; }
  .f-section { padding: 56px 0; }
  .f-section--alt { margin: 0 -20px; padding: 56px 20px; }
  .f-section-header { margin-bottom: 32px; }
  .f-section-title { font-size: 1.5rem; }
  .pain-grid { grid-template-columns: 1fr; gap: 14px; }
  .feature-block { margin-bottom: 48px; }
  .feature-row, .feature-row--reversed { flex-direction: column; gap: 28px; }
  .feature-visual { width: 100%; }
  .feature-title { font-size: 1.25rem; }
  .usecases-grid { grid-template-columns: 1fr; gap: 12px; }
  .principle-grid { grid-template-columns: 1fr; gap: 12px; }
  .f-cta-section { margin: 0 -20px; padding: 56px 20px; }
  .f-cta-title { font-size: 1.5rem; }
  .f-cta-actions { flex-direction: column; }
  .f-footer { padding: 24px 0 40px; }
  .f-footer-links { gap: 14px; flex-wrap: wrap; }
}

/* ── Sub page overrides ── */
.sub-page .f-badge { background: rgba(99,102,241,0.08); color: var(--accent-color, #6366f1); }
.sub-page .f-hero { text-align: left; padding: 16px 0 32px; }
.sub-page .f-hero-title { color: var(--text-primary); font-size: 1.5rem; }
.sub-page .f-hero-desc { color: var(--text-secondary); font-size: 0.88rem; max-width: 100%; margin-bottom: 20px; }
.sub-page .f-hero-cta { justify-content: flex-start; }
.sub-page .btn-primary { padding: 10px 22px; font-size: 0.85rem; border-radius: 10px; }
.sub-page .btn-ghost { padding: 10px 22px; font-size: 0.85rem; border-radius: 10px; border-color: var(--border-color); color: var(--text-secondary); }
.sub-page .f-video-section { display: none; }
.sub-page .f-section { padding: 32px 0; border-bottom: 1px solid var(--border-color); }
.sub-page .f-section--alt { background: transparent; margin: 0; padding: 32px 0; }
.sub-page .f-section-header { text-align: left; margin-bottom: 24px; }
.sub-page .f-section-title { color: var(--text-primary); font-size: 1.2rem; }
.sub-page .f-section-subtitle { color: var(--text-secondary); max-width: 100%; margin: 0; }
.sub-page .f-label { color: var(--accent-color, #6366f1); }
.sub-page .pain-grid { grid-template-columns: 1fr; }
.sub-page .pain-card { background: var(--bg-secondary); border-color: var(--border-color); }
.sub-page .pain-card h3 { color: var(--text-primary); }
.sub-page .pain-card p { color: var(--text-secondary); }
.sub-page .feature-row, .sub-page .feature-row--reversed { flex-direction: column; gap: 20px; margin-bottom: 32px; }
.sub-page .feature-media { border-color: var(--border-color); box-shadow: none; }
.sub-page .feature-title { color: var(--text-primary); font-size: 1.15rem; }
.sub-page .feature-desc { color: var(--text-secondary); }
.sub-page .feature-checks li { color: var(--text-secondary); }
.sub-page .workflow-num { background: rgba(99,102,241,0.08); }
.sub-page .workflow-line { background: var(--border-color); }
.sub-page .workflow-body h3 { color: var(--text-primary); }
.sub-page .workflow-body p { color: var(--text-secondary); }
.sub-page .usecases-grid { grid-template-columns: 1fr; }
.sub-page .usecase-card { background: var(--bg-secondary); border-color: var(--border-color); }
.sub-page .usecase-card h3 { color: var(--text-primary); }
.sub-page .usecase-card p { color: var(--text-secondary); }
.sub-page .principle-grid { grid-template-columns: 1fr; }
.sub-page .principle-card { background: var(--bg-secondary); border-color: var(--border-color); border-left-color: var(--accent-color, #6366f1); }
.sub-page .principle-card h3 { color: var(--text-primary); }
.sub-page .principle-card p { color: var(--text-secondary); }
.sub-page .f-cta-section { background: transparent; margin: 0; padding: 32px 0; }
.sub-page .f-cta-title { color: var(--text-primary); font-size: 1.3rem; }
.sub-page .f-cta-desc { color: var(--text-secondary); }
.sub-page .f-footer { border-top-color: var(--border-color); }
.sub-page .f-footer-links a { color: var(--text-secondary); }
.sub-page .f-footer-biz { color: var(--text-muted); }
</style>
