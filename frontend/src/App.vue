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
  background: #09090b;
}

#app {
  font-family: 'Space Grotesk', 'Noto Sans SC', system-ui, -apple-system, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #fafafa;
  background-color: #09090b;
  min-height: 100vh;
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
  background: rgba(255, 255, 255, 0.15);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.25);
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
