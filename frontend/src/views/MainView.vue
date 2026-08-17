<template>
  <div class="main-view">
    <!-- Header -->
    <header class="app-header">
      <div class="header-left" @click="confirmGoHome" style="cursor:pointer;display:flex;align-items:center;">
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
      <!-- 전체 로딩 -->
      <div v-if="loading" class="panel-full" style="display:flex;align-items:center;justify-content:center;gap:10px;color:var(--text-secondary);font-size:0.85rem;">
        <span class="spinner"></span>
        <span>불러오는 중...</span>
      </div>
      <!-- Graph Panel (완료된 프로젝트에서는 숨김 - 보고서 완료 후 그래프 삭제됨) -->
      <div v-show="!loading && !isProjectCompleted && (viewMode === 'graph' || isDesktop)" class="panel-graph">
        <GraphPanel
          :graphData="graphData"
          :loading="graphLoading"
          :currentPhase="currentPhase"
          :status-message="graphPanelStatusMessage"
          @refresh="refreshGraph"
        />
      </div>

      <!-- Step Components -->
      <div v-show="!loading && (viewMode === 'workbench' || isDesktop)" class="panel-workbench">
        <!-- 완료된 프로젝트: 저장된 보고서 표시 -->
        <div v-if="isProjectCompleted" class="saved-report-view">
          <div v-if="savedReport" class="report-reader">
            <div class="report-reader-header">
              <span class="report-tag">영향 분석 보고서</span>
              <span class="report-date">{{ formatReportDate(savedReport.created_at) }}</span>
            </div>
            <h1 class="report-reader-title">{{ savedReport.title || '시뮬레이션 보고서' }}</h1>
            <p v-if="savedReport.summary" class="report-reader-summary">{{ savedReport.summary }}</p>
            <div class="report-reader-divider"></div>
            <div v-for="(section, idx) in savedReport.sections" :key="idx" class="report-reader-section">
              <h2 class="reader-section-num">{{ String(idx + 1).padStart(2, '0') }}</h2>
              <h3 class="reader-section-title">{{ section.title }}</h3>
              <div class="reader-section-content" v-html="renderMarkdown(section.content)"></div>
            </div>
          </div>
          <div v-else class="report-empty">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
            <p>저장된 보고서가 없습니다.</p>
            <p class="report-empty-sub">이 프로젝트는 보고서가 저장되기 전에 완료 처리되었습니다.</p>
          </div>
        </div>
        <!-- 진행중 프로젝트 -->
        <template v-else>
          <Step1GraphBuild
            v-if="currentStep === 1"
            :currentPhase="currentPhase"
            :projectData="projectData"
            :ontologyProgress="ontologyProgress"
            :buildProgress="buildProgress"
            :graphData="graphData"
            :graph-queue-state="graphQueueState"
            :graph-queue-message="graphQueueMessage"
            :graph-queue-countdown="graphRetryCountdown"
            :graph-build-retry-available="graphBuildRetryAvailable"
            :graph-build-retrying="retryingGraphBuild"
            :graph-build-error="graphBuildRetryErrorMessage"
            :systemLogs="systemLogs"
            @retry-graph-build="retryGraphBuild"
            @next-step="handleNextStep"
          />
          <Step2EnvSetup
            v-else-if="currentStep === 2"
            :simulationId="currentSimulationId"
            :projectData="projectData"
            :graphData="graphData"
            :systemLogs="systemLogs"
            @go-back="handleGoBack"
            @next-step="handleNextStep"
            @add-log="addLog"
          />
        </template>
      </div>
    </main>

    <!-- 하단 네비게이션 -->
    <nav class="bottom-nav">
      <button v-if="!isProjectCompleted" class="nav-item" :class="{ active: viewMode === 'graph' }" @click="viewMode = 'graph'">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="3"/><circle cx="5" cy="6" r="2"/><circle cx="19" cy="6" r="2"/><circle cx="5" cy="18" r="2"/><circle cx="19" cy="18" r="2"/>
          <line x1="7" y1="7" x2="10" y2="10"/><line x1="14" y1="10" x2="17" y2="7"/><line x1="7" y1="17" x2="10" y2="14"/><line x1="14" y1="14" x2="17" y2="17"/>
        </svg>
        <span>구조도</span>
      </button>
      <button class="nav-item" :class="{ active: viewMode === 'workbench' }" @click="viewMode = 'workbench'">
        <svg v-if="isProjectCompleted" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
        <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/>
        </svg>
        <span>{{ isProjectCompleted ? '보고서' : '분석' }}</span>
      </button>
      <button class="nav-item" @click="confirmGoHome">
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
import Step1GraphBuild from '../components/Step1GraphBuild.vue'
import Step2EnvSetup from '../components/Step2EnvSetup.vue'
import HeaderNav from '../components/HeaderNav.vue'
import { generateOntology, getProject, buildGraph, getTaskStatus, getGraphData } from '../api/graph'
import { listSimulations } from '../api/simulation'
import { isCapacityError, getCapacityState, formatCapacityMessage } from '../api/capacity.js'
import { formatQueueMessage, getQueuePollSeconds, getQueueStatus, isQueuedResponse } from '../api/queue.js'
import { getPendingUpload, clearPendingUpload } from '../store/pendingUpload.js'
import { buildAuthFetchOptions } from '../store/auth.js'
import { renderMarkdown } from '../utils/markdown.js'
import {
  PROJECT_STATUS,
  isReportCompletedProject,
  isSimulationRunningProject,
  isSimulationWorkspaceProject,
  normalizeProjectRecord,
} from '../utils/projectStatus.js'

