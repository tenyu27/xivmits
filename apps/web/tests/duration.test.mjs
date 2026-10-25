import assert from 'node:assert/strict'
import { mkdtempSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { after, before, test } from 'node:test'
import { createElement as h } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { MantineProvider } from '@mantine/core'
import { createServer } from 'vite'
import { loadCatalog } from '@xivmits/encounter-data'

let server, MitView, cacheDir
const catalog = loadCatalog()
before(async () => {
  cacheDir = mkdtempSync(join(tmpdir(), 'xivmits-duration-test-'))
  server = await createServer({ cacheDir, server: { middlewareMode: true, hmr: false, ws: false }, appType: 'custom' })
  MitView = (await server.ssrLoadModule('/src/components/MitView.tsx')).default
})
after(async () => {
  try { await server?.close() } finally {
    if (cacheDir) rmSync(cacheDir, { recursive: true, force: true })
  }
})

function render(fightId, phaseId, roleId, options = {}) {
  const { job: jobId, ...view } = options
  const fight = catalog.fights.find(f => f.id === fightId)
  const sheet = catalog.sheets.find(s => s.fightId === fightId)
  return renderToStaticMarkup(h(MantineProvider, {}, h(MitView, {
    fight: { ...fight, phases: fight.phases.filter(p => p.id === phaseId) },
    sheet: { ...sheet, phases: sheet.phases.filter(p => p.id === phaseId) },
    roleId, phaseId, onPhase: () => {},
    job: catalog.jobs.find(j => j.id === (jobId ?? 'WAR')),
    ...view,
  })))
}

const durations = html => [...html.matchAll(/action-duration[^>]*>(\d+s)</g)].map(match => match[1])

test('Reprisal, Feint, and Addle show the duration at the fight sync level', () => {
  const dsr = render('dsr', 'p2', 'MT')
  assert.ok(dsr.includes('Reprisal'))
  assert.ok(durations(dsr).length > 0)
  assert.ok(durations(dsr).every(value => value === '10s'))
  const tea = render('tea', 'p1', 'MT', { job: 'PLD' })
  assert.ok(tea.includes('Reprisal'))
  assert.ok(tea.includes('Sheltron'))
  assert.ok(!tea.includes('Holy Sheltron'))
  assert.ok(durations(tea).length > 0)
  assert.ok(durations(tea).every(value => value === '10s'))
  const fru = render('fru', 'p1', 'MT')
  assert.ok(fru.includes('Reprisal'))
  assert.ok(durations(fru).includes('15s'))
  assert.ok(!durations(fru).includes('10s'))
  // A qualified name still finds the ability's steps.
  const chaos = render('dmu', 'p3', 'M2', { job: 'NIN' })
  assert.ok(chaos.includes('Feint (Chaos)'))
  assert.ok(durations(chaos).includes('15s'))
})

test('the duration stays off the icon-only and cheatsheet displays', () => {
  for (const options of [{ display: 'icon', compact: true }, { display: 'icon' }, { layout: 'grid', display: 'both' }]) {
    const html = render('dsr', 'p2', 'MT', options)
    assert.equal(durations(html).length, 0, JSON.stringify(options))
    assert.ok(!html.includes('>10s<'), JSON.stringify(options))
  }
})
