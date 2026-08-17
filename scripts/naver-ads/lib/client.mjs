import { buildNaverAdsHeaders } from './auth.mjs'

const appendQuery = (pathname, query = {}) => {
  const entries = Object.entries(query).filter(([, value]) => value != null && value !== '')
  if (entries.length === 0) {
    return pathname
  }

  const params = new URLSearchParams()
  for (const [key, value] of entries) {
    if (Array.isArray(value)) {
      for (const item of value) {
        params.append(key, item)
      }
      continue
    }
    params.append(key, String(value))
  }

  return `${pathname}?${params.toString()}`
}

export class NaverAdsClient {
  constructor(config) {
    this.config = config
  }

  async request(pathname, { method = 'GET', query = {}, body } = {}) {
    const pathWithQuery = appendQuery(pathname, query)
    const headers = buildNaverAdsHeaders({
      method,
      uri: pathname,
      config: this.config,
    })

    const response = await fetch(`${this.config.baseUrl}${pathWithQuery}`, {
      method,
      headers,
      body: body == null ? undefined : JSON.stringify(body),
    })

    const text = await response.text()
    const payload = text ? JSON.parse(text) : null

    if (!response.ok) {
      throw new Error(`Naver Ads API request failed (${response.status}) ${pathname}: ${text}`)
    }

    return payload
  }

  async getCustomerLinks(type = 'MYCLIENTS') {
    return this.request('/customer-links', {
      method: 'GET',
      query: { type },
    })
  }

  async getCampaigns() {
    return this.request('/ncc/campaigns', { method: 'GET' })
  }

  async getCampaign(campaignId) {
    return this.request(`/ncc/campaigns/${campaignId}`, { method: 'GET' })
  }

  async createCampaign(campaign) {
    return this.request('/ncc/campaigns', {
      method: 'POST',
      body: {
        customerId: Number(this.config.customerId),
        ...campaign,
      },
    })
  }

  async deleteCampaign(campaignId) {
    return this.request(`/ncc/campaigns/${campaignId}`, { method: 'DELETE' })
  }

  async getAdgroups() {
    return this.request('/ncc/adgroups', { method: 'GET' })
  }

  async getAdgroupsByCampaign(nccCampaignId) {
    return this.request('/ncc/adgroups', {
      method: 'GET',
      query: { nccCampaignId },
    })
  }

  async createAdgroup(group) {
    return this.request('/ncc/adgroups', {
      method: 'POST',
      body: {
        customerId: Number(this.config.customerId),
        ...group,
      },
    })
  }

  async getKeywords(nccAdgroupId) {
    return this.request('/ncc/keywords', {
      method: 'GET',
      query: { nccAdgroupId },
    })
  }

  async createKeywords(nccAdgroupId, keywords) {
    return this.request('/ncc/keywords', {
      method: 'POST',
      query: { nccAdgroupId },
      body: keywords,
    })
  }

  async getAds(nccAdgroupId) {
    return this.request('/ncc/ads', {
      method: 'GET',
      query: { nccAdgroupId },
    })
  }

  async createAd(ad) {
    return this.request('/ncc/ads', {
      method: 'POST',
      body: {
        customerId: Number(this.config.customerId),
        ...ad,
      },
    })
  }

  async estimatePerformanceBulk(items) {
    return this.request('/estimate/performance-bulk', {
      method: 'POST',
      body: { items },
    })
  }
}
