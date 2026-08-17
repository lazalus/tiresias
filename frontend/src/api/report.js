import service, { requestWithRetry } from './index'

/**
 * 보고서 생성 시작
 * @param {Object} data - { simulation_id, force_regenerate? }
 */
export const generateReport = (data) => {
  return requestWithRetry(() => service.post('/api/report/generate', data), 3, 1000)
}

/**
 * 보고서 생성 상태 조회
 * @param {Object} data - { task_id?, simulation_id? }
 */
export const getReportStatus = (data) => {
  return service.post('/api/report/generate/status', data)
}

/**
 * 에이전트 로그 조회 (증분)
 * @param {string} reportId
 * @param {number} fromLine - N번째 줄부터 조회
 */
export const getAgentLog = (reportId, fromLine = 0) => {
  return service.get(`/api/report/${reportId}/agent-log`, { params: { from_line: fromLine } })
}

/**
 * 콘솔 로그 조회 (증분)
 * @param {string} reportId
 * @param {number} fromLine - N번째 줄부터 조회
 */
export const getConsoleLog = (reportId, fromLine = 0) => {
  return service.get(`/api/report/${reportId}/console-log`, { params: { from_line: fromLine } })
}

/**
 * 보고서 상세 조회
 * @param {string} reportId
 */
export const getReport = (reportId) => {
  return service.get(`/api/report/${reportId}`)
}

/**
 * 보고서 생성 진행 상황 조회
 * @param {string} reportId
 */
export const getReportProgress = (reportId) => {
  return service.get(`/api/report/${reportId}/progress`)
}

/**
 * Worker 메타데이터 보고서 저장
 * @param {Object} data - { id?, project_id?, simulation_id?, title, summary, content, sections }
 */
export const saveReportRecord = (data) => {
  return service.post('/api/reports', data)
}

/**
 * Worker 정제본 저장
 * @param {string} reportId
 * @param {Object} data - { title, summary, sections, generated_at }
 */
export const saveRefinedReport = (reportId, data) => {
  return service.post(`/api/reports/${reportId}/refined`, data)
}

/**
 * Worker 정제본 조회
 * @param {string} reportId
 */
export const getRefinedReport = (reportId) => {
  return service.get(`/api/reports/${reportId}/refined`)
}

/**
 * Report Agent 대화
 * @param {Object} data - { simulation_id, message, chat_history? }
 */
export const chatWithReport = (data) => {
  return requestWithRetry(() => service.post('/api/report/chat', data), 3, 1000)
}
