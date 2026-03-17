import { json, hashPassword, createJWT } from './utils.js'

export async function handleAuth(request, env, url) {
  const path = url.pathname.replace('/api/auth', '')

  if (path === '/signup' && request.method === 'POST') {
    const { name, email, password } = await request.json()
    if (!name || !email || !password || password.length < 6) {
      return json({ error: '모든 필드를 올바르게 입력해주세요.' }, 400)
    }

    const existing = await env.DB.prepare('SELECT id FROM users WHERE email = ?').bind(email).first()
    if (existing) {
      return json({ error: '이미 등록된 이메일입니다.' }, 409)
    }

    const id = crypto.randomUUID()
    const passwordHash = await hashPassword(password)
    await env.DB.prepare(
      'INSERT INTO users (id, name, email, password_hash, role, credits, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)'
    ).bind(id, name, email, passwordHash, 'user', 0, new Date().toISOString()).run()

    const token = await createJWT(
      { id, email, name, role: 'user', credits: 0 },
      env.JWT_SECRET
    )
    return json({ user: { id, name, email, role: 'user', credits: 0 }, token })
  }

  if (path === '/login' && request.method === 'POST') {
    const { email, password } = await request.json()
    if (!email || !password) {
      return json({ error: '이메일과 비밀번호를 입력해주세요.' }, 400)
    }

    const passwordHash = await hashPassword(password)
    const user = await env.DB.prepare(
      'SELECT id, name, email, role, credits FROM users WHERE email = ? AND password_hash = ?'
    ).bind(email, passwordHash).first()

    if (!user) {
      return json({ error: '이메일 또는 비밀번호가 올바르지 않습니다.' }, 401)
    }

    const token = await createJWT(
      { id: user.id, email: user.email, name: user.name, role: user.role, credits: user.credits },
      env.JWT_SECRET
    )
    return json({ user: { id: user.id, name: user.name, email: user.email, role: user.role, credits: user.credits }, token })
  }

  if (path === '/me' && request.method === 'GET') {
    const auth = request.headers.get('Authorization')
    if (!auth) return json({ error: 'Unauthorized' }, 401)
    const { verifyJWT } = await import('./utils.js')
    try {
      const payload = await verifyJWT(auth.replace('Bearer ', ''), env.JWT_SECRET)
      const user = await env.DB.prepare('SELECT id, name, email, role, credits, created_at FROM users WHERE id = ?').bind(payload.id).first()
      return json({ user })
    } catch {
      return json({ error: 'Invalid token' }, 401)
    }
  }

  return json({ error: 'Not Found' }, 404)
}
