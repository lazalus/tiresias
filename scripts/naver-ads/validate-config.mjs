import { loadNaverAdsConfig } from './lib/env.mjs'
import { NaverAdsClient } from './lib/client.mjs'

const config = loadNaverAdsConfig()
const client = new NaverAdsClient(config)

const [campaigns, adgroups, channels] = await Promise.all([
  client.getCampaigns(),
  client.getAdgroups(),
  client.request('/ncc/channels', { method: 'GET' }),
])

console.log(JSON.stringify({
  ok: true,
  customerId: config.customerId,
  baseUrl: config.baseUrl,
  campaignCount: Array.isArray(campaigns) ? campaigns.length : 0,
  adgroupCount: Array.isArray(adgroups) ? adgroups.length : 0,
  businessChannelCount: Array.isArray(channels) ? channels.length : 0,
}, null, 2))