const route = useRoute()
const router = useRouter()

// Layout State
const viewMode = ref('workbench') // graph | workbench
const isDesktop = ref(window.innerWidth >= 1024)

// Step State
const currentStep = ref(1) // 1: 그래프 구축, 2: 환경 설정, 3: 시뮬레이션 시작, 4: 보고서 생성, 5: 심층 상호작용
const stepNames = ['구조 분석', '실행 준비', '시나리오 실행', '영향 보고서', '심층 상호작용']

const isProjectCompleted = ref(false)
const savedReport = ref(null)
const savedReportLoading = ref(false)

// Data State
const currentProjectId = ref(route.params.projectId)
const currentSimulationId = ref(null)
const loading = ref(false)
const graphLoading = ref(false)
const error = ref('')
const projectData = ref(null)
const graphData = ref(null)
const currentPhase = ref(-1) // -1: Upload, 0: Ontology, 1: Build, 2: Complete
const ontologyProgress = ref(null)
const buildProgress = ref(null)
const systemLogs = ref([])
const retryingGraphBuild = ref(false)
const graphRetryCountdown = ref(0)
const graphQueueState = ref(null)

// Polling timers
let pollTimer = null
let graphPollTimer = null
let graphRetryTimer = null
let graphQueuePollTimer = null
let queuedGraphBuildPayload = null
let lastGraphQueueLogKey = ''

// --- Status Computed ---
const statusClass = computed(() => {
  if (loading.value || savedReportLoading.value) return 'processing'
  if (error.value || projectData.value?.status === 'failed') return 'error'
  if (isProjectCompleted.value) return 'completed'
  if (graphQueueState.value) return 'processing'
  if (projectData.value?.status === PROJECT_STATUS.GRAPH_COMPLETED || currentPhase.value >= 2) return 'completed'
  return 'processing'
})

const statusText = computed(() => {
  if (loading.value || savedReportLoading.value) return '불러오는 중'
  if (isProjectCompleted.value) return '보고서 완료'
  if (graphQueueState.value?.position) return `구조 분석 대기열 ${graphQueueState.value.position}번`
  if (graphBuildRetryAvailable.value) return '구조 분석 재시도 필요'
  if (error.value || projectData.value?.status === 'failed') return '오류 발생'

  if (projectData.value?.status === PROJECT_STATUS.GRAPH_BUILDING && buildProgress.value?.message) {
    return buildProgress.value.message
  }

  switch (projectData.value?.status) {
    case PROJECT_STATUS.CREATED:
      return '자료 업로드 완료'
    case PROJECT_STATUS.ONTOLOGY_GENERATED:
      return '자료 해석 완료'
    case PROJECT_STATUS.GRAPH_BUILDING:
      return '구조 분석 중'
    case PROJECT_STATUS.GRAPH_COMPLETED:
      return currentStep.value >= 2 ? '행위자 모델 준비 중' : '구조 분석 완료'
    default:
      break
  }

  if (currentStep.value >= 2 && currentSimulationId.value) return '실행 준비 중'
  if (currentPhase.value === 1 && buildProgress.value?.message) return buildProgress.value.message
  if (currentPhase.value === 1) return '구조 분석 중'
  if (currentPhase.value === 0) return '자료 해석 중'
  return '분석 환경 초기화 중'
})

const graphPanelStatusMessage = computed(() => {
  if (currentPhase.value === 1) {
    return buildProgress.value?.message || '이해관계 구조도를 분석하고 있습니다.'
  }
  return ''
})

const hasRecoverableGraphFailure = (project) => {
  return Boolean(
    project?.status === 'failed' &&
    project?.graph_id &&
    isRecoverableGraphRateLimitError(project?.error)
  )
}

const graphBuildRetryAvailable = computed(() => {
  return Boolean(
    currentProjectId.value &&
    currentProjectId.value !== 'new' &&
    projectData.value?.status === 'failed' &&
    projectData.value?.ontology &&
    !hasRecoverableGraphFailure(projectData.value)
  )
})

