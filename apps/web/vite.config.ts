import react, { reactCompilerPreset } from '@vitejs/plugin-react'
import babel from '@rolldown/plugin-babel'
import { defineConfig } from 'vite'
import { existsSync } from 'node:fs'
import { resolve } from 'node:path'
import { fightsDir, iconsFile, jobsFile, loadCatalog } from '@xivmits/encounter-data'

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

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    {
      name: 'mit-catalog',
      buildStart() { readCatalog() },
      resolveId(id) { if (id === 'virtual:mit-catalog') return '\0mit-catalog' },
      load(id) { if (id === '\0mit-catalog') return `export default ${JSON.stringify(readCatalog())}` },
      configureServer(server) {
        server.watcher.add(fightsDir)
        server.watcher.add(iconsFile)
        server.watcher.add(jobsFile)
        server.watcher.on('all', (_event, path) => {
          if (path.startsWith(fightsDir) || path === iconsFile || path === jobsFile) {
            const module = server.moduleGraph.getModuleById('\0mit-catalog')
            if (module) server.moduleGraph.invalidateModule(module)
            server.ws.send({ type: 'full-reload' })
          }
        })
      },
      generateBundle: { order: 'post', handler(_options, bundle) {
        const page = bundle['index.html']
        if (!page || page.type !== 'asset') throw new Error('Missing index.html')
        for (const sheet of readCatalog().sheets) {
          this.emitFile({ type: 'asset', fileName: `${sheet.fightId}/${sheet.id}/index.html`, source: page.source })
        }
        this.emitFile({ type: 'asset', fileName: '404.html', source: page.source })
      } },
    },
    react(),
    babel({ presets: [reactCompilerPreset()] })
  ],
})
