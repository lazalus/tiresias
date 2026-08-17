const CLICK_ID_STORAGE_KEY = 'tiresias_marketing_click_ids'
const CONVERSION_DEDUPE_STORAGE_KEY = 'tiresias_marketing_conversion_dedupe'

let initialized = false

const getEnv = (key) => {
  return import.meta.env?.[key] ? String(import.meta.env[key]).trim() : ''
}

const getPrimaryTagId = () => {
  return getEnv('VITE_GOOGLE_TAG_ID') || getEnv('VITE_GA_MEASUREMENT_ID') || getEnv('VITE_GOOGLE_ADS_ID')
}

const getAdditionalTagIds = () => {
  const ids = [getEnv('VITE_GA_MEASUREMENT_ID'), getEnv('VITE_GOOGLE_ADS_ID')].filter(Boolean)
  return [...new Set(ids.filter((id) => id !== getPrimaryTagId()))]
}

const ensureDataLayer = () => {
  window.dataLayer = window.dataLayer || []
  window.gtag = window.gtag || function gtag() {
    window.dataLayer.push(arguments)
  }
}

const loadTagScript = (tagId) => {
  if (!tagId || document.querySelector(`script[data-google-tag="${tagId}"]`)) {
    return
  }

  const script = document.createElement('script')
  script.async = true
  script.src = `https://www.googletagmanager.com/gtag/js?id=${encodeURIComponent(tagId)}`
  script.dataset.googleTag = tagId
  document.head.appendChild(script)
}

const persistClickIdsFromLocation = () => {
  try {
    const params = new URLSearchParams(window.location.search)
    const clickIds = {
      gclid: params.get('gclid') || '',
      gbraid: params.get('gbraid') || '',
      wbraid: params.get('wbraid') || '',
      utm_source: params.get('utm_source') || '',
      utm_medium: params.get('utm_medium') || '',
      utm_campaign: params.get('utm_campaign') || '',
      captured_at: new Date().toISOString(),
    }

    if (!clickIds.gclid && !clickIds.gbraid && !clickIds.wbraid) {
      return
    }

    localStorage.setItem(CLICK_ID_STORAGE_KEY, JSON.stringify(clickIds))
  } catch (_) {
    // Ignore unavailable storage or malformed URLs.
  }
}

export const getStoredClickIds = () => {
  try {
    const raw = localStorage.getItem(CLICK_ID_STORAGE_KEY)
    return raw ? JSON.parse(raw) : null
  } catch (_) {
    return null
  }
}

export const trackPageView = (path) => {
  if (typeof window === 'undefined' || typeof window.gtag !== 'function') {
    return
  }

  const pagePath = path || `${window.location.pathname}${window.location.search}`
  window.gtag('event', 'page_view', {
    page_path: pagePath,
    page_title: document.title,
    page_location: window.location.href,
  })
}

export const trackMarketingEvent = (eventName, params = {}) => {
  if (typeof window === 'undefined' || typeof window.gtag !== 'function' || !eventName) {
    return
  }

  window.gtag('event', eventName, params)
}

const getAdsConversionLabel = (conversionName) => {
  const labelMap = {
    signup_complete: getEnv('VITE_GOOGLE_ADS_SIGNUP_LABEL'),
    quote_requested: getEnv('VITE_GOOGLE_ADS_QUOTE_LABEL'),
    purchase_completed: getEnv('VITE_GOOGLE_ADS_PURCHASE_LABEL'),
  }
  return labelMap[conversionName] || ''
}

export const trackGoogleAdsConversion = (conversionName, params = {}) => {
  const adsId = getEnv('VITE_GOOGLE_ADS_ID')
  const label = getAdsConversionLabel(conversionName)
  if (!adsId || !label || typeof window === 'undefined' || typeof window.gtag !== 'function') {
    return
  }

  const sendTo = `${adsId}/${label}`
  window.gtag('event', 'conversion', {
    send_to: sendTo,
    ...params,
  })
}

const readConversionDedupeMap = () => {
  try {
    const raw = localStorage.getItem(CONVERSION_DEDUPE_STORAGE_KEY)
    return raw ? JSON.parse(raw) : {}
  } catch (_) {
    return {}
  }
}

const writeConversionDedupeMap = (value) => {
  try {
    localStorage.setItem(CONVERSION_DEDUPE_STORAGE_KEY, JSON.stringify(value))
  } catch (_) {
    // Ignore storage failures.
  }
}

export const trackGoogleAdsConversionOnce = (conversionName, dedupeKey, params = {}) => {
  if (!dedupeKey) {
    trackGoogleAdsConversion(conversionName, params)
    return
  }

  const storageKey = `${conversionName}:${dedupeKey}`
  const dedupeMap = readConversionDedupeMap()
  if (dedupeMap[storageKey]) {
    return
  }

  trackGoogleAdsConversion(conversionName, params)
  dedupeMap[storageKey] = new Date().toISOString()
  writeConversionDedupeMap(dedupeMap)
}

export const initMarketing = (router) => {
  if (initialized || typeof window === 'undefined') {
    return
  }

  const primaryTagId = getPrimaryTagId()
  if (!primaryTagId) {
    initialized = true
    return
  }

  ensureDataLayer()
  loadTagScript(primaryTagId)
  for (const tagId of getAdditionalTagIds()) {
    loadTagScript(tagId)
  }

  window.gtag('js', new Date())
  window.gtag('config', primaryTagId, { send_page_view: false })
  for (const tagId of getAdditionalTagIds()) {
    window.gtag('config', tagId, { send_page_view: false })
  }

  persistClickIdsFromLocation()
  trackPageView()

  if (router?.afterEach) {
    router.afterEach((to) => {
      persistClickIdsFromLocation()
      trackPageView(to.fullPath)
    })
  }

  initialized = true
}
