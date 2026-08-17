export function isCapacityError(error) {
  return error?.isCapacityError === true || error?.response?.status === 429
}

export function getCapacityState(error) {
  if (!error) return null

  const responseData = error.response?.data || {}
  const capacity = error.capacity || responseData.capacity || null
  const retryAfterRaw = error.retryAfter ?? error.response?.headers?.['retry-after']
  const retryAfter = Number.parseInt(retryAfterRaw, 10)

  return {
    isCapacityError: isCapacityError(error),
    message: error.message || responseData.error || '현재 서버가 바쁩니다. 잠시 후 다시 시도해주세요.',
    capacity,
    retryAfter: Number.isFinite(retryAfter) && retryAfter > 0 ? retryAfter : 60
  }
}

function formatLimitLine(label, current, limit) {
  if (typeof current !== 'number' || typeof limit !== 'number') return null
  return `${label} ${current}/${limit}`
}

export function formatCapacityDetails(capacity) {
  if (!capacity?.limits) return ''

  const lines = [
    formatLimitLine('준비', capacity.preparing, capacity.limits.max_concurrent_prepares),
    formatLimitLine('그래프 구축', capacity.graph_building, capacity.limits.max_concurrent_graph_builds),
    formatLimitLine('보고서', capacity.report_generating, capacity.limits.max_concurrent_reports),
    formatLimitLine('실행 중 시뮬레이션', capacity.running_simulations, capacity.limits.max_concurrent_running_simulations),
    formatLimitLine('활성 환경', capacity.alive_simulation_envs, capacity.limits.max_concurrent_simulation_envs)
  ].filter(Boolean)

  return lines.length ? `현재 점유: ${lines.join(' / ')}` : ''
}

export function formatCapacityMessage(error, fallback = '현재 서버가 바쁩니다. 잠시 후 다시 시도해주세요.') {
  const state = getCapacityState(error)
  if (!state) return fallback

  const parts = [state.message || fallback]
  const detail = formatCapacityDetails(state.capacity)

  if (detail) {
    parts.push(detail)
  }

  if (state.retryAfter) {
    parts.push(`약 ${state.retryAfter}초 후 자동으로 다시 시도합니다.`)
  }

  return parts.join(' ')
}
