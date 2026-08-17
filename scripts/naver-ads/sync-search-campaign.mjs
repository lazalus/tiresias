import { loadNaverAdsConfig } from './lib/env.mjs'
import { parseArgs, resolveBlueprintPaths } from './lib/cli.mjs'
import { loadBlueprint } from './lib/blueprints.mjs'
import { NaverAdsClient } from './lib/client.mjs'

const DEFAULT_CHANNEL_KEY = 'https://tiresiasview.com'

function normalizeKeyword(value) {
  return String(value || '').trim().replace(/\s+/g, '')
}

function compactText(value) {
  return String(value || '').trim().replace(/\s+/g, ' ')
}

function buildAdFinalUrl(url) {
  return String(url || DEFAULT_CHANNEL_KEY).trim()
}

async function ensureChannelId(client, landingUrl) {
  const channels = await client.request('/ncc/channels', { method: 'GET' })
  const normalizedUrl = new URL(buildAdFinalUrl(landingUrl))
  const normalized = `${normalizedUrl.origin}`
  const matched = (channels || []).find((channel) => channel?.channelKey === normalized)
  if (!matched) {
    throw new Error(`Naver Ads channel not found for ${normalized}`)
  }
  if (matched.status !== 'ELIGIBLE') {
    throw new Error(`Naver Ads channel is not eligible yet: ${matched.statusReason || matched.status}`)
  }
  return matched.nccBusinessChannelId
}

function buildCampaignPayload(blueprint) {
  return {
    name: blueprint.campaignName,
    campaignTp: 'WEB_SITE',
    deliveryMethod: 'STANDARD',
    trackingMode: 'TRACKING_DISABLED',
    usePeriod: false,
    useDailyBudget: true,
    dailyBudget: Number(blueprint.dailyBudgetKrw || 0),
    userLock: false,
  }
}

function buildAdgroupPayload({ campaignId, channelId, adGroup }) {
  return {
    nccCampaignId: campaignId,
    name: adGroup.name,
    pcChannelId: channelId,
    mobileChannelId: channelId,
    adgroupType: 'WEB_SITE',
    bidAmt: 70,
    contentsNetworkBidAmt: 70,
    useCntsNetworkBidAmt: false,
    mobileNetworkBidWeight: 100,
    pcNetworkBidWeight: 100,
    useDailyBudget: false,
    dailyBudget: 0,
    adRollingType: 'PERFORMANCE',
    systemBiddingType: 'NONE',
    useCntsNetworkBidWeight: false,
    contentsNetworkBidWeight: 100,
    useExpSearch: false,
    userLock: false,
  }
}

function buildKeywordPayload(keyword) {
  return {
    keyword: normalizeKeyword(keyword),
    useGroupBidAmt: true,
    bidAmt: 70,
    userLock: false,
  }
}

function buildAds(adGroup, landingPageUrl) {
  const descriptions = Array.isArray(adGroup.ads?.descriptions) ? adGroup.ads.descriptions : []
  const headlines = Array.isArray(adGroup.ads?.headlines) ? adGroup.ads.headlines : []
  const finalUrl = buildAdFinalUrl(landingPageUrl)

  return headlines.map((headline, index) => ({
    type: 'TEXT_45',
    userLock: false,
    ad: {
      headline: compactText(headline),
      description: compactText(descriptions[index % Math.max(1, descriptions.length)] || descriptions[0] || ''),
      pc: {
        final: finalUrl,
        display: finalUrl,
        punyCode: finalUrl,
      },
      mobile: {
        final: finalUrl,
        display: finalUrl,
        punyCode: finalUrl,
      },
    },
  })).filter((item) => item.ad.description)
}

function sameAd(left, right) {
  return compactText(left?.ad?.headline) === compactText(right?.ad?.headline)
    && compactText(left?.ad?.description) === compactText(right?.ad?.description)
    && buildAdFinalUrl(left?.ad?.pc?.final) === buildAdFinalUrl(right?.ad?.pc?.final)
}

const args = parseArgs()
const apply = args.flags.has('apply')
const config = loadNaverAdsConfig()
const client = new NaverAdsClient(config)
const blueprints = resolveBlueprintPaths(args).map((filePath) => loadBlueprint(filePath, config.defaultLandingUrl))

const allCampaigns = await client.getCampaigns()
const summary = []

for (const blueprint of blueprints) {
  const channelId = await ensureChannelId(client, blueprint.landingPageUrl)
  let campaign = (allCampaigns || []).find((item) => item.name === blueprint.campaignName && item.delFlag !== true)
  let campaignCreated = false

  if (!campaign && apply) {
    campaign = await client.createCampaign(buildCampaignPayload(blueprint))
    campaignCreated = true
  }

  const adgroups = campaign ? await client.getAdgroupsByCampaign(campaign.nccCampaignId) : []
  const groupResults = []

  for (const adGroup of blueprint.adGroups) {
    let currentGroup = (adgroups || []).find((item) => item.name === adGroup.name && item.delFlag !== true)
    let groupCreated = false

    if (!currentGroup && apply && campaign) {
      currentGroup = await client.createAdgroup(buildAdgroupPayload({
        campaignId: campaign.nccCampaignId,
        channelId,
        adGroup,
      }))
      groupCreated = true
    }

    const existingKeywords = currentGroup ? await client.getKeywords(currentGroup.nccAdgroupId) : []
    const existingKeywordSet = new Set((existingKeywords || []).map((item) => normalizeKeyword(item.keyword)))
    const keywordPayloads = adGroup.keywords
      .map(buildKeywordPayload)
      .filter((item) => item.keyword && !existingKeywordSet.has(item.keyword))

    let createdKeywords = []
    if (apply && currentGroup && keywordPayloads.length) {
      createdKeywords = await client.createKeywords(currentGroup.nccAdgroupId, keywordPayloads)
    }

    const existingAds = currentGroup ? await client.getAds(currentGroup.nccAdgroupId) : []
    const desiredAds = buildAds(adGroup, blueprint.landingPageUrl)
      .map((ad) => ({ ...ad, nccAdgroupId: currentGroup?.nccAdgroupId }))
      .filter(Boolean)
    const adsToCreate = desiredAds.filter((candidate) => !(existingAds || []).some((item) => sameAd(candidate, item)))

    const createdAds = []
    if (apply && currentGroup) {
      for (const ad of adsToCreate) {
        createdAds.push(await client.createAd(ad))
      }
    }

    groupResults.push({
      name: adGroup.name,
      adgroupId: currentGroup?.nccAdgroupId || null,
      created: groupCreated,
      keywordCreatesRequested: keywordPayloads.map((item) => item.keyword),
      keywordCreatesApplied: Array.isArray(createdKeywords) ? createdKeywords : [],
      adCreatesRequested: adsToCreate.map((item) => item.ad.headline),
      adCreatesApplied: createdAds.map((item) => item.nccAdId),
    })
  }

  summary.push({
    campaignName: blueprint.campaignName,
    campaignId: campaign?.nccCampaignId || null,
    campaignCreated,
    apply,
    landingPageUrl: blueprint.landingPageUrl,
    channelId,
    adGroups: groupResults,
  })
}

console.log(JSON.stringify({ apply, customerId: config.customerId, summary }, null, 2))
