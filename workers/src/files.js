import { json, getUser } from './utils.js'

export async function handleFiles(request, env, url) {
  const user = await getUser(request, env)
  if (!user) return json({ error: 'Unauthorized' }, 401)

  const path = url.pathname.replace('/api/files', '')

  if (path === '/pending-upload' && request.method === 'POST') {
    const formData = await request.formData()
    const files = formData.getAll('files').filter(Boolean)
    const simulationRequirement = String(formData.get('simulation_requirement') || '')

    if (!files.length) {
      return json({ error: '최소 1개 이상의 파일이 필요합니다.' }, 400)
    }

    const pendingToken = `pending_${Date.now()}_${crypto.randomUUID().slice(0, 8)}`
    const manifest = {
      token: pendingToken,
      simulationRequirement,
      createdAt: new Date().toISOString(),
      files: [],
    }

    for (let index = 0; index < files.length; index += 1) {
      const file = files[index]
      if (!file || typeof file.name !== 'string') continue

      const safeName = file.name.replace(/[^\w.\-가-힣]+/g, '_')
      const key = `${user.id}/pending/${pendingToken}/${index}_${safeName}`

      await env.STORAGE.put(key, file.stream(), {
        httpMetadata: { contentType: file.type || 'application/octet-stream' },
        customMetadata: {
          userId: user.id,
          pendingToken,
          originalName: file.name,
        },
      })

      manifest.files.push({
        index,
        name: file.name,
        size: file.size || 0,
        type: file.type || 'application/octet-stream',
        key,
      })
    }

    await env.STORAGE.put(getPendingManifestKey(user.id, pendingToken), JSON.stringify(manifest), {
      httpMetadata: { contentType: 'application/json' },
    })

    return json({
      pendingUpload: {
        token: pendingToken,
        simulationRequirement,
        fileCount: manifest.files.length,
        createdAt: manifest.createdAt,
      }
    }, 201)
  }

  const pendingDownloadMatch = path.match(/^\/pending\/([^/]+)\/(\d+)$/)
  if (pendingDownloadMatch && request.method === 'GET') {
    const pendingToken = decodeURIComponent(pendingDownloadMatch[1])
    const fileIndex = Number(pendingDownloadMatch[2])
    const manifest = await readPendingManifest(env, user.id, pendingToken)
    if (!manifest) {
      return json({ error: '임시 업로드를 찾을 수 없습니다.' }, 404)
    }

    const fileRecord = manifest.files?.find((entry) => Number(entry.index) === fileIndex)
    if (!fileRecord?.key) {
      return json({ error: '임시 파일을 찾을 수 없습니다.' }, 404)
    }

    const obj = await env.STORAGE.get(fileRecord.key)
    if (!obj) {
      return json({ error: '임시 파일이 저장소에 없습니다.' }, 404)
    }

    return new Response(obj.body, {
      headers: {
        'Content-Type': obj.httpMetadata?.contentType || fileRecord.type || 'application/octet-stream',
        'Content-Disposition': `attachment; filename="${fileRecord.name}"`,
      },
    })
  }

  const pendingManifestMatch = path.match(/^\/pending\/([^/]+)$/)
  if (pendingManifestMatch && request.method === 'GET') {
    const pendingToken = decodeURIComponent(pendingManifestMatch[1])
    const manifest = await readPendingManifest(env, user.id, pendingToken)
    if (!manifest) {
      return json({ error: '임시 업로드를 찾을 수 없습니다.' }, 404)
    }

    return json({
      pendingUpload: {
        token: manifest.token,
        simulationRequirement: manifest.simulationRequirement || '',
        createdAt: manifest.createdAt || null,
        files: (manifest.files || []).map(({ index, name, size, type }) => ({
          index,
          name,
          size,
          type,
        })),
      }
    })
  }

  if (pendingManifestMatch && request.method === 'DELETE') {
    const pendingToken = decodeURIComponent(pendingManifestMatch[1])
    await deletePendingManifest(env, user.id, pendingToken)
    return json({ success: true })
  }

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

function getPendingManifestKey(userId, pendingToken) {
  return `${userId}/pending/${pendingToken}/manifest.json`
}

export async function readPendingManifest(env, userId, pendingToken) {
  const obj = await env.STORAGE.get(getPendingManifestKey(userId, pendingToken))
  if (!obj) return null

  try {
    return JSON.parse(await obj.text())
  } catch {
    return null
  }
}

export async function deletePendingManifest(env, userId, pendingToken) {
  const manifest = await readPendingManifest(env, userId, pendingToken)
  if (manifest?.files?.length) {
    await Promise.allSettled(
      manifest.files
        .map((file) => file?.key)
        .filter(Boolean)
        .map((key) => env.STORAGE.delete(key))
    )
  }
  await env.STORAGE.delete(getPendingManifestKey(userId, pendingToken))
}

export async function loadPendingUploadFiles(env, userId, pendingToken) {
  const manifest = await readPendingManifest(env, userId, pendingToken)
  if (!manifest?.files?.length) {
    return { manifest: null, files: [] }
  }

  const files = []
  for (const fileRecord of manifest.files) {
    if (!fileRecord?.key) continue
    const obj = await env.STORAGE.get(fileRecord.key)
    if (!obj) continue
    const bytes = await obj.arrayBuffer()
    files.push({
      index: Number(fileRecord.index ?? files.length),
      name: fileRecord.name,
      type: obj.httpMetadata?.contentType || fileRecord.type || 'application/octet-stream',
      size: fileRecord.size || bytes.byteLength || 0,
      bytes,
    })
  }

  return { manifest, files }
}
