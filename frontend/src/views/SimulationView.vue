<template>
  <div class="main-view">
    <!-- Header -->
    <header class="app-header">
      <div class="header-left" @click="router.push('/dashboard')" style="cursor:pointer;display:flex;align-items:center;">
        <span class="app-name">TIRESIAS VIEW</span>
      </div>
      <div class="header-right">
        <span class="status-indicator" :class="statusClass">
          <span class="dot"></span>
          {{ statusText }}
        </span>
      </div>
    </header>

    <!-- Main Content Area -->
    <main class="content-area">
      <!-- Graph Panel (그래프 탭 선택 시) -->
      <div v-show="viewMode === 'graph'" class="panel-full">
        <GraphPanel
          :graphData="graphData"
          :loading="graphLoading"
          :currentPhase="2"
          :isVisible="viewMode === 'graph'"
          @refresh="refreshGraph"
        />
      </div>

      <!-- Step2 환경 설정 (워크벤치 탭 선택 시) -->
      <div v-show="viewMode === 'workbench'" class="panel-full">
        <Step2EnvSetup
          :simulationId="currentSimulationId"
          :projectData="projectData"
          :graphData="graphData"
          :systemLogs="systemLogs"
          :autoStartEnabled="prepareAutoStartEnabled"
          @go-back="handleGoBack"
          @next-step="handleNextStep"
          @add-log="addLog"
          @update-status="updateStatus"
        />
      </div>
    </main>

    <!-- 하단 네비게이션 -->
    <nav class="bottom-nav">
      <button class="nav-item" :class="{ active: viewMode === 'graph' }" @click="viewMode = 'graph'">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="3"/><circle cx="5" cy="6" r="2"/><circle cx="19" cy="6" r="2"/><circle cx="5" cy="18" r="2"/><circle cx="19" cy="18" r="2"/>
          <line x1="7" y1="7" x2="10" y2="10"/><line x1="14" y1="10" x2="17" y2="7"/><line x1="7" y1="17" x2="10" y2="14"/><line x1="14" y1="14" x2="17" y2="17"/>
        </svg>
        <span>그래프</span>
      </button>
      <button class="nav-item" :class="{ active: viewMode === 'workbench' }" @click="viewMode = 'workbench'">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/>
        </svg>
        <span>워크벤치</span>
      </button>
      <button class="nav-item" @click="router.push('/dashboard')">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>
        </svg>
        <span>홈</span>
      </button>
    </nav>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import GraphPanel from '../components/GraphPanel.vue'
import Step2EnvSetup from '../components/Step2EnvSetup.vue'
import { getProject, getGraphData } from '../api/graph'
import { getUserProject } from '../api/projects'
import { getSimulation, stopSimulation, getEnvStatus, closeSimulationEnv } from '../api/simulation'
import { PROJECT_STATUS, normalizeProjectStatus } from '../utils/projectStatus.js'

const route = useRoute()
const router = useRouter()

// Props
const props = defineProps({
  simulationId: String
})

// Layout State
const viewMode = ref('workbench')

// Data State
const currentSimulationId = ref(route.params.simulationId)
const projectData = ref(null)
const graphData = ref(null)
const graphLoading = ref(false)
const systemLogs = ref([])
const currentStatus = ref('processing') // processing | completed | error
const prepareAutoStartEnabled = ref(false)
const shouldStopRunningOnEntry = computed(() => route.query.stopRunning === '1')

// --- Status Computed ---
const statusClass = computed(() => {
  return currentStatus.value
})

const statusText = computed(() => {
  if (currentStatus.value === 'error') return 'Error'
  if (currentStatus.value === 'completed') return 'Ready'
  return 'Preparing'
})

// --- Helpers ---
const addLog = (msg) => {
  const time = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }) + '.' + new Date().getMilliseconds().toString().padStart(3, '0')
  systemLogs.value.push({ time, msg })
  if (systemLogs.value.length > 100) {
    systemLogs.value.shift()
  }
}

const updateStatus = (status) => {
  currentStatus.value = status
}

const handleGoBack = () => {
  // process 페이지로 돌아감
  if (projectData.value?.project_id) {
    router.push({ name: 'Process', params: { projectId: projectData.value.project_id } })
  } else {
    router.push('/dashboard')
  }
}

const handleNextStep = (params = {}) => {
  addLog('Step 3 진입: 시뮬레이션 시작')

  // 시뮬레이션 라운드 수 설정 기록
  if (params.maxRounds) {
    addLog(`사용자 지정 시뮬레이션 라운드 수: ${params.maxRounds} 라운드`)
  } else {
    addLog('자동 설정된 시뮬레이션 라운드 수 사용')
  }

  // 라우트 파라미터 구성
  const routeParams = {
    name: 'SimulationRun',
    params: { simulationId: currentSimulationId.value }
  }
  
  // 사용자 지정 라운드 수가 있으면 query 파라미터로 전달
  if (params.maxRounds) {
    routeParams.query = { maxRounds: params.maxRounds }
  }
  
  // Step 3 페이지로 이동
  router.push(routeParams)
}

// --- Data Logic ---

/**
 * 실행 중인 시뮬레이션 확인 및 종료
 * 사용자가 Step 3에서 Step 2로 돌아올 때, 시뮬레이션 종료를 기본으로 처리
 */
