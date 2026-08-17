import { json, getUser } from './utils.js'

const ACTIVE_QUEUE_STATUSES = ['queued', 'dispatching']
const DISPATCH_TIMEOUT_MS = 2 * 60 * 1000
const QUEUED_STALE_TIMEOUT_MS = 60 * 60 * 1000
const DEFAULT_QUEUE_RETRY_AFTER_SECONDS = 10

const QUEUEABLE_ROUTES = {
  '/api/graph/build': { jobType: 'graph_build', resourceField: 'project_id' },
  '/api/simulation/prepare': { jobType: 'simulation_prepare', resourceField: 'simulation_id' },
  '/api/simulation/start': { jobType: 'simulation_start', resourceField: 'simulation_id' },
  '/api/report/generate': { jobType: 'report_generate', resourceField: 'simulation_id' },
}

export async function handleQueue(request, env, url) {
  const user = await getUser(request, env)
  if (!user) return json({ error: 'Unauthorized' }, 401)

  const match = url.pathname.match(/^\/api\/queue\/([^/]+)$/)
  if (!match || request.method !== 'GET') {
    return json({ error: 'Not Found' }, 404)
  }

  const queueId = match[1]
  const entry = await getQueueEntry(env, user.id, queueId)
  if (!entry) {
    return json({ error: '대기열 항목을 찾을 수 없습니다.' }, 404)
  }

  await resetStaleQueuedEntries(env, entry.job_type)
  await resetExpiredDispatch(env, entry)
  const refreshedEntry = await getQueueEntry(env, user.id, queueId)
  if (!refreshedEntry) {
    return json({ error: '대기열 항목을 찾을 수 없습니다.' }, 404)
  }
  const status = await getQueueStatus(env, refreshedEntry)
  return json({ success: true, queue: status })
}

export async function getQueueableRequestMeta(request, url) {
  if (request.method !== 'POST') return null

  const route = QUEUEABLE_ROUTES[url.pathname]
  if (!route) return null

  let body = {}
  try {
    body = await request.clone().json()
  } catch {
    body = {}
  }

  return {
    jobType: route.jobType,
    requestPath: url.pathname,
    resourceKey: body?.[route.resourceField] ? String(body[route.resourceField]) : null,
    queueId: body?.queue_id ? String(body.queue_id) : null,
  }
}

export async function proxyQueueableRequest(request, env, url, user, meta, proxyFn) {
  if (meta.queueId) {
    return dispatchQueuedRequest(request, env, url, user, meta, proxyFn)
  }

  const entry = await createQueueEntry(env, user.id, meta.jobType, meta.requestPath, meta.resourceKey)
  const status = await getQueueStatus(env, entry)
  return buildQueuedResponse(status, '현재 대기열에 등록되었습니다.')
}

async function dispatchQueuedRequest(request, env, url, user, meta, proxyFn) {
  const entry = await getQueueEntry(env, user.id, meta.queueId)
  if (!entry) {
    return json({ error: '유효하지 않은 대기열 항목입니다.' }, 404)
  }

  await resetExpiredDispatch(env, entry)

  if (entry.job_type !== meta.jobType || entry.request_path !== meta.requestPath || (entry.resource_key || null) !== (meta.resourceKey || null)) {
    return json({ error: '대기열 항목과 요청 정보가 일치하지 않습니다.' }, 409)
  }

  const status = await getQueueStatus(env, entry)
  if (!status.ready) {
    return buildQueuedResponse(status, '아직 대기 순서입니다.')
  }

  const locked = await markQueueDispatching(env, entry.id)
  if (!locked) {
    const refreshedEntry = await getQueueEntry(env, user.id, entry.id)
    const refreshedStatus = await getQueueStatus(env, refreshedEntry || entry)
    return buildQueuedResponse(refreshedStatus, '다른 창에서 먼저 실행을 시도했습니다.')
  }

  try {
    const response = await proxyFn()
    if (response.status === 429) {
      await requeueEntry(
        env,
        entry.id,
        buildQueueErrorPayload(
          '서버 용량이 아직 확보되지 않았습니다.',
          getRetryAfterSeconds(response)
        )
      )
      const retriedEntry = await getQueueEntry(env, user.id, entry.id)
      const queuedStatus = await getQueueStatus(env, retriedEntry)
      return buildQueuedResponse(queuedStatus, '아직 실행 슬롯이 비지 않았습니다.')
    }

    await completeQueueEntry(env, entry.id)
    return response
  } catch (error) {
    await requeueEntry(env, entry.id, error.message || '요청 전달 중 오류가 발생했습니다.')
    throw error
  }
}

