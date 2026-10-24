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

let server, MitView, cacheDir
const catalog = loadCatalog()
const fight = catalog.fights.find(f => f.id === 'top')
const sheet = catalog.sheets.find(s => s.fightId === 'top')
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
function render(phaseId, plan, options = {}) {
  return renderToStaticMarkup(h(MantineProvider, {}, h(MitView, {
    fight: { ...fight, phases: fight.phases.filter(p => p.id === phaseId) },
    sheet: { ...sheet, phases: sheet.phases.filter(p => p.id === phaseId) },
    roleId: 'T1', phaseId, onPhase: () => {},
    job: catalog.jobs.find(j => j.id === (plan?.job ?? 'WAR')),
    personalPlan: plan, ...options,
  })))
}

test('all TOP tank assignments, alternatives, and notes render for both seats in every layout', () => {
  for (const plan of sheet.tankMits.plans) {
    const job = catalog.jobs.find(j => j.id === plan.job)
    for (const phase of plan.phases) {
      for (const roleId of ['T1', 'T2']) {
        for (const layout of ['tabs', 'list', 'grid']) {
          for (const compact of [false, true]) {
            const html = render(phase.id, plan, { roleId, layout, compact })
            const context = `${plan.job}/${plan.with}/${phase.id}/${roleId}/${layout}/${compact}`
            for (const row of phase.mechanics) {
              assert.ok(html.includes(escape(row.name)), `${context}: missing ${row.name}`)
              for (const action of [...row.actions, ...(row.alts ?? []).flatMap(a => a.actions)]) {
                const resolved = resolveAction(action.name, job, {}, fight.syncLevel)
                if (resolved.applies) assert.ok(html.includes(escape(resolved.label)), `${context}: missing ${resolved.label}`)
                if (action.note && layout !== 'grid') assert.ok(html.includes(escape(action.note)), `${context}: missing action note`)
              }
              if (row.note && layout !== 'grid') assert.ok(html.includes(escape(row.note)), `${context}: missing row note`)
              for (const alt of row.alts ?? []) assert.ok(html.includes(escape(alt.label)), `${context}: missing alternative`)
            }
            if (phase.note && layout !== 'grid') assert.ok(html.includes(escape(phase.note)), `${context}: missing phase note`)
          }
        }
      }
    }
  }
})

test('hidden monitors appear only for assigned tanks, including Mit only and PiP', () => {
  for (const layout of ['tabs', 'list', 'grid']) {
    assert.ok(!render('p3', undefined, { layout }).includes('Oversampled Wave Cannon'))
    assert.ok(!render('p3', undefined, { layout, roleId: 'SCH', job: catalog.jobs.find(j => j.id === 'SCH') }).includes('Oversampled Wave Cannon'))
    for (const plan of sheet.tankMits.plans) {
      const assigned = plan.phases.find(p => p.id === 'p3').mechanics.some(m => m.after === 'p3-oversampled-wave-cannon-1')
      for (const showUnassigned of [true, false]) {
        const html = render('p3', plan, { layout, compact: true, showUnassigned })
        assert.equal(html.includes('Oversampled Wave Cannon'), assigned)
      }
    }
  }
})

test('tank busters show blank rows for tanks and stay hidden from unassigned healers', () => {
  for (const [phase, name] of [['p1', 'Diffuse Wave Cannon Kyrios'], ['p2', 'Solar Ray'], ['p2', 'Optimized Bladedance'], ['p5', 'Solar Ray']]) {
    assert.ok(render(phase).includes(name))
    assert.ok(!render(phase, undefined, { roleId: 'SCH', job: catalog.jobs.find(j => j.id === 'SCH') }).includes(name))
  }
})

test('P6 exception is pairing-scoped and follows the notes toggle', () => {
  for (const plan of sheet.tankMits.plans) {
    for (const layout of ['tabs', 'list', 'grid']) {
      const paired = [plan.job, plan.with].sort().join('/') === 'DRK/GNB'
      assert.equal(render('p6', plan, { layout, display: layout === 'grid' ? 'icon' : 'both' }).includes('Cosmo Memory instead of Cosmo Dive 1'), paired && layout !== 'grid')
      assert.ok(!render('p6', plan, { layout, display: layout === 'grid' ? 'icon' : 'both', notes: false }).includes('Cosmo Memory instead of Cosmo Dive 1'))
    }
  }
})


test('every supported TOP job renders its assignments across phases, layouts and displays', () => {
  for (const job of catalog.jobs) {
    const slots = job.role === 'tank' ? ['T1', 'T2'] : job.role === 'healer' ? [job.id]
      : job.role === 'melee' ? ['M1', 'M2'] : job.role === 'ranged' ? ['P'] : ['C']
    for (const roleId of slots) for (const phase of sheet.phases) {
      for (const layout of ['tabs', 'list', 'grid']) for (const display of ['both', 'text', 'icon']) {
        for (const showUnassigned of [true, false]) {
          const html = render(phase.id, undefined, { job, roleId, layout, display, showUnassigned })
          for (const row of phase.mechanics) for (const action of row.assignments[roleId] ?? []) {
            const resolved = resolveAction(action.name, job, {}, fight.syncLevel)
            if (resolved.applies) assert.ok(html.includes(escape(resolved.label)), `${job.id}/${roleId}/${phase.id}/${layout}/${display}: ${resolved.label}`)
          }
          if (job.role !== 'tank') assert.ok(!html.includes('aria-label="personal mit"') && !html.includes('assignment personal'))
          if (job.id !== 'MCH') assert.ok(!html.includes('Dismantle'))
          if (job.id !== 'RDM') assert.ok(!html.includes('Magick Barrier'))
        }
      }
    }
  }
})


test('cheatsheets hide notes for TOP, FRU and DMU', () => {
  for (const source of catalog.sheets) {
    const encounter = catalog.fights.find(f => f.id === source.fightId)
    const phaseId = source.phases[0].id
    const marked = { ...source, phases: source.phases.map(p => ({ ...p,
      note: 'AUDIT_PHASE_NOTE', mechanics: p.mechanics.map(m => ({ ...m,
        note: 'AUDIT_MECHANIC_NOTE', assignments: Object.fromEntries(Object.entries(m.assignments).map(([slot, actions]) =>
          [slot, actions.map(a => ({ ...a, note: 'AUDIT_ACTION_NOTE' }))])),
      })),
    })) }
    const html = renderToStaticMarkup(h(MantineProvider, {}, h(MitView, {
      fight: encounter, sheet: marked, roleId: source.slots[0].id, phaseId,
      onPhase: () => {}, layout: 'grid', notes: true, display: 'both',
    })))
    assert.ok(!html.includes('AUDIT_'), source.id)
  }
})
