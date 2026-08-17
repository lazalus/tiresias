const SEARCH_CONSOLE_CACHE_STALE_MS = 12 * 60 * 60 * 1000
const SEARCH_CONSOLE_REFRESH_LOCK_MS = 5 * 60 * 1000
const SEARCH_CONSOLE_DEFAULT_DAYS = 28
const SEARCH_CONSOLE_DATA_DELAY_DAYS = 2
const SEARCH_CONSOLE_MAX_ROWS = 10
const DEFAULT_BASE_URL = 'https://tiresiasview.com'
const CORE_PATHS = ['/', '/features', '/support', '/samples', '/terms', '/privacy', '/open-source']

class SearchConsoleError extends Error {
  constructor(message, { status = 500, code = 'search_console_error', details = null } = {}) {
    super(message)
    this.name = 'SearchConsoleError'
    this.status = status
    this.code = code
    this.details = details
  }
}

function clampDays(value) {
  return Math.max(7, Math.min(Number(value) || SEARCH_CONSOLE_DEFAULT_DAYS, 90))
}

function buildCacheKey(env, days) {
  const explicitSiteUrl = String(env.GOOGLE_SEARCH_CONSOLE_SITE_URL || '').trim() || 'auto'
  const siteKey = explicitSiteUrl.toLowerCase().replace(/[^a-z0-9:/._-]+/g, '_')
  return `search_console:${siteKey}:${days}`
}

function isCacheStale(fetchedAt) {
  if (!fetchedAt) return true
  const fetched = new Date(fetchedAt).getTime()
  if (Number.isNaN(fetched)) return true
  return Date.now() - fetched >= SEARCH_CONSOLE_CACHE_STALE_MS
}

