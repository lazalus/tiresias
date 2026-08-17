<template>
  <div class="main-view">
    <!-- Header -->
    <header class="app-header">
      <div class="header-left" @click="confirmLeave('/dashboard')" style="cursor:pointer;display:flex;align-items:center;">
        <span class="app-name">TIRESIAS VIEW</span>
      </div>
      <div class="header-right">
        <HeaderNav />
        <span class="status-indicator" :class="statusClass">
          <span class="dot"></span>
          {{ statusText }}
          <span v-if="reportProgress && currentStatus === 'processing'" class="progress-text">{{ reportProgress }}</span>
        </span>
      </div>
    </header>

    <main class="content-area">
      <div class="panel-full">
        <Step4Report :reportId="currentReportId" :simulationId="simulationId" :projectId="projectData?.project_id || null" :systemLogs="systemLogs" :activePanel="isDesktop ? '' : viewMode" @add-log="addLog" @update-status="updateStatus" @update-progress="updateProgress" />
      </div>
    </main>
    <nav class="bottom-nav">
      <button class="nav-item" :class="{ active: viewMode === 'report' }" @click="viewMode = 'report'">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
        <span>보고서</span>
      </button>
      <button class="nav-item" :class="{ active: viewMode === 'workflow' }" @click="viewMode = 'workflow'">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
        <span>워크플로우</span>
      </button>
      <button class="nav-item" @click="confirmLeave('/dashboard')">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
        <span>홈</span>
      </button>
    </nav>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter, onBeforeRouteLeave } from 'vue-router'
import HeaderNav from '../components/HeaderNav.vue'
import GraphPanel from '../components/GraphPanel.vue'
import Step4Report from '../components/Step4Report.vue'
import { getProject, getGraphData } from '../api/graph'
import { getSimulation } from '../api/simulation'
import { getReport } from '../api/report'
import { getUserProject } from '../api/projects'

const route = useRoute()
const router = useRouter()

// Props
const props = defineProps({
  reportId: String
})

// Layout State
const isDesktop = ref(window.innerWidth >= 1024)
const viewMode = ref('report') // report | workflow
const onResize = () => { isDesktop.value = window.innerWidth >= 1024 }

// Data State
const currentReportId = ref(route.params.reportId)
const simulationId = ref(null)
const projectData = ref(null)
const graphData = ref(null)
const graphLoading = ref(false)
const systemLogs = ref([])
const currentStatus = ref('processing') // processing | completed | error
const reportProgress = ref('')

// --- Status Computed ---
const statusClass = computed(() => {
  return currentStatus.value
})

const statusText = computed(() => {
  if (currentStatus.value === 'error') return 'Error'
  if (currentStatus.value === 'completed') return 'Completed'
  return 'Generating'
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

const updateProgress = (progress) => {
  reportProgress.value = progress
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
            const [graphProjectResult, userProjectResult] = await Promise.allSettled([
              getProject(simData.project_id),
              getUserProject(simData.project_id),
            ])

            const graphProject = graphProjectResult.status === 'fulfilled' && graphProjectResult.value?.success
              ? graphProjectResult.value.data
              : null
            const userProject = userProjectResult.status === 'fulfilled'
              ? (userProjectResult.value?.project || userProjectResult.value?.data || null)
              : null

            if (graphProject || userProject) {
              projectData.value = {
                ...(graphProject || {}),
                ...(userProject || {}),
                project_id: simData.project_id,
                graph_id: graphProject?.graph_id || userProject?.graph_id || null,
                simulation_id: userProject?.simulation_id || graphProject?.simulation_id || simData.id,
                report_id: userProject?.report_id || userProject?.reportId || graphProject?.report_id || graphProject?.reportId || currentReportId.value,
              }
              addLog(`프로젝트 로드 성공: ${simData.project_id}`)

              if (projectData.value.graph_id) {
                await loadGraph(projectData.value.graph_id)
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

function confirmLeave(path) {
  if (currentStatus.value === 'completed') {
    if (confirm('보고서 화면을 떠나면 심층 상호작용에 진입할 수 없습니다.\n이동하시겠습니까?')) {
      router.push(path)
    }
  } else {
    router.push(path)
  }
}

// 라우터 가드: HeaderNav 등 다른 경로로 이동 시에도 경고
onBeforeRouteLeave((to, from, next) => {
  if (currentStatus.value === 'completed' && to.name !== 'Interaction') {
    if (confirm('보고서 화면을 떠나면 심층 상호작용에 진입할 수 없습니다.\n이동하시겠습니까?')) {
      next()
    } else {
      next(false)
    }
  } else {
    next()
  }
})

onMounted(() => {
  window.addEventListener('resize', onResize)
  addLog('ReportView 초기화')
  loadReportData()
})

onUnmounted(() => {
  window.removeEventListener('resize', onResize)
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

.progress-text {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  font-weight: 600;
  color: var(--text-primary);
  margin-left: 2px;
}

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

@media (min-width: 1024px) {
  .bottom-nav {
    display: none;
  }
}
</style>