const graphBuildRetryErrorMessage = computed(() => {
  return projectData.value?.error || error.value || ''
})

const graphQueueMessage = computed(() => {
  if (!graphQueueState.value) return ''
  return formatQueueMessage(graphQueueState.value, '현재 구조 분석 대기열에 등록되었습니다.')
})

// --- Helpers ---
const addLog = (msg) => {
  const time = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }) + '.' + new Date().getMilliseconds().toString().padStart(3, '0')
  systemLogs.value.push({ time, msg })
  // Keep last 100 logs
  if (systemLogs.value.length > 100) {
    systemLogs.value.shift()
  }
}

const syncProjectStatus = async (status, extra = {}) => {
  if (!currentProjectId.value || currentProjectId.value === 'new') return

  try {
    const API_BASE = import.meta.env.VITE_API_BASE_URL || ''
    await fetch(`${API_BASE}/api/projects/${currentProjectId.value}`, buildAuthFetchOptions({
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        status,
        ...extra,
      }),
    }))
  } catch (syncError) {
    console.warn('프로젝트 상태 동기화 실패:', syncError)
  }
}

const handleNextStep = (params = {}) => {
  if (currentStep.value < 5) {
    currentStep.value++
    addLog(`Step ${currentStep.value} 진입: ${stepNames[currentStep.value - 1]}`)
    
    // Step 2에서 Step 3으로 진입 시, 시뮬레이션 라운드 수 설정 기록
    if (currentStep.value === 3 && params.maxRounds) {
      addLog(`사용자 지정 시뮬레이션 라운드 수: ${params.maxRounds} 라운드`)
    }
  }
}

const handleGoBack = () => {
  if (currentStep.value > 1) {
    currentStep.value--
    addLog(`Step ${currentStep.value}(으)로 돌아감: ${stepNames[currentStep.value - 1]}`)
  }
}

const isRecoverableGraphRateLimitError = (value) => {
  const text = String(value || '')
  return text.includes('Rate limit exceeded for FREE plan') || text.includes('status_code: 429')
}

// --- Data Logic ---

const initProject = async () => {
  addLog('Project view initialized.')
  if (currentProjectId.value === 'new') {
    await handleNewProject()
  } else {
    await loadProject()
  }
}

const handleNewProject = async () => {
  const pending = await getPendingUpload()
  if (!pending.isPending || pending.files.length === 0) {
    error.value = 'No pending files found.'
    addLog('Error: No pending files found for new project.')
    return
  }
  
  try {
    loading.value = true
    currentPhase.value = 0
    ontologyProgress.value = { message: 'Uploading and analyzing docs...' }
    addLog('Starting ontology generation: Uploading files...')
    
    const formData = new FormData()
    pending.files.forEach(f => formData.append('files', f))
    formData.append('simulation_requirement', pending.simulationRequirement)
    if (pending.pendingToken) {
      formData.append('pending_token', pending.pendingToken)
    }
    
    const res = await generateOntology(formData)
    if (res.success) {
      await clearPendingUpload()
      currentProjectId.value = res.data.project_id
      projectData.value = res.data

      // D1에 프로젝트 저장 (보고서 탭에 진행중으로 표시)
      try {
        const API_BASE = import.meta.env.VITE_API_BASE_URL || ''
        await fetch(`${API_BASE}/api/projects`, buildAuthFetchOptions({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            id: res.data.project_id,
            name: pending.simulationRequirement || '시뮬레이션',
            requirement: pending.simulationRequirement,
            status: PROJECT_STATUS.ONTOLOGY_GENERATED,
            simulation_id: res.data.simulation_id || ''
          })
        }))
      } catch(e) { console.error('D1 project save failed:', e) }

      router.replace({ name: 'Process', params: { projectId: res.data.project_id } })
      ontologyProgress.value = null
      addLog(`Ontology generated successfully for project ${res.data.project_id}`)
      await startBuildGraph()
    } else {
      error.value = res.error || 'Ontology generation failed'
      addLog(`Error generating ontology: ${error.value}`)
    }
  } catch (err) {
    error.value = err.message
    addLog(`Exception in handleNewProject: ${err.message}`)
  } finally {
    loading.value = false
  }
}

