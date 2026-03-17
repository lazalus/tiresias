<template>
  <router-view />
</template>

<script setup>
import { useTheme } from './store/theme.js'

// Apply theme on app load
useTheme()
</script>

<style>
/* Theme Variables - Dark (default) */
html[data-theme="dark"] {
  --bg-primary: #111118;
  --bg-secondary: #1a1a24;
  --bg-tertiary: #22222e;
  --bg-surface: rgba(255, 255, 255, 0.03);
  --surface-hover: rgba(255, 255, 255, 0.06);
  --border-color: rgba(255, 255, 255, 0.06);
  --text-primary: #e8e8ed;
  --text-secondary: #8888a0;
  --text-muted: #55556a;
  --accent-color: #6366f1;
  --accent-hover: #5558e6;
  --header-bg: rgba(17, 17, 24, 0.85);
  --nav-bg: rgba(17, 17, 24, 0.92);
}

/* Theme Variables - Light */
html[data-theme="light"] {
  --bg-primary: #fafafa;
  --bg-secondary: #ffffff;
  --bg-tertiary: #f4f4f5;
  --bg-surface: rgba(0, 0, 0, 0.02);
  --surface-hover: rgba(0, 0, 0, 0.04);
  --border-color: rgba(0, 0, 0, 0.08);
  --text-primary: #18181b;
  --text-secondary: #71717a;
  --text-muted: #a1a1aa;
  --accent-color: #6366f1;
  --accent-hover: #5558e6;
  --header-bg: rgba(250, 250, 250, 0.85);
  --nav-bg: rgba(250, 250, 250, 0.92);
}

/* Global reset */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html {
  font-size: 14px;
  background: var(--bg-primary);
}

#app {
  font-family: 'Inter', 'Noto Sans KR', system-ui, -apple-system, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: var(--text-primary);
  background: var(--bg-primary);
  min-height: 100vh;
  letter-spacing: -0.01em;
  line-height: 1.5;
}

/* Scrollbar */
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

/* Global button reset */
button {
  font-family: inherit;
}

/* Global link reset */
a {
  transition: color 0.15s ease;
}

/* Text selection */
::selection {
  background: rgba(99, 102, 241, 0.25);
  color: var(--text-primary);
}

/* Global transition speed */
*, *::before, *::after {
  transition-timing-function: ease;
  transition-duration: 0.15s;
}

/* Opt out elements that shouldn't auto-transition */
input, textarea, button, a, [class*="router"] {
  transition: none;
}
</style>
