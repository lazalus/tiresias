import fs from 'node:fs'
import path from 'node:path'
import { rootDir } from './env.mjs'

export const parseArgs = (argv = process.argv.slice(2)) => {
  const args = {
    flags: new Set(),
    values: new Map(),
  }

  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index]
    if (!token.startsWith('--')) {
      continue
    }

    const [rawKey, rawValue] = token.slice(2).split('=')
    const key = rawKey.trim()
    if (rawValue != null) {
      args.values.set(key, rawValue.trim())
      continue
    }

    const nextValue = argv[index + 1]
    if (nextValue && !nextValue.startsWith('--')) {
      args.values.set(key, nextValue.trim())
      index += 1
      continue
    }

    args.flags.add(key)
  }

  return args
}

export const getArgValue = (args, key, fallback = '') => {
  return args.values.has(key) ? args.values.get(key) : fallback
}

export const resolveBlueprintPaths = (args) => {
  const explicitBlueprint = getArgValue(args, 'blueprint')
  if (explicitBlueprint) {
    const absolutePath = path.isAbsolute(explicitBlueprint)
      ? explicitBlueprint
      : path.join(rootDir, explicitBlueprint)
    return [absolutePath]
  }

  const dataDir = path.join(rootDir, 'scripts', 'naver-ads', 'data')
  return fs.readdirSync(dataDir)
    .filter((name) => name.endsWith('.json') && !name.startsWith('negative-'))
    .map((name) => path.join(dataDir, name))
    .sort()
}
