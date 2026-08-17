import fs from 'node:fs'
import path from 'node:path'
import { rootDir } from './env.mjs'

export const loadJson = (filePath) => {
  return JSON.parse(fs.readFileSync(filePath, 'utf8'))
}

export const loadNegativeKeywords = () => {
  const filePath = path.join(rootDir, 'scripts', 'google-ads', 'data', 'negative-keywords.kr.json')
  return loadJson(filePath)
}

export const loadBlueprint = (filePath, defaultLandingUrl) => {
  const blueprint = loadJson(filePath)
  if (!blueprint.landingPageUrl) {
    blueprint.landingPageUrl = defaultLandingUrl
  }
  return blueprint
}

export const krwToMicros = (amount) => {
  return Math.round(Number(amount || 0) * 1_000_000)
}

export const slugify = (value) => {
  return String(value || '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
}
