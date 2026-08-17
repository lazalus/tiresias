import { getGoogleAdsAccessToken } from './auth.mjs'

const buildHeaders = async (config) => {
  const accessToken = await getGoogleAdsAccessToken(config)
  const headers = {
    Authorization: `Bearer ${accessToken}`,
    'developer-token': config.developerToken,
    'Content-Type': 'application/json',
  }

  if (config.loginCustomerId) {
    headers['login-customer-id'] = config.loginCustomerId
  }

  return headers
}

export class GoogleAdsClient {
  constructor(config) {
    this.config = config
    this.baseUrl = `https://googleads.googleapis.com/${config.apiVersion}`
  }

  async request(path, { method = 'POST', body } = {}) {
    const headers = await buildHeaders(this.config)
    const response = await fetch(`${this.baseUrl}${path}`, {
      method,
      headers,
      body: body == null ? undefined : JSON.stringify(body),
    })

    if (!response.ok) {
      const text = await response.text()
      throw new Error(`Google Ads API request failed (${response.status}) ${path}: ${text}`)
    }

    if (response.status === 204) {
      return null
    }

    return response.json()
  }

  async search(query, customerId = this.config.customerId, pageToken = null) {
    const body = { query }
    if (pageToken) {
      body.pageToken = pageToken
    }
    return this.request(`/customers/${customerId}/googleAds:search`, { body })
  }

  async searchAll(query, customerId = this.config.customerId) {
    const rows = []
    let nextPageToken = null

    do {
      const payload = await this.search(query, customerId, nextPageToken)
      rows.push(...(payload.results || []))
      nextPageToken = payload.nextPageToken || null
    } while (nextPageToken)

    return rows
  }

  async mutate(resource, operations, options = {}) {
    return this.request(`/customers/${this.config.customerId}/${resource}:mutate`, {
      body: {
        operations,
        partialFailure: Boolean(options.partialFailure),
        validateOnly: Boolean(options.validateOnly),
      },
    })
  }

  async createConversionAction(operation, options = {}) {
    return this.request(`/customers/${this.config.customerId}/conversionActions:mutate`, {
      body: {
        operations: [operation],
        validateOnly: Boolean(options.validateOnly),
      },
    })
  }
}

export const findSingleResult = async (client, query) => {
  const rows = await client.searchAll(query)
  return rows[0] || null
}

export const getIdFromResourceName = (resourceName) => {
  const match = String(resourceName || '').match(/\/(\d+)$/)
  return match ? match[1] : null
}
