import type { Catalog } from '@xivmits/core'

export const siteUrl = 'https://xivmits.com'
export const homeDescription = 'View community FFXIV mitigation sheets by fight, role, job, and phase. Read your raid assignments in a cheatsheet or an always-on-top window.'

export function pageInfo(catalog: Catalog, pathname: string) {
  const path = pathname.replace(/\/index\.html$/, '/').replace(/\/?$/, '/')
  const sheet = catalog.sheets.find(s => path === `/${s.fightId}/${s.id}/`)
  const fight = sheet && catalog.fights.find(f => f.id === sheet.fightId)
  const home = path === '/'
  const updates = path === '/updates/'
  const found = home || updates || Boolean(sheet && fight)
  const title = sheet && fight ? `${sheet.name} | ${fight.shortName ?? fight.name} mitigation | XIVMits`
    : home ? 'XIVMits | FFXIV mitigation sheets'
      : updates ? 'Updates | XIVMits' : 'Page not found | XIVMits'
  const description = sheet && fight
    ? `${fight.name}: ${sheet.name} mitigation assignments by role, job, and phase. View the community sheet, tank plans, and raid cheatsheet.`
    : home ? homeDescription : updates ? 'New fights, mitigation sheets, and changes to XIVMits, the FFXIV mitigation sheet viewer.'
      : 'This XIVMits page could not be found. Browse the available FFXIV mitigation sheets.'
  const url = `${siteUrl}${path}`
  const website = { '@type': 'WebSite', '@id': `${siteUrl}/#website`, name: 'XIVMits', url: `${siteUrl}/`, description: homeDescription, inLanguage: 'en' }
  const structuredData = found ? {
    '@context': 'https://schema.org',
    '@graph': [website, {
      '@type': 'WebPage', '@id': `${url}#webpage`, url, name: title, description,
      inLanguage: 'en', isPartOf: { '@id': website['@id'] },
    }],
  } : null
  return { title, description, url, found, sheet, fight, structuredData }
}

export const escapeHtml = (value: string) => value.replaceAll('&', '&amp;').replaceAll('<', '&lt;')
  .replaceAll('>', '&gt;').replaceAll('"', '&quot;').replaceAll("'", '&#39;')

export function renderMetadata(page: ReturnType<typeof pageInfo>) {
  return `<title>${escapeHtml(page.title)}</title>
    <meta name="description" content="${escapeHtml(page.description)}" />
    <meta name="robots" content="${page.found ? 'index, follow, max-image-preview:large' : 'noindex, follow'}" />
    ${page.found ? `<link rel="canonical" href="${escapeHtml(page.url)}" />` : ''}
    <meta property="og:site_name" content="XIVMits" />
    <meta property="og:type" content="website" />
    <meta property="og:title" content="${escapeHtml(page.title)}" />
    <meta property="og:description" content="${escapeHtml(page.description)}" />
    <meta property="og:url" content="${escapeHtml(page.url)}" />
    <meta name="twitter:card" content="summary" />
    <meta name="twitter:title" content="${escapeHtml(page.title)}" />
    <meta name="twitter:description" content="${escapeHtml(page.description)}" />
    ${page.structuredData ? `<script type="application/ld+json">${JSON.stringify(page.structuredData).replaceAll('<', '\\u003c')}</script>` : ''}`.replace(/<(title|meta|link|script)(?=[ >])/g, '<$1 data-seo')
}

export function sitemap(catalog: Catalog) {
  // No synthetic lastmod dates: sheet.updated doesn't track every change to a
  // rendered page, so omit it rather than claim an inaccurate modification time.
  return `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${[
    '/', '/updates/', ...catalog.sheets.map(s => `/${s.fightId}/${s.id}/`),
  ].map(path => `  <url><loc>${escapeHtml(siteUrl + path)}</loc></url>`).join('\n')}\n</urlset>\n`
}
