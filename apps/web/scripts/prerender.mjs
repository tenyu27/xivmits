import { mkdtemp, mkdir, readFile, rm, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { dirname, join } from 'node:path'
import { createServer } from 'vite'

// Reuse Vite's module pipeline and virtual catalog. This server exists only
// during the build; deployment remains static files on GitHub Pages.
const cacheDir = await mkdtemp(join(tmpdir(), 'xivmits-prerender-'))
let server
try {
  server = await createServer({ cacheDir, server: { middlewareMode: true, hmr: false, ws: false }, appType: 'custom' })
  const { pagePaths, renderPage, sitemapXml, robotsTxt } = await server.ssrLoadModule('/src/entry-server.tsx')
  const template = await readFile('dist/index.html', 'utf8')
  for (const path of [...pagePaths, '/404.html']) {
    const file = path === '/404.html' ? 'dist/404.html' : join('dist', path.slice(1), 'index.html')
    await mkdir(dirname(file), { recursive: true })
    await writeFile(file, renderPage(template, path))
  }
  await writeFile('dist/sitemap.xml', sitemapXml)
  await writeFile('dist/robots.txt', robotsTxt)
  console.log(`Prerendered ${pagePaths.length} pages, 404.html, sitemap.xml, and robots.txt`)
} finally {
  await server?.close()
  await rm(cacheDir, { recursive: true, force: true })
}
