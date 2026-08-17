import { json, getUser } from './utils.js'
import { normalizeProjectRecord, normalizeProjectStatus } from './projectStatus.js'
import { reconcileProjectReportState } from './reportState.js'

export async function handleProjects(request, env, url) {
  const user = await getUser(request, env)
  if (!user) return json({ error: 'Unauthorized' }, 401)

  const path = url.pathname.replace('/api/projects', '')

  // List projects
  if (path === '' && request.method === 'GET') {
    const projects = await env.DB.prepare(
      'SELECT p.*, r.pdf_key FROM projects p LEFT JOIN reports r ON p.report_id = r.id WHERE p.user_id = ? ORDER BY p.created_at DESC'
    ).bind(user.id).all()
    const reconciledProjects = await Promise.all(
      (projects.results || []).map((project) => reconcileProjectReportState(env, user.id, project))
    )
    return json({ projects: reconciledProjects })
  }

  // Create project
  if (path === '' && request.method === 'POST') {
    const { id: customId, name, requirement, status, simulation_id, report_id, analysis_plan, planned_agents, planned_rounds } = await request.json()
    const id = customId || crypto.randomUUID()
    const projStatus = normalizeProjectStatus(status || 'created', { reportId: report_id || null })

    const existing = await env.DB.prepare(
      'SELECT id, user_id, analysis_plan, planned_agents, planned_rounds FROM projects WHERE id = ?'
    ).bind(id).first()

    if (existing && existing.user_id !== user.id) {
      return json({ error: 'Forbidden' }, 403)
    }

    if (existing) {
      await env.DB.prepare(
        `UPDATE projects
         SET name = ?, requirement = ?, status = ?, simulation_id = ?, report_id = ?, analysis_plan = ?, planned_agents = ?, planned_rounds = ?
         WHERE id = ? AND user_id = ?`
      ).bind(
        name || 'Untitled',
        requirement || null,
        projStatus,
        simulation_id || null,
        report_id || null,
        analysis_plan !== undefined ? (analysis_plan || null) : (existing.analysis_plan || null),
        planned_agents !== undefined ? (planned_agents ?? null) : (existing.planned_agents ?? null),
        planned_rounds !== undefined ? (planned_rounds ?? null) : (existing.planned_rounds ?? null),
        id,
        user.id
      ).run()
    } else {
      await env.DB.prepare(
        `INSERT INTO projects
           (id, user_id, name, requirement, status, simulation_id, report_id, analysis_plan, planned_agents, planned_rounds, created_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
      ).bind(
        id,
        user.id,
        name || 'Untitled',
        requirement || null,
        projStatus,
        simulation_id || null,
        report_id || null,
        analysis_plan || null,
        planned_agents ?? null,
        planned_rounds ?? null,
        new Date().toISOString()
      ).run()
    }

    return json({
      project: {
        id,
        name: name || 'Untitled',
        requirement: requirement || null,
        status: projStatus,
        simulation_id: simulation_id || null,
        report_id: report_id || null,
        analysis_plan: analysis_plan || null,
        planned_agents: planned_agents ?? null,
        planned_rounds: planned_rounds ?? null,
      }
    }, existing ? 200 : 201)
  }

  // Get single project
  const match = path.match(/^\/([^/]+)$/)
  if (match && request.method === 'GET') {
    const project = await env.DB.prepare(
      'SELECT * FROM projects WHERE id = ? AND user_id = ?'
    ).bind(match[1], user.id).first()
    if (!project) return json({ error: 'Not Found' }, 404)
    const reconciledProject = await reconcileProjectReportState(env, user.id, project)
    return json({ project: reconciledProject })
  }

  // Update project status
  if (match && request.method === 'PUT') {
    const existing = await env.DB.prepare(
      'SELECT report_id FROM projects WHERE id = ? AND user_id = ?'
    ).bind(match[1], user.id).first()
    if (!existing) return json({ error: 'Not Found' }, 404)

    const { status, simulation_id, report_id, name, requirement, analysis_plan, planned_agents, planned_rounds } = await request.json()
    const updates = []
    const params = []
    if (status) {
      updates.push('status = ?')
      const effectiveReportId = report_id !== undefined ? report_id : existing.report_id
      params.push(normalizeProjectStatus(status, { reportId: effectiveReportId || null }))
    }
    if (simulation_id !== undefined) { updates.push('simulation_id = ?'); params.push(simulation_id || null) }
    if (report_id !== undefined) { updates.push('report_id = ?'); params.push(report_id || null) }
    if (name !== undefined) { updates.push('name = ?'); params.push(name || 'Untitled') }
    if (requirement !== undefined) { updates.push('requirement = ?'); params.push(requirement || null) }
    if (analysis_plan !== undefined) { updates.push('analysis_plan = ?'); params.push(analysis_plan || null) }
    if (planned_agents !== undefined) { updates.push('planned_agents = ?'); params.push(planned_agents ?? null) }
    if (planned_rounds !== undefined) { updates.push('planned_rounds = ?'); params.push(planned_rounds ?? null) }
    if (updates.length > 0) {
      params.push(match[1], user.id)
      await env.DB.prepare(
        `UPDATE projects SET ${updates.join(', ')} WHERE id = ? AND user_id = ?`
      ).bind(...params).run()
    }
    return json({ success: true })
  }

  // Delete project
  if (match && request.method === 'DELETE') {
    const project = await env.DB.prepare(
      'SELECT id, simulation_id, report_id FROM projects WHERE id = ? AND user_id = ?'
    ).bind(match[1], user.id).first()

    if (!project) {
      return json({ error: 'Not Found' }, 404)
    }

    if (project.report_id) {
      await cleanupProjectReport(env, user.id, project.report_id)
    }

    await cleanupProjectResources(env, user.id, project)
    await cleanupBackendProject(env, match[1])

    await env.DB.batch([
      env.DB.prepare('DELETE FROM simulations WHERE project_id = ? AND user_id = ?').bind(match[1], user.id),
      env.DB.prepare('DELETE FROM files WHERE project_id = ? AND user_id = ?').bind(match[1], user.id),
      env.DB.prepare('DELETE FROM projects WHERE id = ? AND user_id = ?').bind(match[1], user.id),
    ])

    return json({ success: true })
  }

  return json({ error: 'Not Found' }, 404)
}

async function cleanupProjectReport(env, userId, reportId) {
  const report = await env.DB.prepare(
    'SELECT refined_key, content, pdf_key FROM reports WHERE id = ? AND user_id = ?'
  ).bind(reportId, userId).first()

  if (!report) {
    return
  }

  const storageKey = report.content || `reports/${userId}/${reportId}.json`
  const deletes = [
    env.STORAGE.delete(storageKey),
    env.DB.prepare('DELETE FROM reports WHERE id = ? AND user_id = ?').bind(reportId, userId).run()
  ]

  if (report.refined_key) {
    deletes.push(env.STORAGE.delete(report.refined_key))
  }
  deletes.push(env.STORAGE.delete(report.pdf_key || `pdfs/${reportId}.pdf`))

  await Promise.all(deletes)
}

async function cleanupProjectResources(env, userId, project) {
  const projectId = project?.id
  if (!projectId) return

  const filesResult = await env.DB.prepare(
    'SELECT storage_key FROM files WHERE project_id = ? AND user_id = ?'
  ).bind(projectId, userId).all()

  const deleteTasks = []
  for (const file of filesResult.results || []) {
    if (file?.storage_key) {
      deleteTasks.push(env.STORAGE.delete(file.storage_key))
    }
  }

  const resourceKeys = [
    projectId,
    project?.simulation_id || null,
    project?.report_id || null,
  ].filter(Boolean)

  if (resourceKeys.length > 0) {
    const placeholders = resourceKeys.map(() => '?').join(', ')
    deleteTasks.push(
      env.DB.prepare(
        `DELETE FROM job_queue
         WHERE user_id = ?
           AND resource_key IN (${placeholders})`
      ).bind(userId, ...resourceKeys).run()
    )
  }

  await Promise.all(deleteTasks)
}

async function cleanupBackendProject(env, projectId) {
  const projectRes = await proxyToBackend(env, `/api/graph/project/${encodeURIComponent(projectId)}`)

  if (projectRes.status === 404) {
    return
  }

  if (!projectRes.ok) {
    const payload = await safeJson(projectRes)
    throw new Error(payload?.error || '백엔드 프로젝트 조회 실패')
  }

  const payload = await safeJson(projectRes)
  const graphId = payload?.data?.graph_id

  if (graphId) {
    const deleteGraphRes = await proxyToBackend(env, `/api/graph/delete/${encodeURIComponent(graphId)}`, {
      method: 'DELETE',
    })

    if (!deleteGraphRes.ok && deleteGraphRes.status !== 404) {
      const deleteGraphPayload = await safeJson(deleteGraphRes)
      throw new Error(deleteGraphPayload?.error || '백엔드 그래프 삭제 실패')
    }
  }

  const deleteProjectRes = await proxyToBackend(env, `/api/graph/project/${encodeURIComponent(projectId)}`, {
    method: 'DELETE',
  })

  if (!deleteProjectRes.ok && deleteProjectRes.status !== 404) {
    const deleteProjectPayload = await safeJson(deleteProjectRes)
    throw new Error(deleteProjectPayload?.error || '백엔드 프로젝트 삭제 실패')
  }
}

async function proxyToBackend(env, path, init = {}) {
  const backendUrl = env.SIMULATION_API || 'http://localhost:5001'
  const target = new URL(path, backendUrl)
  const headers = new Headers(init.headers || {})
  headers.set('X-Internal-Key', env.INTERNAL_API_KEY)
  headers.set('Host', new URL(backendUrl).host)

  return fetch(target.toString(), {
    ...init,
    headers,
  })
}

async function safeJson(response) {
  try {
    return await response.json()
  } catch {
    return null
  }
}
