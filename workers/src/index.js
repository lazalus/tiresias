import { handleAuth } from './auth.js'
import { handleProjects } from './projects.js'
import { handleFiles, loadPendingUploadFiles } from './files.js'
import { handleAdmin } from './admin.js'
import { handlePayments } from './payments.js'
import { handleReports } from './reports.js'
import { handleSupport } from './support.js'
import { handleQueue, getQueueableRequestMeta, proxyQueueableRequest } from './queue.js'
import { createJWT, getUser, json } from './utils.js'
import { PROJECT_STATUS, normalizeProjectStatus } from './projectStatus.js'
import { reconcileProjectReportState } from './reportState.js'

const PDF_DOWNLOAD_PAYMENT_AMOUNT = 1000
const PAYMENT_ORDER_TYPE = {
  SIMULATION: 'simulation',
  PDF_DOWNLOAD: 'pdf_download',
}
const ESTIMATE_PRICE_MULTIPLIER = 1.3

const ESTIMATE_PLANS = [
  {
    id: 'quick',
    label: '빠른 탐색',
    description: '초기 가설 확인과 빠른 내부 검토에 적합합니다.',
    priceFloorKRW: 12900,
    agentsMultiplier: 2.2,
    minAgents: 12,
    rounds: 16,
    depth: 'quick',
    costProfileRate: 0.045,
    costSimConfig: 0.18,
    costGraphPerPage: 0.004,
    costGraphBase: 0.04,
    costReportBase: 1.1,
    costReportAgentOver50: 0.01,
    costInteraction: 0.55,
  },
  {
    id: 'standard',
    label: '표준 분석',
    description: '대부분의 정책·시장·여론 검토에 권장되는 기본 옵션입니다.',
    priceFloorKRW: 17900,
    agentsMultiplier: 3,
    minAgents: 15,
    rounds: 32,
    depth: 'standard',
    costProfileRate: 0.07,
    costSimConfig: 0.30,
    costGraphPerPage: 0.005,
    costGraphBase: 0.05,
    costReportBase: 2.0,
    costReportAgentOver50: 0.02,
    costInteraction: 1.15,
  },
  {
    id: 'deep',
    label: '심화 분석',
    description: '이해관계자 수가 많거나 확산 경로를 더 깊게 보고 싶을 때 적합합니다.',
    priceFloorKRW: 25900,
    agentsMultiplier: 3.6,
    minAgents: 18,
    rounds: 52,
    depth: 'deep',
    costProfileRate: 0.09,
    costSimConfig: 0.42,
    costGraphPerPage: 0.006,
    costGraphBase: 0.06,
    costReportBase: 2.9,
    costReportAgentOver50: 0.025,
    costInteraction: 1.45,
  },
]

function getRecommendedEstimatePlanId(estimatedPages) {
  if (estimatedPages <= 20) return 'quick'
  if (estimatedPages <= 80) return 'standard'
  return 'deep'
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(value, max))
}

function buildCorsHeaders(request, env, url) {
  const requestOrigin = request.headers.get('Origin') || ''
  const authBaseUrl = String(env.AUTH_BASE_URL || 'https://tiresiasview.com')
    .trim()
    .replace(/\/+$/, '')
  const allowedOrigins = new Set([
    authBaseUrl,
    url.origin,
    'http://localhost:5173',
    'http://127.0.0.1:5173',
    'http://localhost:4173',
    'http://127.0.0.1:4173',
    'http://localhost:8787',
    'http://127.0.0.1:8787',
  ])

  const headers = {
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    'Vary': 'Origin',
  }

  if (requestOrigin && allowedOrigins.has(requestOrigin)) {
    headers['Access-Control-Allow-Origin'] = requestOrigin
    headers['Access-Control-Allow-Credentials'] = 'true'
  }

  return headers
}

function buildSecurityHeaders() {
  return {
    'Content-Security-Policy': [
      "default-src 'self'",
      "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://js.tosspayments.com https://www.googletagmanager.com",
      "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
      "font-src 'self' https://fonts.gstatic.com data:",
      "img-src 'self' data: blob: https:",
      "connect-src 'self' https: wss: https://www.google-analytics.com https://region1.google-analytics.com",
      "object-src 'none'",
      "base-uri 'self'",
      "frame-ancestors 'none'",
      "form-action 'self' https://api.tosspayments.com",
      "upgrade-insecure-requests",
    ].join('; '),
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'Permissions-Policy': 'camera=(), microphone=(), geolocation=()',
  }
}

