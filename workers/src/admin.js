import { json, getUser, hashPassword } from './utils.js'
import { getSearchConsoleDiagnostics } from './searchConsole.js'

const OPENAI_COST_CACHE_STALE_MS = 15 * 60 * 1000
const OPENAI_COST_REFRESH_LOCK_MS = 2 * 60 * 1000

function buildBaseUrl(env) {
  return String(env.AUTH_BASE_URL || 'https://tiresiasview.com')
    .trim()
    .replace(/\/+$/, '')
}

function generateTemporaryPassword(length = 12) {
  const alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789!@#$%^*'
  const random = crypto.getRandomValues(new Uint8Array(length))
  let value = ''
  for (let i = 0; i < length; i += 1) {
    value += alphabet[random[i] % alphabet.length]
  }
  return value
}

function buildPasswordResetEmail(env, { email, name, temporaryPassword }) {
  const baseUrl = buildBaseUrl(env)
  const fromName = String(env.RESEND_FROM_NAME || 'Tiresias View').trim() || 'Tiresias View'
  const supportEmail = String(env.SUPPORT_EMAIL || 'support@tiresiasview.com').trim() || 'support@tiresiasview.com'
  const displayName = String(name || '').trim() || email
  const loginUrl = `${baseUrl}/login`

  return {
    from: `${fromName} <${env.RESEND_FROM_EMAIL}>`,
    to: [email],
    subject: `[${fromName}] 비밀번호가 관리자에 의해 초기화되었습니다`,
    html: `
      <div style="margin:0;padding:32px 20px;background:#f5f7fb;font-family:'Apple SD Gothic Neo','Noto Sans KR','Malgun Gothic',sans-serif;color:#172033;">
        <div style="max-width:560px;margin:0 auto;background:#ffffff;border:1px solid #d8e0ee;border-radius:18px;overflow:hidden;">
          <div style="padding:28px 28px 18px;border-bottom:1px solid #e5ebf5;background:linear-gradient(180deg,#fbfdff 0%,#f3f7ff 100%);">
            <div style="font-size:12px;font-weight:700;letter-spacing:0.12em;color:#51607a;">TIRESIAS VIEW</div>
            <h1 style="margin:14px 0 8px;font-size:28px;line-height:1.3;color:#203963;">임시 비밀번호가 발급되었습니다</h1>
            <p style="margin:0;font-size:14px;line-height:1.7;color:#4e5b72;">${displayName}님 계정의 비밀번호가 관리자에 의해 초기화되었습니다. 아래 임시 비밀번호로 로그인한 뒤, 바로 새 비밀번호로 변경해주세요.</p>
          </div>
          <div style="padding:24px 28px;">
            <div style="margin-bottom:18px;padding:16px 18px;border:1px solid #d8e0ee;border-radius:12px;background:#fbfcff;font-size:14px;line-height:1.8;color:#334155;">
              임시 비밀번호<br/>
              <strong style="display:inline-block;margin-top:6px;font-size:18px;letter-spacing:0.04em;color:#203963;">${temporaryPassword}</strong>
            </div>
            <div style="text-align:center;margin:22px 0 24px;">
              <a href="${loginUrl}" style="display:inline-block;padding:12px 20px;border-radius:10px;background:#2d4c88;color:#ffffff;text-decoration:none;font-size:14px;font-weight:700;">로그인하고 비밀번호 변경</a>
            </div>
            <div style="font-size:12px;line-height:1.8;color:#667085;word-break:break-all;margin-bottom:18px;">
              로그인 후에는 비밀번호 변경 화면이 자동으로 열립니다.<br/>
              로그인 주소: <a href="${loginUrl}" style="color:#2d4c88;text-decoration:none;">${loginUrl}</a>
            </div>
            <div style="font-size:12px;line-height:1.8;color:#667085;border-top:1px solid #e5ebf5;padding-top:16px;">
              이용약관: <a href="${baseUrl}/terms" style="color:#2d4c88;text-decoration:none;">${baseUrl}/terms</a><br/>
              개인정보처리방침: <a href="${baseUrl}/privacy" style="color:#2d4c88;text-decoration:none;">${baseUrl}/privacy</a><br/>
              문의: <a href="mailto:${supportEmail}" style="color:#2d4c88;text-decoration:none;">${supportEmail}</a>
            </div>
          </div>
        </div>
      </div>
    `.trim(),
    text: [
      `${displayName}님 계정의 비밀번호가 관리자에 의해 초기화되었습니다.`,
      '',
      `임시 비밀번호: ${temporaryPassword}`,
      '',
      `로그인 후 바로 새 비밀번호로 변경해주세요: ${loginUrl}`,
      `이용약관: ${baseUrl}/terms`,
      `개인정보처리방침: ${baseUrl}/privacy`,
      `문의: ${supportEmail}`,
    ].join('\n'),
  }
}

