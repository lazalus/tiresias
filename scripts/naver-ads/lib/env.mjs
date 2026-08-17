import fs from 'node:fs'
import path from 'node:path'

const ROOT_DIR = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../../..')

const parseEnvFile = (filePath) => {
  if (!fs.existsSync(filePath)) {
    return
  }

  const raw = fs.readFileSync(filePath, 'utf8')
  for (const line of raw.split(/\r?\n/)) {
    const trimmed = line.trim()
    if (!trimmed || trimmed.startsWith('#')) {
      continue
    }

    const separatorIndex = trimmed.indexOf('=')
    if (separatorIndex === -1) {
      continue
    }

    const key = trimmed.slice(0, separatorIndex).trim()
    const value = trimmed.slice(separatorIndex + 1).trim()
    if (!process.env[key]) {
      process.env[key] = value.replace(/^['"]|['"]$/g, '')
    }
  }
}

parseEnvFile(path.join(ROOT_DIR, '.env'))
parseEnvFile(path.join(ROOT_DIR, '.env.local'))

export const rootDir = ROOT_DIR

export const requireEnv = (key) => {
  const value = process.env[key] ? String(process.env[key]).trim() : ''
  if (!value) {
    throw new Error(`Missing required environment variable: ${key}`)
  }
  return value
}

export const optionalEnv = (key, fallback = '') => {
  const value = process.env[key]
  return value == null || String(value).trim() === '' ? fallback : String(value).trim()
}

export const sanitizeCustomerId = (value) => {
  return String(value || '').replace(/\D/g, '')
}

export const loadNaverAdsConfig = () => {
  return {
    accessLicense: requireEnv('NAVER_ADS_ACCESS_LICENSE'),
    secretKey: requireEnv('NAVER_ADS_SECRET_KEY'),
    customerId: sanitizeCustomerId(requireEnv('NAVER_ADS_CUSTOMER_ID')),
    baseUrl: optionalEnv('NAVER_ADS_BASE_URL', 'https://api.searchad.naver.com'),
    defaultLandingUrl: optionalEnv('NAVER_ADS_DEFAULT_LANDING_URL', 'https://tiresiasview.com'),
  }
}
