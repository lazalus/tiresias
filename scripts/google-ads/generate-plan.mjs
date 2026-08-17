import path from 'node:path'
import { optionalEnv, rootDir, sanitizeCustomerId } from './lib/env.mjs'
import { parseArgs, resolveBlueprintPaths } from './lib/cli.mjs'
import { loadBlueprint, loadNegativeKeywords } from './lib/blueprints.mjs'

const args = parseArgs()
const defaultLandingUrl = optionalEnv('GOOGLE_ADS_DEFAULT_LANDING_URL', 'https://tiresiasview.com')
const customerId = sanitizeCustomerId(optionalEnv('GOOGLE_ADS_CUSTOMER_ID'))
const negativeKeywords = loadNegativeKeywords()

const plans = resolveBlueprintPaths(args).map((blueprintPath) => {
  const blueprint = loadBlueprint(blueprintPath, defaultLandingUrl)
  return {
    file: path.relative(rootDir, blueprintPath),
    campaignName: blueprint.campaignName,
    channel: blueprint.channelType,
    landingPageUrl: blueprint.landingPageUrl,
    dailyBudgetKrw: blueprint.dailyBudgetKrw,
    biddingStrategy: blueprint.biddingStrategy,
    locales: blueprint.locales,
    adGroupCount: blueprint.adGroups.length,
    adGroups: blueprint.adGroups.map((adGroup) => ({
      name: adGroup.name,
      keywordCount: adGroup.keywords.length,
      headlineCount: adGroup.responsiveSearchAd.headlines.length,
      descriptionCount: adGroup.responsiveSearchAd.descriptions.length,
    })),
  }
})

console.log(JSON.stringify({
  customerId: customerId || null,
  defaultLandingUrl,
  negativeKeywords,
  plans,
}, null, 2))