const loadProject = async () => {
  try {
    loading.value = true
    addLog(`Loading project ${currentProjectId.value}...`)

    // D1에서 프로젝트 상태 먼저 확인
    try {
      const API_BASE = import.meta.env.VITE_API_BASE_URL || ''
      const d1Res = await fetch(`${API_BASE}/api/projects/${currentProjectId.value}`, buildAuthFetchOptions())
      const d1Data = await d1Res.json()
      if (d1Data.project) {
        const d1Project = normalizeProjectRecord(d1Data.project)
        const d1SimId = d1Project.simulation_id
        currentSimulationId.value = d1SimId || null

        if (isReportCompletedProject(d1Project)) {
          isProjectCompleted.value = true
          viewMode.value = 'workbench'
          addLog('보고서 완료 프로젝트 - 보고서 뷰')

          // 그래프 로드
          const res = await getProject(currentProjectId.value)
          if (res.success) {
            projectData.value = res.data
            currentPhase.value = 2
            if (res.data.graph_id) await loadGraph(res.data.graph_id)
          }

          // 저장된 보고서 로드 (report_id 또는 전체 목록에서 찾기)
          await loadSavedReport(d1Project.report_id, d1SimId)
          loading.value = false
          return
        }

        if (d1SimId && isSimulationRunningProject(d1Project)) {
          router.replace({ name: 'SimulationRun', params: { simulationId: d1SimId } })
          return
        }

        if (d1SimId && isSimulationWorkspaceProject(d1Project)) {
          router.replace({ name: 'Simulation', params: { simulationId: d1SimId } })
          return
        }
      }
    } catch (e) { /* D1 조회 실패 시 외부 API로 fallback */ }

    const res = await getProject(currentProjectId.value)
    if (res.success) {
      projectData.value = res.data
      if (res.data.status === 'graph_building' || res.data.status === 'graph_completed') {
        clearQueuedGraphBuild()
      }
      const recoverableGraphFailure = hasRecoverableGraphFailure(res.data)
      if (recoverableGraphFailure) {
        currentPhase.value = 2
        error.value = ''
        addLog('그래프 생성은 완료됐지만 메타데이터 조회가 지연되어 복구 모드로 진입합니다')
      } else {
        updatePhaseByStatus(res.data.status)
      }
      addLog(`Project loaded. Status: ${res.data.status}`)

      let sim = null

      try {
        const simRes = await listSimulations(currentProjectId.value)
        sim = [...(simRes.data || [])]
          .sort((a, b) => (b.updated_at || b.created_at || '').localeCompare(a.updated_at || a.created_at || ''))[0] || null

        if (sim?.simulation_id) {
          currentSimulationId.value = sim.simulation_id
          addLog(`시뮬레이션 상태 복구: ${sim.simulation_id} (${sim.status})`)
        }
      } catch (simErr) {
        console.warn('Simulation lookup failed:', simErr)
      }

      // 시뮬레이션/보고서까지 완료된 경우 해당 Step으로 바로 이동
      if (sim?.status === 'running') {
        if (currentSimulationId.value) {
          router.replace({ name: 'SimulationRun', params: { simulationId: currentSimulationId.value } })
          return
        }
      } else if (sim?.status === 'completed' || sim?.status === 'stopped' || sim?.status === 'ready' || sim?.status === 'preparing' || sim?.config_generated) {
        if (currentSimulationId.value) {
          router.replace({ name: 'Simulation', params: { simulationId: currentSimulationId.value } })
          return
        }
        currentStep.value = 2
        currentPhase.value = 2
        if (res.data.graph_id) await loadGraph(res.data.graph_id)
        addLog(`시뮬레이션 상태 복구: ${sim.status || 'config_generated'} - Step 2로 이동`)
      } else if (res.data.status === 'ontology_generated' && !res.data.graph_id) {
        await startBuildGraph()
      } else if (res.data.status === 'graph_building' && res.data.graph_build_task_id) {
        currentPhase.value = 1
        startPollingTask(res.data.graph_build_task_id)
        startGraphPolling()
      } else if (res.data.status === 'graph_completed' && res.data.graph_id) {
        currentPhase.value = 2
        await loadGraph(res.data.graph_id)
      }
    } else {
      error.value = res.error
      addLog(`Error loading project: ${res.error}`)
    }
  } catch (err) {
    error.value = err.message
    addLog(`Exception in loadProject: ${err.message}`)
  } finally {
    loading.value = false
  }
}

const updatePhaseByStatus = (status) => {
  switch (status) {
    case 'created':
    case 'ontology_generated': currentPhase.value = 0; break;
    case 'graph_building': currentPhase.value = 1; break;
    case 'graph_completed': currentPhase.value = 2; break;
    case 'failed':
      currentPhase.value = projectData.value?.ontology ? 1 : 0
      error.value = projectData.value?.error || 'Project failed'
      break;
  }
}

const startBuildGraph = async () => {
  try {
    stopGraphQueue()
    error.value = ''
    currentPhase.value = 1
    buildProgress.value = { progress: 0, message: '구조 분석을 시작합니다...' }
    addLog('Initiating graph build...')

    await requestGraphBuild({ project_id: currentProjectId.value })
  } catch (err) {
    if (isCapacityError(err)) {
      scheduleGraphRetry(err)
      return
    }
    error.value = err.message
    addLog(`Exception in startBuildGraph: ${err.message}`)
  }
}

