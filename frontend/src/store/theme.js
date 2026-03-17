import { ref, watch } from 'vue'

const theme = ref(localStorage.getItem('tiresias_theme') || 'dark')

export function useTheme() {
  function setTheme(newTheme) {
    theme.value = newTheme
    localStorage.setItem('tiresias_theme', newTheme)
    applyTheme(newTheme)
  }

  function toggleTheme() {
    setTheme(theme.value === 'dark' ? 'light' : 'dark')
  }

  function applyTheme(t) {
    document.documentElement.setAttribute('data-theme', t)
    // iOS status bar 색상 동적 변경
    const meta = document.querySelector('meta[name="theme-color"]')
    if (meta) {
      meta.setAttribute('content', t === 'dark' ? '#0c0a15' : '#f8f9fa')
    }
    // apple status bar style
    const appleMeta = document.querySelector('meta[name="apple-mobile-web-app-status-bar-style"]')
    if (appleMeta) {
      appleMeta.setAttribute('content', t === 'dark' ? 'black-translucent' : 'default')
    }
  }

  // Apply on init
  applyTheme(theme.value)

  return { theme, setTheme, toggleTheme }
}
