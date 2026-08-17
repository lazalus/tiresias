import { PROJECT_STATUS, normalizeProjectRecord, normalizeProjectStatus } from './projectStatus.js'

async function safeJson(response) {
  try {
    return await response.json()
  } catch {
    return null
  }
}

async function fetchBackendReportStatus(env, simulationId) {
  if (!simulationId) return null

  const backendUrl = env.SIMULATION_API || 'http://localhost:5001'
  const target = new URL(`/api/report/check/${encodeURIComponent(simulationId)}`, backendUrl)

  const response = await fetch(target.toString(), {
    method: 'GET',
    headers: {
      'X-Internal-Key': env.INTERNAL_API_KEY,
      'Host': new URL(backendUrl).host,
    },
  })

  if (!response.ok) {
    return null
  }

  const payload = await safeJson(response)
  return payload?.success ? payload.data || null : null
}

async function fetchBackendReportDetail(env, reportId) {
  if (!reportId) return null

  const backendUrl = env.SIMULATION_API || 'http://localhost:5001'
  const target = new URL(`/api/report/${encodeURIComponent(reportId)}`, backendUrl)
  const response = await fetch(target.toString(), {
    method: 'GET',
    headers: {
      'X-Internal-Key': env.INTERNAL_API_KEY,
      'Host': new URL(backendUrl).host,
    },
  })

  if (!response.ok) {
    return null
  }

  const payload = await safeJson(response)
  return payload?.success ? payload.data || null : null
}

function buildReportStorageKey(userId, reportId) {
  return `reports/${userId}/${reportId}.json`
}

async function upsertMirroredReport(env, userId, {
  reportId,
  simulationId,
  status = 'completed',
  createdAt = null,
} = {}) {
  if (!reportId || !simulationId) return

  const existing = await env.DB.prepare(
    'SELECT id, title, summary, content, refined_key, pdf_key, status, created_at FROM reports WHERE id = ? AND user_id = ?'
  ).bind(reportId, userId).first()

  let detail = null
  if (status === 'completed') {
    detail = await fetchBackendReportDetail(env, reportId)
  }

  const storageKey = buildReportStorageKey(userId, reportId)
  const sections = Array.isArray(detail?.sections) ? detail.sections : []
  const payload = detail ? {
    title: detail.title || '',
    summary: detail.summary || '',
    content: detail.markdown_content || '',
    sections,
    generated_at: detail.completed_at || detail.created_at || createdAt || new Date().toISOString(),
  } : null

  if (payload) {
    await env.STORAGE.put(storageKey, JSON.stringify(payload), {
      httpMetadata: { contentType: 'application/json' },
    })
  }

  const nextStatus = payload ? 'completed' : status
  const nextCreatedAt = detail?.created_at || existing?.created_at || createdAt || new Date().toISOString()

  if (existing) {
    await env.DB.prepare(
      `UPDATE reports
       SET simulation_id = ?, title = ?, summary = ?, content = ?, sections = ?, status = ?, created_at = ?
       WHERE id = ? AND user_id = ?`
    ).bind(
      simulationId,
      payload?.title || existing.title || '',
      payload?.summary || existing.summary || '',
      payload ? storageKey : (existing.content || storageKey),
      JSON.stringify(sections),
      nextStatus,
      nextCreatedAt,
      reportId,
      userId,
    ).run()
    return
  }

  await env.DB.prepare(
    `INSERT INTO reports (
       id, simulation_id, user_id, title, summary, content, sections, status, is_sample, created_at
     ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?)`
  ).bind(
    reportId,
    simulationId,
    userId,
    payload?.title || '',
    payload?.summary || '',
    payload ? storageKey : storageKey,
    JSON.stringify(sections),
    nextStatus,
    nextCreatedAt,
  ).run()
}

function resolveDesiredProjectState(project, backendReport) {
  const currentStatus = normalizeProjectStatus(project.status, {
    reportId: project.report_id || project.reportId || null,
  })
  const currentReportId = project.report_id || project.reportId || null

  if (!backendReport) {
    return normalizeProjectRecord(project)
  }

  const hasReport = Boolean(backendReport.has_report)
  const backendStatus = String(backendReport.report_status || '').trim()
  const backendReportId = backendReport.report_id || null

  let nextStatus = currentStatus
  let nextReportId = currentReportId

  if (hasReport && ['pending', 'planning', 'generating'].includes(backendStatus)) {
    nextStatus = PROJECT_STATUS.REPORT_GENERATING
    nextReportId = backendReportId || currentReportId
  } else if (hasReport && backendStatus === 'completed') {
    nextStatus = PROJECT_STATUS.REPORT_COMPLETED
    nextReportId = backendReportId || currentReportId
  } else if (
    backendStatus === 'failed' ||
    (!hasReport && [PROJECT_STATUS.REPORT_GENERATING, PROJECT_STATUS.REPORT_COMPLETED].includes(currentStatus))
  ) {
    nextStatus = PROJECT_STATUS.SIMULATION_COMPLETED
    nextReportId = null
  }

  return normalizeProjectRecord({
    ...project,
    status: nextStatus,
    report_id: nextReportId,
  })
}

export async function reconcileProjectReportState(env, userId, project) {
  if (!project) return project

  const currentStatus = normalizeProjectStatus(project.status, {
    reportId: project.report_id || project.reportId || null,
  })
  const shouldCheckBackend = Boolean(
    project.simulation_id &&
    (
      project.report_id ||
      project.reportId ||
      currentStatus === PROJECT_STATUS.REPORT_GENERATING ||
      currentStatus === PROJECT_STATUS.REPORT_COMPLETED
    )
  )

  if (!shouldCheckBackend) {
    return normalizeProjectRecord(project)
  }

  try {
    const backendReport = await fetchBackendReportStatus(env, project.simulation_id)
    const reconciled = resolveDesiredProjectState(project, backendReport)

    if (
      reconciled.status !== project.status ||
      (reconciled.report_id || null) !== (project.report_id || project.reportId || null)
    ) {
      await env.DB.prepare(
        'UPDATE projects SET status = ?, report_id = ? WHERE id = ? AND user_id = ?'
      ).bind(
        reconciled.status,
        reconciled.report_id || null,
        project.id,
        userId
      ).run()
    }

    if (backendReport?.has_report && backendReport?.report_id) {
      if (String(backendReport.report_status || '') === 'completed') {
        await upsertMirroredReport(env, userId, {
          reportId: backendReport.report_id,
          simulationId: project.simulation_id,
          status: 'completed',
        })
      } else if (['pending', 'planning', 'generating'].includes(String(backendReport.report_status || ''))) {
        await upsertMirroredReport(env, userId, {
          reportId: backendReport.report_id,
          simulationId: project.simulation_id,
          status: 'generating',
        })
      }
    }

    return reconciled
  } catch (error) {
    console.warn('프로젝트 보고서 상태 정합성 확인 실패:', project.id, error?.message || error)
    return normalizeProjectRecord(project)
  }
}

export async function reconcileUserReportMirrors(env, userId, { simulationId = null } = {}) {
  const projects = simulationId
    ? await env.DB.prepare(
        'SELECT * FROM projects WHERE user_id = ? AND simulation_id = ? ORDER BY created_at DESC'
      ).bind(userId, simulationId).all()
    : await env.DB.prepare(
        'SELECT * FROM projects WHERE user_id = ? AND (simulation_id IS NOT NULL OR report_id IS NOT NULL) ORDER BY created_at DESC'
      ).bind(userId).all()

  await Promise.all(
    (projects.results || []).map((project) => reconcileProjectReportState(env, userId, project))
  )
}