const retryGraphBuild = async () => {
  if (!graphBuildRetryAvailable.value || retryingGraphBuild.value) return

  try {
    retryingGraphBuild.value = true
    stopGraphQueue()
    error.value = ''
    currentPhase.value = 1
    buildProgress.value = { progress: 0, message: '구조 분석을 다시 시작합니다...' }
    stopPolling()
    stopGraphPolling()
    addLog('이전 실패 프로젝트에서 그래프 구축 재시도를 시작합니다')

    await requestGraphBuild({
      project_id: currentProjectId.value,
      force: true
    })
  } catch (err) {
    if (isCapacityError(err)) {
      scheduleGraphRetry(err, true)
      return
    }
    error.value = err.message || 'Graph build retry failed'
    addLog(`그래프 구축 재시도 예외: ${error.value}`)
  } finally {
    retryingGraphBuild.value = false
  }
}

const requestGraphBuild = async (payload) => {
  const response = await buildGraph(payload)

  if (isQueuedResponse(response)) {
    enterGraphQueue(response.queue, {
      project_id: currentProjectId.value,
      force: Boolean(payload.force)
    })
    return false
  }

  clearQueuedGraphBuild()

  if (response.success) {
    projectData.value = {
      ...projectData.value,
      status: PROJECT_STATUS.GRAPH_BUILDING,
      graph_build_task_id: response.data.task_id,
      error: null
    }
    await syncProjectStatus(PROJECT_STATUS.GRAPH_BUILDING)
    addLog(`Graph build task started. Task ID: ${response.data.task_id}`)
    startGraphPolling()
    startPollingTask(response.data.task_id)
    return true
  }

  error.value = response.error || 'Graph build retry failed'
  await syncProjectStatus(PROJECT_STATUS.FAILED)
  addLog(`그래프 구축 시작 실패: ${error.value}`)
  return false
}

const startGraphPolling = () => {
  addLog('Started polling for graph data...')
  fetchGraphData()
  graphPollTimer = setInterval(fetchGraphData, 10000)
}

const fetchGraphData = async () => {
  try {
    // Refresh project info to check for graph_id
    const projRes = await getProject(currentProjectId.value)
    if (projRes.success && projRes.data.graph_id) {
      const gRes = await getGraphData(projRes.data.graph_id)
      if (gRes.success) {
        graphData.value = gRes.data
        const nodeCount = gRes.data.node_count || gRes.data.nodes?.length || 0
        const edgeCount = gRes.data.edge_count || gRes.data.edges?.length || 0
        addLog(`Graph data refreshed. Nodes: ${nodeCount}, Edges: ${edgeCount}`)
      }
    }
  } catch (err) {
    if (isRecoverableGraphRateLimitError(err.message)) {
      addLog('그래프 데이터 반영이 잠시 지연되고 있습니다')
      return
    }
    console.warn('Graph fetch error:', err)
  }
}

const startPollingTask = (taskId) => {
  pollTaskStatus(taskId)
  pollTimer = setInterval(() => pollTaskStatus(taskId), 2000)
}

const pollTaskStatus = async (taskId) => {
  try {
    const res = await getTaskStatus(taskId)
    if (res.success) {
      const task = res.data
      
      // Log progress message if it changed
      if (task.message && task.message !== buildProgress.value?.message) {
        addLog(task.message)
      }
      
      buildProgress.value = { progress: task.progress || 0, message: task.message }
      
      if (task.status === 'completed') {
        addLog('Graph build task completed.')
        stopPolling()
        stopGraphPolling() // Stop polling, do final load
        error.value = ''
        currentPhase.value = 2
        await syncProjectStatus(PROJECT_STATUS.GRAPH_COMPLETED)
        
        // Final load
        const projRes = await getProject(currentProjectId.value)
        if (projRes.success && projRes.data.graph_id) {
            projectData.value = projRes.data
            await loadGraph(projRes.data.graph_id)
        }
      } else if (task.status === 'failed') {
        const projRes = await getProject(currentProjectId.value)
        const hasUsableGraph = projRes.success && Boolean(projRes.data?.graph_id)
        if (hasUsableGraph && isRecoverableGraphRateLimitError(task.error || task.message)) {
          stopPolling()
          currentPhase.value = 2
          error.value = ''
          projectData.value = {
            ...projRes.data,
            status: PROJECT_STATUS.GRAPH_COMPLETED
          }
          await syncProjectStatus(PROJECT_STATUS.GRAPH_COMPLETED)
          addLog('그래프는 생성됐지만 통계 수집이 지연되었습니다')
          addLog('기존 graph_id를 사용해 다음 단계로 진행합니다')
          return
        }

        stopPolling()
        stopGraphPolling()
        if (projRes.success) {
          projectData.value = projRes.data
          updatePhaseByStatus(projRes.data.status)
        }
        await syncProjectStatus(PROJECT_STATUS.FAILED)
        error.value = projRes.success ? (projRes.data?.error || task.message || task.error) : (task.message || task.error)
        addLog(`Graph build task failed: ${error.value}`)
        if (graphBuildRetryAvailable.value) {
          addLog('기존 프로젝트 데이터로 그래프 구축을 다시 시작할 수 있습니다')
        }
      }
    }
  } catch (e) {
    if (e?.response?.status === 404) {
      stopPolling()
      stopGraphPolling()
      const projRes = await getProject(currentProjectId.value)
      if (projRes.success) {
        projectData.value = projRes.data
        updatePhaseByStatus(projRes.data.status)
        if (projRes.data.status === PROJECT_STATUS.FAILED) {
          error.value = projRes.data.error || '구조 분석 작업이 중단되었습니다. 다시 시도해주세요.'
          addLog(`Graph build task interrupted: ${error.value}`)
        }
      }
      return
    }
    console.error(e)
  }
}

