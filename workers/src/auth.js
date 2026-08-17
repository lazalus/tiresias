import {
  json,
  hashPassword,
  createJWT,
  verifyPassword,
  needsPasswordRehash,
  assertConfiguredSecret,
  verifyJWT,
  getUser,
  buildSessionCookie,
  clearSessionCookie,
} from './utils.js'

const AUTH_WINDOW_MS = 10 * 60 * 1000
const AUTH_BLOCK_MS = 15 * 60 * 1000
const LOGIN_IP_LIMIT = 12
const LOGIN_EMAIL_LIMIT = 8
const SIGNUP_IP_LIMIT = 8
const SIGNUP_EMAIL_LIMIT = 4

function normalizeEmail(value) {
  return String(value || '').trim().toLowerCase()
}

function getClientIp(request) {
  return String(
    request.headers.get('cf-connecting-ip')
    || request.headers.get('x-forwarded-for')
    || ''
  ).split(',')[0].trim()
}

function buildBaseUrl(env) {
  return String(env.AUTH_BASE_URL || 'https://tiresiasview.com')
    .trim()
    .replace(/\/+$/, '')
}

function getSignupVerificationSecret(env) {
  return assertConfiguredSecret(
    env.AUTH_SIGNUP_VERIFICATION_SECRET || env.JWT_SECRET,
    'AUTH_SIGNUP_VERIFICATION_SECRET'
  )
}

function getSignupVerificationTtlMs(env) {
  const hours = Number(env.AUTH_SIGNUP_VERIFICATION_TTL_HOURS || 24)
  return Math.max(1, Math.min(hours, 168)) * 60 * 60 * 1000
}

