import { loadGoogleAdsConfig } from './lib/env.mjs'
import { GoogleAdsClient } from './lib/client.mjs'
import { parseArgs, getArgValue } from './lib/cli.mjs'

const args = parseArgs()
const config = loadGoogleAdsConfig()
const client = new GoogleAdsClient(config)

const campaignNameFilter = getArgValue(args, 'campaign')
const days = Number(getArgValue(args, 'days', '14'))

const filters = [
  `segments.date DURING LAST_${days}_DAYS`,
  'metrics.impressions > 0',
]

if (campaignNameFilter) {
  filters.push(`campaign.name LIKE '%${campaignNameFilter.replace(/'/g, "\\'")}%'`)
}

const query = `
  SELECT
    campaign.name,
    ad_group.name,
    search_term_view.search_term,
    metrics.impressions,
    metrics.clicks,
    metrics.cost_micros,
    metrics.conversions,
    metrics.conversions_value
  FROM search_term_view
  WHERE ${filters.join(' AND ')}
  ORDER BY metrics.clicks DESC
  LIMIT 200
`

const rows = await client.searchAll(query)
console.log(JSON.stringify({
  rowCount: rows.length,
  rows,
}, null, 2))