const loadGraph = async (graphId) => {
  graphLoading.value = true
  addLog(`Loading full graph data: ${graphId}`)
  try {
    const res = await getGraphData(graphId)
    if (res.success) {
      graphData.value = res.data
      addLog('Graph data loaded successfully.')
    } else {
      addLog(`Failed to load graph data: ${res.error}`)
    }
  } catch (e) {
    if (isRecoverableGraphRateLimitError(e.message)) {
      addLog('그래프 상세 데이터 로딩이 잠시 지연되고 있습니다')
      return
    }
    addLog(`Exception loading graph: ${e.message}`)
  } finally {
    graphLoading.value = false
  }
}

const refreshGraph = () => {
  if (projectData.value?.graph_id) {
    addLog('Manual graph refresh triggered.')
    loadGraph(projectData.value.graph_id)
  }
}

const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

const stopGraphPolling = () => {
  if (graphPollTimer) {
    clearInterval(graphPollTimer)
    graphPollTimer = null
    addLog('Graph polling stopped.')
  }
}

const clearQueuedGraphBuild = () => {
  if (graphQueuePollTimer) {
    clearTimeout(graphQueuePollTimer)
    graphQueuePollTimer = null
  }
  queuedGraphBuildPayload = null
  graphQueueState.value = null
  lastGraphQueueLogKey = ''
  stopGraphRetry()
}

const stopGraphRetry = () => {
  if (graphRetryTimer) {
    clearInterval(graphRetryTimer)
    graphRetryTimer = null
  }
  graphRetryCountdown.value = 0
}

const stopGraphQueue = () => {
  clearQueuedGraphBuild()
}

const enterGraphQueue = (queue, payload) => {
  queuedGraphBuildPayload = payload
  graphQueueState.value = queue
  error.value = ''
  currentPhase.value = 1

  const message = formatQueueMessage(queue, '현재 구조 분석 대기열에 등록되었습니다.')
  buildProgress.value = { progress: 0, message }
  logGraphQueueState(queue)
  scheduleGraphQueuePoll(getQueuePollSeconds(queue))
}

const logGraphQueueState = (queue) => {
  if (!queue) return
  const logKey = `${queue.status}:${queue.position}:${queue.totalWaiting}:${queue.lastError || ''}`
  if (logKey === lastGraphQueueLogKey) {
    return
  }
  lastGraphQueueLogKey = logKey
  addLog(formatQueueMessage(queue, '현재 구조 분석 대기열에 등록되었습니다.'))
}

const scheduleGraphQueuePoll = (seconds) => {
  if (graphQueuePollTimer) {
    clearTimeout(graphQueuePollTimer)
    graphQueuePollTimer = null
  }

  stopGraphRetry()
  graphRetryCountdown.value = seconds
  graphRetryTimer = setInterval(() => {
    graphRetryCountdown.value -= 1
    if (graphRetryCountdown.value <= 0) {
      stopGraphRetry()
    }
  }, 1000)

  graphQueuePollTimer = setTimeout(async () => {
    graphQueuePollTimer = null
    await pollGraphQueueStatus()
  }, seconds * 1000)
}

const pollGraphQueueStatus = async () => {
  const queueId = graphQueueState.value?.id
  if (!queueId) {
    return
  }

  try {
    const response = await getQueueStatus(queueId)
    const queue = response.queue
    if (!queue) {
      clearQueuedGraphBuild()
      return
    }

    if (queue.status === 'completed') {
      clearQueuedGraphBuild()
      await loadProject()
      return
    }

    if (queue.status === 'failed') {
      clearQueuedGraphBuild()
      error.value = queue.lastError || '구조 분석 대기열 처리에 실패했습니다.'
      buildProgress.value = null
      addLog(error.value)
      return
    }

    graphQueueState.value = queue
    buildProgress.value = {
      progress: 0,
      message: formatQueueMessage(queue, '현재 구조 분석 대기열에 등록되었습니다.')
    }
    logGraphQueueState(queue)

    if (queue.ready) {
      const payload = queuedGraphBuildPayload || { project_id: currentProjectId.value }
      clearQueuedGraphBuild()
      await requestGraphBuild({ ...payload, queue_id: queue.id })
      return
    }

    scheduleGraphQueuePoll(getQueuePollSeconds(queue))
  } catch (queueError) {
    buildProgress.value = {
      progress: 0,
      message: '대기열 상태를 다시 확인하는 중입니다...'
    }
    scheduleGraphQueuePoll(3)
  }
}

