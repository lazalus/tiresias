import { loadNaverAdsConfig } from './lib/env.mjs'
import { parseArgs, getArgValue } from './lib/cli.mjs'
import { NaverAdsClient } from './lib/client.mjs'

const args = parseArgs()
const config = loadNaverAdsConfig()
const client = new NaverAdsClient(config)

const rawKeywords = getArgValue(args, 'keywords', '')
const keywords = rawKeywords
  .split(',')
  .map((value) => value.trim())
  .filter(Boolean)

if (keywords.length === 0) {
  throw new Error('Pass --keywords "정책 시뮬레이션,시장 반응 예측"')
}

const bid = Number(getArgValue(args, 'bid', '1500'))
const device = getArgValue(args, 'device', 'PC').toUpperCase()

const estimates = await client.estimatePerformanceBulk(
  keywords.map((keyword) => ({
    device,
    keywordplus: true,
    keyword,
    bid,
  }))
)

console.log(JSON.stringify({
  customerId: config.customerId,
  device,
  bid,
  estimates,
}, null, 2))
