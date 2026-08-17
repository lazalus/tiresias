export const PROJECT_STATUS = Object.freeze({
  CREATED: 'created',
  ONTOLOGY_GENERATED: 'ontology_generated',
  GRAPH_BUILDING: 'graph_building',
  GRAPH_COMPLETED: 'graph_completed',
  SIMULATION_PREPARING: 'simulation_preparing',
  SIMULATION_READY: 'simulation_ready',
  SIMULATION_RUNNING: 'simulation_running',
  SIMULATION_COMPLETED: 'simulation_completed',
  REPORT_GENERATING: 'report_generating',
  REPORT_COMPLETED: 'report_completed',
  FAILED: 'failed',
  SIMULATION_STOPPED: 'simulation_stopped',
})

const LEGACY_STATUS_MAP = Object.freeze({
  pending: PROJECT_STATUS.CREATED,
  in_progress: PROJECT_STATUS.ONTOLOGY_GENERATED,
  preparing: PROJECT_STATUS.SIMULATION_PREPARING,
  ready: PROJECT_STATUS.SIMULATION_READY,
  running: PROJECT_STATUS.SIMULATION_RUNNING,
  completed: PROJECT_STATUS.SIMULATION_COMPLETED,
  stopped: PROJECT_STATUS.SIMULATION_STOPPED,
})

export function normalizeProjectStatus(status, { reportId = null } = {}) {
  const raw = String(status || '').trim()
  let normalized = LEGACY_STATUS_MAP[raw] || raw || PROJECT_STATUS.CREATED

  if (normalized === PROJECT_STATUS.SIMULATION_COMPLETED && reportId) {
    normalized = PROJECT_STATUS.REPORT_COMPLETED
  }

  return normalized
}

export function normalizeProjectRecord(project) {
  if (!project) return project
  return {
    ...project,
    status: normalizeProjectStatus(project.status, {
      reportId: project.report_id || project.reportId || null,
    }),
  }
}

export function isReportCompletedProject(project) {
  return normalizeProjectStatus(project?.status, {
    reportId: project?.report_id || project?.reportId || null,
  }) === PROJECT_STATUS.REPORT_COMPLETED
}

export function isSimulationRunningProject(project) {
  return normalizeProjectStatus(project?.status, {
    reportId: project?.report_id || project?.reportId || null,
  }) === PROJECT_STATUS.SIMULATION_RUNNING
}

export function isSimulationWorkspaceProject(project) {
  const status = normalizeProjectStatus(project?.status, {
    reportId: project?.report_id || project?.reportId || null,
  })

  return new Set([
    PROJECT_STATUS.SIMULATION_PREPARING,
    PROJECT_STATUS.SIMULATION_READY,
    PROJECT_STATUS.SIMULATION_COMPLETED,
    PROJECT_STATUS.SIMULATION_STOPPED,
    PROJECT_STATUS.REPORT_GENERATING,
  ]).has(status)
}

export function getProjectStatusLabel(status, { reportId = null } = {}) {
  const normalized = normalizeProjectStatus(status, { reportId })
  const labels = {
    [PROJECT_STATUS.CREATED]: '생성됨',
    [PROJECT_STATUS.ONTOLOGY_GENERATED]: '온톨로지 완료',
    [PROJECT_STATUS.GRAPH_BUILDING]: '그래프 구축 중',
    [PROJECT_STATUS.GRAPH_COMPLETED]: '그래프 준비 완료',
    [PROJECT_STATUS.SIMULATION_PREPARING]: '시뮬레이션 준비 중',
    [PROJECT_STATUS.SIMULATION_READY]: '시뮬레이션 준비 완료',
    [PROJECT_STATUS.SIMULATION_RUNNING]: '시뮬레이션 진행 중',
    [PROJECT_STATUS.SIMULATION_COMPLETED]: '시뮬레이션 완료',
    [PROJECT_STATUS.REPORT_GENERATING]: '보고서 생성 중',
    [PROJECT_STATUS.REPORT_COMPLETED]: '보고서 완료',
    [PROJECT_STATUS.FAILED]: '오류',
    [PROJECT_STATUS.SIMULATION_STOPPED]: '중단됨',
  }
  return labels[normalized] || normalized || '-'
}

export function getProjectStatusClass(status, { reportId = null } = {}) {
  const normalized = normalizeProjectStatus(status, { reportId })

  if ([PROJECT_STATUS.REPORT_COMPLETED, PROJECT_STATUS.SIMULATION_COMPLETED].includes(normalized)) {
    return 'status--done'
  }

  if (normalized === PROJECT_STATUS.FAILED || normalized === PROJECT_STATUS.SIMULATION_STOPPED) {
    return 'status--fail'
  }

  if ([
    PROJECT_STATUS.ONTOLOGY_GENERATED,
    PROJECT_STATUS.GRAPH_BUILDING,
    PROJECT_STATUS.GRAPH_COMPLETED,
    PROJECT_STATUS.SIMULATION_PREPARING,
    PROJECT_STATUS.SIMULATION_READY,
    PROJECT_STATUS.SIMULATION_RUNNING,
    PROJECT_STATUS.REPORT_GENERATING,
  ].includes(normalized)) {
    return 'status--running'
  }

  return ''
}

export function getProjectFilterGroup(status, { reportId = null } = {}) {
  const normalized = normalizeProjectStatus(status, { reportId })

  if (normalized === PROJECT_STATUS.FAILED || normalized === PROJECT_STATUS.SIMULATION_STOPPED) {
    return 'failed'
  }

  if ([PROJECT_STATUS.REPORT_COMPLETED, PROJECT_STATUS.SIMULATION_COMPLETED].includes(normalized)) {
    return 'completed'
  }

  return 'running'
}