const scheduleGraphRetry = (err, force = false) => {
  const capacity = getCapacityState(err)
  const retryAfter = capacity?.retryAfter || 60
  const baseMessage = formatCapacityMessage(err, '현재 다른 구조 분석 작업이 진행 중입니다.')

  graphQueueState.value = null
  queuedGraphBuildPayload = null
  error.value = ''
  currentPhase.value = 1
  stopGraphRetry()
  graphRetryCountdown.value = retryAfter
  addLog(baseMessage)
  buildProgress.value = { progress: 0, message: `${baseMessage} 남은 대기 ${graphRetryCountdown.value}초` }

  graphRetryTimer = setInterval(async () => {
    graphRetryCountdown.value -= 1

    if (graphRetryCountdown.value > 0) {
      buildProgress.value = { progress: 0, message: `${baseMessage} 남은 대기 ${graphRetryCountdown.value}초` }
      return
    }

    stopGraphRetry()
    buildProgress.value = { progress: 0, message: '다시 시도 중...' }
    if (force) {
      await retryGraphBuild()
    } else {
      await startBuildGraph()
    }
  }, 1000)
}

const handleResize = () => {
  isDesktop.value = window.innerWidth >= 1024
}

// --- 저장된 보고서 로드 ---
const loadSavedReport = async (reportId, simulationId) => {
  savedReportLoading.value = true
  try {
    const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

    if (reportId) {
      // report_id가 있으면 직접 조회
      const res = await fetch(`${API_BASE}/api/reports/${reportId}`, buildAuthFetchOptions())
      const data = await res.json()
      if (data.report) {
        savedReport.value = data.report
        return
      }
    }

    const query = simulationId ? `?simulation_id=${encodeURIComponent(simulationId)}` : ''
    const res = await fetch(`${API_BASE}/api/reports${query}`, buildAuthFetchOptions())
    const data = await res.json()
    if (data.reports && data.reports.length > 0) {
      // 가장 최근 보고서 사용
      const latestId = data.reports[0].id
      const detailRes = await fetch(`${API_BASE}/api/reports/${latestId}`, buildAuthFetchOptions())
      const detailData = await detailRes.json()
      if (detailData.report) {
        savedReport.value = detailData.report
      }
    }
  } catch (e) {
    addLog(`보고서 로드 실패: ${e.message}`)
  } finally {
    savedReportLoading.value = false
  }
}

const formatReportDate = (d) => {
  if (!d) return ''
  return new Date(d).toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric' })
}

const confirmGoHome = () => {
  if (isProjectCompleted.value) {
    router.push('/dashboard')
    return
  }

  if (confirm('시뮬레이션을 종료하고 홈으로 돌아가시겠습니까?\n진행 중인 작업은 저장됩니다.')) {
    router.push('/dashboard')
  }
}

// 화면 복귀 시 폴링 재시작 (모바일 화면 꺼짐 대응)
const handleVisibilityChange = () => {
  if (document.visibilityState === 'visible') {
    // 화면 복귀: 진행 중이면 폴링 재시작
    if (currentPhase.value === 1 && currentProjectId.value && currentProjectId.value !== 'new') {
      addLog('화면 복귀 - 상태 재확인 중...')
      loadProject()
    }
  }
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
  document.addEventListener('visibilitychange', handleVisibilityChange)
  initProject()
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  document.removeEventListener('visibilitychange', handleVisibilityChange)
  stopPolling()
  stopGraphPolling()
  stopGraphQueue()
})
</script>

<style scoped>
.main-view {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background:
    radial-gradient(circle at top right, rgba(15, 95, 219, 0.05), transparent 24%),
    linear-gradient(180deg, #f4f7fb 0%, #eef3f9 100%);
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
  font-size: 0.76rem;
  color: #475569;
  font-weight: 600;
  padding: 7px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(148, 163, 184, 0.16);
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--text-muted);
}

