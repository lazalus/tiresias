<template>
  <div class="sub-page">
    <header class="sub-header">
      <router-link to="/profile?from=support" class="back-btn">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="15 18 9 12 15 6"/>
        </svg>
      </router-link>
      <h1 class="sub-title">서비스 이용약관</h1>
      <div class="spacer"></div>
    </header>

    <main class="sub-content">
      <section class="legal-section">
        <h2>제1조 (사업자 정보 및 목적)</h2>
        <p>본 약관은 에스아이(서비스명: TIRESIAS VIEW, 대표자: 정희수, 사업자등록번호: 111-63-00101, 통신판매업신고번호: 2024-안양동안-0010, 문의: support@tiresiasview.com)가 제공하는 AI 기반 예측 시뮬레이션 서비스의 이용조건, 권리·의무 및 책임사항을 규정함을 목적으로 합니다.</p>
      </section>

      <section class="legal-section">
        <h2>제2조 (정의)</h2>
        <p>1. "서비스"란 이용자가 업로드한 자료와 입력한 요구사항을 바탕으로 온톨로지 생성, 지식 그래프 구축, 페르소나·환경 준비, 시뮬레이션 실행, 보고서 생성 및 후속 질의를 제공하는 온라인 서비스를 말합니다.</p>
        <p>2. "이용자"란 본 약관에 동의하고 서비스를 이용하는 회원 또는 방문자를 말합니다.</p>
        <p>3. "프로젝트"란 이용자가 업로드한 자료와 요구사항을 기준으로 생성되는 개별 작업 단위를 말합니다.</p>
        <p>4. "결제"란 서비스 이용을 위해 견적 확인 후 토스페이먼츠를 통해 결제 승인하는 행위를 말합니다.</p>
      </section>

      <section class="legal-section">
        <h2>제3조 (회원가입 및 계정)</h2>
        <p>1. 이용자는 정확한 이름, 이메일, 비밀번호 등 가입 정보를 입력해야 하며, 타인의 정보나 권한을 도용해서는 안 됩니다.</p>
        <p>2. 계정과 인증정보의 관리 책임은 이용자에게 있으며, 계정 오남용으로 발생한 손해는 이용자의 귀책이 있는 한 회사가 책임지지 않습니다.</p>
        <p>3. 회사는 보안상 필요하거나 약관 위반이 의심되는 경우 인증, 이용 제한 또는 추가 확인을 요청할 수 있습니다.</p>
      </section>

      <section class="legal-section">
        <h2>제4조 (서비스의 내용)</h2>
        <p>1. 서비스는 업로드 자료 분석, 온톨로지 생성, 지식 그래프 구축, 시뮬레이션 준비, 시뮬레이션 실행, 보고서 생성, 결과 조회 및 후속 질의 기능을 제공합니다.</p>
        <p>2. 서비스는 시스템 상황에 따라 일부 기능의 순서, 처리 시간, 대기열 정책, 지원 파일 형식, 결과 표현 방식을 변경할 수 있습니다.</p>
        <p>3. 회사는 안정적인 운영을 위해 작업 대기열, 동시 실행 제한, 자동 재시도 정책을 둘 수 있습니다.</p>
      </section>

      <section class="legal-section">
        <h2>제5조 (결제, 대기열, 환불)</h2>
        <p>1. 이용요금은 업로드 자료의 규모, 예상 페이지 수, 분석 깊이 등 서비스 화면에 제시되는 견적에 따라 결정됩니다.</p>
        <p>2. 결제는 토스페이먼츠를 통해 처리되며, 결제 승인 후 회사 서버가 주문 정보와 금액 일치 여부를 확인한 경우에만 프로젝트가 시작됩니다.</p>
        <p>3. 결제 후 대기열에 진입하거나 순번을 기다리는 경우에도 동일 프로젝트에 대해 중복 과금되지 않습니다.</p>
        <p>4. 회사 시스템 오류로 프로젝트 생성 전 결제가 정상 사용 처리되지 못한 경우 회사는 결제를 해제하거나 사용 처리하지 않습니다.</p>
        <p>5. 프로젝트 생성 이후 회사 귀책으로 서비스가 정상 제공되지 못한 경우 회사는 재실행, 결제 복구, 환불 등 합리적인 조치를 검토할 수 있습니다.</p>
        <p>6. 전자상거래 등에서의 소비자보호에 관한 법률 등 관계 법령에 따라, 미사용 결제분에 대해서는 결제일로부터 7일 이내 청약철회 또는 환불을 요청할 수 있습니다. 다만 이용자의 요청으로 디지털 서비스 제공이 개시된 후에는 법령상 청약철회가 제한될 수 있습니다.</p>
      </section>

      <section class="legal-section">
        <h2>제6조 (업로드 자료와 이용자 책임)</h2>
        <p>1. 이용자는 자신이 적법하게 이용할 권리를 가진 자료만 업로드해야 합니다.</p>
        <p>2. 이용자는 법령상 근거 없이 타인의 개인정보, 민감정보, 영업비밀, 저작권 침해 자료, 불법정보를 업로드해서는 안 됩니다.</p>
        <p>3. 회사는 법령 위반, 보안 위험, 과도한 시스템 부하, 타인 권리 침해 우려가 있는 자료나 프로젝트에 대해 생성 거부, 삭제, 이용 제한 조치를 취할 수 있습니다.</p>
      </section>

      <section class="legal-section">
        <h2>제7조 (금지행위)</h2>
        <ul>
          <li>타인의 계정이나 결제수단을 무단 사용하거나 가장하는 행위</li>
          <li>서비스를 역설계, 크롤링, 우회 호출, 자동 대량호출 등으로 과부하시키는 행위</li>
          <li>불법자료, 악성코드, 권리침해 자료, 무단 개인정보를 업로드하는 행위</li>
          <li>서비스 결과를 사실인 것처럼 허위·과장하여 제3자를 기망하는 행위</li>
        </ul>
      </section>

      <section class="legal-section">
        <h2>제8조 (지식재산권)</h2>
        <p>1. 서비스 UI, 소프트웨어, 상표, 운영 로직 등 회사가 작성한 구성요소에 대한 권리는 회사 또는 정당한 권리자에게 귀속됩니다.</p>
        <p>2. 이용자가 업로드한 자료의 권리는 원칙적으로 해당 이용자 또는 원권리자에게 귀속됩니다.</p>
        <p>3. 회사는 서비스 제공, 보안 점검, 장애 대응, 결과 생성 범위에서만 업로드 자료와 프로젝트 데이터를 이용합니다.</p>
      </section>

      <section class="legal-section">
        <h2>제9조 (서비스 변경·중단)</h2>
        <p>회사는 점검, 업데이트, 외부 API 장애, 천재지변, 보안 이슈, 법령 변경 등의 사유로 서비스 전부 또는 일부를 변경하거나 일시 중단할 수 있습니다. 중대한 변경이 있는 경우 서비스 화면 또는 공지로 안내합니다.</p>
      </section>

      <section class="legal-section">
        <h2>제10조 (AI 결과물의 한계)</h2>
        <p>1. 서비스 결과물은 AI 기반 참고 자료이며 실제 사회·시장·정책 결과를 보장하지 않습니다.</p>
        <p>2. 결과물은 투자, 금융, 법률, 의료, 정책, 채용 등 전문적 판단을 대체하지 않으며, 이용자는 별도의 검토와 전문가 자문을 병행해야 합니다.</p>
        <p>3. 이용자가 결과물을 활용해 내린 의사결정의 책임은 이용자에게 있으며, 회사는 회사의 고의 또는 중대한 과실이 없는 한 그 결과에 대한 책임을 부담하지 않습니다.</p>
      </section>

      <section class="legal-section">
        <h2>제11조 (이용제한 및 계약해지)</h2>
        <p>회사는 약관 위반, 법령 위반, 타인 권리 침해, 결제 부정 사용, 서비스 안정성 훼손 등이 확인되는 경우 사전 통지 후 또는 긴급 시 즉시 계정 이용을 제한하거나 계약을 해지할 수 있습니다.</p>
      </section>

      <section class="legal-section">
        <h2>제12조 (준거법 및 분쟁해결)</h2>
        <p>본 약관은 대한민국 법령에 따라 해석되며, 회사와 이용자 간 분쟁은 관계 법령과 소비자분쟁해결기준에 따릅니다.</p>
      </section>

      <div class="legal-footer">
        <p>시행일: 2026년 3월 20일</p>
      </div>
    </main>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'
import { applySeoMeta, resetSeoMeta } from '../utils/seo.js'

onMounted(() => {
  applySeoMeta({
    title: '이용약관 | 테이레시아스 뷰',
    description: '테이레시아스 뷰의 회원가입, 결제, 환불, 업로드 자료 이용, 책임 제한에 관한 서비스 이용약관입니다.',
    canonical: 'https://tiresiasview.com/terms',
  })
})

onUnmounted(() => {
  resetSeoMeta()
})
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

.legal-section {
  margin-bottom: 28px;
}

.legal-section h2 {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 12px;
}

.legal-section p {
  font-size: 0.85rem;
  color: var(--text-secondary);
  line-height: 1.7;
  margin: 0 0 6px;
}

.legal-section ul {
  padding-left: 20px;
  margin: 0;
}

.legal-section li {
  font-size: 0.85rem;
  color: var(--text-secondary);
  line-height: 1.7;
  margin: 0 0 6px;
}

.legal-footer {
  margin-top: 40px;
  padding-top: 20px;
  border-top: 1px solid var(--border-color);
}

.legal-footer p {
  font-size: 0.78rem;
  color: var(--text-muted);
}
</style>
