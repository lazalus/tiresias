import { json, getUser } from './utils.js'

export async function handleFiles(request, env, url) {
  const user = await getUser(request, env)
  if (!user) return json({ error: 'Unauthorized' }, 401)

  const path = url.pathname.replace('/api/files', '')

  // Upload file
  if (path === '/upload' && request.method === 'POST') {
    const formData = await request.formData()
    const file = formData.get('file')
    const projectId = formData.get('project_id')

    if (!file || !projectId) {
      return json({ error: 'file and project_id are required' }, 400)
    }

    const key = `${user.id}/${projectId}/${Date.now()}_${file.name}`
    await env.STORAGE.put(key, file.stream(), {
      httpMetadata: { contentType: file.type },
      customMetadata: { userId: user.id, projectId, originalName: file.name },
    })

    const id = crypto.randomUUID()
    await env.DB.prepare(
      'INSERT INTO files (id, project_id, user_id, name, storage_key, size, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)'
    ).bind(id, projectId, user.id, file.name, key, file.size, new Date().toISOString()).run()

    return json({ file: { id, name: file.name, key, size: file.size } }, 201)
  }

  // List files for a project
  const listMatch = path.match(/^\/project\/([a-f0-9-]+)$/)
  if (listMatch && request.method === 'GET') {
    const files = await env.DB.prepare(
      'SELECT * FROM files WHERE project_id = ? AND user_id = ?'
    ).bind(listMatch[1], user.id).all()
    return json({ files: files.results })
  }

  // Download file
  const dlMatch = path.match(/^\/download\/([a-f0-9-]+)$/)
  if (dlMatch && request.method === 'GET') {
    const fileRecord = await env.DB.prepare(
      'SELECT * FROM files WHERE id = ? AND user_id = ?'
    ).bind(dlMatch[1], user.id).first()
    if (!fileRecord) return json({ error: 'Not Found' }, 404)

    const obj = await env.STORAGE.get(fileRecord.storage_key)
    if (!obj) return json({ error: 'File not found in storage' }, 404)

    return new Response(obj.body, {
      headers: {
        'Content-Type': obj.httpMetadata?.contentType || 'application/octet-stream',
        'Content-Disposition': `attachment; filename="${fileRecord.name}"`,
      },
    })
  }

  return json({ error: 'Not Found' }, 404)
}
