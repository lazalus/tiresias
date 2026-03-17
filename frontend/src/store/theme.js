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
  }

  // Apply on init
  applyTheme(theme.value)

  return { theme, setTheme, toggleTheme }
}
