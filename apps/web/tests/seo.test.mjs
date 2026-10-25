import assert from 'node:assert/strict'
import { mkdtempSync, readFileSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { after, before, test } from 'node:test'
import { createServer } from 'vite'
import { loadCatalog } from '@xivmits/encounter-data'

const catalog = loadCatalog()
const template = readFileSync(new URL('../index.html', import.meta.url), 'utf8')
let server, entry, seo, cacheDir
before(async () => {
  cacheDir = mkdtempSync(join(tmpdir(), 'xivmits-seo-test-'))
  server = await createServer({ cacheDir, server: { middlewareMode: true, hmr: false, ws: false }, appType: 'custom' })
  entry = await server.ssrLoadModule('/src/entry-server.tsx')
  seo = await server.ssrLoadModule('/src/seo.ts')
})
after(async () => {
  try { await server?.close() } finally {
    if (cacheDir) rmSync(cacheDir, { recursive: true, force: true })
  }
})

const bodyOf = html => html.split('<body>')[1]
const jsonLd = html => JSON.parse(html.match(/<script[^>]*type="application\/ld\+json"[^>]*>(.*?)<\/script>/s)[1])

test('every indexable route has unique metadata, a canonical, real HTML, and matching structured data', () => {
  const titles = new Set()
  const descriptions = new Set()
  for (const path of entry.pagePaths) {
    const html = entry.renderPage(template, path)
    const page = seo.pageInfo(catalog, path)
    assert.equal((html.match(/<title\b/g) ?? []).length, 1, path)
    assert.equal((html.match(/rel="canonical"/g) ?? []).length, 1, path)
    assert.ok(html.includes(`href="https://xivmits.com${path}"`), path)
    assert.ok(html.includes('index, follow, max-image-preview:large'), path)
    assert.ok(!html.includes('noindex'), path)
    assert.equal((bodyOf(html).match(/<h1\b/g) ?? []).length, 1, path)
    assert.ok(bodyOf(html).includes('<main'), path)
    assert.equal(jsonLd(html)['@graph'][1].url, page.url)
    assert.ok(html.includes('twitter:card" content="summary_large_image"'), path)
    assert.ok(html.includes(`property="og:image" content="${page.image}"`), path)
    assert.ok(html.includes('property="og:image:width" content="1200"'), path)
    assert.ok(html.includes('property="og:image:height" content="630"'), path)
    assert.ok(html.includes(`name="twitter:image" content="${page.image}"`), path)
    assert.equal(page.image, path === '/' || path === '/updates/' ? 'https://xivmits.com/og/site.png' : `https://xivmits.com/og/${page.fight.id}.png`)
    titles.add(page.title)
    descriptions.add(page.description)
  }
  assert.equal(titles.size, entry.pagePaths.length)
  assert.equal(descriptions.size, entry.pagePaths.length)
})

test('sitemap discovers every sheet and matches generated routes', () => {
  for (const sheet of catalog.sheets) {
    const path = `/${sheet.fightId}/${sheet.id}/`
    assert.ok(entry.sitemapXml.includes(`<loc>https://xivmits.com${path}</loc>`), path)
  }
  const urls = [...entry.sitemapXml.matchAll(/<loc>(.*?)<\/loc>/g)].map(m => m[1])
  assert.deepEqual(urls, entry.pagePaths.map(path => `https://xivmits.com${path}`))
  assert.ok(urls.every(url => !url.includes('?')))
  assert.ok(!entry.sitemapXml.includes('404'))
  assert.equal(entry.robotsTxt, 'User-agent: *\nAllow: /\n\nSitemap: https://xivmits.com/sitemap.xml\n')
})

test('prerendering preserves the original selection UI without SEO-only sections', () => {
  for (const path of entry.pagePaths.filter(path => path !== '/updates/')) {
    const html = bodyOf(entry.renderPage(template, path))
    assert.ok(html.includes('What do I mit?'))
    assert.ok(html.includes('Easy focus on your own mit without distraction.'))
    assert.ok(!html.includes('About this mitigation sheet'))
    assert.ok(!html.includes('Browse mitigation sheets'))
    assert.ok(!html.includes('Phases and mechanics'))
  }
})

test('unknown URLs are noindex with useful recovery links, never canonicalized to the homepage', () => {
  for (const path of ['/404.html', '/not-a-fight/not-a-sheet/']) {
    const html = entry.renderPage(template, path)
    assert.ok(html.includes('noindex, follow'))
    assert.ok(html.includes('twitter:card" content="summary_large_image"'))
    assert.ok(html.includes('property="og:image" content="https://xivmits.com/og/site.png"'))
    assert.ok(!html.includes('rel="canonical"'))
    assert.ok(!html.includes('application/ld+json'))
    assert.ok(bodyOf(html).includes('Mit sheet not found.'))
    assert.ok(bodyOf(html).includes('Change fight/sheet'))
  }
})

test('explicit index.html aliases render the same landing content and canonical as directory URLs', () => {
  for (const path of entry.pagePaths) {
    const html = entry.renderPage(template, `${path}index.html`)
    assert.ok(html.includes(`rel="canonical" href="https://xivmits.com${path}"`))
    assert.ok(!bodyOf(html).includes('Mit sheet not found.'))
    assert.ok(!bodyOf(html).includes('Page not found'))
  }
})

test('metadata escapes sheet text and script terminators', () => {
  const sheet = { ...catalog.sheets[0], name: '"<script>&</script><script>alert(1)</script>' }
  const page = seo.pageInfo({ ...catalog, sheets: [sheet] }, `/${sheet.fightId}/${sheet.id}/`)
  const html = seo.renderMetadata(page)
  assert.ok(html.includes('&quot;&lt;script&gt;&amp;'))
  assert.ok(!html.includes('</script><script>'))
  assert.equal(jsonLd(html)['@graph'][1].name, page.title)
})

test('footer omits Updates while the homepage retains the history link', () => {
  const html = entry.renderPage(template, '/')
  assert.ok(bodyOf(html).includes('href="/updates/"'))
  assert.ok(!html.split('<footer')[1].split('</footer>')[0].includes('href="/updates/"'))
})
