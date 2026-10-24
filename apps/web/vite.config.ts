import react, { reactCompilerPreset } from '@vitejs/plugin-react'
import babel from '@rolldown/plugin-babel'
import { defineConfig, type Plugin } from 'vite'
import { existsSync } from 'node:fs'
import { resolve } from 'node:path'
import { abilitiesFile, fightsDir, iconsFile, jobsFile, loadCatalog } from '@xivmits/encounter-data'
import type { Catalog } from '@xivmits/core'
import { pageInfo, renderMetadata } from './src/seo.ts'

function readCatalog() {
  const catalog = loadCatalog()
  // A map entry pointing at a missing PNG would render a broken image, so fail
  // the build instead. Re-run scripts/fetch_icons.py to regenerate both.
  for (const [name, file] of Object.entries(catalog.icons)) {
    if (!existsSync(resolve('public/icons', file))) {
      throw new Error(`icons.json: ${name} -> public/icons/${file} is missing`)
    }
  }
  return catalog
}

function toIndex(catalog: Catalog) {
  return {
    fights: catalog.fights.map(fight => ({
      id: fight.id, name: fight.name, shortName: fight.shortName, released: fight.released,
      type: fight.type, syncLevel: fight.syncLevel,
      phases: fight.phases.map(phase => ({ id: phase.id, label: phase.label, name: phase.name, start: phase.start })),
    })),
    sheets: catalog.sheets.map(sheet => ({
      id: sheet.id, fightId: sheet.fightId, name: sheet.name, updated: sheet.updated,
      author: sheet.author, description: sheet.description, source: sheet.source, slots: sheet.slots,
    })),
    jobs: catalog.jobs,
    icons: catalog.icons,
    abilities: catalog.abilities,
  }
}

function fightBundle(catalog: Catalog, fightId: string) {
  const fight = catalog.fights.find(candidate => candidate.id === fightId)
  if (!fight) throw new Error(`Unknown fight chunk ${fightId}`)
  return { fight, sheets: catalog.sheets.filter(sheet => sheet.fightId === fightId) }
}

// The home page and prerender only need names, slots, and phase ids. Each
// fight's mechanics and assignments load as their own chunk the first time
// that fight is selected. Static import() paths are what lets Rollup split them.
function mitCatalog(): Plugin {
  const virtualIds = new Set<string>()
  const watched = [iconsFile, jobsFile, abilitiesFile]
  return {
    name: 'mit-catalog',
    transformIndexHtml(html, context) {
      return html.replace(/<!--seo:start-->[\s\S]*?<!--seo:end-->/,
        () => `<!--seo:start-->${renderMetadata(pageInfo(readCatalog(), context.path))}<!--seo:end-->`)
    },
    buildStart() { readCatalog() },
    resolveId(id) {
      if (id === 'virtual:mit-index') return '\0mit-index'
      if (id === 'virtual:mit-load') return '\0mit-load'
      if (id.startsWith('virtual:mit-fight/')) return `\0${id.slice('virtual:'.length)}`
    },
    load(id) {
      if (id !== '\0mit-index' && id !== '\0mit-load' && !id.startsWith('\0mit-fight/')) return
      virtualIds.add(id)
      const catalog = readCatalog()
      if (id === '\0mit-index') return `export default ${JSON.stringify(toIndex(catalog))}`
      if (id === '\0mit-load') {
        const loaders = catalog.fights.map(fight =>
          `  ${JSON.stringify(fight.id)}: () => import(${JSON.stringify(`virtual:mit-fight/${fight.id}`)}),`).join('\n')
        return `const loaders = {\n${loaders}\n}\nexport function loadFight(id) {\n  const load = loaders[id]\n  return load ? load().then(module => module.default) : Promise.resolve(null)\n}\n`
      }
      const fightId = id.slice('\0mit-fight/'.length)
      return `export default ${JSON.stringify(fightBundle(catalog, fightId))}`
    },
    configureServer(server) {
      server.watcher.add(fightsDir)
      for (const file of watched) server.watcher.add(file)
      server.watcher.on('all', (_event, path) => {
        if (!path.startsWith(fightsDir) && !watched.includes(path)) return
        for (const id of virtualIds) {
          const module = server.moduleGraph.getModuleById(id)
          if (module) server.moduleGraph.invalidateModule(module)
        }
        server.ws.send({ type: 'full-reload' })
      })
    },
  }
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    mitCatalog(),
    react(),
    babel({ presets: [reactCompilerPreset()] }),
  ],
  optimizeDeps: { exclude: ['virtual:mit-index', 'virtual:mit-load'] },
})