function buildEstimatePlan(plan, estimatedPages, preanalysis = null) {
  const complexityMultiplier = clamp(Number(preanalysis?.complexity_multiplier || 1), 0.8, 1.3)
  const actorDensityMultiplier = clamp(Number(preanalysis?.actor_density_multiplier || 1), 0.8, 1.35)
  const combinedAgentMultiplier = complexityMultiplier * actorDensityMultiplier
  const agents = Math.max(
    plan.minAgents,
    Math.ceil(estimatedPages * plan.agentsMultiplier * combinedAgentMultiplier)
  )
  const profileCost = agents * plan.costProfileRate
  const simConfigCost = plan.costSimConfig
  const graphCost = estimatedPages * plan.costGraphPerPage + plan.costGraphBase
  const reportCost = plan.costReportBase + Math.max(0, (agents - 50) * plan.costReportAgentOver50)
  const interactionCost = plan.costInteraction
  const totalCostUSD = profileCost + simConfigCost + graphCost + reportCost + interactionCost
  const totalCostKRW = Math.ceil(totalCostUSD * 1400 * ESTIMATE_PRICE_MULTIPLIER)
  const finalPrice = Math.max(plan.priceFloorKRW, Math.ceil(totalCostKRW / 100) * 100)

  return {
    id: plan.id,
    label: plan.label,
    description: plan.description,
    agents,
    rounds: plan.rounds,
    depth: plan.depth,
    estimatedPages,
    preanalysis: preanalysis ? {
      complexity: preanalysis.complexity,
      actorDensity: preanalysis.actor_density,
      confidence: preanalysis.confidence,
      documentType: preanalysis.document_type,
      rationale: preanalysis.rationale,
    } : null,
    costKRW: totalCostKRW,
    finalPrice,
    breakdown: [
      { key: 'document_parse', label: '자료 해석 및 페이지 분석' },
      { key: 'graph_build', label: '구조 분석 및 관계 정리' },
      { key: 'persona', label: `행위자 모델 생성 (${agents}개)` },
      { key: 'simulation', label: `다중 라운드 시뮬레이션 (${plan.rounds}라운드)` },
      { key: 'report', label: '요약 보고서 생성' },
    ],
  }
}

