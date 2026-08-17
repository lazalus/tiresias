import fs from 'node:fs'
import path from 'node:path'
import { rootDir } from './env.mjs'

export const loadJson = (filePath) => {
  return JSON.parse(fs.readFileSync(filePath, 'utf8'))
}

export const loadNegativeKeywords = () => {
  const filePath = path.join(rootDir, 'scripts', 'naver-ads', 'data', 'negative-keywords.kr.json')
  return loadJson(filePath)
}

export const loadBlueprint = (filePath, defaultLandingUrl) => {
  const blueprint = loadJson(filePath)
  if (!blueprint.landingPageUrl) {
    blueprint.landingPageUrl = defaultLandingUrl
  }
  return blueprint
}
