import { renderToStaticMarkup } from 'react-dom/server'
import App from './App'
import catalog from './data/catalog'
import { pageInfo, renderMetadata, sitemap, siteUrl } from './seo'

export const pagePaths = ['/', '/updates/', ...catalog.sheets.map(s => `/${s.fightId}/${s.id}/`)]
export const sitemapXml = sitemap(catalog)
// Wildcard access includes Googlebot, Bingbot, OAI-SearchBot, Claude-SearchBot,
// and other search crawlers. No user-agent-specific HTML or hidden AI content.
export const robotsTxt = `User-agent: *\nAllow: /\n\nSitemap: ${siteUrl}/sitemap.xml\n`

export function renderPage(template: string, path: string) {
  if (!template.includes('<div id="root"></div>') || !template.includes('<!--seo:start-->')) {
    throw new Error('Prerender template is missing the root or SEO placeholder')
  }
  const body = renderToStaticMarkup(<App initialPath={path} />)
  return template.replace(/<!--seo:start-->[\s\S]*?<!--seo:end-->/,
    () => `<!--seo:start-->${renderMetadata(pageInfo(catalog, path))}<!--seo:end-->`)
    .replace('<div id="root"></div>', () => `<div id="root">${body}</div>`)
}
