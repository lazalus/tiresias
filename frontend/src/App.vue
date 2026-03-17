<template>
  <router-view />
</template>

<script setup>
import { useTheme } from './store/theme.js'

// Apply theme on app load
useTheme()
</script>

<style>
/* Theme Variables */
html[data-theme="dark"] {
  --bg-primary: #0c0a15;
  --bg-secondary: rgba(255, 255, 255, 0.03);
  --bg-surface: rgba(255, 255, 255, 0.04);
  --border-color: rgba(255, 255, 255, 0.06);
  --text-primary: #f0f0f5;
  --text-secondary: rgba(255, 255, 255, 0.4);
  --text-muted: rgba(255, 255, 255, 0.25);
  --header-bg: rgba(12, 10, 21, 0.72);
  --nav-bg: rgba(12, 10, 21, 0.92);
}

html[data-theme="light"] {
  --bg-primary: #f8f9fa;
  --bg-secondary: #ffffff;
  --bg-surface: #ffffff;
  --border-color: #e5e7eb;
  --text-primary: #111827;
  --text-secondary: #6b7280;
  --text-muted: #9ca3af;
  --header-bg: rgba(255, 255, 255, 0.85);
  --nav-bg: rgba(255, 255, 255, 0.92);
}

/* 전역 스타일 리셋 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html {
  background: var(--bg-primary);
}

#app {
  font-family: 'Inter', 'Noto Sans KR', system-ui, -apple-system, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: var(--text-primary);
  background: var(--bg-primary);
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
  background: var(--text-muted);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--text-secondary);
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