const checkAndStopRunningSimulation = async () => {
  if (!currentSimulationId.value) return
  
  try {
    // 시뮬레이션 환경이 활성 상태인지 확인
    const envStatusRes = await getEnvStatus({ simulation_id: currentSimulationId.value })
    
    if (envStatusRes.success && envStatusRes.data?.env_alive) {
      addLog('시뮬레이션 환경 실행 중 감지, 종료 중...')
      
      // 시뮬레이션 환경 정상 종료 시도
      try {
        const closeRes = await closeSimulationEnv({ 
          simulation_id: currentSimulationId.value,
          timeout: 10  // 10초 타임아웃
        })
        
        if (closeRes.success) {
          addLog('시뮬레이션 환경 종료 완료')
        } else {
          addLog(`시뮬레이션 환경 종료 실패: ${closeRes.error || '알 수 없는 오류'}`)
          // 정상 종료 실패 시, 강제 중지 시도
          await forceStopSimulation()
        }
      } catch (closeErr) {
        addLog(`시뮬레이션 환경 종료 오류: ${closeErr.message}`)
        // 정상 종료 오류 시, 강제 중지 시도
        await forceStopSimulation()
      }
    } else {
      // 환경이 실행 중이 아니지만 프로세스가 남아있을 수 있으므로 시뮬레이션 상태 확인
      const simRes = await getSimulation(currentSimulationId.value)
      if (simRes.success && simRes.data?.status === 'running') {
        addLog('시뮬레이션 실행 중 상태 감지, 중지 중...')
        await forceStopSimulation()
      }
    }
  } catch (err) {
    // 환경 상태 확인 실패는 후속 흐름에 영향 없음
    console.warn('시뮬레이션 상태 확인 실패:', err)
  }
}

/**
 * 시뮬레이션 강제 중지
 */
const forceStopSimulation = async () => {
  try {
    const stopRes = await stopSimulation({ simulation_id: currentSimulationId.value })
    if (stopRes.success) {
      addLog('시뮬레이션 강제 중지 완료')
    } else {
      addLog(`시뮬레이션 강제 중지 실패: ${stopRes.error || '알 수 없는 오류'}`)
    }
  } catch (err) {
    addLog(`시뮬레이션 강제 중지 오류: ${err.message}`)
  }
}

const shouldRedirectToReport = (project) => {
  if (!project) return false

  const normalizedStatus = normalizeProjectStatus(project.status, {
    reportId: project.report_id || project.reportId || null,
  })

  return Boolean(
    project.report_id ||
    project.reportId ||
    normalizedStatus === PROJECT_STATUS.REPORT_COMPLETED ||
    normalizedStatus === PROJECT_STATUS.REPORT_GENERATING
  )
}

const loadSimulationData = async () => {
  try {
    addLog(`시뮬레이션 데이터 로드: ${currentSimulationId.value}`)

    // simulation 정보 가져오기
    const simRes = await getSimulation(currentSimulationId.value)
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
            simulation_id: userProject?.simulation_id || graphProject?.simulation_id || currentSimulationId.value,
            report_id: userProject?.report_id || userProject?.reportId || graphProject?.report_id || graphProject?.reportId || null,
          }
          addLog(`프로젝트 로드 성공: ${simData.project_id}`)

          if (shouldRedirectToReport(projectData.value)) {
            const reportId = projectData.value.report_id || projectData.value.reportId
            addLog('이미 보고서가 생성된 프로젝트라 보고서 화면으로 이동합니다.')
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

      prepareAutoStartEnabled.value = !shouldRedirectToReport(projectData.value)
    } else {
      addLog(`시뮬레이션 데이터 로드 실패: ${simRes.error || '알 수 없는 오류'}`)
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

onMounted(async () => {
  addLog('SimulationView 초기화')

  // 시뮬레이션 데이터 로드
  await loadSimulationData()

  if (shouldRedirectToReport(projectData.value)) {
    return
  }

  // 명시적으로 stopRunning=1 로 돌아온 경우에만 실행 중인 시뮬레이션을 정리한다.
  // 단순 재진입/새로고침으로는 실행 중 작업을 끊지 않는다.
  if (shouldStopRunningOnEntry.value) {
    await checkAndStopRunningSimulation()
    router.replace({
      name: 'Simulation',
      params: { simulationId: currentSimulationId.value },
    })
  }
})
</script>

<style scoped>
.main-view {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
  overflow: hidden;
  font-family: 'Inter', 'Noto Sans KR', system-ui, -apple-system, sans-serif;
  -webkit-font-smoothing: antialiased;
}

/* Header */
.app-header {
  position: sticky;
  top: 0;
  z-index: 100;
  height: 52px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  background: var(--header-bg);
  backdrop-filter: saturate(180%) blur(20px);
  -webkit-backdrop-filter: saturate(180%) blur(20px);
  flex-shrink: 0;
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
  gap: 6px;
  font-size: 0.75rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--text-muted);
}

.status-indicator.processing .dot { background: #FF5722; animation: pulse 1s infinite; }
.status-indicator.completed .dot { background: #4CAF50; }
.status-indicator.error .dot { background: #F44336; }

@keyframes pulse { 50% { opacity: 0.5; } }

/* Content */
.content-area {
  flex: 1;
  overflow: hidden;
  position: relative;
  min-height: 0;
}

.panel-full {
  width: 100%;
  height: 100%;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}

/* Bottom Nav */
.bottom-nav {
  display: flex;
  align-items: center;
  justify-content: space-around;
  height: 56px;
  background: var(--bg-secondary);
  border-top: 1px solid var(--border-color);
  flex-shrink: 0;
  z-index: 200;
  padding-bottom: env(safe-area-inset-bottom, 0);
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  border: none;
  background: none;
  padding: 6px 16px;
  font-size: 0.65rem;
  font-weight: 500;
  color: var(--text-muted);
  cursor: pointer;
  transition: color 0.2s;
  font-family: inherit;
}

.nav-item.active {
  color: var(--accent-color, #6366f1);
}

.nav-item svg {
  width: 20px;
  height: 20px;
}
</style>
