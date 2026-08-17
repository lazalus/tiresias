<template>
  <div class="main-view">
    <!-- Header -->
    <header class="app-header">
      <div class="header-left" @click="router.push('/dashboard')" style="cursor:pointer;display:flex;align-items:center;">
        <span class="app-name">TIRESIAS VIEW</span>
      </div>
      <div class="header-right">
        <HeaderNav />
        <span class="status-indicator" :class="statusClass">
          <span class="dot"></span>
          {{ statusText }}
        </span>
      </div>
    </header>

    <!-- Main Content Area -->
    <main class="content-area">
      <div v-show="viewMode === 'graph' || isDesktop" class="panel-graph">
        <GraphPanel
          :graphData="graphData"
          :loading="graphLoading"
          :currentPhase="3"
          :isSimulating="isSimulating"
          :isVisible="viewMode === 'graph' || isDesktop"
          @refresh="refreshGraph"
        />
      </div>
      <div v-show="viewMode === 'workbench' || isDesktop" class="panel-workbench">
        <Step3Simulation
          :simulationId="currentSimulationId"
          :maxRounds="maxRounds"
          :minutesPerRound="minutesPerRound"
          :projectData="projectData"
          :graphData="graphData"
          :systemLogs="systemLogs"
          @go-back="handleGoBack"
          @next-step="handleNextStep"
          @add-log="addLog"
          @update-status="updateStatus"
        />
      </div>
    </main>

    <nav class="bottom-nav">
      <button class="nav-item" :class="{ active: viewMode === 'graph' }" @click="viewMode = 'graph'">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="3"/><circle cx="5" cy="6" r="2"/><circle cx="19" cy="6" r="2"/><circle cx="5" cy="18" r="2"/><circle cx="19" cy="18" r="2"/><line x1="7" y1="7" x2="10" y2="10"/><line x1="14" y1="10" x2="17" y2="7"/><line x1="7" y1="17" x2="10" y2="14"/><line x1="14" y1="14" x2="17" y2="17"/></svg>
        <span>그래프</span>
      </button>
      <button class="nav-item" :class="{ active: viewMode === 'workbench' }" @click="viewMode = 'workbench'">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/></svg>
        <span>워크벤치</span>
      </button>
      <button class="nav-item" @click="router.push('/dashboard')">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
        <span>홈</span>
      </button>
    </nav>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import HeaderNav from '../components/HeaderNav.vue'
import GraphPanel from '../components/GraphPanel.vue'
import Step3Simulation from '../components/Step3Simulation.vue'
import { getProject, getGraphData } from '../api/graph'
import { getUserProject } from '../api/projects'
import { getSimulation, getSimulationConfig, stopSimulation, closeSimulationEnv, getEnvStatus } from '../api/simulation'
import { PROJECT_STATUS, normalizeProjectStatus } from '../utils/projectStatus.js'

const route = useRoute()
const router = useRouter()

// Props
const props = defineProps({
  simulationId: String
})

// Layout State
const viewMode = ref('workbench')
const isDesktop = ref(window.innerWidth >= 1024)
const MIN_SIMULATION_ROUNDS = 10

// Data State
const currentSimulationId = ref(route.params.simulationId)
// 초기화 시 query 파라미터에서 maxRounds를 직접 가져와 하위 컴포넌트가 즉시 값을 받을 수 있도록 함
const maxRounds = ref(
  route.query.maxRounds
    ? Math.max(MIN_SIMULATION_ROUNDS, parseInt(route.query.maxRounds, 10) || MIN_SIMULATION_ROUNDS)
    : null
)
const minutesPerRound = ref(30) // 기본 라운드당 30분
const projectData = ref(null)
const graphData = ref(null)
const graphLoading = ref(false)
const systemLogs = ref([])
const currentStatus = ref('processing') // processing | completed | error

// --- Status ---

// --- Status Computed ---
const statusClass = computed(() => {
  return currentStatus.value
})

const statusText = computed(() => {
  if (currentStatus.value === 'error') return 'Error'
  if (currentStatus.value === 'completed') return 'Completed'
  return 'Running'
})

const isSimulating = computed(() => currentStatus.value === 'processing')

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

const handleGoBack = async () => {
  // Step 2로 돌아가기 전에 실행 중인 시뮬레이션 종료
  addLog('Step 2로 돌아가기 준비, 시뮬레이션 종료 중...')
  
  // 폴링 중지
  stopGraphRefresh()
  
  try {
    // 시뮬레이션 환경 정상 종료 시도
    const envStatusRes = await getEnvStatus({ simulation_id: currentSimulationId.value })
    
    if (envStatusRes.success && envStatusRes.data?.env_alive) {
      addLog('시뮬레이션 환경 종료 중...')
      try {
        await closeSimulationEnv({ 
          simulation_id: currentSimulationId.value,
          timeout: 10
        })
        addLog('시뮬레이션 환경 종료 완료')
      } catch (closeErr) {
        addLog(`시뮬레이션 환경 종료 실패, 강제 중지 시도...`)
        try {
          await stopSimulation({ simulation_id: currentSimulationId.value })
          addLog('시뮬레이션 강제 중지 완료')
        } catch (stopErr) {
          addLog(`강제 중지 실패: ${stopErr.message}`)
        }
      }
    } else {
      // 환경이 실행 중이 아님, 프로세스 중지 필요 여부 확인
      if (isSimulating.value) {
        addLog('시뮬레이션 프로세스 중지 중...')
        try {
          await stopSimulation({ simulation_id: currentSimulationId.value })
          addLog('시뮬레이션 중지 완료')
        } catch (err) {
          addLog(`시뮬레이션 중지 실패: ${err.message}`)
        }
      }
    }
  } catch (err) {
    addLog(`시뮬레이션 상태 확인 실패: ${err.message}`)
  }
  
  // Step 2 (환경 설정)로 돌아감
  router.push({
    name: 'Simulation',
    params: { simulationId: currentSimulationId.value },
    query: { stopRunning: '1' },
  })
}

