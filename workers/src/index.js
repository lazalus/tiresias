import { handleAuth } from './auth.js'
import { handleProjects } from './projects.js'
import { handleFiles } from './files.js'
import { handleAdmin } from './admin.js'
import { handlePayments } from './payments.js'
import { getUser, json } from './utils.js'

export default {
  async fetch(request, env) {
    const url = new URL(request.url)
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    }

    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders })
    }

    try {
      let response

      // CF Worker가 직접 처리 (D1 + R2)
      if (url.pathname.startsWith('/api/auth')) {
        response = await handleAuth(request, env, url)
      } else if (url.pathname.startsWith('/api/admin')) {
        response = await handleAdmin(request, env, url)
      } else if (url.pathname.startsWith('/api/payments')) {
        response = await handlePayments(request, env, url)
      } else if (url.pathname.startsWith('/api/projects')) {
        response = await handleProjects(request, env, url)
      } else if (url.pathname.startsWith('/api/files')) {
        response = await handleFiles(request, env, url)

      // Python 백엔드로 프록시 (Vercel)
      } else if (
        url.pathname.startsWith('/api/graph') ||
        url.pathname.startsWith('/api/simulation') ||
        url.pathname.startsWith('/api/report')
      ) {
        // Verify authenticated user with credits before proxying
        const user = await getUser(request, env)
        if (!user) {
          response = json({ error: 'Unauthorized' }, 401)
        } else {
          const dbUser = await env.DB.prepare('SELECT credits FROM users WHERE id = ?').bind(user.id).first()
          if (!dbUser || dbUser.credits <= 0) {
            response = json({ error: '크레딧이 부족합니다. 이용권을 구매해주세요.' }, 403)
          } else {
            response = await proxyToBackend(request, env, url)
          }
        }

      // 나머지 → Vue SPA
      } else {
        return env.ASSETS.fetch(request)
      }

      const newHeaders = new Headers(response.headers)
      Object.entries(corsHeaders).forEach(([k, v]) => newHeaders.set(k, v))
      return new Response(response.body, { status: response.status, headers: newHeaders })
    } catch (err) {
      return new Response(JSON.stringify({ error: err.message }), {
        status: 500,
        headers: { 'Content-Type': 'application/json', ...corsHeaders },
      })
    }
  },
}

async function proxyToBackend(request, env, url) {
  const backendUrl = env.SIMULATION_API || 'http://localhost:5001'
  const target = new URL(url.pathname + url.search, backendUrl)

  const headers = new Headers(request.headers)
  headers.set('Host', new URL(backendUrl).host)
  headers.set('X-Internal-Key', env.INTERNAL_API_KEY)

  return fetch(target.toString(), {
    method: request.method,
    headers,
    body: request.method !== 'GET' ? request.body : undefined,
  })
}
