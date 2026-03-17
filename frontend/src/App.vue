<template>
  <router-view />
</template>

<script setup>
// Vue Router로 페이지 관리
</script>

<style>
/* 전역 스타일 리셋 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html {
  background: #0c0a15;
}

#app {
  font-family: 'Inter', 'Noto Sans KR', system-ui, -apple-system, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #f0f0f5;
  background: #0c0a15;
  min-height: 100vh;
  position: relative;
}

/* 미세한 배경 그라디언트 */
#app::before {
  content: '';
  position: fixed;
  inset: 0;
  background:
    radial-gradient(ellipse 80% 60% at 50% -10%, rgba(99, 102, 241, 0.07) 0%, transparent 60%),
    radial-gradient(ellipse 60% 50% at 80% 100%, rgba(129, 140, 248, 0.04) 0%, transparent 50%);
  pointer-events: none;
  z-index: 0;
}

/* 스크롤바 스타일 */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.12);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.2);
}

/* 전역 버튼 스타일 */
button {
  font-family: inherit;
}

/* 전역 텍스트 선택 색상 */
::selection {
  background: rgba(99, 102, 241, 0.3);
  color: #fff;
}
</style>