async function runEstimatePreanalysis(env, user, pendingToken, requirement = '') {
  const { manifest, files } = await loadPendingUploadFiles(env, user.id, pendingToken)
  if (!manifest || !files.length) {
    return null
  }

  const formData = new FormData()
  for (const file of files) {
    formData.append(
      'files',
      new File([file.bytes], file.name, {
        type: file.type || 'application/octet-stream',
      })
    )
  }
  formData.append('simulation_requirement', requirement || manifest.simulationRequirement || '')

  const backendUrl = env.SIMULATION_API || 'http://localhost:5001'
  const target = new URL('/api/graph/preanalysis', backendUrl)
  const response = await fetch(target.toString(), {
    method: 'POST',
    headers: {
      'X-Internal-Key': env.INTERNAL_API_KEY,
    },
    body: formData,
  })

  if (!response.ok) {
    const payload = await response.text().catch(() => '')
    throw new Error(`Preanalysis failed (${response.status}): ${payload.slice(0, 200)}`)
  }

  const payload = await response.json().catch(() => null)
  return payload?.data || null
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url)
    const requestHost = url.hostname.toLowerCase()
    const shouldEnforceHttps =
      url.protocol === 'http:' &&
      (requestHost === 'tiresiasview.com' || requestHost === 'www.tiresiasview.com')

    if (shouldEnforceHttps) {
      url.protocol = 'https:'
      return Response.redirect(url.toString(), 301)
    }

    const corsHeaders = buildCorsHeaders(request, env, url)
    const securityHeaders = buildSecurityHeaders()

    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders })
    }

    try {
      let response

      if (url.pathname === '/sitemap.xml' && request.method === 'GET') {
        response = await handleDynamicSitemap(env)

      // CF Worker가 직접 처리 (D1 + R2)
      } else if (url.pathname.startsWith('/api/auth')) {
        response = await handleAuth(request, env, url, ctx)
      } else if (url.pathname.startsWith('/api/admin')) {
        response = await handleAdmin(request, env, url, ctx)
      } else if (url.pathname === '/api/payments/webhook' && request.method === 'POST') {
        response = await handleTossWebhook(request, env)
      } else if (url.pathname.startsWith('/api/payments')) {
        response = await handlePayments(request, env, url)
      } else if (url.pathname.startsWith('/api/projects')) {
        response = await handleProjects(request, env, url)
      } else if (url.pathname.startsWith('/api/files')) {
        response = await handleFiles(request, env, url)
      } else if (url.pathname.match(/^\/api\/reports\/samples\/[^/]+\/pdf$/) && request.method === 'GET') {
        response = await handlePublicSamplePdfDownload(env, url)
      } else if (url.pathname.startsWith('/api/reports')) {
        response = await handleReports(request, env, url)
      } else if (url.pathname.startsWith('/api/support')) {
        response = await handleSupport(request, env, url)
      } else if (url.pathname.startsWith('/api/queue')) {
        response = await handleQueue(request, env, url)

      // 챗봇 응답 (Workers AI)
      } else if (url.pathname === '/api/chat' && request.method === 'POST') {
        const { message, history } = await request.json()
        try {
          const chatMessages = [
            {
              role: 'system',
              content: `당신은 Tiresias View의 AI 컨설턴트입니다. AI 에이전트들이 가상 세계에서 여론·시장·정책의 미래 반응을 시뮬레이션하는 플랫폼입니다.

절대 규칙:
- 한국어로만 답변
- 반드시 1-2문장 이내로 답변. 절대 3문장 이상 금지
- 길게 설명하지 마. 핵심만 짧게
- 인사 → "안녕하세요! 어떤 주제를 시뮬레이션해 볼까요?"
- 주제 언급 → "좋은 주제네요. 관련 자료를 업로드해 주시면 바로 시작할 수 있습니다."
- 목록, 번호 매기기, 부연 설명 금지`
            }
          ]
          // 이전 대화 히스토리 추가 (최근 10개)
          if (history && Array.isArray(history)) {
            history.slice(-10).forEach(m => {
              chatMessages.push({ role: m.role === 'assistant' ? 'assistant' : 'user', content: m.content })
            })
          } else {
            chatMessages.push({ role: 'user', content: message })
          }

          const result = await env.AI.run('@cf/meta/llama-3.3-70b-instruct-fp8-fast', {
            messages: chatMessages,
            max_tokens: 250
          })

          const reply = result.response || ''
          const showUpload = /업로드|파일.*올려|자료.*첨부|시작할 수 있습니다/.test(reply)
          response = json({ reply, show_upload: showUpload })
        } catch(e) {
          response = json({ reply: '무엇이든 물어보세요! 시뮬레이션하고 싶은 주제가 있으시면 알려주세요.', show_upload: false })
        }

      // 시뮬레이션 비용 견적
      } else if (url.pathname === '/api/estimate' && request.method === 'POST') {
        const user = await getUser(request, env)
        if (!user) {
          response = json({ error: 'Unauthorized' }, 401)
        } else {
          const { fileCount, totalSize, requirement, hasPdf, actualPages, pendingToken } = await request.json()
          let preanalysis = null
          let estimatedPages
          if (pendingToken) {
            try {
              preanalysis = await runEstimatePreanalysis(env, user, pendingToken, requirement || '')
            } catch (error) {
              console.warn('Estimate preanalysis failed:', error)
            }
          }

          if (preanalysis?.actual_pages && Number(preanalysis.actual_pages) > 0) {
            estimatedPages = Number(preanalysis.actual_pages)
          } else if (actualPages && actualPages > 0) {
            estimatedPages = actualPages
          } else {
            const bytesPerPage = hasPdf ? 150000 : 3000
            estimatedPages = Math.max(1, Math.ceil((totalSize || 0) / bytesPerPage))
          }
          const quoteTtlMs = 15 * 60 * 1000
          const recommendedPlanId = preanalysis?.recommended_plan_id || getRecommendedEstimatePlanId(estimatedPages)

          const plans = await Promise.all(ESTIMATE_PLANS.map(async (plan) => {
            const planEstimate = buildEstimatePlan(plan, estimatedPages, preanalysis)
            const quoteToken = await createJWT({
              scope: 'payment_quote',
              user_id: user.id,
              amount: planEstimate.finalPrice,
              plan_id: planEstimate.id,
              agents: planEstimate.agents,
              rounds: planEstimate.rounds,
              file_count: fileCount || 0,
              total_size: totalSize || 0,
              has_pdf: Boolean(hasPdf),
              pending_token: pendingToken || null,
              quote_expires_at: Date.now() + quoteTtlMs,
            }, env.JWT_SECRET, quoteTtlMs)

            return {
              ...planEstimate,
              quoteToken,
            }
          }))

          const recommendedPlan = plans.find((plan) => plan.id === recommendedPlanId) || plans[0]

          response = json({
            fileCount: fileCount || 0,
            estimatedPages,
            requirement: requirement || '',
            recommendedPlanId,
            preanalysis,
            plans,
            agents: recommendedPlan.agents,
            rounds: recommendedPlan.rounds,
            depth: recommendedPlan.depth,
            costKRW: recommendedPlan.costKRW,
            finalPrice: recommendedPlan.finalPrice,
            quoteToken: recommendedPlan.quoteToken,
            breakdown: recommendedPlan.breakdown,
          })
        }

      // PDF 다운로드 (R2 캐시 + 백엔드 프록시)
      } else if (url.pathname.match(/^\/api\/report\/pdf\//) && request.method === 'GET') {
        const user = await getUser(request, env)
        if (!user) {
          response = json({ error: 'Unauthorized' }, 401)
        } else {
          response = await handlePdfDownload(request, env, url, user)
        }

      // Python 백엔드로 프록시
      } else if (
        url.pathname.startsWith('/api/graph') ||
        url.pathname.startsWith('/api/simulation') ||
        url.pathname.startsWith('/api/report')
      ) {
        const user = await getUser(request, env)
        if (!user) {
          response = json({ error: 'Unauthorized' }, 401)
        } else {
          const queueMeta = await getQueueableRequestMeta(request, url)
          if (queueMeta) {
            response = await proxyQueueableRequest(
              request,
              env,
              url,
              user,
              queueMeta,
              () => proxyToBackendWithGuards(request, env, url, user)
            )
          } else {
            response = await proxyToBackendWithGuards(request, env, url, user)
          }
        }

      // 방문 기록 API (IP 기준 같은 경로 5분 이내 중복 제거, KST 기준)
      } else if (url.pathname === '/api/track' && request.method === 'POST') {
        const body = await request.json().catch(() => ({}))
        const ip = request.headers.get('cf-connecting-ip') || ''
        const ua = request.headers.get('user-agent') || ''
        const userId = body.user_id || null
        const path = body.path || '/'

        // 어드민 계정 방문 제외
        let isAdmin = false
        if (userId) {
          const u = await env.DB.prepare('SELECT role FROM users WHERE id = ?').bind(userId).first()
          if (u?.role === 'admin') isAdmin = true
        }

        if (!isAdmin) {
          const nowKST = new Date(Date.now() + 9 * 60 * 60 * 1000).toISOString()
          await env.DB.prepare(
            "DELETE FROM page_views WHERE created_at < datetime(?, '-3 months')"
          ).bind(nowKST).run()
          const recent = await env.DB.prepare(
            "SELECT id FROM page_views WHERE ip = ? AND path = ? AND created_at > datetime(?, '-5 minutes')"
          ).bind(ip, path, nowKST).first()
          if (!recent) {
            await env.DB.prepare(
              'INSERT INTO page_views (path, user_id, ip, user_agent, created_at) VALUES (?, ?, ?, ?, ?)'
            ).bind(path, userId, ip, ua, nowKST).run()
          }
        }
        response = json({ ok: true })

      // 나머지 → Vue SPA
      } else {
        return env.ASSETS.fetch(request)
      }

      const newHeaders = new Headers(response.headers)
      Object.entries(corsHeaders).forEach(([k, v]) => newHeaders.set(k, v))
      Object.entries(securityHeaders).forEach(([k, v]) => newHeaders.set(k, v))
      return new Response(response.body, { status: response.status, headers: newHeaders })
    } catch (err) {
      return new Response(JSON.stringify({ error: err.message }), {
        status: 500,
        headers: { 'Content-Type': 'application/json', ...corsHeaders, ...securityHeaders },
      })
    }
  },
}