.status-indicator.processing .dot { background: #0F5FDB; animation: pulse 1s infinite; }
.status-indicator.completed .dot { background: #4CAF50; }
.status-indicator.error .dot { background: #F44336; }

@keyframes pulse { 50% { opacity: 0.5; } }

/* Content */
.content-area {
  flex: 1;
  overflow: hidden;
  position: relative;
}

.panel-full,
.panel-graph,
.panel-workbench {
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
  color: #0f5fdb;
}

.nav-item svg {
  width: 20px;
  height: 20px;
}

/* Saved Report Viewer */
.saved-report-view {
  height: 100%;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}

.report-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 80px 0;
  color: var(--text-secondary);
  font-size: 0.85rem;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid var(--border-color);
  border-top-color: #6366f1;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

.report-reader {
  max-width: 680px;
  margin: 0 auto;
  padding: 32px 24px 80px;
}

.report-reader-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.report-tag {
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #0f5fdb;
  background: rgba(15, 95, 219, 0.1);
  padding: 3px 10px;
  border-radius: 4px;
}

.report-date {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.report-reader-title {
  font-size: 1.4rem;
  font-weight: 700;
  line-height: 1.3;
  margin: 0 0 10px;
  color: var(--text-primary);
}

.report-reader-summary {
  font-size: 0.9rem;
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 0 0 20px;
}

.report-reader-divider {
  height: 1px;
  background: var(--border-color);
  margin-bottom: 28px;
}

.report-reader-section {
  margin-bottom: 32px;
}

.reader-section-num {
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--text-muted);
  letter-spacing: 0.04em;
  margin: 0 0 4px;
}

.reader-section-title {
  font-size: 1.05rem;
  font-weight: 600;
  margin: 0 0 12px;
  color: var(--text-primary);
}

.reader-section-content {
  font-size: 0.88rem;
  line-height: 1.8;
  color: var(--text-secondary);
  overflow-wrap: break-word;
}

.reader-section-content :deep(.md-p) { margin-bottom: 0.8em; }
.reader-section-content :deep(strong) { color: var(--text-primary); font-weight: 600; }
.reader-section-content :deep(.md-ul),
.reader-section-content :deep(.md-ol) { padding-left: 20px; margin-bottom: 0.8em; }
.reader-section-content :deep(.md-li),
.reader-section-content :deep(.md-oli) { margin-bottom: 4px; }
.reader-section-content :deep(.md-h2),
.reader-section-content :deep(.md-h3),
.reader-section-content :deep(.md-h4) { color: var(--text-primary); margin: 16px 0 8px; font-weight: 600; }
.reader-section-content :deep(.md-quote) { border-left: 3px solid var(--accent-color, #6366f1); padding: 12px 16px; margin: 16px 0; background: var(--bg-surface, rgba(0,0,0,0.02)); border-radius: 0 8px 8px 0; color: var(--text-secondary); font-style: italic; line-height: 1.7; }
.reader-section-content :deep(.code-block) { background: var(--bg-secondary); padding: 12px; border-radius: 8px; overflow-x: auto; border: 1px solid var(--border-color); margin: 1em 0; }
.reader-section-content :deep(.inline-code) { padding: 0.16rem 0.42rem; background: rgba(15, 23, 42, 0.06); border-radius: 6px; font-family: 'JetBrains Mono', monospace; font-size: 0.92em; }
.reader-section-content :deep(.md-table) { width: 100%; border-collapse: collapse; margin: 1rem 0 1.25rem; border: 1px solid var(--border-color); border-radius: 10px; overflow: hidden; background: var(--bg-primary); }
.reader-section-content :deep(.md-th),
.reader-section-content :deep(.md-td) { padding: 12px 14px; border-bottom: 1px solid var(--border-color); text-align: left; vertical-align: top; }
.reader-section-content :deep(.md-th) { font-weight: 700; color: var(--text-primary); background: rgba(15, 23, 42, 0.04); }
.reader-section-content :deep(.md-table tr:last-child .md-td) { border-bottom: 0; }

/* Report Empty */
.report-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 60px 24px;
  text-align: center;
  color: var(--text-muted);
  gap: 8px;
}

.report-empty p { font-size: 0.85rem; margin: 0; }
.report-empty-sub { font-size: 0.8rem !important; }

@media (max-width: 640px) {
  .report-reader { padding: 24px 16px 80px; }
  .report-reader-title { font-size: 1.2rem; }
}

/* Desktop: side-by-side split layout */
@media (min-width: 1024px) {
  .app-header {
    height: 60px;
    padding: 0 32px;
  }

  .app-name {
    font-size: 0.9rem;
  }

  .bottom-nav {
    display: none;
  }

  .content-area {
    display: flex;
    flex-direction: row;
  }

  .panel-graph {
    width: 50%;
    height: 100%;
    overflow-y: auto;
    border-right: 1px solid var(--border-color);
    flex-shrink: 0;
  }

  .panel-workbench {
    width: 50%;
    height: 100%;
    overflow-y: auto;
  }

  .report-reader {
    max-width: 760px;
    margin: 0 auto;
    padding: 48px 40px 60px;
  }

  .panel-workbench {
    width: 100%;
  }
}
</style>
