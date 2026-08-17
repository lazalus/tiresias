import { createRouter, createWebHistory } from 'vue-router'
import { isAuthenticated, currentUser } from '../store/auth.js'
import Home from '../views/Home.vue'
import Landing from '../views/Landing.vue'
import Features from '../views/Features.vue'
import Pricing from '../views/Pricing.vue'
import Login from '../views/Login.vue'
import Signup from '../views/Signup.vue'
import SignupVerify from '../views/SignupVerify.vue'
import Process from '../views/MainView.vue'
import SimulationView from '../views/SimulationView.vue'
import SimulationRunView from '../views/SimulationRunView.vue'
import ReportView from '../views/ReportView.vue'
import InteractionView from '../views/InteractionView.vue'
import Admin from '../views/Admin.vue'
import Credits from '../views/Credits.vue'
import History from '../views/History.vue'
import Profile from '../views/Profile.vue'
import Terms from '../views/Terms.vue'
import Privacy from '../views/Privacy.vue'
import Support from '../views/Support.vue'
import SampleReports from '../views/SampleReports.vue'
import SampleReportView from '../views/SampleReportView.vue'
import OpenSource from '../views/OpenSource.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { guest: true }
  },
  {
    path: '/signup',
    name: 'Signup',
    component: Signup,
    meta: { guest: true }
  },
  {
    path: '/signup/verify',
    name: 'SignupVerify',
    component: SignupVerify,
    meta: { guest: true }
  },
  {
    path: '/features',
    name: 'Features',
    component: Features
  },
  {
    path: '/pricing',
    name: 'Pricing',
    component: Pricing
  },
  {
    path: '/',
    name: 'Landing',
    component: Landing,
    meta: { guest: true }
  },
  {
    path: '/dashboard',
    name: 'Home',
    component: Home,
    meta: { requiresAuth: true }
  },
  {
    path: '/process/:projectId',
    name: 'Process',
    component: Process,
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/simulation/:simulationId',
    name: 'Simulation',
    component: SimulationView,
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/simulation/:simulationId/start',
    name: 'SimulationRun',
    component: SimulationRunView,
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/report/:reportId',
    name: 'Report',
    component: ReportView,
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/interaction/:reportId',
    name: 'Interaction',
    component: InteractionView,
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/admin',
    name: 'Admin',
    component: Admin,
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/credits',
    name: 'Credits',
    component: Credits,
    meta: { requiresAuth: true }
  },
  {
    path: '/history',
    name: 'Reports',
    component: History,
    meta: { requiresAuth: true }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: Profile,
    meta: { requiresAuth: true }
  },
  {
    path: '/terms',
    name: 'Terms',
    component: Terms
  },
  {
    path: '/privacy',
    name: 'Privacy',
    component: Privacy
  },
  {
    path: '/support',
    name: 'Support',
    component: Support
  },
  {
    path: '/open-source',
    name: 'OpenSource',
    component: OpenSource
  },
  {
    path: '/samples',
    name: 'SampleReports',
    component: SampleReports
  },
  {
    path: '/samples/:reportId',
    name: 'SampleReport',
    component: SampleReportView,
    props: true
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 인증 가드
router.beforeEach((to, from, next) => {
  if (to.meta.requiresAuth && !isAuthenticated.value) {
    next({ name: 'Login' })
  } else if (currentUser.value?.mustChangePassword && to.meta.requiresAuth && to.name !== 'Profile') {
    next({ name: 'Profile', query: { forcePassword: '1' } })
  } else if (to.meta.requiresAdmin && (!currentUser.value || currentUser.value.role !== 'admin')) {
    next({ name: 'Home' })
  } else if (to.meta.guest && isAuthenticated.value && !['Landing', 'SignupVerify'].includes(String(to.name))) {
    next(currentUser.value?.mustChangePassword ? { name: 'Profile', query: { forcePassword: '1' } } : { name: 'Home' })
  } else if (to.name === 'Landing' && isAuthenticated.value) {
    next(currentUser.value?.mustChangePassword ? { name: 'Profile', query: { forcePassword: '1' } } : { name: 'Home' })
  } else {
    next()
  }
})

export default router
