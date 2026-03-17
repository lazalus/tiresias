import { json, getUser } from './utils.js'

export async function handleAdmin(request, env, url) {
  const user = await getUser(request, env)
  if (!user || user.role !== 'admin') {
    return json({ error: 'Forbidden' }, 403)
  }

  const path = url.pathname.replace('/api/admin', '')

  // List all users
  if (path === '/users' && request.method === 'GET') {
    const users = await env.DB.prepare(
      'SELECT id, name, email, role, credits, created_at FROM users ORDER BY created_at DESC'
    ).all()
    return json({ users: users.results })
  }

  // Approve user (pending → user)
  if (path.match(/^\/users\/[^/]+\/approve$/) && request.method === 'POST') {
    const userId = path.split('/')[2]
    await env.DB.prepare('UPDATE users SET role = ? WHERE id = ?').bind('user', userId).run()
    return json({ success: true })
  }

  // Reject/delete user
  if (path.match(/^\/users\/[^/]+\/reject$/) && request.method === 'POST') {
    const userId = path.split('/')[2]
    await env.DB.prepare('DELETE FROM users WHERE id = ?').bind(userId).run()
    return json({ success: true })
  }

  // Grant credits to user
  if (path.match(/^\/users\/[^/]+\/credits$/) && request.method === 'POST') {
    const userId = path.split('/')[2]
    const { amount, description } = await request.json()
    await env.DB.prepare('UPDATE users SET credits = credits + ? WHERE id = ?').bind(amount, userId).run()
    const txId = crypto.randomUUID()
    await env.DB.prepare(
      'INSERT INTO credit_transactions (id, user_id, amount, type, description, created_at) VALUES (?, ?, ?, ?, ?, ?)'
    ).bind(txId, userId, amount, 'admin_grant', description || '관리자 지급', new Date().toISOString()).run()
    return json({ success: true })
  }

  // Set user as admin
  if (path.match(/^\/users\/[^/]+\/set-admin$/) && request.method === 'POST') {
    const userId = path.split('/')[2]
    await env.DB.prepare('UPDATE users SET role = ? WHERE id = ?').bind('admin', userId).run()
    return json({ success: true })
  }

  // List credit plans
  if (path === '/plans' && request.method === 'GET') {
    const plans = await env.DB.prepare('SELECT * FROM credit_plans WHERE active = 1').all()
    return json({ plans: plans.results })
  }

  // Dashboard stats
  if (path === '/stats' && request.method === 'GET') {
    const totalUsers = await env.DB.prepare('SELECT COUNT(*) as count FROM users').first()
    const pendingUsers = await env.DB.prepare("SELECT COUNT(*) as count FROM users WHERE role = 'pending'").first()
    const totalProjects = await env.DB.prepare('SELECT COUNT(*) as count FROM projects').first()
    const totalRevenue = await env.DB.prepare("SELECT COALESCE(SUM(amount * 10000), 0) as total FROM credit_transactions WHERE type = 'purchase'").first()
    return json({
      totalUsers: totalUsers.count,
      pendingUsers: pendingUsers.count,
      totalProjects: totalProjects.count,
      totalRevenue: totalRevenue.total
    })
  }

  return json({ error: 'Not Found' }, 404)
}
