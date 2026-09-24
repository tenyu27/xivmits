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
import { resolveAction } from '@xivmits/core'

const catalog = loadCatalog()
const fight = catalog.fights.find(f => f.id === 'dmu')
const sheet = catalog.sheets.find(s => s.fightId === 'dmu' && s.id === 'ikuya')
let server, MitView, cacheDir
before(async () => {
  cacheDir = mkdtempSync(join(tmpdir(), 'xivmits-ikuya-test-'))
  server = await createServer({ cacheDir, server: { middlewareMode: true, hmr: false, ws: false }, appType: 'custom' })
  MitView = (await server.ssrLoadModule('/src/components/MitView.tsx')).default
})
after(async () => {
  try { await server?.close() } finally {
    if (cacheDir) rmSync(cacheDir, { recursive: true, force: true })
  }
})

function renderRow(phaseId, mechanicId, slot, job, options = {}) {
  const phase = sheet.phases.find(p => p.id === phaseId)
  return renderToStaticMarkup(h(MantineProvider, {}, h(MitView, {
    fight, sheet: { ...sheet, phases: [{ ...phase, mechanics: phase.mechanics.filter(m => m.id === mechanicId) }] },
    phaseId, roleId: slot.id, job, onPhase: () => {}, ...options,
  })))
}

test('Ikuya press notes follow the assigned job, never blank rows or carry-overs', () => {
  const rows = [
    ['p1', 'p1-light-of-judgment-1', 'Use late into the castbar'],
    ['p1', 'p1-light-of-judgment-2', 'Use late into the castbar'],
    ['p5', 'p5-forsaken-1', 'Use any timed mitigation'],
    ['p5', 'p5-forsaken-3', 'Apply the new round'],
  ]
  for (const [phaseId, mechanicId, note] of rows) {
    const row = sheet.phases.find(p => p.id === phaseId).mechanics.find(m => m.id === mechanicId)
    assert.ok(row, mechanicId)
    for (const job of catalog.jobs) {
      for (const slot of sheet.slots.filter(s => s.role === job.role && (!s.job || s.job === job.id))) {
        const assigned = (row.assignments[slot.id] ?? []).some(a => !a.carryOver && resolveAction(a.name, job).applies)
        for (const compact of [false, true]) {
          const context = `${mechanicId}/${slot.id}/${job.id}/${compact}`
          assert.equal(renderRow(phaseId, mechanicId, slot, job, { compact }).includes(note), assigned, context)
          assert.ok(!renderRow(phaseId, mechanicId, slot, job, { notes: false, compact }).includes(note), context)
        }
      }
    }
  }
})

test('Accretion advice is specific to healer jobs or non-healers', () => {
  const phase = sheet.phases.find(p => p.id === 'p3')
  const row = phase.mechanics.find(m => m.name === 'Accretions')
  for (const job of catalog.jobs) {
    const slot = sheet.slots.find(s => s.role === job.role && (!s.job || s.job === job.id))
    const html = renderRow('p3', row.id, slot, job)
    assert.equal(html.includes('popping Macrocosmos'), job.id === 'AST', job.id)
    assert.equal(html.includes('WHM can use Benediction'), job.id === 'WHM', job.id)
    assert.equal(html.includes('Non-healers should avoid'), job.role !== 'healer', job.id)
    assert.equal(html.includes('The H1 and H2'), job.role === 'healer', job.id)
  }
})
