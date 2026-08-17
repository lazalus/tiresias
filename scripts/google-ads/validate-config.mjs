import { loadGoogleAdsConfig } from './lib/env.mjs'

try {
  const config = loadGoogleAdsConfig()
  console.log(JSON.stringify({
    ok: true,
    customerId: config.customerId,
    loginCustomerId: config.loginCustomerId || null,
    apiVersion: config.apiVersion,
    defaultLandingUrl: config.defaultLandingUrl,
  }, null, 2))
} catch (error) {
  console.error(JSON.stringify({
    ok: false,
    error: error.message,
  }, null, 2))
  process.exit(1)
}