async function getActiveQueueEntry(env, userId, jobType, requestPath, resourceKey) {
  const placeholders = ACTIVE_QUEUE_STATUSES.map(() => '?').join(', ')
  return env.DB.prepare(
    `SELECT *
     FROM job_queue
     WHERE user_id = ?
       AND job_type = ?
       AND request_path = ?
       AND resource_key IS ?
       AND status IN (${placeholders})
     ORDER BY created_at ASC, id ASC
     LIMIT 1`
  ).bind(userId, jobType, requestPath, resourceKey, ...ACTIVE_QUEUE_STATUSES).first()
}

async function createQueueEntry(env, userId, jobType, requestPath, resourceKey) {
  await resetStaleQueuedEntries(env, jobType)

  const existing = await getActiveQueueEntry(env, userId, jobType, requestPath, resourceKey)
  if (existing) {
    return existing
  }

  const id = crypto.randomUUID()
  const now = new Date().toISOString()

  try {
    await env.DB.prepare(
      `INSERT INTO job_queue (id, user_id, job_type, resource_key, request_path, status, created_at, updated_at)
       VALUES (?, ?, ?, ?, ?, 'queued', ?, ?)`
    ).bind(id, userId, jobType, resourceKey, requestPath, now, now).run()
  } catch (error) {
    const duplicated = await getActiveQueueEntry(env, userId, jobType, requestPath, resourceKey)
    if (duplicated) {
      return duplicated
    }
    throw error
  }

  return getQueueEntry(env, userId, id)
}

async function getQueueEntry(env, userId, queueId) {
  return env.DB.prepare(
    'SELECT * FROM job_queue WHERE id = ? AND user_id = ? LIMIT 1'
  ).bind(queueId, userId).first()
}

async function getQueueStatus(env, entry) {
  await resetStaleQueuedEntries(env, entry.job_type)
  const currentEntry = await env.DB.prepare(
    'SELECT * FROM job_queue WHERE id = ? LIMIT 1'
  ).bind(entry.id).first()
  if (!currentEntry) {
    return {
      id: entry.id,
      jobType: entry.job_type,
      status: 'failed',
      position: 0,
      totalWaiting: 0,
      ready: false,
      retryAfterSeconds: 0,
      resourceKey: entry.resource_key,
      requestPath: entry.request_path,
      createdAt: entry.created_at,
      startedAt: entry.started_at,
      finishedAt: entry.finished_at,
      lastError: '대기열 항목을 찾을 수 없습니다.',
    }
  }

  const placeholders = ACTIVE_QUEUE_STATUSES.map(() => '?').join(', ')
  const lastError = parseQueueErrorPayload(currentEntry.last_error)
  const totalWaitingRow = await env.DB.prepare(
    `SELECT COUNT(*) AS count
     FROM job_queue
     WHERE job_type = ?
       AND status IN (${placeholders})`
  ).bind(currentEntry.job_type, ...ACTIVE_QUEUE_STATUSES).first()

  let position = 0
  if (ACTIVE_QUEUE_STATUSES.includes(currentEntry.status)) {
    const aheadRow = await env.DB.prepare(
      `SELECT COUNT(*) AS count
       FROM job_queue
       WHERE job_type = ?
         AND status IN (${placeholders})
         AND (
           created_at < ?
           OR (created_at = ? AND id < ?)
         )`
    ).bind(currentEntry.job_type, ...ACTIVE_QUEUE_STATUSES, currentEntry.created_at, currentEntry.created_at, currentEntry.id).first()
    position = Number(aheadRow?.count || 0) + 1
  }

  const retryAfterSeconds = getRemainingRetryAfterSeconds(currentEntry.updated_at, lastError.retryAfterSeconds)
  const ready = currentEntry.status === 'queued' && position === 1 && retryAfterSeconds === 0

  return {
    id: currentEntry.id,
    jobType: currentEntry.job_type,
    status: currentEntry.status,
    position,
    totalWaiting: Number(totalWaitingRow?.count || 0),
    ready,
    retryAfterSeconds,
    resourceKey: currentEntry.resource_key,
    requestPath: currentEntry.request_path,
    createdAt: currentEntry.created_at,
    startedAt: currentEntry.started_at,
    finishedAt: currentEntry.finished_at,
    lastError: lastError.message,
  }
}

async function markQueueDispatching(env, queueId) {
  const now = new Date().toISOString()
  const result = await env.DB.prepare(
    `UPDATE job_queue
     SET status = 'dispatching',
         started_at = COALESCE(started_at, ?),
         updated_at = ?,
         last_error = NULL
     WHERE id = ?
       AND status = 'queued'`
  ).bind(now, now, queueId).run()
  return Boolean(result.meta?.changes)
}

async function completeQueueEntry(env, queueId) {
  const now = new Date().toISOString()
  await env.DB.prepare(
    `UPDATE job_queue
     SET status = 'completed',
         finished_at = ?,
         updated_at = ?
     WHERE id = ?`
  ).bind(now, now, queueId).run()
}

