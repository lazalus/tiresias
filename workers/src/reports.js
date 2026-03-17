import { json, getUser } from './utils.js'

export async function handleReports(request, env, url) {
  const user = await getUser(request, env)
  if (!user) return json({ error: 'Unauthorized' }, 401)

  const path = url.pathname.replace('/api/reports', '')

  // Save report
  if (path === '' && request.method === 'POST') {
    const { project_id, simulation_id, title, summary, content, sections } = await request.json()
    const id = crypto.randomUUID()
    await env.DB.prepare(
      'INSERT INTO reports (id, simulation_id, user_id, title, summary, content, sections, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)'
    ).bind(id, simulation_id || '', user.id, title || '', summary || '', content || '', JSON.stringify(sections || []), 'completed', new Date().toISOString()).run()
    return json({ report: { id, title, summary }, success: true }, 201)
  }

  // List my reports
  if (path === '' && request.method === 'GET') {
    const reports = await env.DB.prepare(
      'SELECT id, simulation_id, title, summary, status, created_at FROM reports WHERE user_id = ? ORDER BY created_at DESC'
    ).bind(user.id).all()
    return json({ reports: reports.results })
  }

  // Get single report
  const match = path.match(/^\/([a-f0-9-]+)$/)
  if (match && request.method === 'GET') {
    const report = await env.DB.prepare(
      'SELECT * FROM reports WHERE id = ? AND user_id = ?'
    ).bind(match[1], user.id).first()
    if (!report) return json({ error: 'Not Found' }, 404)
    // Parse sections back from JSON
    try { report.sections = JSON.parse(report.sections) } catch { report.sections = [] }
    return json({ report })
  }

  // Delete report
  if (match && request.method === 'DELETE') {
    await env.DB.prepare('DELETE FROM reports WHERE id = ? AND user_id = ?').bind(match[1], user.id).run()
    return json({ success: true })
  }

  return json({ error: 'Not Found' }, 404)
}
