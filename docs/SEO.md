# Search discovery

The production build prerenders the homepage, every catalog sheet, and the
updates page using the same React components as the browser. The viewer then
mounts with the reader's saved preferences. No server runs in production.

The visible selection screen stays unchanged. Prerendering includes its existing
headings and selectors; assignments still require the reader's role/job.
There are no added overview sections or sheet directories. Search crawlers can
discover sheet URLs through the sitemap. Adding a catalog sheet adds its page
and sitemap entry automatically. Without the interactive selection, crawlers
see the selection screen rather than the full assignment content.

`src/seo.ts` owns titles, descriptions, canonical URLs, social metadata, and
JSON-LD. `src/entry-server.tsx` renders the pages; `scripts/prerender.mjs` writes
the production files after Vite builds the browser assets. Canonical URLs omit
personalization parameters. The 404 page is `noindex` and has no canonical.
GitHub Pages supplies the actual 404 HTTP status for missing paths.

`robots.txt` permits all crawlers and advertises `/sitemap.xml`. This includes
Googlebot, Bingbot, and AI search crawlers such as OAI-SearchBot. Search crawlers
get the same HTML as visitors. There are no hidden keyword blocks, fabricated
ratings, or separate bot pages. Sitemap dates are omitted because a sheet's
data update date does not capture every change to the rendered page.

Google says its AI search features do not use `llms.txt` or require special AI
markup. Readable content, crawlable links, accurate metadata, and crawler access
are the supported foundations:

- [Google AI search guidance](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide)
- [OpenAI search crawler documentation](https://developers.openai.com/api/docs/bots)

## After deployment

1. Verify the `xivmits.com` domain in Google Search Console with the DNS record
   Google provides. Do not commit an invented verification token.
2. Submit `https://xivmits.com/sitemap.xml`. Inspect the homepage and a sheet URL,
   run the live test, and request indexing. Check the rendered HTML and the
   selected canonical if Google reports an indexing problem.
3. Add the site to Bing Webmaster Tools and submit the same sitemap. A verified
   Search Console property can also be imported there.
4. Link to the site from relevant community resources where appropriate. Search
   engines still decide whether to index and rank each page; these changes do
   not guarantee listing or AI citations.

## Verification

Run the root `lint`, `build`, and `test` scripts through Yarn. SEO tests render
all public routes without a browser and check sitemap coverage, unique metadata,
canonical URLs, the original visible copy, structured data, escaping, and missing pages.
The build itself verifies that prerendering succeeds against production HTML.
Check `/`, a sheet URL, `/updates/`, `/sitemap.xml`, `/robots.txt`, and a missing
path against the deployed GitHub Pages host after publishing.
