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

const catalog = loadCatalog()
let server, MitView, cacheDir
before(async () => {
  cacheDir = mkdtempSync(join(tmpdir(), 'xivmits-note-test-'))
  server = await createServer({ cacheDir, server: { middlewareMode: true, hmr: false, ws: false }, appType: 'custom' })
  MitView = (await server.ssrLoadModule('/src/components/MitView.tsx')).default
})
after(async () => {
  try { await server?.close() } finally {
    if (cacheDir) rmSync(cacheDir, { recursive: true, force: true })
  }
})

function render(sheetId, phaseId, job, options = {}, mechanicId) {
  const sheet = catalog.sheets.find(s => s.id === sheetId)
  const fight = catalog.fights.find(f => f.id === sheet.fightId)
  const slot = sheet.slots.find(s => s.role === job.role && (!s.job || s.job === job.id))
  const phase = sheet.phases.find(p => p.id === phaseId)
  return renderToStaticMarkup(h(MantineProvider, {}, h(MitView, {
    fight: { ...fight, phases: fight.phases.filter(p => p.id === phaseId) },
    sheet: { ...sheet, phases: [{ ...phase, mechanics: phase.mechanics.filter(m => !mechanicId || m.id === mechanicId) }] },
    roleId: slot.id, job, phaseId, onPhase: () => {}, ...options,
  })))
}

test('strategy and healer notes stay with their audience across jobs, layouts and PiP', () => {
  const cases = [
    ['lpdu', 'p2', 'Wall priority:', ['tank']],
    ['lpdu', 'p3', 'Paladin is the forced', ['tank']],
    ['lpdu', 'p3', 'Tank LB priority:', ['tank']],
    ['lpdu', 'p3', 'Both tanks swap bosses', ['tank']],
    ['fmbg', 'p1', 'can cause buff cap', ['tank', 'healer']],
    ['fmbg', 'p4', 'look at relevant Tank CDs', ['tank']],
    ['topmitty', 'p2', 'After Playstation:', ['melee', 'caster']],
    ['topmitty', 'p5', 'Healers must put personal mit', ['healer']],
    ['dsrmitty', 'p5', 'Healers need to mitigate tanks', ['healer']],
    ['dsrmitty', 'rewind', 'Use the assigned shields before the first bait.', ['SCH', 'SGE', 'AST']],
  ]
  for (const [sheet, phase, note, audience] of cases) for (const job of catalog.jobs) {
    for (const layout of ['tabs', 'list']) for (const compact of [false, true]) {
      const html = render(sheet, phase, job, { layout, compact })
      assert.equal(html.includes(note), audience.includes(job.role) || audience.includes(job.id),
        `${sheet}/${phase}/${job.id}/${layout}/${compact}: ${note}`)
    }
    assert.ok(!render(sheet, phase, job, { notes: false }).includes(note))
    assert.ok(!render(sheet, phase, job, { layout: 'grid' }).includes(note))
  }
})

test('TOP timing notes disappear for blank or job-filtered assignments', () => {
  for (const id of ['BLM', 'SMN', 'PCT', 'WHM', 'RDM']) {
    const job = catalog.jobs.find(j => j.id === id)
    const html = render('topmitty', 'p6', job, {}, 'p6-wave-cannon-6')
    assert.equal(html.includes('after the 1st set of proteans'), id === 'RDM', id)
  }
})

test('DSR pre-bait shield note does not move later actions before the first bait', () => {
  for (const id of ['SCH', 'SGE', 'AST']) {
    const job = catalog.jobs.find(j => j.id === id)
    assert.ok(render('dsrmitty', 'rewind', job, {}, 'rewind-brightwing-1').includes('before the first bait'))
    for (const mechanic of ['rewind-brightwing-2', 'rewind-brightwing-3', 'rewind-pure-of-heart-1'])
      assert.ok(!render('dsrmitty', 'rewind', job, {}, mechanic).includes('before the first bait'))
  }
})

test('LPDU Passage of Arms and its alternative-use note are PLD-only', () => {
  const note = 'Choose one use across these two rows.'
  for (const id of ['PLD', 'WAR', 'DRK', 'GNB', 'SMN', 'SCH']) {
    const job = catalog.jobs.find(j => j.id === id)
    for (const mechanic of ['p3-shocking-impact-1', 'p3-shocking-impact-2']) {
      for (const layout of ['tabs', 'list', 'grid']) for (const compact of [false, true]) {
        const options = { layout, compact, ...(job.role === 'tank' ? { roleId: 'OT' } : {}) }
        const html = render('lpdu', 'p3', job, options, mechanic)
        assert.equal(html.includes('Passage of Arms'), id === 'PLD', `${id}/${mechanic}/${layout}`)
        assert.equal(html.includes(note), id === 'PLD' && layout !== 'grid')
      }
    }
    const html = render('lpdu', 'p3', job, {}, 'p3-thunder-iii-4')
    assert.ok(!html.includes('Use the first beam set'))
  }
})
