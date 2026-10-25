import assert from 'node:assert/strict'
import { mkdtempSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { after, before, test } from 'node:test'
import { createElement as h } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { MantineProvider } from '@mantine/core'
import { createServer } from 'vite'

let server, FightLoadNotice, readFight, cacheDir
before(async () => {
  cacheDir = mkdtempSync(join(tmpdir(), 'xivmits-fight-load-test-'))
  server = await createServer({ cacheDir, server: { middlewareMode: true, hmr: false, ws: false }, appType: 'custom' })
  FightLoadNotice = (await server.ssrLoadModule('/src/components/FightLoadNotice.tsx')).default
  readFight = (await server.ssrLoadModule('/src/data/catalog.ts')).readFight
})
after(async () => {
  try { await server?.close() } finally {
    if (cacheDir) rmSync(cacheDir, { recursive: true, force: true })
  }
})

const notice = failed => renderToStaticMarkup(h(MantineProvider, {}, h(FightLoadNotice, { failed, onRetry: () => {} })))

test('a rejected or empty fight load becomes a failure the view can retry', async () => {
  assert.equal(await readFight('dmu', async () => { throw new Error('chunk failed') }), null)
  assert.equal(await readFight('dmu', async () => null), null)
  assert.equal(await readFight('dmu', async () => ({ fight: { id: 'top' }, sheets: [] })), null)
  const bundle = await readFight('dmu', async () => ({ fight: { id: 'dmu' }, sheets: [] }))
  assert.equal(bundle.fight.id, 'dmu')

  const failed = notice(true)
  assert.match(failed, /This fight could not be loaded/)
  assert.match(failed, /role="alert"/)
  assert.match(failed, />Retry</)
  const waiting = notice(false)
  assert.match(waiting, /Loading fight/)
  assert.match(waiting, /role="status"/)
  assert.doesNotMatch(waiting, /Retry/)
})
