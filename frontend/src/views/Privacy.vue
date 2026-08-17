<template>
  <div class="sub-page">
    <header class="sub-header">
      <router-link to="/profile?from=support" class="back-btn">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="15 18 9 12 15 6"/>
        </svg>
      </router-link>
      <h1 class="sub-title">개인정보 처리방침</h1>
      <div class="spacer"></div>
    </header>

    <main class="sub-content">
      <section class="legal-section">
        <h2>1. 개인정보처리방침 개요</h2>
        <p>에스아이(서비스명: TIRESIAS VIEW)는 개인정보보호법 등 관계 법령에 따라 이용자의 개인정보를 처리하며, 본 방침은 서비스 이용 과정에서 어떤 정보를 어떤 목적으로 처리하는지 설명합니다.</p>
        <p>문의처: support@tiresiasview.com</p>
      </section>

      <section class="legal-section">
        <h2>2. 처리하는 개인정보 항목</h2>
        <p>회사는 현재 서비스 제공에 필요한 범위의 정보만 처리하며, 별도 광고성 정보 수신 동의 항목은 운영하지 않습니다.</p>
        <ul>
          <li>회원가입 및 계정 관리: 이름, 이메일 주소, 비밀번호 해시, 닉네임, 프로필 이미지(선택 입력 시)</li>
          <li>결제 및 주문 처리: 주문번호, 결제금액, 결제상태, 결제키, 거래일시</li>
          <li>서비스 이용 데이터: 업로드 파일, 프로젝트명, 요구사항, 시뮬레이션 설정값, 그래프/시뮬레이션/보고서 결과, 후속 질의 내용, 운영 로그</li>
          <li>접속 및 기기 정보: IP 주소, 사용자 에이전트, 방문 경로, 생성·로그인·이용 시각</li>
          <li>브라우저 저장소: 로그인 토큰, 사용자 테마, 결제 진행 상태, 업로드 복구용 임시 데이터(IndexedDB/localStorage)</li>
        </ul>
      </section>

      <section class="legal-section">
        <h2>3. 개인정보 처리 목적</h2>
        <ul>
          <li>회원 식별, 로그인 유지, 계정 및 프로젝트 관리</li>
          <li>견적 계산, 결제 검증, 주문 처리, 환불·고객문의 대응</li>
          <li>온톨로지 생성, 지식 그래프 구축, 시뮬레이션 실행, 보고서 생성 및 후속 질의 제공</li>
          <li>보안, 장애 대응, 부정 사용 방지, 서비스 품질 개선</li>
        </ul>
      </section>

      <section class="legal-section">
        <h2>4. 보관 및 이용기간</h2>
        <p>회사는 처리 목적이 달성되면 지체 없이 해당 정보를 파기합니다. 다만 관계 법령에 따라 보관이 필요한 경우 아래 기간 동안 보관할 수 있습니다.</p>
        <ul>
          <li>회원정보: 회원 탈퇴 또는 계약 종료 시까지</li>
          <li>업로드 파일, 프로젝트, 시뮬레이션, 보고서: 이용자가 직접 삭제하거나 회원 탈퇴 시까지</li>
          <li>계약 또는 청약철회, 대금결제 및 재화·서비스 공급 기록: 전자상거래 등에서의 소비자보호에 관한 법률에 따라 5년</li>
          <li>소비자 불만 또는 분쟁처리 기록: 전자상거래 등에서의 소비자보호에 관한 법률에 따라 3년</li>
          <li>접속기록 및 접근 로그: 통신비밀보호법에 따라 3개월</li>
          <li>브라우저 저장소 데이터: 이용자가 로그아웃하거나 브라우저 데이터를 삭제할 때까지</li>
        </ul>
      </section>

      <section class="legal-section">
        <h2>5. 파기절차 및 방법</h2>
        <p>회원 탈퇴, 프로젝트 삭제, 보고서 삭제 등으로 더 이상 보관이 필요하지 않은 데이터는 서비스 운영 범위에서 지체 없이 삭제합니다. 전자적 파일은 복구가 어렵도록 삭제하거나 덮어쓰기 방식으로 파기하며, 법령상 별도 보관 대상은 분리 보관합니다.</p>
      </section>

      <section class="legal-section">
        <h2>6. 처리위탁 및 국외 이전</h2>
        <p>회사는 서비스 제공을 위해 아래 외부 사업자를 이용합니다.</p>
        <ul>
          <li>토스페이먼츠: 결제 승인, 결제수단 인증, 환불 처리</li>
          <li>Cloudflare, Inc.: 웹 애플리케이션 인프라, API 게이트웨이, 데이터베이스(D1), 파일 저장소(R2), 보안 및 접속 처리</li>
          <li>OpenAI, LLC: 문서 분석, 온톨로지 생성, 보고서 생성 등 AI 처리</li>
        </ul>
      </section>

      <section class="legal-section">
        <h2>7. 국외 이전 세부사항</h2>
        <ul>
          <li>OpenAI, LLC(미국): 업로드 문서의 일부 텍스트, 프로젝트 요구사항, 시뮬레이션 요약, 보고서 작성용 프롬프트를 API 호출 시 전송합니다. 목적은 AI 분석 및 결과 생성입니다.</li>
          <li>Cloudflare, Inc.(미국 및 글로벌 인프라 운영 지역): 계정·프로젝트 메타데이터, 업로드 파일, 접근 로그가 서비스 제공 과정에서 처리될 수 있습니다. 목적은 서비스 호스팅, 저장, 보안 및 성능 제공입니다.</li>
        </ul>
        <p>이용자는 국외 이전을 거부할 수 있으나, 이 경우 서비스 핵심 기능 이용이 제한될 수 있습니다. 민감정보나 제3자의 개인정보는 법적 근거 없이 업로드하지 않도록 주의해 주세요.</p>
      </section>

      <section class="legal-section">
        <h2>8. 제3자 제공</h2>
        <p>회사는 이용자의 개인정보를 원칙적으로 외부에 제공하지 않습니다. 다만 법령에 따른 제공 의무가 있거나 이용자가 사전에 동의한 경우에는 예외로 할 수 있습니다.</p>
      </section>

      <section class="legal-section">
        <h2>9. 이용자의 권리</h2>
        <p>이용자는 언제든지 자신의 개인정보에 대해 다음 권리를 행사할 수 있습니다.</p>
        <ul>
          <li>개인정보 열람, 정정, 삭제, 처리정지 요청</li>
          <li>프로젝트·보고서 삭제 및 회원 탈퇴 요청</li>
          <li>개인정보 처리방침, 보관기간, 외부 제공 범위 문의</li>
        </ul>
        <p>권리행사는 support@tiresiasview.com으로 접수할 수 있으며, 회사는 관련 법령에서 정한 범위 내에서 지체 없이 처리합니다.</p>
      </section>

      <section class="legal-section">
        <h2>10. 자동화된 처리와 AI 사용</h2>
        <p>회사는 이용자의 업로드 자료를 바탕으로 AI를 이용해 그래프, 시뮬레이션 설정, 보고서 초안을 생성할 수 있습니다. 다만 회사는 이용자에게 법률효과 또는 이에 준하는 중대한 영향을 미치는 완전 자동화된 결정을 내리지 않습니다.</p>
      </section>

      <section class="legal-section">
        <h2>11. 안전성 확보조치</h2>
        <ul>
          <li>비밀번호 해시 저장 및 인증 토큰 관리</li>
          <li>접근통제, 내부키 기반 백엔드 보호, 결제 검증 로직 운영</li>
          <li>업로드 데이터, 프로젝트, 보고서의 저장소 분리 및 운영 로그 관리</li>
        </ul>
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
    title: '개인정보처리방침 | 테이레시아스 뷰',
    description: '테이레시아스 뷰가 수집하는 개인정보 항목, 처리 목적, 보관 기간, 외부 처리 위탁과 국외 이전에 대한 안내입니다.',
    canonical: 'https://tiresiasview.com/privacy',
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
  margin: 8px 0 0;
  padding-left: 20px;
}

.legal-section li {
  font-size: 0.85rem;
  color: var(--text-secondary);
  line-height: 1.8;
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
