import { json, getUser } from './utils.js'
import { PROJECT_STATUS } from './projectStatus.js'
import { reconcileUserReportMirrors } from './reportState.js'

export async function handleReports(request, env, url) {
  const path = url.pathname.replace('/api/reports', '')

  // 공개 샘플 보고서 목록 (인증 불필요)
  if (path === '/samples' && request.method === 'GET') {
    const reports = await env.DB.prepare(
      'SELECT r.id, r.title, r.summary, r.simulation_id, r.created_at, r.refined_key FROM reports r WHERE r.is_sample = 1 ORDER BY r.created_at DESC'
    ).all()

    // 각 보고서에 프로젝트 정보(주제, 파일) 추가
    const enriched = await Promise.all(reports.results.map(async (r) => {
      try {
        const project = await env.DB.prepare(
          'SELECT p.name, p.requirement FROM projects p JOIN simulations s ON p.id = s.project_id WHERE s.id = ?'
        ).bind(r.simulation_id).first()
        if (project) {
          r.requirement = project.requirement || project.name || ''
        }
        const files = await env.DB.prepare(
          'SELECT f.name FROM files f JOIN projects p ON f.project_id = p.id JOIN simulations s ON p.id = s.project_id WHERE s.id = ?'
        ).bind(r.simulation_id).all()
        r.files = (files.results || []).map(f => f.name)
      } catch {}
      delete r.simulation_id
      return r
    }))

    return json({ reports: enriched })
  }

  // 공개 샘플 보고서 상세 (인증 불필요)
  const sampleMatch = path.match(/^\/samples\/([^/]+)$/)
  if (sampleMatch && request.method === 'GET') {
    const report = await env.DB.prepare(
      'SELECT * FROM reports WHERE id = ? AND is_sample = 1'
    ).bind(sampleMatch[1]).first()
    if (!report) return json({ error: 'Not Found' }, 404)

    // 프로젝트 정보 추가
    try {
      const project = await env.DB.prepare(
        'SELECT p.name, p.requirement FROM projects p JOIN simulations s ON p.id = s.project_id WHERE s.id = ?'
      ).bind(report.simulation_id).first()
      if (project) {
        report.requirement = project.requirement || project.name || ''
      }
      const files = await env.DB.prepare(
        'SELECT f.name FROM files f JOIN projects p ON f.project_id = p.id JOIN simulations s ON p.id = s.project_id WHERE s.id = ?'
      ).bind(report.simulation_id).all()
      report.files = (files.results || []).map(f => f.name)
    } catch {}

    // R2에서 refined 또는 원본 로드
    const key = report.refined_key || report.content || `reports/${report.user_id}/${report.id}.json`
    const r2Object = await env.STORAGE.get(key)
    if (r2Object) {
      const body = await r2Object.json()
      report.title = body.title || report.title
      report.summary = body.summary || report.summary
      report.sections = body.sections || []
      report.content = body.content || ''
    } else {
      try { report.sections = JSON.parse(report.sections) } catch { report.sections = [] }
    }
    // 민감 정보 숨기기
    delete report.user_id
    delete report.simulation_id
    return json({ report })
  }

  // 이하 인증 필요
  const user = await getUser(request, env)
  if (!user) return json({ error: 'Unauthorized' }, 401)

  // Save report — 본문은 R2, 메타데이터는 D1
  if (path === '' && request.method === 'POST') {
    try {
      const body = await request.json()
      const { id: requestedId, project_id, simulation_id, title, summary, content, sections } = body
      const id = requestedId || crypto.randomUUID()
      const storageKey = `reports/${user.id}/${id}.json`
      const existing = await env.DB.prepare(
        'SELECT id, user_id FROM reports WHERE id = ?'
      ).bind(id).first()

      if (existing && existing.user_id !== user.id) {
        return json({ error: 'Forbidden', success: false }, 403)
      }

      console.log('[reports] POST 시작:', { id, simulation_id, title: title?.substring(0, 30), userId: user.id })

      // R2에 보고서 본문 저장
      await env.STORAGE.put(storageKey, JSON.stringify({
        title: title || '',
        summary: summary || '',
        content: content || '',
        sections: sections || []
      }), {
        httpMetadata: { contentType: 'application/json' }
      })
      console.log('[reports] R2 저장 완료:', storageKey)

      // D1에 메타데이터만 저장
      if (existing) {
        await env.DB.prepare(
          'UPDATE reports SET simulation_id = ?, title = ?, summary = ?, content = ?, sections = ?, status = ? WHERE id = ? AND user_id = ?'
        ).bind(
          simulation_id || '',
          title || '',
          summary || '',
          storageKey,
          JSON.stringify(sections || []),
          'completed',
          id,
          user.id
        ).run()
      } else {
        const isSample = user.role === 'admin' ? 1 : 0
        await env.DB.prepare(
          'INSERT INTO reports (id, simulation_id, user_id, title, summary, content, sections, status, is_sample, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
        ).bind(
          id,
          simulation_id || '',
          user.id,
          title || '',
          summary || '',
          storageKey,
          JSON.stringify(sections || []),
          'completed',
          isSample,
          new Date().toISOString()
        ).run()
      }
      console.log('[reports] D1 저장 완료')

      // 관련 프로젝트 상태를 report_completed로 자동 업데이트
      if (project_id) {
        await env.DB.prepare(
          'UPDATE projects SET status = ?, report_id = ? WHERE id = ? AND user_id = ?'
        ).bind(PROJECT_STATUS.REPORT_COMPLETED, id, project_id, user.id).run()
      } else if (simulation_id) {
        const updateResult = await env.DB.prepare(
          'UPDATE projects SET status = ?, report_id = ? WHERE simulation_id = ? AND user_id = ?'
        ).bind(PROJECT_STATUS.REPORT_COMPLETED, id, simulation_id, user.id).run()
        console.log('[reports] 프로젝트 상태 업데이트:', { simulation_id, changes: updateResult.meta?.changes })
      }

      return json({ report: { id, title, summary }, success: true }, 201)
    } catch (err) {
      console.error('[reports] POST 에러:', err.message, err.stack)
      return json({ error: err.message, success: false }, 500)
    }
  }

  // List my reports
  if (path === '' && request.method === 'GET') {
    const simulationId = url.searchParams.get('simulation_id')
    await reconcileUserReportMirrors(env, user.id, { simulationId })
    const reports = simulationId
      ? await env.DB.prepare(
          'SELECT id, simulation_id, title, summary, status, refined_key, pdf_key, is_sample, created_at FROM reports WHERE user_id = ? AND simulation_id = ? ORDER BY created_at DESC'
        ).bind(user.id, simulationId).all()
      : await env.DB.prepare(
          'SELECT id, simulation_id, title, summary, status, refined_key, pdf_key, is_sample, created_at FROM reports WHERE user_id = ? ORDER BY created_at DESC'
        ).bind(user.id).all()
    return json({ reports: reports.results })
  }

  // Save refined content to R2
  const refineMatch = path.match(/^\/([^/]+)\/refined$/)
  if (refineMatch && request.method === 'POST') {
    try {
      const reportId = refineMatch[1]
      const { title, summary, sections, generated_at } = await request.json()
      const refinedKey = `reports/${user.id}/${reportId}_refined.json`
      const pdfKey = `pdfs/${reportId}.pdf`
      const nextPayload = {
        title: title || '',
        summary: summary || '',
        sections: sections || [],
        generated_at: generated_at || new Date().toISOString(),
      }
      const existingRecord = await env.DB.prepare(
        'SELECT refined_key FROM reports WHERE id = ? AND user_id = ?'
      ).bind(reportId, user.id).first()
      let shouldInvalidatePdf = true

      if (existingRecord?.refined_key) {
        const existingObject = await env.STORAGE.get(existingRecord.refined_key)
        if (existingObject) {
          try {
            const currentPayload = await existingObject.json()
            shouldInvalidatePdf = !isEquivalentRefinedReport(currentPayload, nextPayload)
          } catch {
            shouldInvalidatePdf = true
          }
        }
      }

      await env.STORAGE.put(refinedKey, JSON.stringify(nextPayload), {
        httpMetadata: { contentType: 'application/json' }
      })

      if (shouldInvalidatePdf) {
        await env.STORAGE.delete(pdfKey).catch(() => null)
      }

      await env.DB.prepare(
        `UPDATE reports
         SET refined_key = ?, pdf_key = CASE WHEN ? THEN NULL ELSE pdf_key END
         WHERE id = ? AND user_id = ?`
      ).bind(refinedKey, shouldInvalidatePdf ? 1 : 0, reportId, user.id).run()

      return json({ success: true, refined_key: refinedKey })
    } catch (err) {
      return json({ error: err.message }, 500)
    }
  }

  // Get refined content
  if (refineMatch && request.method === 'GET') {
    const reportId = refineMatch[1]
    const report = await env.DB.prepare(
      'SELECT refined_key FROM reports WHERE id = ? AND user_id = ?'
    ).bind(reportId, user.id).first()
    if (!report || !report.refined_key) return json({ error: 'Not Found' }, 404)

    const r2Object = await env.STORAGE.get(report.refined_key)
    if (!r2Object) return json({ error: 'Not Found' }, 404)
    const body = await r2Object.json()
    return json({ success: true, refined: body })
  }

  // Get single report — R2에서 본문 로드
  const match = path.match(/^\/([^/]+)$/)
  if (match && request.method === 'GET') {
    let report = await env.DB.prepare(
      'SELECT * FROM reports WHERE id = ? AND user_id = ?'
    ).bind(match[1], user.id).first()
    if (!report) {
      await reconcileUserReportMirrors(env, user.id)
      report = await env.DB.prepare(
        'SELECT * FROM reports WHERE id = ? AND user_id = ?'
      ).bind(match[1], user.id).first()
    }
    if (!report) return json({ error: 'Not Found' }, 404)

    const storageKey = report.refined_key || report.content || `reports/${user.id}/${report.id}.json`
    const r2Object = await env.STORAGE.get(storageKey)
    if (r2Object) {
      const body = await r2Object.json()
      report.title = body.title || report.title
      report.summary = body.summary || report.summary
      report.content = body.content || ''
      report.sections = body.sections || []
      report.generated_at = body.generated_at || report.created_at
    } else {
      try { report.sections = JSON.parse(report.sections) } catch { report.sections = [] }
      report.generated_at = report.created_at
    }

    return json({ report })
  }

  // Delete report — R2 + D1 모두 삭제
  if (match && request.method === 'DELETE') {
    const report = await env.DB.prepare(
      'SELECT simulation_id, refined_key, content, pdf_key FROM reports WHERE id = ? AND user_id = ?'
    ).bind(match[1], user.id).first()
    if (!report) return json({ error: 'Not Found' }, 404)

    const storageKey = report.content || `reports/${user.id}/${match[1]}.json`
    const deletes = [
      env.STORAGE.delete(storageKey),
      env.DB.prepare('DELETE FROM reports WHERE id = ? AND user_id = ?').bind(match[1], user.id).run(),
      env.DB.prepare(
        'UPDATE projects SET report_id = NULL, status = CASE WHEN status = ? THEN ? ELSE status END WHERE report_id = ? AND user_id = ?'
      ).bind(PROJECT_STATUS.REPORT_COMPLETED, PROJECT_STATUS.SIMULATION_COMPLETED, match[1], user.id).run()
    ]
    if (report?.refined_key) deletes.push(env.STORAGE.delete(report.refined_key))
    deletes.push(env.STORAGE.delete(report?.pdf_key || `pdfs/${match[1]}.pdf`))
    await Promise.all(deletes)
    return json({ success: true })
  }

  return json({ error: 'Not Found' }, 404)
}

function isEquivalentRefinedReport(left = {}, right = {}) {
  return (
    String(left.title || '') === String(right.title || '') &&
    String(left.summary || '') === String(right.summary || '') &&
    JSON.stringify(left.sections || []) === JSON.stringify(right.sections || [])
  )
}