async function sendPasswordResetEmail(env, payload) {
  if (!env.RESEND_API_KEY || !env.RESEND_FROM_EMAIL) {
    throw new Error('RESEND_API_KEY 또는 RESEND_FROM_EMAIL이 설정되지 않았습니다.')
  }

  const response = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${env.RESEND_API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(buildPasswordResetEmail(env, payload)),
  })

  if (!response.ok) {
    const body = await response.text().catch(() => '')
    throw new Error(`Resend password reset email failed (${response.status}): ${body.slice(0, 300)}`)
  }
}

async function resetUserPassword(env, userRow) {
  const currentRow = await env.DB.prepare(
    'SELECT password_hash, must_change_password FROM users WHERE id = ? LIMIT 1'
  ).bind(userRow.id).first()
  const temporaryPassword = generateTemporaryPassword()
  const passwordHash = await hashPassword(temporaryPassword)

  await env.DB.prepare(
    'UPDATE users SET password_hash = ?, must_change_password = 1 WHERE id = ?'
  ).bind(passwordHash, userRow.id).run()

  try {
    await sendPasswordResetEmail(env, {
      email: userRow.email,
      name: userRow.name,
      temporaryPassword,
    })
  } catch (error) {
    if (currentRow?.password_hash) {
      await env.DB.prepare(
        'UPDATE users SET password_hash = ?, must_change_password = ? WHERE id = ?'
      ).bind(
        currentRow.password_hash,
        Number(currentRow.must_change_password || 0),
        userRow.id,
      ).run()
    }
    throw error
  }

  return { success: true, email: userRow.email }
}

function clampCostDays(value) {
  return Math.max(1, Math.min(Number(value) || 30, 90))
}

function buildOpenAiCostCacheKey(days) {
  return `openai_costs:${days}`
}

function buildCacheResponse(row) {
  if (!row?.payload) return null

  try {
    const payload = JSON.parse(row.payload)
    return {
      ...payload,
      fetched_at: row.fetched_at || null,
      cached: true,
      last_error: row.last_error || null,
    }
  } catch {
    return null
  }
}

function isCacheStale(fetchedAt) {
  if (!fetchedAt) return true
  const fetched = new Date(fetchedAt).getTime()
  if (Number.isNaN(fetched)) return true
  return Date.now() - fetched >= OPENAI_COST_CACHE_STALE_MS
}

