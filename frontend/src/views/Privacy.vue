<template>
  <div class="sub-page">
    <header class="sub-header">
      <router-link to="/profile" class="back-btn">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="15 18 9 12 15 6"/>
        </svg>
      </router-link>
      <h1 class="sub-title">개인정보 처리방침</h1>
      <div class="spacer"></div>
    </header>

    <main class="sub-content">
      <section class="legal-section">
        <h2>1. 수집하는 개인정보</h2>
        <p>서비스는 회원가입 및 서비스 제공을 위해 다음의 개인정보를 수집합니다.</p>
        <ul>
          <li>필수 항목: 이름, 이메일 주소, 비밀번호(암호화 저장)</li>
          <li>결제 시: 결제 수단 정보(토스페이먼츠를 통해 처리, 서비스에 직접 저장하지 않음)</li>
        </ul>
      </section>

      <section class="legal-section">
        <h2>2. 이용 목적</h2>
        <p>수집된 개인정보는 다음의 목적으로 이용됩니다.</p>
        <ul>
          <li>회원 식별 및 서비스 제공</li>
          <li>이용권 결제 처리 및 이용 내역 관리</li>
          <li>서비스 관련 공지 및 고객 문의 대응</li>
        </ul>
      </section>

      <section class="legal-section">
        <h2>3. 보관 기간</h2>
        <p>개인정보는 회원 탈퇴 시까지 보관되며, 탈퇴 후 즉시 파기합니다. 다만, 관계 법령에 따라 보존이 필요한 경우 해당 기간 동안 보관합니다.</p>
        <ul>
          <li>결제 기록: 전자상거래법에 따라 5년 보관</li>
          <li>로그인 기록: 통신비밀보호법에 따라 3개월 보관</li>
        </ul>
      </section>

      <section class="legal-section">
        <h2>4. 제3자 제공</h2>
        <p>서비스는 이용자의 동의 없이 개인정보를 제3자에게 제공하지 않습니다. 다만, 다음의 경우는 예외로 합니다.</p>
        <ul>
          <li>결제 처리를 위한 토스페이먼츠 연동 (결제 정보에 한함)</li>
          <li>법령에 의한 수사기관의 요청</li>
        </ul>
      </section>

      <section class="legal-section">
        <h2>5. 이용자의 권리</h2>
        <p>이용자는 언제든지 다음의 권리를 행사할 수 있습니다.</p>
        <ul>
          <li>개인정보 열람, 수정 요청</li>
          <li>회원 탈퇴 및 개인정보 삭제 요청</li>
          <li>개인정보 처리 정지 요청</li>
        </ul>
        <p>상기 요청은 고객센터(support@tiresiasview.com)를 통해 접수할 수 있습니다.</p>
      </section>

      <div class="legal-footer">
        <p>시행일: 2024년 1월 1일</p>
      </div>
    </main>
  </div>
</template>

<script setup>
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
  color: rgba(255, 255, 255, 0.7);
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
  color: rgba(255, 255, 255, 0.85);
  margin: 0 0 12px;
}

.legal-section p {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.5);
  line-height: 1.7;
  margin: 0 0 6px;
}

.legal-section ul {
  margin: 8px 0 0;
  padding-left: 20px;
}

.legal-section li {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.45);
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
