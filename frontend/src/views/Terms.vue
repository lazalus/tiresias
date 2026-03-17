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
        <h2>제1조 (목적)</h2>
        <p>이 약관은 TIRESIAS VIEW(이하 "서비스")가 제공하는 시뮬레이션 서비스의 이용에 관한 제반 사항을 규정함을 목적으로 합니다.</p>
      </section>

      <section class="legal-section">
        <h2>제2조 (정의)</h2>
        <p>1. "서비스"란 TIRESIAS VIEW가 제공하는 시뮬레이션 분석 및 보고서 생성 서비스를 의미합니다.</p>
        <p>2. "이용자"란 본 약관에 동의하고 서비스를 이용하는 자를 의미합니다.</p>
        <p>3. "이용권(크레딧)"이란 서비스 내에서 시뮬레이션을 실행하기 위해 필요한 디지털 이용 단위를 의미합니다.</p>
      </section>

      <section class="legal-section">
        <h2>제3조 (이용권 및 결제)</h2>
        <p>1. 이용권(크레딧) 1개는 시뮬레이션 1회 실행 권한에 해당합니다.</p>
        <p>2. 이용권은 구매 후 사용 기한 없이 보유할 수 있으며, 서비스 종료 시까지 유효합니다.</p>
        <p>3. 결제는 토스페이먼츠를 통해 처리되며, 결제 완료 후 즉시 크레딧이 충전됩니다.</p>
        <p>4. 환불은 미사용 크레딧에 한하여 구매일로부터 7일 이내에 고객센터를 통해 요청할 수 있습니다.</p>
      </section>

      <section class="legal-section">
        <h2>제4조 (서비스 이용)</h2>
        <p>1. 이용자는 서비스를 본래의 목적에 맞게 이용하여야 합니다.</p>
        <p>2. 이용자는 타인의 계정을 무단으로 사용하거나, 서비스를 부정한 방법으로 이용해서는 안 됩니다.</p>
        <p>3. 서비스는 시스템 점검, 업데이트 등의 사유로 사전 공지 후 일시적으로 중단될 수 있습니다.</p>
      </section>

      <section class="legal-section">
        <h2>제5조 (면책)</h2>
        <p>1. 서비스에서 제공하는 시뮬레이션 결과 및 보고서는 AI 기반 예측 참고 자료이며, 실제 결과와 다를 수 있습니다. 서비스는 시뮬레이션 결과의 정확성, 완전성, 신뢰성을 보장하지 않습니다.</p>
        <p>2. 본 서비스의 결과물은 투자, 금융, 법률, 의료 등 전문적 판단을 대체하지 않으며, 투자 자문 또는 권유에 해당하지 않습니다.</p>
        <p>3. 이용자가 시뮬레이션 결과를 기반으로 내린 투자, 사업, 정책 등 일체의 의사결정에 대해 서비스 제공자는 어떠한 법적 책임도 부담하지 않으며, 이로 인한 직접적·간접적·부수적 손해에 대해 배상 의무가 없습니다.</p>
        <p>4. 천재지변, 시스템 장애 등 불가항력적 사유로 인한 서비스 중단에 대해 서비스는 책임을 지지 않습니다.</p>
        <p>5. 이용자는 시뮬레이션 결과를 활용할 때 반드시 독립적인 판단과 전문가 자문을 병행해야 하며, 이에 대한 책임은 전적으로 이용자에게 있습니다.</p>
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
