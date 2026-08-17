import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { initMarketing } from './utils/marketing.js'
import { refreshProfile, currentUser } from './store/auth.js'

const app = createApp(App)

app.use(router)
initMarketing(router)

refreshProfile().finally(() => {
  const route = router.currentRoute.value
  if (currentUser.value?.mustChangePassword && route?.meta?.requiresAuth && route.name !== 'Profile') {
    router.replace({ name: 'Profile', query: { forcePassword: '1' } }).finally(() => {
      app.mount('#app')
    })
    return
  }
  app.mount('#app')
})