function parseCachedPayload(row) {
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

function buildEmptySummary() {
  return {
    clicks: 0,
    impressions: 0,
    ctr: 0,
    position: 0,
  }
}

function buildFailurePayload(days, error, cachedPayload = null) {
  const code = error?.code || 'search_console_error'
  const message = error?.message || 'Search Console 데이터를 불러오지 못했습니다.'

  return {
    connected: false,
    configured: false,
    site_url: cachedPayload?.site_url || null,
    site_source: cachedPayload?.site_source || null,
    days,
    data_through: cachedPayload?.data_through || null,
    summary: cachedPayload?.summary || buildEmptySummary(),
    previous_summary: cachedPayload?.previous_summary || buildEmptySummary(),
    deltas: cachedPayload?.deltas || buildEmptySummary(),
    top_queries: cachedPayload?.top_queries || [],
    top_pages: cachedPayload?.top_pages || [],
    daily: cachedPayload?.daily || [],
    inspections: cachedPayload?.inspections || [],
    diagnostics: cachedPayload?.diagnostics || { issues: [], opportunities: [], wins: [] },
    fetched_at: cachedPayload?.fetched_at || null,
    cached: Boolean(cachedPayload),
    stale: Boolean(cachedPayload),
    error_code: code,
    error_message: message,
    setup_hint: buildSetupHint(code),
    last_error: message,
  }
}

function buildSetupHint(code) {
  if (code === 'missing_credentials') {
    return 'Worker secret에 Search Console용 OAuth 자격을 추가해야 합니다.'
  }
  if (code === 'insufficient_scope') {
    return '현재 refresh token에는 Search Console scope가 없습니다. https://www.googleapis.com/auth/webmasters 권한으로 새 refresh token을 발급받아 넣어야 합니다.'
  }
  if (code === 'site_not_found') {
    return 'Search Console에 등록된 속성에서 tiresiasview.com을 찾지 못했습니다. URL-prefix 또는 Domain property를 확인해 주세요.'
  }
  if (code === 'invalid_grant') {
    return 'Google refresh token이 만료되었거나 폐기됐습니다. 새 refresh token으로 교체해야 합니다.'
  }
  return 'Search Console 설정 또는 권한을 확인해 주세요.'
}

async function readSearchConsoleCache(env, days) {
  const row = await env.DB.prepare(
    `SELECT payload, fetched_at, refresh_started_at, last_error
     FROM search_console_cache
     WHERE cache_key = ?`
  ).bind(buildCacheKey(env, days)).first()

  return row ? { row, payload: parseCachedPayload(row) } : { row: null, payload: null }
}

async function markRefreshStarted(env, days) {
  const cacheKey = buildCacheKey(env, days)
  const now = new Date().toISOString()
  const existing = await env.DB.prepare(
    `SELECT refresh_started_at
     FROM search_console_cache
     WHERE cache_key = ?`
  ).bind(cacheKey).first()

  if (existing?.refresh_started_at) {
    const started = new Date(existing.refresh_started_at).getTime()
    if (!Number.isNaN(started) && (Date.now() - started) < SEARCH_CONSOLE_REFRESH_LOCK_MS) {
      return false
    }
  }

  await env.DB.prepare(
    `INSERT INTO search_console_cache (
       cache_key, days, site_url, payload, fetched_at, refresh_started_at, last_error, created_at, updated_at
     ) VALUES (?, ?, NULL, NULL, NULL, ?, NULL, ?, ?)
     ON CONFLICT(cache_key) DO UPDATE SET
       refresh_started_at = excluded.refresh_started_at,
       updated_at = excluded.updated_at`
  ).bind(cacheKey, days, now, now, now).run()

  return true
}

async function persistCache(env, days, payload) {
  const now = new Date().toISOString()
  await env.DB.prepare(
    `INSERT INTO search_console_cache (
       cache_key, days, site_url, payload, fetched_at, refresh_started_at, last_error, created_at, updated_at
     ) VALUES (?, ?, ?, ?, ?, NULL, NULL, ?, ?)
     ON CONFLICT(cache_key) DO UPDATE SET
       site_url = excluded.site_url,
       payload = excluded.payload,
       fetched_at = excluded.fetched_at,
       refresh_started_at = NULL,
       last_error = NULL,
       updated_at = excluded.updated_at`
  ).bind(
    buildCacheKey(env, days),
    days,
    payload.site_url || null,
    JSON.stringify(payload),
    now,
    now,
    now,
  ).run()

  return {
    ...payload,
    fetched_at: now,
    cached: true,
    stale: false,
    last_error: null,
  }
}

async function markRefreshFailed(env, days, errorMessage) {
  const now = new Date().toISOString()
  await env.DB.prepare(
    `UPDATE search_console_cache
     SET refresh_started_at = NULL,
         last_error = ?,
         updated_at = ?
     WHERE cache_key = ?`
  ).bind(
    String(errorMessage || 'unknown error').slice(0, 800),
    now,
    buildCacheKey(env, days),
  ).run()
}

async function getAccessToken(env) {
  const clientId = String(env.GOOGLE_SEARCH_CONSOLE_CLIENT_ID || env.GOOGLE_ADS_CLIENT_ID || '').trim()
  const clientSecret = String(env.GOOGLE_SEARCH_CONSOLE_CLIENT_SECRET || env.GOOGLE_ADS_CLIENT_SECRET || '').trim()
  const refreshToken = String(env.GOOGLE_SEARCH_CONSOLE_REFRESH_TOKEN || env.GOOGLE_ADS_REFRESH_TOKEN || '').trim()

  if (!clientId || !clientSecret || !refreshToken) {
    throw new SearchConsoleError('Search Console OAuth 자격이 설정되지 않았습니다.', {
      status: 400,
      code: 'missing_credentials',
    })
  }

  const tokenResponse = await fetch('https://oauth2.googleapis.com/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      client_id: clientId,
      client_secret: clientSecret,
      refresh_token: refreshToken,
      grant_type: 'refresh_token',
    }),
  })

  const payload = await tokenResponse.json().catch(() => ({}))
  if (!tokenResponse.ok || !payload?.access_token) {
    throw new SearchConsoleError(
      payload?.error_description || payload?.error || `OAuth token refresh failed (${tokenResponse.status})`,
      {
        status: tokenResponse.status,
        code: payload?.error === 'invalid_grant' ? 'invalid_grant' : 'oauth_refresh_failed',
        details: payload,
      }
    )
  }

  return payload.access_token
}

