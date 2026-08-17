import path from 'node:path'
import { loadGoogleAdsConfig, rootDir } from './lib/env.mjs'
import { GoogleAdsClient, findSingleResult } from './lib/client.mjs'
import { parseArgs, hasFlag, resolveBlueprintPaths } from './lib/cli.mjs'
import { krwToMicros, loadBlueprint, loadNegativeKeywords } from './lib/blueprints.mjs'

const args = parseArgs()
const apply = hasFlag(args, 'apply')
const config = loadGoogleAdsConfig()
const client = new GoogleAdsClient(config)
const negativeKeywords = loadNegativeKeywords()

const today = new Date()
const formatDate = (date) => date.toISOString().slice(0, 10).replace(/-/g, '')

const buildBiddingBlock = (blueprint) => {
  switch (blueprint.biddingStrategy) {
    case 'MAXIMIZE_CONVERSIONS':
      return { maximizeConversions: {} }
    case 'MANUAL_CPC':
      return { manualCpc: {} }
    case 'MAXIMIZE_CLICKS':
    default:
      return { maximizeClicks: {} }
  }
}

const escapeGaql = (value) => String(value || '').replace(/'/g, "\\'")

const ensureCampaignBudget = async (blueprint) => {
  const budgetName = `${blueprint.campaignName} | Budget`
  const existing = await findSingleResult(client, `
    SELECT campaign_budget.resource_name, campaign_budget.name
    FROM campaign_budget
    WHERE campaign_budget.name = '${escapeGaql(budgetName)}'
    LIMIT 1
  `)

  if (existing?.campaignBudget?.resourceName) {
    return existing.campaignBudget.resourceName
  }

  const operation = {
    create: {
      name: budgetName,
      amountMicros: String(krwToMicros(blueprint.dailyBudgetKrw)),
      deliveryMethod: 'STANDARD',
      explicitlyShared: false,
    },
  }

  if (!apply) {
    return `dry-run:campaignBudgets/${budgetName}`
  }

  const response = await client.mutate('campaignBudgets', [operation])
  return response.results?.[0]?.resourceName
}

const resolveLocationResourceNames = async (countryCodes) => {
  const resourceNames = []
  for (const countryCode of countryCodes) {
    const row = await findSingleResult(client, `
      SELECT geo_target_constant.resource_name
      FROM geo_target_constant
      WHERE geo_target_constant.country_code = '${escapeGaql(countryCode)}'
        AND geo_target_constant.target_type = 'Country'
      LIMIT 1
    `)

    if (!row?.geoTargetConstant?.resourceName) {
      throw new Error(`Geo target constant not found for country code: ${countryCode}`)
    }

    resourceNames.push(row.geoTargetConstant.resourceName)
  }

  return resourceNames
}

const resolveLanguageResourceNames = async (languageCodes) => {
  const resourceNames = []
  for (const languageCode of languageCodes) {
    const row = await findSingleResult(client, `
      SELECT language_constant.resource_name
      FROM language_constant
      WHERE language_constant.code = '${escapeGaql(languageCode)}'
      LIMIT 1
    `)

    if (!row?.languageConstant?.resourceName) {
      throw new Error(`Language constant not found for language code: ${languageCode}`)
    }

    resourceNames.push(row.languageConstant.resourceName)
  }

  return resourceNames
}

const ensureCampaign = async (blueprint, budgetResourceName) => {
  const existing = await findSingleResult(client, `
    SELECT campaign.resource_name, campaign.name
    FROM campaign
    WHERE campaign.name = '${escapeGaql(blueprint.campaignName)}'
    LIMIT 1
  `)

  if (existing?.campaign?.resourceName) {
    return existing.campaign.resourceName
  }

  const operation = {
    create: {
      name: blueprint.campaignName,
      status: 'PAUSED',
      advertisingChannelType: blueprint.channelType || 'SEARCH',
      campaignBudget: budgetResourceName,
      startDate: blueprint.startDate || formatDate(today),
      networkSettings: {
        targetGoogleSearch: true,
        targetSearchNetwork: false,
        targetContentNetwork: false,
        targetPartnerSearchNetwork: Boolean(blueprint.searchPartners),
      },
      ...buildBiddingBlock(blueprint),
    },
  }

  if (!apply) {
    return `dry-run:campaigns/${blueprint.campaignName}`
  }

  const response = await client.mutate('campaigns', [operation])
  return response.results?.[0]?.resourceName
}

const ensureCampaignCriteria = async (campaignResourceName, blueprint) => {
  if (!apply) {
    return
  }

  const existingCriteria = await client.searchAll(`
    SELECT campaign_criterion.resource_name
    FROM campaign_criterion
    WHERE campaign_criterion.campaign = '${escapeGaql(campaignResourceName)}'
  `)

  if (existingCriteria.length > 0) {
    return
  }

  const locationResourceNames = await resolveLocationResourceNames(blueprint.locales.countryCodes || [])
  const languageResourceNames = await resolveLanguageResourceNames(blueprint.locales.languageCodes || [])

  const operations = [
    ...locationResourceNames.map((resourceName) => ({
      create: {
        campaign: campaignResourceName,
        location: {
          geoTargetConstant: resourceName,
        },
      },
    })),
    ...languageResourceNames.map((resourceName) => ({
      create: {
        campaign: campaignResourceName,
        language: {
          languageConstant: resourceName,
        },
      },
    })),
    ...(negativeKeywords.keywords || []).map((keyword) => ({
      create: {
        campaign: campaignResourceName,
        negative: true,
        keyword: {
          text: keyword,
          matchType: 'PHRASE',
        },
      },
    })),
  ]

  if (operations.length > 0) {
    await client.mutate('campaignCriteria', operations)
  }
}

const ensureAdGroup = async (campaignResourceName, adGroup) => {
  const existing = await findSingleResult(client, `
    SELECT ad_group.resource_name, ad_group.name
    FROM ad_group
    WHERE ad_group.name = '${escapeGaql(adGroup.name)}'
      AND ad_group.campaign = '${escapeGaql(campaignResourceName)}'
    LIMIT 1
  `)

  if (existing?.adGroup?.resourceName) {
    return existing.adGroup.resourceName
  }

  const operation = {
    create: {
      campaign: campaignResourceName,
      name: adGroup.name,
      status: 'PAUSED',
      type: 'SEARCH_STANDARD',
    },
  }

  if (adGroup.cpcBidKrw) {
    operation.create.cpcBidMicros = String(krwToMicros(adGroup.cpcBidKrw))
  }

  if (!apply) {
    return `dry-run:adGroups/${adGroup.name}`
  }

  const response = await client.mutate('adGroups', [operation])
  return response.results?.[0]?.resourceName
}

const ensureKeywords = async (adGroupResourceName, adGroup) => {
  if (!apply) {
    return adGroup.keywords.length
  }

  const existingRows = await client.searchAll(`
    SELECT ad_group_criterion.keyword.text, ad_group_criterion.keyword.match_type
    FROM keyword_view
    WHERE ad_group.resource_name = '${escapeGaql(adGroupResourceName)}'
  `)

  const existingKeys = new Set(existingRows.map((row) => {
    const text = row.adGroupCriterion?.keyword?.text || ''
    const matchType = row.adGroupCriterion?.keyword?.matchType || ''
    return `${text}::${matchType}`
  }))

  const operations = adGroup.keywords
    .filter((keyword) => !existingKeys.has(`${keyword.text}::${keyword.matchType}`))
    .map((keyword) => ({
      create: {
        adGroup: adGroupResourceName,
        status: 'ENABLED',
        keyword: {
          text: keyword.text,
          matchType: keyword.matchType,
        },
      },
    }))

  if (operations.length > 0) {
    await client.mutate('adGroupCriteria', operations)
  }

  return operations.length
}

const ensureResponsiveSearchAd = async (adGroupResourceName, blueprint, adGroup) => {
  if (!apply) {
    return
  }

  const existing = await findSingleResult(client, `
    SELECT ad_group_ad.resource_name
    FROM ad_group_ad
    WHERE ad_group_ad.ad_group = '${escapeGaql(adGroupResourceName)}'
      AND ad_group_ad.status != 'REMOVED'
    LIMIT 1
  `)

  if (existing?.adGroupAd?.resourceName) {
    return
  }

  const operation = {
    create: {
      adGroup: adGroupResourceName,
      status: 'PAUSED',
      ad: {
        finalUrls: [adGroup.landingPageUrl || blueprint.landingPageUrl],
        responsiveSearchAd: {
          headlines: adGroup.responsiveSearchAd.headlines.map((text) => ({ text })),
          descriptions: adGroup.responsiveSearchAd.descriptions.map((text) => ({ text })),
        },
      },
    },
  }

  await client.mutate('adGroupAds', [operation])
}

const blueprintPaths = resolveBlueprintPaths(args)
const summary = []

for (const blueprintPath of blueprintPaths) {
  const blueprint = loadBlueprint(blueprintPath, config.defaultLandingUrl)
  const budgetResourceName = await ensureCampaignBudget(blueprint)
  const campaignResourceName = await ensureCampaign(blueprint, budgetResourceName)

  if (apply) {
    await ensureCampaignCriteria(campaignResourceName, blueprint)
  }

  const adGroups = []
  for (const adGroup of blueprint.adGroups) {
    const adGroupResourceName = await ensureAdGroup(campaignResourceName, adGroup)
    const newKeywordCount = await ensureKeywords(adGroupResourceName, adGroup)
    await ensureResponsiveSearchAd(adGroupResourceName, blueprint, adGroup)
    adGroups.push({
      name: adGroup.name,
      resourceName: adGroupResourceName,
      keywordCount: adGroup.keywords.length,
      newKeywordCount,
    })
  }

  summary.push({
    blueprint: path.relative(rootDir, blueprintPath),
    apply,
    campaignName: blueprint.campaignName,
    budgetResourceName,
    campaignResourceName,
    adGroups,
  })
}

console.log(JSON.stringify({ summary }, null, 2))
