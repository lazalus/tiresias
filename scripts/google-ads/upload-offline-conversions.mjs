import fs from 'node:fs'
import path from 'node:path'
import { loadGoogleAdsConfig, rootDir } from './lib/env.mjs'
import { GoogleAdsClient, findSingleResult } from './lib/client.mjs'
import { parseArgs, getArgValue } from './lib/cli.mjs'

const args = parseArgs()
const fileArg = getArgValue(args, 'file')

if (!fileArg) {
  console.error('Usage: npm run ads:conversions:upload -- --file path/to/conversions.json')
  process.exit(1)
}

const config = loadGoogleAdsConfig()
const client = new GoogleAdsClient(config)
const absolutePath = path.isAbsolute(fileArg) ? fileArg : path.join(rootDir, fileArg)
const conversions = JSON.parse(fs.readFileSync(absolutePath, 'utf8'))

const byActionName = new Map()
for (const row of conversions) {
  byActionName.set(row.conversionActionName, true)
}

const actionResourceNames = new Map()
for (const conversionActionName of byActionName.keys()) {
  const action = await findSingleResult(client, `
    SELECT conversion_action.resource_name, conversion_action.name
    FROM conversion_action
    WHERE conversion_action.name = '${String(conversionActionName).replace(/'/g, "\\'")}'
    LIMIT 1
  `)

  if (!action?.conversionAction?.resourceName) {
    throw new Error(`Conversion action not found: ${conversionActionName}`)
  }

  actionResourceNames.set(conversionActionName, action.conversionAction.resourceName)
}

const conversionsPayload = conversions.map((row) => {
  if (!row.gclid && !row.gbraid && !row.wbraid) {
    throw new Error(`Conversion row is missing gclid/gbraid/wbraid: ${JSON.stringify(row)}`)
  }

  return {
    conversionAction: actionResourceNames.get(row.conversionActionName),
    conversionDateTime: row.conversionDateTime,
    conversionValue: Number(row.conversionValue || 0),
    currencyCode: row.currencyCode || 'KRW',
    orderId: row.orderId || undefined,
    gclid: row.gclid || undefined,
    gbraid: row.gbraid || undefined,
    wbraid: row.wbraid || undefined,
  }
})

const response = await client.request(`/customers/${config.customerId}:uploadClickConversions`, {
  body: {
    conversions: conversionsPayload,
    partialFailure: true,
  },
})

console.log(JSON.stringify(response, null, 2))