async function googleApiRequest(accessToken, target, options = {}) {
  const response = await fetch(target, {
    ...options,
    headers: {
      Authorization: `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
  })

  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    const reason = payload?.error?.details?.[0]?.reason || payload?.error?.errors?.[0]?.reason || payload?.error?.status
    let code = 'google_api_error'
    if (reason === 'ACCESS_TOKEN_SCOPE_INSUFFICIENT' || reason === 'insufficientPermissions') {
      code = 'insufficient_scope'
    } else if (response.status === 404) {
      code = 'site_not_found'
    }

    throw new SearchConsoleError(
      payload?.error?.message || `Google API request failed (${response.status})`,
      {
        status: response.status,
        code,
        details: payload,
      }
    )
  }

  return payload
}

function normalizeHost(value) {
  return String(value || '').trim().replace(/^https?:\/\//, '').replace(/^sc-domain:/, '').replace(/^www\./, '').replace(/\/.*$/, '')
}

async function resolveSiteUrl(accessToken, env) {
  const explicit = String(env.GOOGLE_SEARCH_CONSOLE_SITE_URL || '').trim()
  if (explicit) {
    return { siteUrl: explicit, siteSource: 'explicit' }
  }

  const siteResponse = await googleApiRequest(accessToken, 'https://www.googleapis.com/webmasters/v3/sites', {
    method: 'GET',
  })
  const siteEntries = Array.isArray(siteResponse?.siteEntry) ? siteResponse.siteEntry : []
  const host = normalizeHost(env.AUTH_BASE_URL || env.GOOGLE_ADS_DEFAULT_LANDING_URL || DEFAULT_BASE_URL)
  const candidates = [
    `sc-domain:${host}`,
    `https://${host}/`,
    `https://www.${host}/`,
    `http://${host}/`,
    `http://www.${host}/`,
  ]

  const matched = candidates.find((candidate) => siteEntries.some((entry) => entry?.siteUrl === candidate))
  if (!matched) {
    throw new SearchConsoleError('tiresiasview.com에 해당하는 Search Console 속성을 찾지 못했습니다.', {
      status: 404,
      code: 'site_not_found',
      details: {
        sites: siteEntries.map((entry) => entry?.siteUrl).filter(Boolean),
      },
    })
  }

  return { siteUrl: matched, siteSource: 'auto' }
}

function toDateText(date) {
  return date.toISOString().slice(0, 10)
}

function addDays(base, delta) {
  const next = new Date(base.getTime())
  next.setUTCDate(next.getUTCDate() + delta)
  return next
}

function buildDateRanges(days) {
  const end = addDays(new Date(), -SEARCH_CONSOLE_DATA_DELAY_DAYS)
  const start = addDays(end, -(days - 1))
  const previousEnd = addDays(start, -1)
  const previousStart = addDays(previousEnd, -(days - 1))
  return {
    current: {
      startDate: toDateText(start),
      endDate: toDateText(end),
    },
    previous: {
      startDate: toDateText(previousStart),
      endDate: toDateText(previousEnd),
    },
  }
}

async function searchAnalyticsQuery(accessToken, siteUrl, body) {
  const target = `https://www.googleapis.com/webmasters/v3/sites/${encodeURIComponent(siteUrl)}/searchAnalytics/query`
  return googleApiRequest(accessToken, target, {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

function toMetricRow(row = {}) {
  return {
    clicks: Number(row.clicks || 0),
    impressions: Number(row.impressions || 0),
    ctr: Number(row.ctr || 0),
    position: Number(row.position || 0),
  }
}

function toDelta(currentValue, previousValue) {
  if (!previousValue) return 0
  return ((currentValue - previousValue) / previousValue) * 100
}

function toTopRows(rows = [], labelKey) {
  return rows.map((row) => {
    const metrics = toMetricRow(row)
    return {
      [labelKey]: row?.keys?.[0] || '',
      ...metrics,
    }
  })
}

function buildCoreInspectionUrls(env) {
  const baseUrl = String(env.AUTH_BASE_URL || DEFAULT_BASE_URL).trim().replace(/\/+$/, '')
  return CORE_PATHS.map((path) => `${baseUrl}${path === '/' ? '' : path}`)
}

async function inspectUrl(accessToken, siteUrl, inspectionUrl) {
  const payload = await googleApiRequest(
    accessToken,
    'https://searchconsole.googleapis.com/v1/urlInspection/index:inspect',
    {
      method: 'POST',
      body: JSON.stringify({
        inspectionUrl,
        siteUrl,
      }),
    }
  )

  const result = payload?.inspectionResult?.indexStatusResult || {}
  return {
    url: inspectionUrl,
    verdict: result.verdict || 'UNKNOWN',
    coverage_state: result.coverageState || '',
    indexing_state: result.indexingState || '',
    robots_txt_state: result.robotsTxtState || '',
    page_fetch_state: result.pageFetchState || '',
    last_crawl_time: result.lastCrawlTime || null,
    google_canonical: result.googleCanonical || '',
    user_canonical: result.userCanonical || '',
    referring_urls_count: Array.isArray(result.referringUrls) ? result.referringUrls.length : 0,
  }
}

function summarizeDiagnostics(summary, topQueries, topPages, inspections) {
  const issues = []
  const opportunities = []
  const wins = []

  const lowCtrPages = topPages.filter((row) => row.impressions >= 30 && row.ctr < 0.02)
  const opportunityPages = topPages.filter((row) => row.impressions >= 20 && row.position > 3 && row.position <= 12)
  const weakQueries = topQueries.filter((row) => row.impressions >= 20 && row.ctr < 0.02)
  const notIndexed = inspections.filter((item) => item.verdict !== 'PASS')

  if (summary.impressions === 0) {
    issues.push({
      type: 'visibility',
      severity: 'warning',
      title: '검색 노출 데이터가 거의 없습니다.',
      detail: 'Search Console 기준 최근 기간 노출이 잡히지 않았습니다. 색인 상태와 브랜딩 키워드 노출을 먼저 확인해야 합니다.',
    })
  }

  if (summary.impressions >= 200 && summary.ctr < 0.02) {
    issues.push({
      type: 'ctr',
      severity: 'warning',
      title: '전체 CTR이 낮습니다.',
      detail: `최근 기간 CTR이 ${(summary.ctr * 100).toFixed(2)}%입니다. 제목과 설명문을 검색 의도에 더 맞춰야 합니다.`,
    })
  }

  if (lowCtrPages.length) {
    issues.push({
      type: 'page_ctr',
      severity: 'warning',
      title: `노출은 있는데 클릭이 약한 페이지 ${lowCtrPages.length}개`,
      detail: lowCtrPages.slice(0, 3).map((row) => row.page).join(', '),
    })
  }

  if (weakQueries.length) {
    issues.push({
      type: 'query_ctr',
      severity: 'warning',
      title: '클릭률이 약한 검색어가 보입니다.',
      detail: weakQueries.slice(0, 3).map((row) => row.query).join(', '),
    })
  }

  if (notIndexed.length) {
    issues.push({
      type: 'indexing',
      severity: 'critical',
      title: `핵심 페이지 ${notIndexed.length}개가 정상 색인 상태가 아닙니다.`,
      detail: notIndexed.slice(0, 3).map((item) => item.url).join(', '),
    })
  }

  if (opportunityPages.length) {
    opportunities.push({
      type: 'position',
      title: '조금만 다듬으면 클릭을 더 받을 페이지가 있습니다.',
      detail: opportunityPages.slice(0, 3).map((row) => `${row.page} (평균 ${row.position.toFixed(1)}위)`).join(', '),
    })
  }

  if (topQueries.length) {
    wins.push({
      type: 'queries',
      title: '현재 가장 많이 잡히는 검색어',
      detail: topQueries.slice(0, 3).map((row) => row.query).join(', '),
    })
  }

  return { issues, opportunities, wins }
}

async function fetchFreshDiagnostics(env, days) {
  const accessToken = await getAccessToken(env)
  const { siteUrl, siteSource } = await resolveSiteUrl(accessToken, env)
  const dateRanges = buildDateRanges(days)

  const [summaryCurrent, summaryPrevious, topQueries, topPages, dailyTrend, inspections] = await Promise.all([
    searchAnalyticsQuery(accessToken, siteUrl, {
      startDate: dateRanges.current.startDate,
      endDate: dateRanges.current.endDate,
      dataState: 'final',
    }),
    searchAnalyticsQuery(accessToken, siteUrl, {
      startDate: dateRanges.previous.startDate,
      endDate: dateRanges.previous.endDate,
      dataState: 'final',
    }),
    searchAnalyticsQuery(accessToken, siteUrl, {
      startDate: dateRanges.current.startDate,
      endDate: dateRanges.current.endDate,
      dimensions: ['query'],
      rowLimit: SEARCH_CONSOLE_MAX_ROWS,
      dataState: 'final',
    }),
    searchAnalyticsQuery(accessToken, siteUrl, {
      startDate: dateRanges.current.startDate,
      endDate: dateRanges.current.endDate,
      dimensions: ['page'],
      rowLimit: SEARCH_CONSOLE_MAX_ROWS,
      dataState: 'final',
    }),
    searchAnalyticsQuery(accessToken, siteUrl, {
      startDate: dateRanges.current.startDate,
      endDate: dateRanges.current.endDate,
      dimensions: ['date'],
      rowLimit: days,
      dataState: 'final',
    }),
    Promise.all(
      buildCoreInspectionUrls(env).map(async (inspectionUrl) => {
        try {
          return await inspectUrl(accessToken, siteUrl, inspectionUrl)
        } catch (error) {
          return {
            url: inspectionUrl,
            verdict: 'ERROR',
            coverage_state: '',
            indexing_state: '',
            robots_txt_state: '',
            page_fetch_state: '',
            last_crawl_time: null,
            google_canonical: '',
            user_canonical: '',
            referring_urls_count: 0,
            error_message: error?.message || 'Inspection failed',
          }
        }
      })
    ),
  ])

  const currentSummary = toMetricRow(summaryCurrent?.rows?.[0] || {})
  const previousSummary = toMetricRow(summaryPrevious?.rows?.[0] || {})
  const queryRows = toTopRows(topQueries?.rows || [], 'query')
  const pageRows = toTopRows(topPages?.rows || [], 'page')
  const dailyRows = (dailyTrend?.rows || []).map((row) => ({
    date: row?.keys?.[0] || '',
    ...toMetricRow(row),
  }))
  const diagnostics = summarizeDiagnostics(currentSummary, queryRows, pageRows, inspections)

  return {
    connected: true,
    configured: true,
    site_url: siteUrl,
    site_source: siteSource,
    days,
    data_through: dateRanges.current.endDate,
    summary: currentSummary,
    previous_summary: previousSummary,
    deltas: {
      clicks: toDelta(currentSummary.clicks, previousSummary.clicks),
      impressions: toDelta(currentSummary.impressions, previousSummary.impressions),
      ctr: toDelta(currentSummary.ctr, previousSummary.ctr),
      position: currentSummary.position - previousSummary.position,
    },
    top_queries: queryRows,
    top_pages: pageRows,
    daily: dailyRows,
    inspections,
    diagnostics,
    error_code: null,
    error_message: null,
    setup_hint: null,
  }
}

async function refreshSearchConsoleCache(env, days) {
  const claimed = await markRefreshStarted(env, days)
  if (!claimed) return null

  try {
    const payload = await fetchFreshDiagnostics(env, days)
    return await persistCache(env, days, payload)
  } catch (error) {
    await markRefreshFailed(env, days, error?.message || String(error))
    throw error
  }
}

export async function getSearchConsoleDiagnostics(env, ctx, daysInput) {
  const days = clampDays(daysInput)
  const cached = await readSearchConsoleCache(env, days)
  const hasCachedPayload = Boolean(cached.payload)
  const stale = isCacheStale(cached.row?.fetched_at)

  if (hasCachedPayload) {
    if (stale && ctx?.waitUntil) {
      ctx.waitUntil(refreshSearchConsoleCache(env, days).catch((error) => {
        console.warn('Search Console 캐시 갱신 실패:', error?.message || error)
      }))
    }

    return {
      ...cached.payload,
      stale,
    }
  }

  try {
    const fresh = await refreshSearchConsoleCache(env, days)
    return {
      ...(fresh || buildFailurePayload(days, new SearchConsoleError('Search Console 데이터를 준비하지 못했습니다.'))),
      stale: false,
    }
  } catch (error) {
    return buildFailurePayload(days, error)
  }
}