async function handleDynamicSitemap(env) {
  const baseUrl = 'https://tiresiasview.com'
  const staticUrls = [
    { loc: `${baseUrl}/`, changefreq: 'weekly', priority: '1.0' },
    { loc: `${baseUrl}/features`, changefreq: 'monthly', priority: '0.8' },
    { loc: `${baseUrl}/pricing`, changefreq: 'monthly', priority: '0.8' },
    { loc: `${baseUrl}/samples`, changefreq: 'weekly', priority: '0.8' },
    { loc: `${baseUrl}/support`, changefreq: 'monthly', priority: '0.4' },
    { loc: `${baseUrl}/terms`, changefreq: 'yearly', priority: '0.3' },
    { loc: `${baseUrl}/privacy`, changefreq: 'yearly', priority: '0.3' },
    { loc: `${baseUrl}/open-source`, changefreq: 'monthly', priority: '0.3' },
  ]

  const sampleReports = await env.DB.prepare(
    'SELECT id, created_at FROM reports WHERE is_sample = 1 ORDER BY created_at DESC'
  ).all()

  const dynamicUrls = (sampleReports.results || []).map((report) => ({
    loc: `${baseUrl}/samples/${encodeURIComponent(report.id)}`,
    changefreq: 'monthly',
    priority: '0.7',
    lastmod: report.created_at ? new Date(report.created_at).toISOString() : null,
  }))

  const allUrls = [...staticUrls, ...dynamicUrls]
  const body = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${allUrls.map((entry) => {
    const lastmod = entry.lastmod ? `\n    <lastmod>${entry.lastmod}</lastmod>` : ''
    return `  <url>\n    <loc>${entry.loc}</loc>${lastmod}\n    <changefreq>${entry.changefreq}</changefreq>\n    <priority>${entry.priority}</priority>\n  </url>`
  }).join('\n')}\n</urlset>\n`

  return new Response(body, {
    status: 200,
    headers: {
      'Content-Type': 'application/xml; charset=UTF-8',
      'Cache-Control': 'public, max-age=900',
    },
  })
}

async function proxyToBackendWithGuards(request, env, url, user) {
  if (
    request.method === 'POST' &&
    url.pathname === '/api/graph/ontology/generate' &&
    user.role !== 'admin'
  ) {
    const formData = await request.clone().formData().catch(() => null)
    const pendingToken = String(formData?.get?.('pending_token') || '').trim() || null
    const reservation = await reserveSimulationPayment(env, user.id, pendingToken)
    if (!reservation) {
      return json({ error: pendingToken ? '현재 업로드와 일치하는 결제 주문이 없습니다. 다시 견적을 확인해주세요.' : '결제 완료된 주문이 없습니다. 결제 후 다시 시도해주세요.' }, pendingToken ? 409 : 402)
    }

    try {
      const response = await proxyToBackend(request, env, url)
      const payload = await response.clone().json().catch(() => null)
      const projectId = payload?.data?.project_id
      const success = response.ok && payload?.success !== false && Boolean(projectId)

      if (success) {
        await ensurePaidProjectRecord(env, user.id, {
          projectId,
          projectName: payload?.data?.project_name || formData?.get?.('project_name'),
          requirement: formData?.get?.('simulation_requirement'),
          analysisPlan: reservation.planId,
          plannedAgents: reservation.plannedAgents,
          plannedRounds: reservation.plannedRounds,
        })
        await consumeSimulationPayment(env, user.id, reservation.orderId, projectId)
      } else {
        await releaseSimulationPayment(env, user.id, reservation.orderId)
      }

      return response
    } catch (error) {
      await releaseSimulationPayment(env, user.id, reservation.orderId)
      throw error
    }
  }

  if (
    request.method === 'POST' &&
    url.pathname === '/api/simulation/start'
  ) {
    const payload = await request.clone().json().catch(() => null)
    const simulationId = payload?.simulation_id ? String(payload.simulation_id).trim() : ''

    if (simulationId) {
      const project = await env.DB.prepare(
        `SELECT id, status, report_id, planned_rounds
         FROM projects
         WHERE simulation_id = ? AND user_id = ?
         LIMIT 1`
      ).bind(simulationId, user.id).first()

      if (project) {
        const normalizedStatus = normalizeProjectStatus(project.status, {
          reportId: project.report_id || null,
        })

        if (
          project.report_id ||
          normalizedStatus === PROJECT_STATUS.REPORT_COMPLETED ||
          normalizedStatus === PROJECT_STATUS.REPORT_GENERATING
        ) {
          return json({
            error: '이미 보고서가 생성된 프로젝트입니다. 기존 보고서를 확인해주세요.',
            code: 'REPORT_ALREADY_EXISTS',
            project_id: project.id,
            report_id: project.report_id || null,
          }, 409)
        }

        if (!payload?.max_rounds && project.planned_rounds) {
          return proxyToBackend(
            buildJsonProxyRequest(request, {
              ...(payload || {}),
              max_rounds: Number(project.planned_rounds),
            }),
            env,
            url
          )
        }
      }
    }
  }

  if (
    request.method === 'POST' &&
    url.pathname === '/api/simulation/prepare'
  ) {
    const payload = await request.clone().json().catch(() => null)
    const simulationId = payload?.simulation_id ? String(payload.simulation_id).trim() : ''

    if (simulationId) {
      const project = await env.DB.prepare(
        `SELECT id, analysis_plan, planned_agents, planned_rounds
         FROM projects
         WHERE simulation_id = ? AND user_id = ?
         LIMIT 1`
      ).bind(simulationId, user.id).first()

      if (project) {
        const mergedPayload = {
          ...(payload || {}),
          ...(project.analysis_plan ? { simulation_mode: project.analysis_plan } : {}),
          ...(project.planned_agents ? { target_agent_count: Number(project.planned_agents) } : {}),
          ...(project.planned_rounds ? { max_rounds: Number(project.planned_rounds) } : {}),
        }
        return proxyToBackend(buildJsonProxyRequest(request, mergedPayload), env, url)
      }
    }
  }

  if (
    request.method === 'POST' &&
    url.pathname === '/api/report/generate'
  ) {
    const payload = await request.clone().json().catch(() => null)
    const simulationId = payload?.simulation_id ? String(payload.simulation_id).trim() : ''

    if (simulationId) {
      const project = await env.DB.prepare(
        `SELECT id, status, report_id
         FROM projects
         WHERE simulation_id = ? AND user_id = ?
         LIMIT 1`
      ).bind(simulationId, user.id).first()

      const reconciledProject = project
        ? await reconcileProjectReportState(env, user.id, project)
        : null

      if (
        reconciledProject?.report_id &&
        reconciledProject.status === PROJECT_STATUS.REPORT_COMPLETED
      ) {
        return json({
          success: true,
          data: {
            simulation_id: simulationId,
            report_id: reconciledProject.report_id,
            status: 'completed',
            message: '보고서가 이미 존재합니다',
            already_generated: true,
          }
        })
      }
    }
  }

  return proxyToBackend(request, env, url)
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

function buildJsonProxyRequest(request, payload) {
  const headers = new Headers(request.headers)
  headers.set('Content-Type', 'application/json')

  return new Request(request.url, {
    method: request.method,
    headers,
    body: JSON.stringify(payload),
  })
}

async function handlePdfDownload(request, env, url, user) {
  const reportId = decodeURIComponent(url.pathname.replace('/api/report/pdf/', '')).trim()
  if (!reportId) return json({ error: '보고서 ID가 필요합니다.' }, 400)

  const refresh = url.searchParams.get('refresh') === '1'
  const report = await env.DB.prepare(
    'SELECT id, user_id, title, summary, sections, content, refined_key, pdf_key, created_at FROM reports WHERE id = ? AND user_id = ?'
  ).bind(reportId, user.id).first()

  if (!report) {
    return json({ error: '보고서를 찾을 수 없습니다.' }, 404)
  }

  const pdfKey = report.pdf_key || `pdfs/${reportId}.pdf`

  if (!refresh) {
    const cached = await env.STORAGE.get(pdfKey)
    if (cached) {
      return buildPdfResponse(cached.body, report.title || reportId)
    }
  }

  const reportDocument = await loadPdfReportDocument(env, user.id, report)
  const backendResponse = await renderPdfViaBackend(env, reportDocument)

  if (!backendResponse.ok) {
    return backendResponse
  }

  const pdfBytes = await backendResponse.arrayBuffer()
  await env.STORAGE.put(pdfKey, pdfBytes, {
    httpMetadata: { contentType: 'application/pdf' }
  })

  try {
    await env.DB.prepare(
      'UPDATE reports SET pdf_key = ? WHERE id = ? AND user_id = ?'
    ).bind(pdfKey, reportId, user.id).run()
  } catch {}

  return buildPdfResponse(pdfBytes, reportDocument.title || report.title || reportId)
}

async function handlePublicSamplePdfDownload(env, url) {
  const reportId = decodeURIComponent(url.pathname.replace('/api/reports/samples/', '').replace(/\/pdf$/, '')).trim()
  if (!reportId) return json({ error: '보고서 ID가 필요합니다.' }, 400)

  const report = await env.DB.prepare(
    `SELECT id, user_id, title, summary, sections, content, refined_key, pdf_key, created_at
     FROM reports
     WHERE id = ? AND is_sample = 1`
  ).bind(reportId).first()

  if (!report) {
    return json({ error: '샘플 보고서를 찾을 수 없습니다.' }, 404)
  }

  const pdfKey = report.pdf_key || `pdfs/${reportId}.pdf`
  const cached = await env.STORAGE.get(pdfKey)
  if (cached) {
    return buildPdfResponse(cached.body, report.title || reportId)
  }

  const reportDocument = await loadPdfReportDocument(env, report.user_id, report)
  const backendResponse = await renderPdfViaBackend(env, reportDocument)
  if (!backendResponse.ok) {
    return backendResponse
  }

  const pdfBytes = await backendResponse.arrayBuffer()
  await env.STORAGE.put(pdfKey, pdfBytes, {
    httpMetadata: { contentType: 'application/pdf' }
  })

  try {
    await env.DB.prepare(
      'UPDATE reports SET pdf_key = ? WHERE id = ? AND is_sample = 1'
    ).bind(pdfKey, reportId).run()
  } catch {}

  return buildPdfResponse(pdfBytes, reportDocument.title || report.title || reportId)
}

function buildPdfResponse(body, title) {
  const filenameBase = String(title || '보고서')
    .replace(/[\\/:*?"<>|]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim() || '보고서'

  const headers = new Headers()
  headers.set('Content-Type', 'application/pdf')
  headers.set('Content-Disposition', `attachment; filename="${filenameBase}.pdf"`)
  return new Response(body, { status: 200, headers })
}

function normalizePdfSectionTitle(title, index) {
  const cleaned = String(title || '')
    .replace(/^#+\s*/, '')
    .replace(/^\s*제?\s*\d+\s*(장|절|항)\s*/u, '')
    .replace(/^\s*[IVXLC]+\.\s*/iu, '')
    .replace(/^\s*\d+[\.\)]\s*/u, '')
    .trim()

  const baseTitle = cleaned || `주요 분석 ${index + 1}`
  return `제${index + 1}장 ${baseTitle}`
}

function buildPdfReportDocument(payload = {}) {
  const sections = Array.isArray(payload.sections) ? payload.sections : []
  return {
    report_id: payload.report_id || '',
    title: String(payload.title || '정책 시뮬레이션 분석보고서').trim(),
    summary: String(payload.summary || '').trim(),
    generated_at: payload.generated_at || payload.created_at || new Date().toISOString(),
    format: 'ko-government-report-v1',
    sections: sections.map((section, index) => ({
      title: normalizePdfSectionTitle(section?.title, index),
      content: String(section?.content || ''),
    })),
  }
}

async function loadPdfReportDocument(env, userId, report) {
  const fallbackSections = safeJsonParse(report.sections, [])
  const fallbackDocument = buildPdfReportDocument({
    report_id: report.id,
    title: report.title,
    summary: report.summary,
    sections: fallbackSections,
    created_at: report.created_at,
  })

  const storageKey = report.refined_key || report.content || `reports/${userId}/${report.id}.json`
  const stored = await env.STORAGE.get(storageKey)
  if (!stored) {
    return fallbackDocument
  }

  try {
    const payload = await stored.json()
    return buildPdfReportDocument({
      ...payload,
      report_id: report.id,
      title: payload?.title || report.title,
      summary: payload?.summary || report.summary,
      sections: Array.isArray(payload?.sections) ? payload.sections : fallbackSections,
      generated_at: payload?.generated_at || report.created_at,
    })
  } catch {
    return fallbackDocument
  }
}

function safeJsonParse(value, fallbackValue) {
  try {
    const parsed = JSON.parse(value)
    return Array.isArray(parsed) ? parsed : fallbackValue
  } catch {
    return fallbackValue
  }
}

async function renderPdfViaBackend(env, reportDocument) {
  const backendUrl = env.SIMULATION_API || 'http://localhost:5001'
  const target = new URL('/api/report/pdf/render', backendUrl)
  const headers = new Headers({
    'Content-Type': 'application/json',
    'X-Internal-Key': env.INTERNAL_API_KEY,
  })
  headers.set('Host', new URL(backendUrl).host)

  return fetch(target.toString(), {
    method: 'POST',
    headers,
    body: JSON.stringify(reportDocument),
  })
}

async function findPdfDownloadOrder(env, userId, reportId, { allowConsumedFallback = false } = {}) {
  const statuses = allowConsumedFallback
    ? ['confirmed', 'consumed']
    : ['confirmed']
  const placeholders = statuses.map(() => '?').join(', ')

  return env.DB.prepare(
    `SELECT order_id, status
     FROM payment_orders
     WHERE user_id = ?
       AND order_type = ?
       AND resource_id = ?
       AND status IN (${placeholders})
     ORDER BY
       CASE status WHEN 'confirmed' THEN 0 ELSE 1 END,
       COALESCE(confirmed_at, consumed_at, created_at) DESC
     LIMIT 1`
  ).bind(userId, PAYMENT_ORDER_TYPE.PDF_DOWNLOAD, reportId, ...statuses).first()
}

async function consumePdfDownloadPayment(env, userId, orderId) {
  await env.DB.prepare(
    `UPDATE payment_orders
     SET status = ?, consumed_at = COALESCE(consumed_at, ?)
     WHERE order_id = ?
       AND user_id = ?
       AND order_type = ?
       AND status = ?`
  ).bind(
    'consumed',
    new Date().toISOString(),
    orderId,
    userId,
    PAYMENT_ORDER_TYPE.PDF_DOWNLOAD,
    'confirmed'
  ).run()
}

async function handleTossWebhook(request, env) {
  try {
    const body = await request.json()
    const { eventType, data } = body

    // 웹훅 시크릿 검증
    const signature = request.headers.get('Toss-Signature')
    if (signature) {
      const encoder = new TextEncoder()
      const key = await crypto.subtle.importKey(
        'raw', encoder.encode(env.TOSS_WEBHOOK_SECRET),
        { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']
      )
      const rawBody = JSON.stringify(body)
      const sig = await crypto.subtle.sign('HMAC', key, encoder.encode(rawBody))
      const expected = btoa(String.fromCharCode(...new Uint8Array(sig)))
      if (expected !== signature) {
        return json({ error: 'Invalid signature' }, 401)
      }
    }

    if (eventType === 'PAYMENT_STATUS_CHANGED' && data) {
      const { paymentKey, orderId, status, totalAmount } = data

      if (status === 'DONE' && orderId && paymentKey) {
        // 이미 처리된 건인지 확인
        const existing = await env.DB.prepare(
          'SELECT id FROM credit_transactions WHERE payment_key = ? LIMIT 1'
        ).bind(paymentKey).first()

        if (!existing) {
          // 주문 조회
          const order = await env.DB.prepare(
            'SELECT order_id, user_id, amount, order_type, status FROM payment_orders WHERE order_id = ? LIMIT 1'
          ).bind(orderId).first()

          if (order && order.status === 'pending') {
            const txId = crypto.randomUUID()
            const amount = totalAmount || order.amount
            const transactionType = order.order_type === PAYMENT_ORDER_TYPE.PDF_DOWNLOAD
              ? 'pdf_payment'
              : 'simulation_payment'
            const transactionDescription = order.order_type === PAYMENT_ORDER_TYPE.PDF_DOWNLOAD
              ? `PDF 다운로드 결제 (${Number(amount).toLocaleString()}원)`
              : `시뮬레이션 결제 (${Number(amount).toLocaleString()}원)`
            await env.DB.prepare(
              'INSERT INTO credit_transactions (id, user_id, amount, type, description, payment_key, reference_key, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)'
            ).bind(txId, order.user_id, amount, transactionType, transactionDescription, paymentKey, order.order_id, new Date().toISOString()).run()
            await env.DB.prepare(
              'UPDATE payment_orders SET status = ?, payment_key = ?, confirmed_at = ? WHERE order_id = ?'
            ).bind('confirmed', paymentKey, new Date().toISOString(), orderId).run()
          }
        }
      }

      if (status === 'CANCELED' && paymentKey) {
        const order = await env.DB.prepare(
          `SELECT order_id, user_id, amount, order_type, status, project_id, consumed_at
           FROM payment_orders
           WHERE payment_key = ?
           LIMIT 1`
        ).bind(paymentKey).first()

        if (order && order.status !== 'canceled') {
          const cancelType = order.order_type === PAYMENT_ORDER_TYPE.PDF_DOWNLOAD
            ? 'pdf_refund'
            : 'simulation_refund'
          const cancelAmount = Number(totalAmount || order.amount || 0)
          const cancelDescription = order.order_type === PAYMENT_ORDER_TYPE.PDF_DOWNLOAD
            ? `PDF 다운로드 결제 취소 (${cancelAmount.toLocaleString()}원)`
            : `시뮬레이션 결제 취소 (${cancelAmount.toLocaleString()}원)`

          const existingCancel = await env.DB.prepare(
            `SELECT id
             FROM credit_transactions
             WHERE reference_key = ?
               AND type = ?
             LIMIT 1`
          ).bind(order.order_id, cancelType).first()

          if (!existingCancel) {
            await env.DB.prepare(
              'INSERT INTO credit_transactions (id, user_id, amount, type, description, payment_key, reference_key, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)'
            ).bind(
              crypto.randomUUID(),
              order.user_id,
              -Math.abs(cancelAmount),
              cancelType,
              cancelDescription,
              null,
              order.order_id,
              new Date().toISOString()
            ).run()
          }

          await env.DB.prepare(
            `UPDATE payment_orders
             SET status = ?, reserved_at = NULL
             WHERE order_id = ?`
          ).bind('canceled', order.order_id).run()
        }
      }
    }

    return json({ success: true })
  } catch (err) {
    console.error('Webhook error:', err)
    return json({ success: true }) // 토스에 200 반환해야 재시도 안 함
  }
}

async function reserveSimulationPayment(env, userId, pendingToken = null) {
  const now = new Date().toISOString()
  const staleCutoff = new Date(Date.now() - 15 * 60 * 1000).toISOString()
  const order = await env.DB.prepare(
    `SELECT order_id, plan_id, planned_agents, planned_rounds, resource_id
     FROM payment_orders
     WHERE user_id = ?
       AND COALESCE(order_type, 'simulation') = ?
       AND (? IS NULL OR resource_id = ?)
       AND (status = 'confirmed' OR (status = 'processing' AND reserved_at IS NOT NULL AND reserved_at <= ?))
     ORDER BY COALESCE(confirmed_at, created_at) DESC
     LIMIT 1`
  ).bind(userId, PAYMENT_ORDER_TYPE.SIMULATION, pendingToken, pendingToken, staleCutoff).first()

  if (!order?.order_id) {
    return null
  }

  const result = await env.DB.prepare(
    `UPDATE payment_orders
     SET status = ?, reserved_at = ?
     WHERE order_id = ?
       AND user_id = ?
       AND COALESCE(order_type, 'simulation') = ?
       AND (? IS NULL OR resource_id = ?)
       AND (status = 'confirmed' OR (status = 'processing' AND reserved_at IS NOT NULL AND reserved_at <= ?))`
  ).bind('processing', now, order.order_id, userId, PAYMENT_ORDER_TYPE.SIMULATION, pendingToken, pendingToken, staleCutoff).run()

  if (!result.meta?.changes) {
    return null
  }

  return {
    orderId: order.order_id,
    planId: order.plan_id || null,
    plannedAgents: order.planned_agents ?? null,
    plannedRounds: order.planned_rounds ?? null,
  }
}

async function consumeSimulationPayment(env, userId, orderId, projectId) {
  await env.DB.prepare(
    `UPDATE payment_orders
     SET status = ?, reserved_at = NULL, consumed_at = ?, project_id = ?
     WHERE order_id = ? AND user_id = ? AND COALESCE(order_type, 'simulation') = ? AND status = ?`
  ).bind('consumed', new Date().toISOString(), projectId, orderId, userId, PAYMENT_ORDER_TYPE.SIMULATION, 'processing').run()
}

async function ensurePaidProjectRecord(env, userId, { projectId, projectName, requirement, analysisPlan, plannedAgents, plannedRounds }) {
  if (!projectId) return

  const existing = await env.DB.prepare(
    'SELECT id, user_id, name, requirement, status, report_id FROM projects WHERE id = ? LIMIT 1'
  ).bind(projectId).first()

  const normalizedName = String(projectName || requirement || '시뮬레이션').trim() || '시뮬레이션'
  const normalizedRequirement = requirement ? String(requirement).trim() : null

  if (!existing) {
    await env.DB.prepare(
      `INSERT INTO projects
         (id, user_id, name, requirement, status, simulation_id, report_id, analysis_plan, planned_agents, planned_rounds, created_at)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
    ).bind(
      projectId,
      userId,
      normalizedName,
      normalizedRequirement,
      PROJECT_STATUS.ONTOLOGY_GENERATED,
      null,
      null,
      analysisPlan || null,
      plannedAgents ?? null,
      plannedRounds ?? null,
      new Date().toISOString()
    ).run()
    return
  }

  if (existing.user_id !== userId) {
    throw new Error('결제된 프로젝트 소유자가 일치하지 않습니다.')
  }

  const existingStatus = normalizeProjectStatus(existing.status, {
    reportId: existing.report_id || null,
  })
  const preservedStatuses = new Set([
    PROJECT_STATUS.GRAPH_BUILDING,
    PROJECT_STATUS.GRAPH_COMPLETED,
    PROJECT_STATUS.SIMULATION_PREPARING,
    PROJECT_STATUS.SIMULATION_READY,
    PROJECT_STATUS.SIMULATION_RUNNING,
    PROJECT_STATUS.SIMULATION_COMPLETED,
    PROJECT_STATUS.REPORT_GENERATING,
    PROJECT_STATUS.REPORT_COMPLETED,
    PROJECT_STATUS.FAILED,
    PROJECT_STATUS.SIMULATION_STOPPED,
  ])
  const nextStatus = preservedStatuses.has(existingStatus)
    ? existingStatus
    : PROJECT_STATUS.ONTOLOGY_GENERATED

  await env.DB.prepare(
    `UPDATE projects
     SET name = ?, requirement = ?, status = ?, analysis_plan = COALESCE(analysis_plan, ?), planned_agents = COALESCE(planned_agents, ?), planned_rounds = COALESCE(planned_rounds, ?)
     WHERE id = ? AND user_id = ?`
  ).bind(
    existing.name || normalizedName,
    existing.requirement || normalizedRequirement,
    nextStatus,
    analysisPlan || null,
    plannedAgents ?? null,
    plannedRounds ?? null,
    projectId,
    userId
  ).run()
}

async function releaseSimulationPayment(env, userId, orderId) {
  await env.DB.prepare(
    `UPDATE payment_orders
     SET status = ?, reserved_at = NULL
     WHERE order_id = ? AND user_id = ? AND COALESCE(order_type, 'simulation') = ? AND status = ?`
  ).bind('confirmed', orderId, userId, PAYMENT_ORDER_TYPE.SIMULATION, 'processing').run()
}
