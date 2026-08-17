import { loadGoogleAdsConfig } from './lib/env.mjs'
import { GoogleAdsClient, findSingleResult } from './lib/client.mjs'
import { parseArgs, hasFlag } from './lib/cli.mjs'

const args = parseArgs()
const apply = hasFlag(args, 'apply')

const config = loadGoogleAdsConfig()
const client = new GoogleAdsClient(config)

const escapeGaql = (value) => String(value || '').replace(/'/g, "\\'")

const desiredActions = [
  {
    name: 'signup_complete',
    category: 'SIGNUP',
    type: 'WEBPAGE',
    status: 'ENABLED',
    valueSettings: {
      defaultValue: 1,
      alwaysUseDefaultValue: true,
    },
    countingType: 'ONE_PER_CLICK',
    primaryForGoal: false,
  },
  {
    name: 'quote_requested',
    category: 'LEAD',
    type: 'WEBPAGE',
    status: 'ENABLED',
    valueSettings: {
      defaultValue: 1,
      alwaysUseDefaultValue: true,
    },
    countingType: 'ONE_PER_CLICK',
    primaryForGoal: false,
  },
  {
    name: 'purchase_completed',
    category: 'PURCHASE',
    type: 'WEBPAGE',
    status: 'ENABLED',
    valueSettings: {
      defaultValue: 0,
      alwaysUseDefaultValue: false,
    },
    countingType: 'ONE_PER_CLICK',
    primaryForGoal: true,
  },
]

const summary = []

for (const action of desiredActions) {
  const existing = await findSingleResult(client, `
    SELECT
      conversion_action.resource_name,
      conversion_action.name,
      conversion_action.status,
      conversion_action.category,
      conversion_action.type
    FROM conversion_action
    WHERE conversion_action.name = '${escapeGaql(action.name)}'
    LIMIT 1
  `)

  if (existing?.conversionAction?.resourceName) {
    summary.push({
      name: action.name,
      status: 'exists',
      resourceName: existing.conversionAction.resourceName,
      category: existing.conversionAction.category,
      type: existing.conversionAction.type,
    })
    continue
  }

  const operation = {
    create: {
      name: action.name,
      category: action.category,
      type: action.type,
      status: action.status,
      primaryForGoal: action.primaryForGoal,
      countingType: action.countingType,
      clickThroughLookbackWindowDays: 30,
      viewThroughLookbackWindowDays: 1,
      valueSettings: action.valueSettings,
    },
  }

  if (!apply) {
    summary.push({
      name: action.name,
      status: 'would_create',
      operation,
    })
    continue
  }

  const response = await client.createConversionAction(operation)
  summary.push({
    name: action.name,
    status: 'created',
    resourceName: response.results?.[0]?.resourceName || null,
  })
}

console.log(JSON.stringify({ apply, summary }, null, 2))
