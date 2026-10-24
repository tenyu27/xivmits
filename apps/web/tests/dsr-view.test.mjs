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
const fight = catalog.fights.find(f => f.id === 'dsr')
const sheet = catalog.sheets.find(s => s.fightId === 'dsr')
let server, MitView, cacheDir
before(async () => {
  // Test servers must not replace the running dev server's optimized dependencies.
  cacheDir = mkdtempSync(join(tmpdir(), 'xivmits-vite-test-'))
  server = await createServer({ cacheDir, server: { middlewareMode: true, hmr: false, ws: false }, appType: 'custom' })
  MitView = (await server.ssrLoadModule('/src/components/MitView.tsx')).default
})
after(async () => {
  try { await server?.close() } finally {
    if (cacheDir) rmSync(cacheDir, { recursive: true, force: true })
  }
})

const escape = value => value.replaceAll('&', '&amp;').replaceAll('<', '&lt;')
  .replaceAll('>', '&gt;').replaceAll('"', '&quot;').replaceAll("'", '&#x27;')
function render(phase, roleId, job, options) {
  return renderToStaticMarkup(h(MantineProvider, {}, h(MitView, {
    fight: { ...fight, phases: fight.phases.filter(p => p.id === phase.id) },
    sheet: { ...sheet, phases: [phase] }, phaseId: phase.id,
    roleId, job, onPhase: () => {}, ...options,
  })))
}

test('DSR party assignments survive every layout, job filtering, Mit only, and compact rendering', () => {
  for (const job of catalog.jobs) {
    const slots = sheet.slots.filter(s => s.role === job.role && (!s.job || s.job === job.id))
    for (const slot of slots) for (const phase of sheet.phases) {
      for (const layout of ['tabs', 'list', 'grid']) {
        const html = render(phase, slot.id, job, { layout, compact: true, showUnassigned: false })
        const context = `${job.id}/${slot.id}/${phase.id}/${layout}`
        for (const row of phase.mechanics) for (const action of row.assignments[slot.id] ?? []) {
          const resolved = resolveAction(action.name, job, {}, fight.syncLevel)
          if (resolved.applies) assert.ok(html.includes(escape(resolved.label)), `${context}: ${resolved.label}`)
        }
        if (job.id !== 'MCH') assert.ok(!html.includes('Dismantle'), context)
        if (job.id !== 'RDM') assert.ok(!html.includes('Magick Barrier'), context)
      }
    }
  }
})

test('DSR tank plans preserve every personal and buddy assignment and phase note in both seats', () => {
  for (const plan of sheet.tankMits.plans) {
    const job = catalog.jobs.find(j => j.id === plan.job)
    for (const personal of plan.phases) {
      const phase = sheet.phases.find(p => p.id === personal.id)
      for (const seat of ['MT', 'OT']) for (const layout of ['tabs', 'list', 'grid']) {
        const html = render(phase, seat, job, { personalPlan: plan, layout, showUnassigned: false })
        const context = `${plan.job}/${plan.with}/${phase.id}/${seat}/${layout}`
        for (const row of personal.mechanics) for (const action of row.actions) {
          const resolved = resolveAction(action.name, job, {}, fight.syncLevel)
          if (resolved.applies) assert.ok(html.includes(escape(resolved.label)), `${context}: ${resolved.label}`)
          if (action.note && layout !== 'grid') assert.ok(html.includes(escape(action.note)), context)
        }
        if (personal.note && layout !== 'grid') assert.ok(html.includes(escape(personal.note)), context)
        for (const row of personal.mechanics.filter(r => r.note)) {
          if (layout === 'grid') {
            assert.ok(!html.includes(escape(row.note)), context)
            continue
          }
          const heading = html.indexOf(`>${escape(row.name)}</h3>`)
          const note = html.indexOf(escape(row.note))
          const nextHeading = html.indexOf('<h3', heading + 1)
          assert.ok(heading >= 0 && note > heading, `${context}: note follows ${row.name}`)
          assert.ok(nextHeading < 0 || note < nextHeading, `${context}: note stays under ${row.name}`)
          const hidden = render(phase, seat, job, { personalPlan: plan, layout, notes: false })
          assert.ok(!hidden.includes(escape(row.note)), `${context}: notes toggle`)
        }
      }
    }
  }
})

test('DSR second P5 buster keeps the source healer instruction visible in Mit only', () => {
  const phase = sheet.phases.find(p => p.id === 'p5')
  for (const id of ['SCH', 'SGE', 'WHM', 'AST']) {
    const job = catalog.jobs.find(j => j.id === id)
    for (const layout of ['tabs', 'list', 'grid']) for (const compact of [false, true]) {
      const html = render(phase, id, job, { layout, compact, showUnassigned: false })
      assert.ok(html.includes('Assist Tanks'), `${id}/${layout}/${compact}`)
      assert.ok(html.includes('Heavenly Heel 3'), `${id}/${layout}/${compact}: buster`)
      if (layout !== 'grid') assert.ok(html.includes('Healers need to mitigate tanks for this buster.'))
    }
  }
})

test('DSR renders Final Chorus only in P2 across layouts and filtering modes', () => {
  const p2 = sheet.phases.find(p => p.id === 'p2')
  const p3 = sheet.phases.find(p => p.id === 'p3')
  const job = catalog.jobs.find(j => j.id === 'SCH')
  for (const layout of ['tabs', 'list', 'grid']) for (const showUnassigned of [false, true]) {
    for (const compact of [false, true]) {
      const options = { layout, showUnassigned, compact }
      assert.ok(render(p2, 'SCH', job, options).includes('Final Chorus'))
      assert.ok(!render(p3, 'SCH', job, options).includes('Final Chorus'))
    }
  }
})
