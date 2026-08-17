import service from './index'

export const DEFAULT_QUEUE_POLL_SECONDS = 3

const JOB_LABELS = {
  graph_build: '그래프 구축',
  simulation_prepare: '환경 준비',
  simulation_start: '시뮬레이션 시작',
  report_generate: '보고서 생성',
}

export function getQueueStatus(queueId) {
  return service.get(`/api/queue/${queueId}`)
}

export function isQueuedResponse(response) {
  return Boolean(response?.queued && response?.queue?.id)
}

export function getQueueAheadCount(queue) {
  return Math.max((Number(queue?.position || 0)) - 1, 0)
}

export function getQueueJobLabel(jobType) {
  return JOB_LABELS[jobType] || '작업'
}

export function getQueuePollSeconds(queue) {
  if (Number(queue?.retryAfterSeconds || 0) > 0) {
    return Math.max(2, Number(queue.retryAfterSeconds))
  }
  return queue?.status === 'dispatching' ? 2 : DEFAULT_QUEUE_POLL_SECONDS
}

export function formatQueueMessage(queue, fallback = '현재 작업 대기열에 등록되었습니다.') {
  if (!queue) {
    return fallback
  }

  const jobLabel = getQueueJobLabel(queue.jobType)
  const ahead = getQueueAheadCount(queue)
  const totalWaiting = Number(queue.totalWaiting || 0)
  const parts = []

  if (queue.status === 'dispatching') {
    parts.push(`${jobLabel} 실행 슬롯을 확보했습니다. 곧 시작됩니다.`)
  } else if (Number(queue.retryAfterSeconds || 0) > 0) {
    parts.push(`${jobLabel} 차례를 기다리고 있습니다. 서버 슬롯이 정리되면 약 ${queue.retryAfterSeconds}초 후 다시 시도합니다.`)
  } else if (queue.ready) {
    parts.push(`${jobLabel} 차례가 되었습니다. 자동으로 시작합니다.`)
  } else if (queue.position > 0) {
    parts.push(`${jobLabel} 대기열 ${queue.position}번입니다.`)
    if (ahead > 0) {
      parts.push(`앞에 ${ahead}건의 작업이 있습니다.`)
    } else {
      parts.push('곧 자동으로 시작합니다.')
    }
  } else {
    parts.push(fallback)
  }

  if (totalWaiting > 0) {
    parts.push(`현재 같은 작업 대기열은 총 ${totalWaiting}건입니다.`)
  }

  if (queue.lastError) {
    parts.push(`최근 상태: ${queue.lastError}`)
  }

  return parts.join(' ')
}