async function requeueEntry(env, queueId, lastError = null) {
  const now = new Date().toISOString()
  await env.DB.prepare(
    `UPDATE job_queue
     SET status = 'queued',
         updated_at = ?,
         started_at = NULL,
         last_error = ?
     WHERE id = ?`
  ).bind(now, lastError, queueId).run()
}

async function resetExpiredDispatch(env, entry) {
  if (entry.status !== 'dispatching' || !entry.updated_at) {
    return
  }

  const updatedAt = Date.parse(entry.updated_at)
  if (!Number.isFinite(updatedAt)) {
    return
  }

  if (Date.now() - updatedAt <= DISPATCH_TIMEOUT_MS) {
    return
  }

  await requeueEntry(env, entry.id, '이전 실행 시도가 만료되어 다시 대기열에 넣었습니다.')
}

async function resetStaleQueuedEntries(env, jobType) {
  if (!jobType) return

  const cutoffIso = new Date(Date.now() - QUEUED_STALE_TIMEOUT_MS).toISOString()
  const nowIso = new Date().toISOString()

  await env.DB.prepare(
    `UPDATE job_queue
     SET status = 'failed',
         finished_at = ?,
         updated_at = ?,
         last_error = ?
     WHERE job_type = ?
       AND status = 'queued'
       AND updated_at < ?`
  ).bind(
    nowIso,
    nowIso,
    '오래된 대기열 항목을 정리했습니다. 다시 시도해주세요.',
    jobType,
    cutoffIso,
  ).run()
}

function buildQueuedResponse(status, fallbackMessage) {
  return json({
    success: true,
    queued: true,
    queue: status,
    message: formatQueueMessage(status, fallbackMessage),
  }, 202)
}

function formatQueueMessage(status, fallbackMessage) {
  if (!status) {
    return fallbackMessage
  }

  const jobLabel = getJobLabel(status.jobType)
  const ahead = Math.max((Number(status.position || 0)) - 1, 0)

  if (status.status === 'dispatching') {
    return `${jobLabel} 실행 슬롯을 확보했습니다. 곧 시작됩니다.`
  }

  if (status.retryAfterSeconds > 0) {
    return `${jobLabel} 차례를 기다리고 있습니다. 서버 슬롯이 정리되면 약 ${status.retryAfterSeconds}초 후 다시 시도합니다.`
  }

  if (status.ready) {
    return `${jobLabel} 차례가 되었습니다. 자동으로 시작합니다.`
  }

  if (status.position > 0) {
    if (ahead > 0) {
      return `${jobLabel} 대기열 ${status.position}번입니다. 앞에 ${ahead}건의 작업이 있습니다.`
    }
    return `${jobLabel} 대기열 1번입니다. 곧 시작됩니다.`
  }

  return fallbackMessage
}

function getJobLabel(jobType) {
  switch (jobType) {
    case 'graph_build':
      return '그래프 구축'
    case 'simulation_prepare':
      return '환경 준비'
    case 'simulation_start':
      return '시뮬레이션 시작'
    case 'report_generate':
      return '보고서 생성'
    default:
      return '작업'
  }
}

function buildQueueErrorPayload(message, retryAfterSeconds = null) {
  const payload = {
    message: message || '요청 처리 중 오류가 발생했습니다.',
  }

  if (Number.isFinite(retryAfterSeconds) && retryAfterSeconds > 0) {
    payload.retryAfterSeconds = retryAfterSeconds
  }

  return JSON.stringify(payload)
}

function parseQueueErrorPayload(rawValue) {
  if (!rawValue) {
    return { message: null, retryAfterSeconds: 0 }
  }

  try {
    const parsed = JSON.parse(rawValue)
    if (parsed && typeof parsed === 'object') {
      return {
        message: typeof parsed.message === 'string' ? parsed.message : rawValue,
        retryAfterSeconds: normalizeRetryAfterSeconds(parsed.retryAfterSeconds),
      }
    }
  } catch {
    // 기존 문자열 포맷도 그대로 지원
  }

  return {
    message: String(rawValue),
    retryAfterSeconds: 0,
  }
}

function getRetryAfterSeconds(response) {
  return normalizeRetryAfterSeconds(response?.headers?.get('Retry-After'))
}

function normalizeRetryAfterSeconds(value) {
  const parsed = Number.parseInt(value, 10)
  if (!Number.isFinite(parsed) || parsed <= 0) {
    return DEFAULT_QUEUE_RETRY_AFTER_SECONDS
  }
  return parsed
}

function getRemainingRetryAfterSeconds(updatedAt, retryAfterSeconds) {
  if (!retryAfterSeconds || !updatedAt) {
    return 0
  }

  const updatedAtMs = Date.parse(updatedAt)
  if (!Number.isFinite(updatedAtMs)) {
    return 0
  }

  const remaining = retryAfterSeconds - Math.floor((Date.now() - updatedAtMs) / 1000)
  return Math.max(0, remaining)
}