async function deleteUserData(env, userId) {
  const user = await env.DB.prepare(
    'SELECT id, email FROM users WHERE id = ?'
  ).bind(userId).first()

  if (!user) return { deleted: false, reason: 'not_found' }

  const files = await env.DB.prepare(
    'SELECT storage_key FROM files WHERE user_id = ?'
  ).bind(userId).all()

  const reports = await env.DB.prepare(
    'SELECT id, content, refined_key, pdf_key FROM reports WHERE user_id = ?'
  ).bind(userId).all()

  const storageDeletes = []

  for (const file of files.results || []) {
    if (file?.storage_key) storageDeletes.push(env.STORAGE.delete(file.storage_key))
  }

  for (const report of reports.results || []) {
    const baseKey = report.refined_key || report.content || `reports/${userId}/${report.id}.json`
    if (baseKey) storageDeletes.push(env.STORAGE.delete(baseKey))
    if (report.refined_key && report.refined_key !== baseKey) {
      storageDeletes.push(env.STORAGE.delete(report.refined_key))
    }
    storageDeletes.push(env.STORAGE.delete(report.pdf_key || `pdfs/${report.id}.pdf`))
  }

  await Promise.allSettled(storageDeletes)

  const statements = [
    env.DB.prepare('DELETE FROM files WHERE user_id = ?').bind(userId),
    env.DB.prepare('DELETE FROM reports WHERE user_id = ?').bind(userId),
    env.DB.prepare('DELETE FROM simulations WHERE user_id = ?').bind(userId),
    env.DB.prepare('DELETE FROM credit_transactions WHERE user_id = ?').bind(userId),
    env.DB.prepare('DELETE FROM payment_orders WHERE user_id = ?').bind(userId),
    env.DB.prepare('DELETE FROM job_queue WHERE user_id = ?').bind(userId),
    env.DB.prepare('DELETE FROM projects WHERE user_id = ?').bind(userId),
    env.DB.prepare('DELETE FROM page_views WHERE user_id = ?').bind(userId),
    env.DB.prepare('DELETE FROM signup_verifications WHERE email = ?').bind(user.email),
    env.DB.prepare('DELETE FROM users WHERE id = ?').bind(userId),
  ]

  await env.DB.batch(statements)
  return { deleted: true }
}

async function readOpenAiCostCache(env, days) {
  const row = await env.DB.prepare(
    `SELECT payload, fetched_at, refresh_started_at, last_error
     FROM openai_cost_cache
     WHERE cache_key = ?`
  ).bind(buildOpenAiCostCacheKey(days)).first()

  return row ? { row, payload: buildCacheResponse(row) } : { row: null, payload: null }
}

async function fetchOpenAiCostsFromBackend(env, days) {
  const backendUrl = env.SIMULATION_API || 'http://localhost:5001'
  const target = new URL(`/api/admin/openai-costs?days=${encodeURIComponent(days)}`, backendUrl)
  const res = await fetch(target.toString(), {
    headers: {
      'X-Internal-Key': env.INTERNAL_API_KEY,
      'X-OpenAI-Admin-Key': env.OPENAI_ADMIN_KEY || '',
    }
  })

  const data = await res.json()
  if (!res.ok) {
    throw new Error(data?.error || `OpenAI cost fetch failed (${res.status})`)
  }

  return {
    total_cost_usd: Number(data?.total_cost_usd || 0),
    total_cost_krw: Number(data?.total_cost_krw || 0),
    days,
    daily: Array.isArray(data?.daily) ? data.daily : [],
  }
}

async function persistOpenAiCostCache(env, days, payload) {
  const now = new Date().toISOString()
  await env.DB.prepare(
    `INSERT INTO openai_cost_cache (
       cache_key, days, payload, total_cost_usd, total_cost_krw,
       fetched_at, refresh_started_at, last_error, created_at, updated_at
     ) VALUES (?, ?, ?, ?, ?, ?, NULL, NULL, ?, ?)
     ON CONFLICT(cache_key) DO UPDATE SET
       payload = excluded.payload,
       total_cost_usd = excluded.total_cost_usd,
       total_cost_krw = excluded.total_cost_krw,
       fetched_at = excluded.fetched_at,
       refresh_started_at = NULL,
       last_error = NULL,
       updated_at = excluded.updated_at`
  ).bind(
    buildOpenAiCostCacheKey(days),
    days,
    JSON.stringify(payload),
    Number(payload.total_cost_usd || 0),
    Number(payload.total_cost_krw || 0),
    now,
    now,
    now,
  ).run()

  return {
    ...payload,
    fetched_at: now,
    cached: true,
    last_error: null,
  }
}

