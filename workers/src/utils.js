export function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

export async function hashPassword(password) {
  const encoder = new TextEncoder()
  const data = encoder.encode(password)
  const hash = await crypto.subtle.digest('SHA-256', data)
  return btoa(String.fromCharCode(...new Uint8Array(hash)))
}

function toBase64Url(str) {
  return btoa(unescape(encodeURIComponent(str)))
    .replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '')
}

function fromBase64Url(str) {
  const pad = str + '='.repeat((4 - str.length % 4) % 4)
  return decodeURIComponent(escape(atob(pad.replace(/-/g, '+').replace(/_/g, '/'))))
}

export async function createJWT(payload, secret) {
  const header = toBase64Url(JSON.stringify({ alg: 'HS256', typ: 'JWT' }))
  const body = toBase64Url(JSON.stringify({ ...payload, exp: Date.now() + 7 * 24 * 60 * 60 * 1000 }))
  const signature = await sign(`${header}.${body}`, secret)
  return `${header}.${body}.${signature}`
}

export async function verifyJWT(token, secret) {
  const parts = token.split('.')
  if (parts.length !== 3) throw new Error('Invalid token')
  const signature = await sign(`${parts[0]}.${parts[1]}`, secret)
  if (signature !== parts[2]) throw new Error('Invalid signature')
  const payload = JSON.parse(fromBase64Url(parts[1]))
  if (payload.exp < Date.now()) throw new Error('Token expired')
  return payload
}

async function sign(data, secret) {
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
  const auth = request.headers.get('Authorization')
  if (!auth?.startsWith('Bearer ')) return null
  try {
    return await verifyJWT(auth.slice(7), env.JWT_SECRET)
  } catch {
    return null
  }
}
