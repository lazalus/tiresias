<template>
  <div class="main-view">
    <!-- Header -->
    <header class="app-header">
      <div class="header-left" @click="router.push('/dashboard')" style="cursor:pointer;display:flex;align-items:center;">
        <span class="app-name">TIRESIAS VIEW</span>
      </div>
      <div class="header-right">
        <button class="back-to-report-btn" @click="goBackToReport">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
          <span>보고서</span>
        </button>
        <HeaderNav />
        <span class="status-indicator" :class="statusClass">
          <span class="dot"></span>
          {{ statusText }}
        </span>
      </div>
    </header>

    <main class="content-area">
      <div class="panel-full">
        <Step5Interaction :reportId="currentReportId" :simulationId="simulationId" :systemLogs="systemLogs" :mobilePanel="mobilePanel" @add-log="addLog" @update-status="updateStatus" />
      </div>
    </main>
    <nav class="bottom-nav">
      <button class="nav-item" :class="{ active: mobilePanel === 'report' }" @click="mobilePanel = 'report'">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
        <span>보고서</span>
      </button>
      <button class="nav-item" :class="{ active: mobilePanel === 'chat' }" @click="mobilePanel = 'chat'">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
        <span>심층대화</span>
      </button>
      <button class="nav-item" @click="confirmLeave">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
        <span>홈</span>
      </button>
    </nav>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import HeaderNav from '../components/HeaderNav.vue'
import GraphPanel from '../components/GraphPanel.vue'
import Step5Interaction from '../components/Step5Interaction.vue'
import { getProject, getGraphData } from '../api/graph'
import { getSimulation } from '../api/simulation'
import { getReport } from '../api/report'

const route = useRoute()
const router = useRouter()

// Props
const props = defineProps({
  reportId: String
})

// Layout State - 기본적으로 워크벤치 뷰로 전환
const viewMode = ref('workbench')

const mobilePanel = ref('chat') // 'report' | 'chat'

function confirmLeave() {
  if (confirm('심층 대화를 종료하시겠습니까?\n나가면 다시 돌아올 수 없습니다.')) {
    router.push('/dashboard')
  }
}

// Data State
const currentReportId = ref(route.params.reportId)
const simulationId = ref(null)
const projectData = ref(null)
const graphData = ref(null)
const graphLoading = ref(false)
const systemLogs = ref([])
const currentStatus = ref('ready') // ready | processing | completed | error

// --- Status Computed ---
const statusClass = computed(() => {
  return currentStatus.value
})

const statusText = computed(() => {
  if (currentStatus.value === 'error') return 'Error'
  if (currentStatus.value === 'completed') return 'Completed'
  if (currentStatus.value === 'processing') return 'Processing'
  return 'Ready'
})

// --- Helpers ---
const addLog = (msg) => {
  const time = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }) + '.' + new Date().getMilliseconds().toString().padStart(3, '0')
  systemLogs.value.push({ time, msg })
  if (systemLogs.value.length > 200) {
    systemLogs.value.shift()
  }
}

const updateStatus = (status) => {
  currentStatus.value = status
}


// --- Data Logic ---
const loadReportData = async () => {
  try {
    addLog(`보고서 데이터 로드: ${currentReportId.value}`)

    // report 정보에서 simulation_id 가져오기
    const reportRes = await getReport(currentReportId.value)
    if (reportRes.success && reportRes.data) {
      const reportData = reportRes.data
      simulationId.value = reportData.simulation_id
      
      if (simulationId.value) {
        // simulation 정보 가져오기
        const simRes = await getSimulation(simulationId.value)
        if (simRes.success && simRes.data) {
          const simData = simRes.data
          
          // project 정보 가져오기
          if (simData.project_id) {
            const projRes = await getProject(simData.project_id)
            if (projRes.success && projRes.data) {
              projectData.value = projRes.data
              addLog(`프로젝트 로드 성공: ${projRes.data.project_id}`)

              // graph 데이터 가져오기
              if (projRes.data.graph_id) {
                await loadGraph(projRes.data.graph_id)
              }
            }
          }
        }
      }
    } else {
      addLog(`보고서 정보 가져오기 실패: ${reportRes.error || '알 수 없는 오류'}`)
    }
  } catch (err) {
    addLog(`로드 오류: ${err.message}`)
  }
}

const loadGraph = async (graphId) => {
  graphLoading.value = true

  try {
    const res = await getGraphData(graphId)
    if (res.success) {
      graphData.value = res.data
      addLog('그래프 데이터 로드 성공')
    }
  } catch (err) {
    addLog(`그래프 로드 실패: ${err.message}`)
  } finally {
    graphLoading.value = false
  }
}

const refreshGraph = () => {
  if (projectData.value?.graph_id) {
    loadGraph(projectData.value.graph_id)
  }
}

// Watch route params
watch(() => route.params.reportId, (newId) => {
  if (newId && newId !== currentReportId.value) {
    currentReportId.value = newId
    loadReportData()
  }
}, { immediate: true })

onMounted(() => {
  addLog('InteractionView 초기화')
  loadReportData()
})
</script>

<style scoped>
.main-view {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #FFF;
  overflow: hidden;
  font-family: 'Space Grotesk', 'Noto Sans SC', system-ui, sans-serif;
}

/* Header */
.app-header {
  height: 60px;
  border-bottom: 1px solid #EAEAEA;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: #FFF;
  z-index: 100;
  position: relative;
}

.app-name {
  font-family: 'Outfit', sans-serif;
  font-weight: 700;
  letter-spacing: 0.08em;
  font-size: 0.82rem;
  color: var(--text-primary);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #666;
  font-weight: 500;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #CCC;
}

.status-indicator.ready .dot { background: #4CAF50; }
.status-indicator.processing .dot { background: #FF9800; animation: pulse 1s infinite; }
.status-indicator.completed .dot { background: #4CAF50; }
.status-indicator.error .dot { background: #F44336; }

@keyframes pulse { 50% { opacity: 0.5; } }

/* Content */
.content-area {
  flex: 1;
  display: flex;
  position: relative;
  overflow: hidden;
  min-height: 0;
}

.panel-full {
  width: 100%;
  height: 100%;
  overflow-y: auto;
  overflow-x: hidden;
  -webkit-overflow-scrolling: touch;
}

/* Bottom Navigation */
.bottom-nav {
  display: flex;
  border-top: 1px solid var(--border-color, #EAEAEA);
  background: var(--bg-primary, #FFF);
  padding: 6px 0 env(safe-area-inset-bottom, 6px);
  z-index: 100;
}

.nav-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 6px 0;
  background: none;
  border: none;
  color: var(--text-muted, #999);
  font-size: 10px;
  font-family: inherit;
  cursor: pointer;
  transition: color 0.15s;
}

.nav-item.active {
  color: var(--text-primary, #111);
}

.nav-item svg {
  width: 20px;
  height: 20px;
}

/* Back to Report Button */
.back-to-report-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  background: none;
  border: 1px solid var(--border-color, #EAEAEA);
  border-radius: 6px;
  padding: 5px 12px;
  font-size: 0.78rem;
  font-weight: 500;
  color: var(--text-secondary, #666);
  cursor: pointer;
  font-family: inherit;
  transition: all 0.15s;
}

.back-to-report-btn:hover {
  color: var(--text-primary, #111);
  border-color: var(--text-muted, #999);
}

/* Desktop */
@media (min-width: 1024px) {
  .bottom-nav {
    display: none;
  }

  .app-header {
    background: var(--header-bg, #FFF);
    backdrop-filter: saturate(180%) blur(20px);
  }
}
</style>