async function markOpenAiCostRefreshStarted(env, days) {
  const cacheKey = buildOpenAiCostCacheKey(days)
  const now = new Date().toISOString()
  const existing = await env.DB.prepare(
    `SELECT refresh_started_at
     FROM openai_cost_cache
     WHERE cache_key = ?`
  ).bind(cacheKey).first()

  if (existing?.refresh_started_at) {
    const lastRefresh = new Date(existing.refresh_started_at).getTime()
    if (!Number.isNaN(lastRefresh) && (Date.now() - lastRefresh) < OPENAI_COST_REFRESH_LOCK_MS) {
      return false
    }
  }

  await env.DB.prepare(
    `INSERT INTO openai_cost_cache (
       cache_key, days, payload, total_cost_usd, total_cost_krw,
       fetched_at, refresh_started_at, last_error, created_at, updated_at
     ) VALUES (?, ?, NULL, 0, 0, NULL, ?, NULL, ?, ?)
     ON CONFLICT(cache_key) DO UPDATE SET
       refresh_started_at = excluded.refresh_started_at,
       updated_at = excluded.updated_at`
  ).bind(cacheKey, days, now, now, now).run()

  return true
}

async function markOpenAiCostRefreshFailed(env, days, errorMessage) {
  const now = new Date().toISOString()
  await env.DB.prepare(
    `UPDATE openai_cost_cache
     SET refresh_started_at = NULL,
         last_error = ?,
         updated_at = ?
     WHERE cache_key = ?`
  ).bind(
    String(errorMessage || 'unknown error').slice(0, 500),
    now,
    buildOpenAiCostCacheKey(days),
  ).run()
}

async function refreshOpenAiCostCache(env, days) {
  const claimed = await markOpenAiCostRefreshStarted(env, days)
  if (!claimed) return null

  try {
    const payload = await fetchOpenAiCostsFromBackend(env, days)
    return await persistOpenAiCostCache(env, days, payload)
  } catch (error) {
    await markOpenAiCostRefreshFailed(env, days, error?.message || String(error))
    throw error
  }
}

