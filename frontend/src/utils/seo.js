const DEFAULT_TITLE = '테이레시아스 뷰 | 정책·시장·여론 시나리오 분석 AI'
const DEFAULT_DESCRIPTION = '테이레시아스 뷰는 보고서·정책 문서·시장 자료를 업로드하면 AI 에이전트가 반응을 시뮬레이션하고 분석 보고서를 만드는 시나리오 분석 서비스입니다.'
const DEFAULT_OG_IMAGE = 'https://tiresiasview.com/logos1.png'
const MANAGED_META_KEYS = ['description', 'og:title', 'og:description', 'og:url', 'twitter:title', 'twitter:description']

function ensureMeta(selector, attrs) {
  let el = document.head.querySelector(selector)
  if (!el) {
    el = document.createElement('meta')
    Object.entries(attrs).forEach(([key, value]) => el.setAttribute(key, value))
    document.head.appendChild(el)
  }
  return el
}

function ensureCanonicalLink() {
  let link = document.head.querySelector('link[rel="canonical"]')
  if (!link) {
    link = document.createElement('link')
    link.setAttribute('rel', 'canonical')
    document.head.appendChild(link)
  }
  return link
}

function setStructuredData(id, payload) {
  let script = document.head.querySelector(`script[data-seo-jsonld="${id}"]`)
  if (!script) {
    script = document.createElement('script')
    script.type = 'application/ld+json'
    script.dataset.seoJsonld = id
    document.head.appendChild(script)
  }
  script.textContent = JSON.stringify(payload)
}

function removeStructuredData(id) {
  document.head.querySelector(`script[data-seo-jsonld="${id}"]`)?.remove()
}

export function applySeoMeta({
  title = DEFAULT_TITLE,
  description = DEFAULT_DESCRIPTION,
  canonical = 'https://tiresiasview.com',
  robots = 'index,follow',
  ogImage = DEFAULT_OG_IMAGE,
  structuredData = [],
} = {}) {
  document.title = title
  ensureMeta('meta[name="description"]', { name: 'description' }).setAttribute('content', description)
  ensureMeta('meta[property="og:title"]', { property: 'og:title' }).setAttribute('content', title)
  ensureMeta('meta[property="og:description"]', { property: 'og:description' }).setAttribute('content', description)
  ensureMeta('meta[property="og:url"]', { property: 'og:url' }).setAttribute('content', canonical)
  ensureMeta('meta[property="og:image"]', { property: 'og:image' }).setAttribute('content', ogImage)
  ensureMeta('meta[name="twitter:title"]', { name: 'twitter:title' }).setAttribute('content', title)
  ensureMeta('meta[name="twitter:description"]', { name: 'twitter:description' }).setAttribute('content', description)
  ensureMeta('meta[name="robots"]', { name: 'robots' }).setAttribute('content', robots)
  ensureCanonicalLink().setAttribute('href', canonical)

  for (const item of structuredData) {
    if (item?.id && item?.data) {
      setStructuredData(item.id, item.data)
    }
  }
}

export function resetSeoMeta(structuredDataIds = []) {
  document.title = DEFAULT_TITLE
  ensureMeta('meta[name="description"]', { name: 'description' }).setAttribute('content', DEFAULT_DESCRIPTION)
  ensureMeta('meta[property="og:title"]', { property: 'og:title' }).setAttribute('content', DEFAULT_TITLE)
  ensureMeta('meta[property="og:description"]', { property: 'og:description' }).setAttribute('content', DEFAULT_DESCRIPTION)
  ensureMeta('meta[property="og:url"]', { property: 'og:url' }).setAttribute('content', 'https://tiresiasview.com')
  ensureMeta('meta[property="og:image"]', { property: 'og:image' }).setAttribute('content', DEFAULT_OG_IMAGE)
  ensureMeta('meta[name="twitter:title"]', { name: 'twitter:title' }).setAttribute('content', DEFAULT_TITLE)
  ensureMeta('meta[name="twitter:description"]', { name: 'twitter:description' }).setAttribute('content', DEFAULT_DESCRIPTION)
  ensureMeta('meta[name="robots"]', { name: 'robots' }).setAttribute('content', 'index,follow')
  ensureCanonicalLink().setAttribute('href', 'https://tiresiasview.com')

  for (const id of structuredDataIds) {
    removeStructuredData(id)
  }
}

export { DEFAULT_TITLE, DEFAULT_DESCRIPTION, MANAGED_META_KEYS }
