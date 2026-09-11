import { readFileSync, readdirSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { resolve } from 'node:path'
import type { Catalog } from '@xivmits/core'
import { validateCatalog } from '@xivmits/core/schema'

/** Package root, so consumers never need a relative path into node_modules. */
export const dataRoot = fileURLToPath(new URL('../', import.meta.url))
export const fightsDir = resolve(dataRoot, 'fights')
export const iconsFile = resolve(dataRoot, 'icons.json')
export const jobsFile = resolve(dataRoot, 'jobs.json')

const readJson = (path: string) => JSON.parse(readFileSync(path, 'utf8'))

/** Every fight/sheet JSON, keyed by absolute path - validateCatalog reads the
 *  path to check that ids match their location on disk. */
export function readFightFiles(): Record<string, unknown> {
  return Object.fromEntries(readdirSync(fightsDir, { recursive: true, encoding: 'utf8' })
    .filter(path => path.endsWith('.json'))
    .map(path => [`${fightsDir}/${path}`, readJson(resolve(fightsDir, path))]))
}

/** The validated catalog. Node-only (it reads from disk), so apps call it from
 *  a build step and ship the result, rather than at runtime in a browser. */
export function loadCatalog(): Catalog {
  return validateCatalog(readFightFiles(), readJson(iconsFile), readJson(jobsFile))
}