export async function handleAdmin(request, env, url, ctx) {
  const path = url.pathname.replace('/api/admin', '')

  if (path === '/internal/reset-password' && request.method === 'POST') {
    const internalKey = request.headers.get('X-Internal-Key')
    if (!env.INTERNAL_API_KEY || internalKey !== env.INTERNAL_API_KEY) {
      return json({ error: 'Forbidden' }, 403)
    }

    const { email } = await request.json()
    const normalizedEmail = String(email || '').trim().toLowerCase()
    if (!normalizedEmail) {
      return json({ error: '이메일이 필요합니다.' }, 400)
    }

    const userRow = await env.DB.prepare(
      'SELECT id, name, email FROM users WHERE email = ? LIMIT 1'
    ).bind(normalizedEmail).first()

    if (!userRow) {
      return json({ error: 'User not found' }, 404)
    }

    await resetUserPassword(env, userRow)
    return json({ success: true, email: userRow.email })
  }

  const user = await getUser(request, env)
  if (!user || user.role !== 'admin') {
    return json({ error: 'Forbidden' }, 403)
  }

  // List all users
  if (path === '/users' && request.method === 'GET') {
    const users = await env.DB.prepare(
      'SELECT id, name, email, role, must_change_password, created_at FROM users ORDER BY created_at DESC'
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
    try {
      const result = await deleteUserData(env, userId)
      if (!result.deleted && result.reason === 'not_found') {
        return json({ error: 'User not found' }, 404)
      }
      return json({ success: true })
    } catch (error) {
      return json({ error: error instanceof Error ? error.message : 'User delete failed' }, 500)
    }
  }

  // Set user as admin
  if (path.match(/^\/users\/[^/]+\/set-admin$/) && request.method === 'POST') {
    const userId = path.split('/')[2]
    await env.DB.prepare('UPDATE users SET role = ? WHERE id = ?').bind('admin', userId).run()
    return json({ success: true })
  }

  // Set admin back to user
  if (path.match(/^\/users\/[^/]+\/set-user$/) && request.method === 'POST') {
    const userId = path.split('/')[2]
    await env.DB.prepare('UPDATE users SET role = ? WHERE id = ?').bind('user', userId).run()
    return json({ success: true })
  }

  if (path.match(/^\/users\/[^/]+\/reset-password$/) && request.method === 'POST') {
    const userId = path.split('/')[2]
    const userRow = await env.DB.prepare(
      'SELECT id, name, email FROM users WHERE id = ? LIMIT 1'
    ).bind(userId).first()

    if (!userRow) {
      return json({ error: 'User not found' }, 404)
    }

    try {
      await resetUserPassword(env, userRow)
      return json({ success: true, email: userRow.email })
    } catch (error) {
      return json({ error: error instanceof Error ? error.message : 'Password reset failed' }, 500)
    }
  }

  // Visit stats (KST 기준)
  if (path === '/visits' && request.method === 'GET') {
    const todayKST = new Date(Date.now() + 9 * 60 * 60 * 1000).toISOString().slice(0, 10)
    const monthStartKST = todayKST.slice(0, 7) + '-01'
    const weekAgoKST = new Date(Date.now() + 9 * 60 * 60 * 1000 - 6 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10)

    const todayVisits = await env.DB.prepare(
      "SELECT COUNT(*) as count FROM page_views WHERE created_at >= ?"
    ).bind(todayKST).first()
    const todayUnique = await env.DB.prepare(
      "SELECT COUNT(DISTINCT ip) as count FROM page_views WHERE created_at >= ?"
    ).bind(todayKST).first()
    const monthlyVisits = await env.DB.prepare(
      "SELECT COUNT(*) as count FROM page_views WHERE created_at >= ?"
    ).bind(monthStartKST).first()
    const monthlyUnique = await env.DB.prepare(
      "SELECT COUNT(DISTINCT ip) as count FROM page_views WHERE created_at >= ?"
    ).bind(monthStartKST).first()
    const daily = await env.DB.prepare(
      "SELECT date(created_at) as day, COUNT(*) as views, COUNT(DISTINCT ip) as unique_views FROM page_views WHERE created_at >= ? GROUP BY date(created_at) ORDER BY day"
    ).bind(weekAgoKST).all()

    return json({
      todayVisits: todayVisits.count,
      todayUnique: todayUnique.count,
      monthlyVisits: monthlyVisits.count,
      monthlyUnique: monthlyUnique.count,
      daily: daily.results
    })
  }

  // Dashboard stats (enhanced)
  if (path === '/stats' && request.method === 'GET') {
    const totalUsers = await env.DB.prepare('SELECT COUNT(*) as count FROM users').first()
    const pendingUsers = await env.DB.prepare("SELECT COUNT(*) as count FROM users WHERE role = 'pending'").first()
    const todaySignups = await env.DB.prepare("SELECT COUNT(*) as count FROM users WHERE created_at >= date('now')").first()
    const todayRevenue = await env.DB.prepare(
      `SELECT COALESCE(COUNT(*), 0) as count, COALESCE(SUM(amount), 0) as total
       FROM payment_orders
       WHERE order_type IN ('simulation', 'pdf_download')
         AND status IN ('confirmed', 'processing', 'consumed')
         AND payment_key IS NOT NULL
         AND COALESCE(confirmed_at, created_at) >= date('now')`
    ).first()
    const monthlyRevenue = await env.DB.prepare(
      `SELECT COALESCE(COUNT(*), 0) as count, COALESCE(SUM(amount), 0) as total
       FROM payment_orders
       WHERE order_type IN ('simulation', 'pdf_download')
         AND status IN ('confirmed', 'processing', 'consumed')
         AND payment_key IS NOT NULL
         AND COALESCE(confirmed_at, created_at) >= date('now', 'start of month')`
    ).first()
    const totalProjects = await env.DB.prepare('SELECT COUNT(*) as count FROM projects').first()
    const monthlySimulations = await env.DB.prepare(
      `SELECT COUNT(*) as count
       FROM payment_orders
       WHERE order_type = 'simulation'
         AND status IN ('confirmed', 'processing', 'consumed')
         AND payment_key IS NOT NULL
         AND COALESCE(confirmed_at, created_at) >= date('now', 'start of month')`
    ).first()

    return json({
      totalUsers: totalUsers.count,
      pendingUsers: pendingUsers.count,
      todaySignups: todaySignups.count,
      todayRevenue: todayRevenue.total,
      monthlyRevenue: monthlyRevenue.total,
      todayPurchases: todayRevenue.count,
      monthlyPurchases: monthlyRevenue.count,
      totalProjects: totalProjects.count,
      monthlySimulations: monthlySimulations.count
    })
  }

  // 전체 보고서 목록 (어드민)
  if (path === '/reports' && request.method === 'GET') {
    const reports = await env.DB.prepare(
      'SELECT r.id, r.title, r.summary, r.status, r.is_sample, r.refined_key, r.user_id, r.created_at, u.name as user_name FROM reports r LEFT JOIN users u ON r.user_id = u.id ORDER BY r.created_at DESC'
    ).all()
    return json({ reports: reports.results })
  }

  // 보고서 삭제
  const deleteMatch = path.match(/^\/reports\/([^/]+)\/delete$/)
  if (deleteMatch && request.method === 'POST') {
    const reportId = deleteMatch[1]
    await env.DB.prepare('DELETE FROM reports WHERE id = ?').bind(reportId).run()
    return json({ success: true })
  }

  // 매출 일별 로그
  if (path === '/revenue-daily' && request.method === 'GET') {
    const days = Number(url.searchParams.get('days') || 30)
    const daily = await env.DB.prepare(
      `SELECT date(COALESCE(confirmed_at, created_at)) as date, COUNT(*) as count, SUM(amount) as total
       FROM payment_orders
       WHERE order_type IN ('simulation', 'pdf_download')
         AND status IN ('confirmed', 'processing', 'consumed')
         AND payment_key IS NOT NULL
         AND COALESCE(confirmed_at, created_at) >= date('now', '-' || ? || ' days')
       GROUP BY date(COALESCE(confirmed_at, created_at))
       ORDER BY date DESC`
    ).bind(days).all()
    return json({ daily: daily.results })
  }

  // OpenAI API 비용 통계
  if (path === '/openai-costs' && request.method === 'GET') {
    const days = clampCostDays(url.searchParams.get('days'))

    try {
      const cached = await readOpenAiCostCache(env, days)
      const hasCachedPayload = Boolean(cached.payload)
      const stale = isCacheStale(cached.row?.fetched_at)

      if (hasCachedPayload) {
        if (stale && ctx?.waitUntil) {
          ctx.waitUntil(refreshOpenAiCostCache(env, days).catch((error) => {
            console.warn('OpenAI 비용 캐시 갱신 실패:', error?.message || error)
          }))
        }

        return json({
          ...cached.payload,
          stale,
        })
      }

      const fresh = await refreshOpenAiCostCache(env, days)
      return json({
        ...(fresh || {
          total_cost_usd: 0,
          total_cost_krw: 0,
          days,
          daily: [],
          fetched_at: null,
          cached: true,
          stale: false,
          last_error: null,
        }),
        stale: false,
      })
    } catch (e) {
      return json({ error: e.message }, 500)
    }
  }

  // Google Search Console 진단
  if (path === '/search-console' && request.method === 'GET') {
    const days = Number(url.searchParams.get('days') || 28)
    try {
      const diagnostics = await getSearchConsoleDiagnostics(env, ctx, days)
      return json(diagnostics)
    } catch (error) {
      return json({ error: error instanceof Error ? error.message : 'Search Console fetch failed' }, 500)
    }
  }

  return json({ error: 'Not Found' }, 404)
}