function buildSignupVerificationEmail(env, { name, email, token }) {
  const baseUrl = buildBaseUrl(env)
  const verifyUrl = `${baseUrl}/signup/verify?token=${encodeURIComponent(token)}`
  const fromName = String(env.RESEND_FROM_NAME || 'Tiresias View').trim() || 'Tiresias View'
  const supportEmail = String(env.SUPPORT_EMAIL || 'support@tiresiasview.com').trim() || 'support@tiresiasview.com'
  const displayName = String(name || '').trim() || email

  return {
    from: `${fromName} <${env.RESEND_FROM_EMAIL}>`,
    to: [email],
    subject: `[${fromName}] 회원가입 이메일 인증`,
    html: `
      <div style="margin:0;padding:32px 20px;background:#f5f7fb;font-family:'Apple SD Gothic Neo','Noto Sans KR','Malgun Gothic',sans-serif;color:#172033;">
        <div style="max-width:560px;margin:0 auto;background:#ffffff;border:1px solid #d8e0ee;border-radius:18px;overflow:hidden;">
          <div style="padding:28px 28px 18px;border-bottom:1px solid #e5ebf5;background:linear-gradient(180deg,#fbfdff 0%,#f3f7ff 100%);">
            <div style="font-size:12px;font-weight:700;letter-spacing:0.12em;color:#51607a;">TIRESIAS VIEW</div>
            <h1 style="margin:14px 0 8px;font-size:28px;line-height:1.3;color:#203963;">이메일 인증을 완료해주세요</h1>
            <p style="margin:0;font-size:14px;line-height:1.7;color:#4e5b72;">${displayName}님, 회원가입을 완료하려면 아래 버튼을 눌러 이메일 인증을 진행해주세요. 인증이 끝나야 실제 계정이 생성됩니다.</p>
          </div>
          <div style="padding:24px 28px;">
            <div style="margin-bottom:18px;padding:16px 18px;border:1px solid #d8e0ee;border-radius:12px;background:#fbfcff;font-size:14px;line-height:1.8;color:#334155;">
              인증 링크는 24시간 동안 유효합니다.<br/>
              본인이 요청하지 않았다면 이 메일은 무시하셔도 됩니다.
            </div>
            <div style="text-align:center;margin:22px 0 24px;">
              <a href="${verifyUrl}" style="display:inline-block;padding:12px 20px;border-radius:10px;background:#2d4c88;color:#ffffff;text-decoration:none;font-size:14px;font-weight:700;">이메일 인증 완료</a>
            </div>
            <div style="font-size:12px;line-height:1.8;color:#667085;word-break:break-all;margin-bottom:18px;">
              버튼이 동작하지 않으면 아래 링크를 직접 열어주세요.<br/>
              <a href="${verifyUrl}" style="color:#2d4c88;text-decoration:none;">${verifyUrl}</a>
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
      `${displayName}님, Tiresias View 회원가입을 완료하려면 이메일 인증이 필요합니다.`,
      '',
      `인증 링크: ${verifyUrl}`,
      '',
      `이용약관: ${baseUrl}/terms`,
      `개인정보처리방침: ${baseUrl}/privacy`,
      `문의: ${supportEmail}`,
    ].join('\n'),
  }
}

async function sendSignupVerificationEmail(env, payload) {
  if (!env.RESEND_API_KEY || !env.RESEND_FROM_EMAIL) {
    throw new Error('RESEND_API_KEY 또는 RESEND_FROM_EMAIL이 설정되지 않았습니다.')
  }

  const response = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${env.RESEND_API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(buildSignupVerificationEmail(env, payload)),
  })

  if (!response.ok) {
    const body = await response.text().catch(() => '')
    throw new Error(`Resend signup email failed (${response.status}): ${body.slice(0, 300)}`)
  }
}

async function findPendingSignupByEmail(env, email) {
  return env.DB.prepare(
    `SELECT id, email, name, password_hash, expires_at, consumed_at, created_at, updated_at
     FROM signup_verifications
     WHERE email = ?
     LIMIT 1`
  ).bind(email).first()
}

async function upsertPendingSignup(env, payload) {
  await env.DB.prepare(
    `INSERT INTO signup_verifications (
       id, email, name, password_hash, expires_at, consumed_at, created_at, updated_at
     ) VALUES (?, ?, ?, ?, ?, NULL, ?, ?)
     ON CONFLICT(email) DO UPDATE SET
       id = excluded.id,
       name = excluded.name,
       password_hash = excluded.password_hash,
       expires_at = excluded.expires_at,
       consumed_at = NULL,
       updated_at = excluded.updated_at`
  ).bind(
    payload.id,
    payload.email,
    payload.name,
    payload.passwordHash,
    payload.expiresAt,
    payload.createdAt,
    payload.updatedAt,
  ).run()
}

function isExpired(isoText) {
  const expiresAt = new Date(isoText).getTime()
  return Number.isNaN(expiresAt) || expiresAt < Date.now()
}

async function completeSignupVerification(env, signupRow) {
  const existingUser = await env.DB.prepare(
    'SELECT id, name, email, role, credits, must_change_password FROM users WHERE email = ? LIMIT 1'
  ).bind(signupRow.email).first()

  if (existingUser) {
    return { alreadyVerified: true, user: existingUser }
  }

  const userId = crypto.randomUUID()
  await env.DB.prepare(
    `INSERT INTO users (id, name, email, password_hash, must_change_password, role, credits, created_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?)`
  ).bind(
    userId,
    signupRow.name,
    signupRow.email,
    signupRow.password_hash,
    0,
    'user',
    0,
    new Date().toISOString(),
  ).run()

  await env.DB.prepare(
    `UPDATE signup_verifications
     SET consumed_at = ?, updated_at = ?
     WHERE email = ? AND id = ?`
  ).bind(
    new Date().toISOString(),
    new Date().toISOString(),
    signupRow.email,
    signupRow.id,
  ).run()

  return {
    alreadyVerified: false,
    user: {
      id: userId,
      name: signupRow.name,
      email: signupRow.email,
      must_change_password: 0,
      role: 'user',
      credits: 0,
    },
  }
}

async function enforceAuthRateLimit(env, bucket, identifier, { limit, windowMs = AUTH_WINDOW_MS, blockMs = AUTH_BLOCK_MS }) {
  const normalizedIdentifier = String(identifier || '').trim().toLowerCase()
  if (!normalizedIdentifier) {
    return null
  }

  const key = `${bucket}:${normalizedIdentifier}`
  const now = Date.now()
  const nowIso = new Date(now).toISOString()
  const existing = await env.DB.prepare(
    `SELECT attempts, window_started_at, blocked_until
     FROM auth_rate_limits
     WHERE key = ?`
  ).bind(key).first()

  const blockedUntilMs = existing?.blocked_until ? new Date(existing.blocked_until).getTime() : 0
  if (blockedUntilMs && !Number.isNaN(blockedUntilMs) && blockedUntilMs > now) {
    return Math.ceil((blockedUntilMs - now) / 1000)
  }

  const windowStartedMs = existing?.window_started_at ? new Date(existing.window_started_at).getTime() : 0
  const inWindow = windowStartedMs && !Number.isNaN(windowStartedMs) && (now - windowStartedMs) < windowMs
  const attempts = (inWindow ? Number(existing?.attempts || 0) : 0) + 1
  const nextBlockedUntil = attempts > limit ? new Date(now + blockMs).toISOString() : null

  await env.DB.prepare(
    `INSERT INTO auth_rate_limits (key, bucket, attempts, window_started_at, blocked_until, created_at, updated_at)
     VALUES (?, ?, ?, ?, ?, ?, ?)
     ON CONFLICT(key) DO UPDATE SET
       attempts = excluded.attempts,
       window_started_at = excluded.window_started_at,
       blocked_until = excluded.blocked_until,
       updated_at = excluded.updated_at`
  ).bind(
    key,
    bucket,
    attempts,
    inWindow ? existing.window_started_at : nowIso,
    nextBlockedUntil,
    existing?.created_at || nowIso,
    nowIso,
  ).run()

  if (nextBlockedUntil) {
    return Math.ceil(blockMs / 1000)
  }

  return null
}

async function clearAuthRateLimit(env, bucket, identifier) {
  const normalizedIdentifier = String(identifier || '').trim().toLowerCase()
  if (!normalizedIdentifier) return
  const key = `${bucket}:${normalizedIdentifier}`
  await env.DB.prepare('DELETE FROM auth_rate_limits WHERE key = ?').bind(key).run()
}

export async function handleAuth(request, env, url) {
  assertConfiguredSecret(env.JWT_SECRET)
  const path = url.pathname.replace('/api/auth', '')

  if (path === '/signup' && request.method === 'POST') {
    const { name, email, password } = await request.json()
    const normalizedName = String(name || '').trim()
    const normalizedEmail = normalizeEmail(email)

    if (!normalizedName || !normalizedEmail || !password || password.length < 6) {
      return json({ error: '모든 필드를 올바르게 입력해주세요.' }, 400)
    }

    const signupIpRetryAfter = await enforceAuthRateLimit(env, 'signup_ip', getClientIp(request), { limit: SIGNUP_IP_LIMIT })
    if (signupIpRetryAfter) {
      return json({ error: '요청이 너무 많습니다. 잠시 후 다시 시도해주세요.' }, 429, {
        'Retry-After': String(signupIpRetryAfter),
      })
    }
    const signupEmailRetryAfter = await enforceAuthRateLimit(env, 'signup_email', normalizedEmail, { limit: SIGNUP_EMAIL_LIMIT })
    if (signupEmailRetryAfter) {
      return json({ error: '요청이 너무 많습니다. 잠시 후 다시 시도해주세요.' }, 429, {
        'Retry-After': String(signupEmailRetryAfter),
      })
    }

    const existingUser = await env.DB.prepare(
      'SELECT id FROM users WHERE email = ?'
    ).bind(normalizedEmail).first()
    if (existingUser) {
      return json({ error: '이미 등록된 이메일입니다.' }, 409)
    }

    const pendingId = crypto.randomUUID()
    const passwordHash = await hashPassword(password)
    const now = new Date().toISOString()
    const expiresAt = new Date(Date.now() + getSignupVerificationTtlMs(env)).toISOString()

    await upsertPendingSignup(env, {
      id: pendingId,
      email: normalizedEmail,
      name: normalizedName,
      passwordHash,
      expiresAt,
      createdAt: now,
      updatedAt: now,
    })

    const verificationToken = await createJWT(
      {
        type: 'signup_verification',
        signup_id: pendingId,
        email: normalizedEmail,
      },
      getSignupVerificationSecret(env),
      getSignupVerificationTtlMs(env)
    )

    await sendSignupVerificationEmail(env, {
      name: normalizedName,
      email: normalizedEmail,
      token: verificationToken,
    })

    return json({
      success: true,
      pending: true,
      email: normalizedEmail,
      message: '인증 메일을 보냈습니다. 링크를 눌러 회원가입을 완료해주세요.',
    })
  }

  if (path === '/signup/verify' && request.method === 'POST') {
    const { token } = await request.json()
    if (!token) {
      return json({ error: '인증 토큰이 필요합니다.' }, 400)
    }

    let payload
    try {
      payload = await verifyJWT(String(token), getSignupVerificationSecret(env))
    } catch {
      return json({ error: '유효하지 않거나 만료된 인증 링크입니다.' }, 401)
    }

    if (payload?.type !== 'signup_verification' || !payload?.signup_id || !payload?.email) {
      return json({ error: '유효하지 않은 인증 요청입니다.' }, 400)
    }

    const signupRow = await findPendingSignupByEmail(env, normalizeEmail(payload.email))
    if (!signupRow || signupRow.id !== payload.signup_id) {
      return json({ error: '가입 대기 정보를 찾을 수 없습니다. 다시 회원가입을 진행해주세요.' }, 404)
    }

    if (signupRow.consumed_at) {
      return json({ error: '이미 사용된 인증 링크입니다. 로그인해주세요.' }, 409)
    }

    if (isExpired(signupRow.expires_at)) {
      return json({ error: '인증 링크가 만료되었습니다. 다시 회원가입을 진행해주세요.' }, 410)
    }

    const completed = await completeSignupVerification(env, signupRow)
    const tokenForLogin = await createJWT(
      {
        id: completed.user.id,
        email: completed.user.email,
        name: completed.user.name,
        must_change_password: completed.user.must_change_password,
        role: completed.user.role,
        credits: completed.user.credits,
      },
      env.JWT_SECRET
    )
    await clearAuthRateLimit(env, 'signup_email', signupRow.email)

    return json({
      success: true,
      already_verified: completed.alreadyVerified,
      user: completed.user,
      token: tokenForLogin,
    }, 200, {
      'Set-Cookie': buildSessionCookie(tokenForLogin),
    })
  }

  if (path === '/login' && request.method === 'POST') {
    const { email, password } = await request.json()
    const normalizedEmail = normalizeEmail(email)
    if (!normalizedEmail || !password) {
      return json({ error: '이메일과 비밀번호를 입력해주세요.' }, 400)
    }

    const loginIpRetryAfter = await enforceAuthRateLimit(env, 'login_ip', getClientIp(request), { limit: LOGIN_IP_LIMIT })
    if (loginIpRetryAfter) {
      return json({ error: '로그인 시도가 너무 많습니다. 잠시 후 다시 시도해주세요.' }, 429, {
        'Retry-After': String(loginIpRetryAfter),
      })
    }
    const loginEmailRetryAfter = await enforceAuthRateLimit(env, 'login_email', normalizedEmail, { limit: LOGIN_EMAIL_LIMIT })
    if (loginEmailRetryAfter) {
      return json({ error: '로그인 시도가 너무 많습니다. 잠시 후 다시 시도해주세요.' }, 429, {
        'Retry-After': String(loginEmailRetryAfter),
      })
    }

    const user = await env.DB.prepare(
      'SELECT id, name, email, role, credits, password_hash, must_change_password FROM users WHERE email = ?'
    ).bind(normalizedEmail).first()

    if (!user) {
      const pendingSignup = await findPendingSignupByEmail(env, normalizedEmail)
      if (pendingSignup && !pendingSignup.consumed_at && !isExpired(pendingSignup.expires_at)) {
        return json({ error: '이메일 인증이 아직 완료되지 않았습니다. 받은편지함의 인증 링크를 확인해주세요.' }, 403)
      }
    }

    if (!user || !(await verifyPassword(password, user.password_hash))) {
      return json({ error: '이메일 또는 비밀번호가 올바르지 않습니다.' }, 401)
    }

    if (needsPasswordRehash(user.password_hash)) {
      try {
        const upgradedHash = await hashPassword(password)
        await env.DB.prepare(
          'UPDATE users SET password_hash = ? WHERE id = ?'
        ).bind(upgradedHash, user.id).run()
      } catch (error) {
        console.error('Password rehash failed:', error)
      }
    }

    const token = await createJWT(
      {
        id: user.id,
        email: user.email,
        name: user.name,
        must_change_password: user.must_change_password,
        role: user.role,
        credits: user.credits,
      },
      env.JWT_SECRET
    )
    await clearAuthRateLimit(env, 'login_email', normalizedEmail)
    return json({
      user: {
        id: user.id,
        name: user.name,
        email: user.email,
        must_change_password: user.must_change_password,
        role: user.role,
        credits: user.credits,
      },
      token,
    }, 200, {
      'Set-Cookie': buildSessionCookie(token),
    })
  }

  if (path === '/me' && request.method === 'GET') {
    const user = await getUser(request, env)
    if (!user) return json({ error: 'Unauthorized' }, 401)
    return json({ user })
  }

  if (path === '/profile' && request.method === 'PUT') {
    const user = await getUser(request, env)
    if (!user) return json({ error: 'Unauthorized' }, 401)
    const { name, nickname, profile_image } = await request.json()

    await env.DB.prepare(
      'UPDATE users SET name = ?, nickname = ?, profile_image = ? WHERE id = ?'
    ).bind(name || user.name, nickname || null, profile_image || null, user.id).run()

    const refreshedUser = await env.DB.prepare(
      'SELECT id, name, email, role, credits, nickname, profile_image, created_at, must_change_password FROM users WHERE id = ?'
    ).bind(user.id).first()

    return json({ user: refreshedUser })
  }

  if (path === '/change-password' && request.method === 'POST') {
    const user = await getUser(request, env)
    if (!user) return json({ error: 'Unauthorized' }, 401)

    const { currentPassword, newPassword } = await request.json()
    if (!currentPassword || !newPassword || String(newPassword).length < 8) {
      return json({ error: '현재 비밀번호와 8자 이상의 새 비밀번호를 입력해주세요.' }, 400)
    }

    const currentRow = await env.DB.prepare(
      'SELECT id, name, email, role, credits, password_hash, must_change_password FROM users WHERE id = ?'
    ).bind(user.id).first()

    if (!currentRow || !(await verifyPassword(String(currentPassword), currentRow.password_hash))) {
      return json({ error: '현재 비밀번호가 올바르지 않습니다.' }, 401)
    }

    if (String(currentPassword) === String(newPassword)) {
      return json({ error: '새 비밀번호를 기존 비밀번호와 다르게 입력해주세요.' }, 400)
    }

    const nextHash = await hashPassword(String(newPassword))
    await env.DB.prepare(
      'UPDATE users SET password_hash = ?, must_change_password = 0 WHERE id = ?'
    ).bind(nextHash, user.id).run()

    const refreshedUser = await env.DB.prepare(
      'SELECT id, name, email, role, credits, nickname, profile_image, created_at, must_change_password FROM users WHERE id = ?'
    ).bind(user.id).first()

    const token = await createJWT(
      {
        id: refreshedUser.id,
        email: refreshedUser.email,
        name: refreshedUser.name,
        must_change_password: refreshedUser.must_change_password,
        role: refreshedUser.role,
        credits: refreshedUser.credits,
      },
      env.JWT_SECRET
    )

    return json({ success: true, user: refreshedUser, token }, 200, {
      'Set-Cookie': buildSessionCookie(token),
    })
  }

  if (path === '/logout' && request.method === 'POST') {
    return json({ success: true }, 200, {
      'Set-Cookie': clearSessionCookie(),
    })
  }

  return json({ error: 'Not Found' }, 404)
}
