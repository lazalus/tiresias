import { json, getUser } from './utils.js'

export async function handleProjects(request, env, url) {
  const user = await getUser(request, env)
  if (!user) return json({ error: 'Unauthorized' }, 401)

  const path = url.pathname.replace('/api/projects', '')

  // List projects
  if (path === '' && request.method === 'GET') {
    const projects = await env.DB.prepare(
      'SELECT * FROM projects WHERE user_id = ? ORDER BY created_at DESC'
    ).bind(user.id).all()
    return json({ projects: projects.results })
  }

  // Create project
  if (path === '' && request.method === 'POST') {
    const { name, requirement } = await request.json()
    const id = crypto.randomUUID()
    await env.DB.prepare(
      'INSERT INTO projects (id, user_id, name, requirement, status, created_at) VALUES (?, ?, ?, ?, ?, ?)'
    ).bind(id, user.id, name || 'Untitled', requirement, 'created', new Date().toISOString()).run()
    return json({ project: { id, name, requirement, status: 'created' } }, 201)
  }

  // Get single project
  const match = path.match(/^\/([a-f0-9-]+)$/)
  if (match && request.method === 'GET') {
    const project = await env.DB.prepare(
      'SELECT * FROM projects WHERE id = ? AND user_id = ?'
    ).bind(match[1], user.id).first()
    if (!project) return json({ error: 'Not Found' }, 404)
    return json({ project })
  }

  // Delete project
  if (match && request.method === 'DELETE') {
    await env.DB.prepare(
      'DELETE FROM projects WHERE id = ? AND user_id = ?'
    ).bind(match[1], user.id).run()
    return json({ success: true })
  }

  return json({ error: 'Not Found' }, 404)
}
