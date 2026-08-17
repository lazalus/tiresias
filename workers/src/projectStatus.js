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
