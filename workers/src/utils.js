const SESSION_COOKIE_NAME = 'tv_session'

export function json(data, status = 200, extraHeaders = {}) {
  const headers = new Headers(extraHeaders)
  headers.set('Content-Type', 'application/json')
  return new Response(JSON.stringify(data), {
    status,
    headers,
  })
}

const PASSWORD_HASH_PREFIX = 'pbkdf2_sha256'
// Cloudflare Workers WebCrypto caps PBKDF2 at 100000 iterations.
const PASSWORD_HASH_ITERATIONS = 100000
const PASSWORD_HASH_BYTES = 32
const PASSWORD_SALT_BYTES = 16

export function assertConfiguredSecret(secret, name = 'JWT_SECRET') {
  if (typeof secret !== 'string' || secret.length < 32 || secret === 'change-this-in-production') {
    throw new Error(`${name} is not configured securely`)
  }
  return secret
}

function bytesToBase64Url(bytes) {
  return btoa(String.fromCharCode(...bytes))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=/g, '')
}

function base64UrlToBytes(value) {
  const normalized = value.replace(/-/g, '+').replace(/_/g, '/')
  const padded = normalized + '='.repeat((4 - normalized.length % 4) % 4)
  return Uint8Array.from(atob(padded), (char) => char.charCodeAt(0))
}

async function legacyHashPassword(password) {
  const encoder = new TextEncoder()
  const data = encoder.encode(password)
  const hash = await crypto.subtle.digest('SHA-256', data)
  return btoa(String.fromCharCode(...new Uint8Array(hash)))
}

async function derivePasswordHash(password, saltBytes, iterations) {
  const passwordKey = await crypto.subtle.importKey(
    'raw',
    new TextEncoder().encode(password),
    { name: 'PBKDF2' },
    false,
    ['deriveBits']
  )
  const bits = await crypto.subtle.deriveBits(
    {
      name: 'PBKDF2',
      salt: saltBytes,
      iterations,
      hash: 'SHA-256',
    },
    passwordKey,
    PASSWORD_HASH_BYTES * 8
  )
  return new Uint8Array(bits)
}

function constantTimeEqual(left, right) {
  if (left.length !== right.length) return false
  let diff = 0
  for (let i = 0; i < left.length; i += 1) {
    diff |= left.charCodeAt(i) ^ right.charCodeAt(i)
  }
  return diff === 0
}

export async function hashPassword(password) {
  const salt = crypto.getRandomValues(new Uint8Array(PASSWORD_SALT_BYTES))
  const derived = await derivePasswordHash(password, salt, PASSWORD_HASH_ITERATIONS)
  return [
    PASSWORD_HASH_PREFIX,
    PASSWORD_HASH_ITERATIONS,
    bytesToBase64Url(salt),
    bytesToBase64Url(derived),
  ].join('$')
}

export function needsPasswordRehash(passwordHash) {
  return !passwordHash?.startsWith(`${PASSWORD_HASH_PREFIX}$`)
}

export async function verifyPassword(password, passwordHash) {
  if (!passwordHash) return false

  try {
    if (passwordHash.startsWith(`${PASSWORD_HASH_PREFIX}$`)) {
      const [, iterationsText, saltText, expectedHash] = passwordHash.split('$')
      const iterations = Number(iterationsText)
      if (!iterations || !saltText || !expectedHash) return false

      const derived = await derivePasswordHash(password, base64UrlToBytes(saltText), iterations)
      return constantTimeEqual(bytesToBase64Url(derived), expectedHash)
    }

    const legacyHash = await legacyHashPassword(password)
    return constantTimeEqual(legacyHash, passwordHash)
  } catch {
    return false
  }
}

function toBase64Url(str) {
  return btoa(unescape(encodeURIComponent(str)))
    .replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '')
}

function fromBase64Url(str) {
  const pad = str + '='.repeat((4 - str.length % 4) % 4)
  return decodeURIComponent(escape(atob(pad.replace(/-/g, '+').replace(/_/g, '/'))))
}

export async function createJWT(payload, secret, ttlMs = 7 * 24 * 60 * 60 * 1000) {
  assertConfiguredSecret(secret)
  const header = toBase64Url(JSON.stringify({ alg: 'HS256', typ: 'JWT' }))
  const body = toBase64Url(JSON.stringify({ ...payload, exp: Date.now() + ttlMs }))
  const signature = await sign(`${header}.${body}`, secret)
  return `${header}.${body}.${signature}`
}

export function parseCookies(request) {
  const cookieHeader = request.headers.get('Cookie') || ''
  return cookieHeader.split(';').reduce((acc, part) => {
    const [key, ...rest] = part.trim().split('=')
    if (!key || rest.length === 0) return acc
    acc[key] = decodeURIComponent(rest.join('='))
    return acc
  }, {})
}

export function getAuthTokenFromRequest(request) {
  const auth = request.headers.get('Authorization')
  if (auth?.startsWith('Bearer ')) {
    return auth.slice(7)
  }

  const cookies = parseCookies(request)
  return cookies[SESSION_COOKIE_NAME] || null
}

export function buildSessionCookie(token, { maxAgeSeconds = 7 * 24 * 60 * 60 } = {}) {
  return [
    `${SESSION_COOKIE_NAME}=${encodeURIComponent(token)}`,
    'Path=/',
    'HttpOnly',
    'Secure',
    'SameSite=Lax',
    `Max-Age=${Math.max(0, Math.floor(maxAgeSeconds))}`,
  ].join('; ')
}

export function clearSessionCookie() {
  return [
    `${SESSION_COOKIE_NAME}=`,
    'Path=/',
    'HttpOnly',
    'Secure',
    'SameSite=Lax',
    'Max-Age=0',
  ].join('; ')
}

export async function verifyJWT(token, secret) {
  assertConfiguredSecret(secret)
  const parts = token.split('.')
  if (parts.length !== 3) throw new Error('Invalid token')
  const signature = await sign(`${parts[0]}.${parts[1]}`, secret)
  if (signature !== parts[2]) throw new Error('Invalid signature')
  const payload = JSON.parse(fromBase64Url(parts[1]))
  if (payload.exp < Date.now()) throw new Error('Token expired')
  return payload
}

async function sign(data, secret) {
  assertConfiguredSecret(secret)
  const key = await crypto.subtle.importKey(
    'raw',
    new TextEncoder().encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign']
  )
  const sig = await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(data))
  return btoa(String.fromCharCode(...new Uint8Array(sig)))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=/g, '')
}

export async function getUser(request, env) {
  const token = getAuthTokenFromRequest(request)
  if (!token) return null
  try {
    const payload = await verifyJWT(token, env.JWT_SECRET)
    if (!payload?.id || !env?.DB) {
      return payload
    }

    const user = await env.DB.prepare(
      'SELECT id, name, email, role, credits, nickname, profile_image, created_at, must_change_password FROM users WHERE id = ?'
    ).bind(payload.id).first()

    return user || null
  } catch {
    return null
  }
}