const handleNextStep = () => {
  // Step3Simulation 컴포넌트가 보고서 생성 및 라우트 이동을 직접 처리
  // 이 메서드는 백업용
  addLog('Step 4 진입: 보고서 생성')
}

// --- Data Logic ---
const loadSimulationData = async () => {
  try {
    addLog(`시뮬레이션 데이터 로드: ${currentSimulationId.value}`)

    // simulation 정보 가져오기
    const simRes = await getSimulation(currentSimulationId.value)
    if (simRes.success && simRes.data) {
      const simData = simRes.data
      
      // simulation config에서 minutes_per_round 가져오기
      try {
        const configRes = await getSimulationConfig(currentSimulationId.value)
        if (configRes.success && configRes.data?.time_config?.minutes_per_round) {
          minutesPerRound.value = configRes.data.time_config.minutes_per_round
          addLog(`시간 설정: 라운드당 ${minutesPerRound.value}분`)
        }
      } catch (configErr) {
        addLog(`시간 설정 가져오기 실패, 기본값 사용: ${minutesPerRound.value}분/라운드`)
      }
      
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
            simulation_id: userProject?.simulation_id || graphProject?.simulation_id || currentSimulationId.value,
            report_id: userProject?.report_id || userProject?.reportId || graphProject?.report_id || graphProject?.reportId || null,
          }
          addLog(`프로젝트 로드 성공: ${simData.project_id}`)

          const normalizedStatus = normalizeProjectStatus(projectData.value.status, {
            reportId: projectData.value.report_id || projectData.value.reportId || null,
          })
          if (
            projectData.value.report_id ||
            projectData.value.reportId ||
            normalizedStatus === PROJECT_STATUS.REPORT_COMPLETED ||
            normalizedStatus === PROJECT_STATUS.REPORT_GENERATING
          ) {
            addLog('이미 보고서가 생성된 프로젝트라 보고서 화면으로 이동합니다.')
            currentStatus.value = 'completed'
            const reportId = projectData.value.report_id || projectData.value.reportId
            if (reportId) {
              router.replace({ name: 'Report', params: { reportId } })
            } else {
              router.replace({ name: 'Process', params: { projectId: simData.project_id } })
            }
            return
          }

          // graph 데이터 가져오기
          if (projectData.value.graph_id) {
            await loadGraph(projectData.value.graph_id)
          }
        }
      }
    } else {
      addLog(`시뮬레이션 데이터 로드 실패: ${simRes.error || '알 수 없는 오류'}`)
    }
  } catch (err) {
    addLog(`로드 오류: ${err.message}`)
  }
}

const loadGraph = async (graphId) => {
  // 시뮬레이션 중일 때 자동 새로고침 시 전체화면 로딩을 표시하지 않아 깜빡임 방지
  // 수동 새로고침 또는 초기 로드 시 로딩 표시
  if (!isSimulating.value) {
    graphLoading.value = true
  }
  
  try {
    const res = await getGraphData(graphId)
    if (res.success) {
      graphData.value = res.data
      if (!isSimulating.value) {
        addLog('그래프 데이터 로드 성공')
      }
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

// --- Auto Refresh Logic ---
let graphRefreshTimer = null

const startGraphRefresh = () => {
  if (graphRefreshTimer) return
  addLog('그래프 실시간 새로고침 시작 (30초)')
  // 즉시 한 번 새로고침 후 30초마다 새로고침
  graphRefreshTimer = setInterval(refreshGraph, 30000)
}

const stopGraphRefresh = () => {
  if (graphRefreshTimer) {
    clearInterval(graphRefreshTimer)
    graphRefreshTimer = null
    addLog('그래프 실시간 새로고침 중지')
  }
}

watch(isSimulating, (newValue) => {
  if (newValue) {
    startGraphRefresh()
  } else {
    stopGraphRefresh()
  }
}, { immediate: true })

const onResize = () => { isDesktop.value = window.innerWidth >= 1024 }

onMounted(() => {
  window.addEventListener('resize', onResize)
  addLog('SimulationRunView 초기화')

  if (maxRounds.value) {
    addLog(`사용자 지정 시뮬레이션 라운드 수: ${maxRounds.value}`)
  }

  loadSimulationData()
})

onUnmounted(() => {
  window.removeEventListener('resize', onResize)
  stopGraphRefresh()
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

.status-indicator.processing .dot { background: #FF5722; animation: pulse 1s infinite; }
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

.panel-full,
.panel-graph,
.panel-workbench {
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

/* Desktop: side-by-side split */
@media (min-width: 1024px) {
  .bottom-nav {
    display: none;
  }

  .content-area {
    flex-direction: row;
  }

  .panel-graph {
    width: 50%;
    border-right: 1px solid var(--border-color, #EAEAEA);
    flex-shrink: 0;
  }

  .panel-workbench {
    width: 50%;
  }
}
</style>
