<template>
  <div class="legal-screen">
    <header class="legal-header">
      <div class="legal-header-inner">
        <router-link to="/" class="brand-link">TIRESIAS VIEW</router-link>
        <div class="legal-nav">
          <router-link to="/terms">이용약관</router-link>
          <router-link to="/privacy">개인정보처리방침</router-link>
        </div>
      </div>
    </header>

    <main class="legal-main">
      <section class="legal-card">
        <p class="eyebrow">Open Source Notice</p>
        <h1>오픈소스 및 소스코드 고지</h1>
        <p class="lead">
          Tiresias View는 AGPL-3.0 라이선스 기반 오픈소스 소프트웨어를 포함하며,
          현재 서비스에 배포 중인 수정 버전의 소스코드를 아래 저장소에서 확인할 수 있습니다.
        </p>

        <div class="callout">
          <span class="callout-label">배포 중인 소스코드</span>
          <a href="https://github.com/lazalus/tiresias" target="_blank" rel="noopener noreferrer">
            github.com/lazalus/tiresias
          </a>
        </div>

        <div class="grid">
          <article class="info-card">
            <h2>현재 라이선스</h2>
            <p>이 프로젝트 전체는 GNU Affero General Public License v3.0에 따라 배포됩니다.</p>
            <a href="https://github.com/lazalus/tiresias/blob/main/LICENSE" target="_blank" rel="noopener noreferrer">
              LICENSE 보기
            </a>
          </article>

          <article class="info-card">
            <h2>원본 프로젝트</h2>
            <p>MiroFish를 기반으로 수정되었으며, 원본 프로젝트의 저작권 고지와 변경 고지를 유지합니다.</p>
            <a href="https://github.com/666ghj/MiroFish" target="_blank" rel="noopener noreferrer">
              원본 저장소 보기
            </a>
          </article>

          <article class="info-card">
            <h2>변경 고지</h2>
            <p>브랜딩, 인프라, 결제, 보고서, 그래프 저장소, 한국어 서비스 흐름에 대한 수정 사항을 별도 고지합니다.</p>
            <a href="https://github.com/lazalus/tiresias/blob/main/NOTICE.md" target="_blank" rel="noopener noreferrer">
              NOTICE 보기
            </a>
          </article>
        </div>

        <section class="detail-block">
          <h2>이용자에게 안내하는 사항</h2>
          <ul>
            <li>이 서비스는 AGPL-3.0 기반 수정 버전을 네트워크를 통해 제공합니다.</li>
            <li>서비스 이용자는 현재 배포 중인 버전의 소스코드에 접근할 수 있습니다.</li>
            <li>본 소프트웨어는 별도 약정이 없는 한 어떠한 보증도 없이 제공됩니다.</li>
          </ul>
        </section>

        <section class="detail-block">
          <h2>추가 참고 링크</h2>
          <ul>
            <li><a href="https://www.gnu.org/licenses/agpl-3.0.en.html" target="_blank" rel="noopener noreferrer">GNU AGPL v3 원문</a></li>
            <li><a href="https://www.gnu.org/licenses/gpl-faq.html#UnreleasedModsAGPL" target="_blank" rel="noopener noreferrer">GNU FAQ: 웹서비스와 AGPL</a></li>
          </ul>
        </section>
      </section>
    </main>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'
import { applySeoMeta, resetSeoMeta } from '../utils/seo.js'

onMounted(() => {
  applySeoMeta({
    title: '오픈소스 고지 | 테이레시아스 뷰',
    description: '테이레시아스 뷰 서비스에 적용된 오픈소스 라이선스와 배포 중인 소스코드, 변경 고지를 안내합니다.',
    canonical: 'https://tiresiasview.com/open-source',
  })
})

onUnmounted(() => {
  resetSeoMeta()
})
</script>

<style scoped>
.legal-screen {
  min-height: 100vh;
  background: var(--bg-primary);
  color: var(--text-primary);
}

.legal-header {
  position: sticky;
  top: 0;
  z-index: 20;
  background: var(--header-bg);
  backdrop-filter: saturate(180%) blur(20px);
  -webkit-backdrop-filter: saturate(180%) blur(20px);
  border-bottom: 1px solid var(--border-color);
}

.legal-header-inner {
  max-width: 1080px;
  margin: 0 auto;
  padding: 16px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.brand-link,
.legal-nav a,
.callout a,
.info-card a,
.detail-block a {
  color: inherit;
  text-decoration: none;
}

.brand-link {
  font-weight: 700;
  letter-spacing: 0.08em;
}

.legal-nav {
  display: flex;
  gap: 16px;
  font-size: 0.92rem;
  color: var(--text-secondary);
}

.legal-main {
  max-width: 1080px;
  margin: 0 auto;
  padding: 40px 20px 72px;
}

.legal-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 24px;
  padding: 32px;
}

.eyebrow {
  color: var(--accent-color);
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  margin-bottom: 10px;
}

h1 {
  font-size: clamp(2rem, 4vw, 3rem);
  line-height: 1.1;
  margin-bottom: 14px;
}

.lead {
  color: var(--text-secondary);
  max-width: 760px;
  margin-bottom: 24px;
}

.callout {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 18px 20px;
  border-radius: 18px;
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  margin-bottom: 24px;
}

.callout-label {
  font-size: 0.82rem;
  color: var(--text-secondary);
}

.callout a,
.info-card a,
.detail-block a {
  color: var(--accent-color);
  word-break: break-all;
}

.grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.info-card,
.detail-block {
  border: 1px solid var(--border-color);
  background: var(--bg-surface);
  border-radius: 18px;
  padding: 20px;
}

.info-card h2,
.detail-block h2 {
  font-size: 1rem;
  margin-bottom: 10px;
}

.info-card p,
.detail-block li {
  color: var(--text-secondary);
}

.detail-block + .detail-block {
  margin-top: 16px;
}

.detail-block ul {
  padding-left: 18px;
  display: grid;
  gap: 8px;
}

@media (max-width: 900px) {
  .grid {
    grid-template-columns: 1fr;
  }

  .legal-card {
    padding: 24px;
  }
}

@media (max-width: 640px) {
  .legal-header-inner {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
