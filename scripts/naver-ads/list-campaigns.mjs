import { loadNaverAdsConfig } from './lib/env.mjs'
import { NaverAdsClient } from './lib/client.mjs'

const config = loadNaverAdsConfig()
const client = new NaverAdsClient(config)

const [campaigns, adgroups] = await Promise.all([
  client.getCampaigns(),
  client.getAdgroups(),
])

console.log(JSON.stringify({
  customerId: config.customerId,
  campaignCount: Array.isArray(campaigns) ? campaigns.length : 0,
  adgroupCount: Array.isArray(adgroups) ? adgroups.length : 0,
  campaigns: Array.isArray(campaigns) ? campaigns.slice(0, 20) : [],
}, null, 2))
