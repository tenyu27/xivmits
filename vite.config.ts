import react, { reactCompilerPreset } from '@vitejs/plugin-react'
import babel from '@rolldown/plugin-babel'
import { defineConfig } from 'vite'
import { existsSync, readFileSync, readdirSync } from 'node:fs'
import { resolve } from 'node:path'
import { validateCatalog } from './src/data/schema.ts'

function readCatalog() {
  const root = resolve('data/fights')
  const files = Object.fromEntries(readdirSync(root, { recursive: true, encoding: 'utf8' })
    .filter(path => path.endsWith('.json'))
    .map(path => [`${root}/${path}`, JSON.parse(readFileSync(resolve(root, path), 'utf8'))]))
  const read = (path: string, fallback: unknown) =>
    existsSync(resolve(path)) ? JSON.parse(readFileSync(resolve(path), 'utf8')) : fallback
  const catalog = validateCatalog(files, read('data/icons.json', {}), read('data/jobs.json', { jobs: [] }))
  // A map entry pointing at a missing PNG would render a broken image, so fail
  // the build instead. Re-run scripts/fetch_icons.py to regenerate both.
  for (const [name, file] of Object.entries(catalog.icons)) {
    if (!existsSync(resolve('public/icons', file))) {
      throw new Error(`data/icons.json: ${name} -> public/icons/${file} is missing`)
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
        server.watcher.add(resolve('data/fights'))
        server.watcher.add(resolve('data/icons.json'))
        server.watcher.add(resolve('data/jobs.json'))
        server.watcher.on('all', (_event, path) => {
          if (path.includes('/data/') && path.endsWith('.json')) {
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
