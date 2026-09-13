import assert from 'node:assert/strict'
import test from 'node:test'
import { loadCatalog, readFightFiles } from '@xivmits/encounter-data'
import { availableTankChoices, selectTankRoute, tankChoices } from '@xivmits/core'
import { validateCatalog } from '@xivmits/core/schema'

const sheet = loadCatalog().sheets.find(s => s.fightId === 'fru')!
const plans = sheet.tankMits!.plans
const planFor = (job: string, other: string) => plans.find(p => p.job === job && p.with === other)!
const selected = (job: string, other: string, route: string, powder = 'first', akh = '') =>
  selectTankRoute(planFor(job, other), { powder, akh },
    route.slice(0, 3).toUpperCase() === job ? 'MT' : 'OT')
const routesFor = (job: string, other: string) => [job, other].map(j => `${j.toLowerCase()}-opens`)
const actionsAt = (job: string, other: string, route: string, anchor: string) =>
  selected(job, other, route).phases.flatMap(p => p.mechanics)
    .filter(m => m.after === anchor).flatMap(m => m.actions)
const invulns = new Set(['Holmgang', 'Superbolide', 'Hallowed Ground', 'Living Dead'])

test('FRU covers all pairings and every route assigns exactly one invuln to each Wings sequence', () => {
  assert.equal(plans.length, 12)
  for (const plan of plans) {
    assert.equal(new Set(plan.phases.map(p => p.id)).size, 5)
    for (const route of routesFor(plan.job, plan.with!)) {
      for (const anchor of ['p2-quadruple-slap-1', 'p4-somber-dance-1', 'p5-wings-dark-and-light-1', 'p5-wings-dark-and-light-3']) {
        const actions = [...actionsAt(plan.job, plan.with!, route, anchor), ...actionsAt(plan.with!, plan.job, route, anchor)]
        assert.equal(actions.filter(a => invulns.has(a.name)).length, 1, `${plan.job}/${plan.with}/${route}/${anchor}`)
      }
    }
  }
})

test('FRU uses standard P3 plans with no alternate invuln branches', () => {
  for (const plan of plans) {
    for (const seat of ['MT', 'OT']) {
      assert.ok(!availableTankChoices(plan, seat).some(c => c.id === 'p3'))
      assert.deepEqual(selectTankRoute(plan, { p3: 'dance' }, seat), selectTankRoute(plan, {}, seat))
    }
    assert.ok(plan.phases.every(p => p.mechanics.every(m => !('p3' in (m.when ?? {})))))
  }
  assert.equal(actionsAt('GNB', 'DRK', 'gnb-opens', 'p3-black-halo-1')[0].name, 'Superbolide')
  assert.equal(actionsAt('GNB', 'DRK', 'drk-opens', 'p3-black-halo-1')[0].name, 'Kitchen Sink')
  for (const [job, other] of [['DRK', 'GNB'], ['PLD', 'WAR']]) {
    for (const route of routesFor(job, other)) {
      assert.ok(actionsAt(job, other, route, 'p3-darkest-dance-1').every(a => !invulns.has(a.name)))
    }
  }
})

test('FRU P1 alternatives select one Powder invuln, and 7/1 selects solo versus buddy duties', () => {
  for (const plan of plans) {
    for (const route of routesFor(plan.job, plan.with!)) {
      for (const powder of ['first', 'second']) {
        const pair = [plan.job, plan.with!].map((job, i) => selected(job, i ? plan.job : plan.with!, route, powder))
        const p1 = pair.flatMap(p => p.phases[0].mechanics)
        const pressed = p1.filter(m => m.actions.some(a => invulns.has(a.name)))
        assert.equal(pressed.length, 1)
        assert.equal(pressed[0].after, `p1-powder-mark-trail-${powder === 'first' ? 1 : 2}`)
      }
      assert.equal(selected(plan.job, plan.with!, route).phases[3].mechanics.filter(m => m.after?.includes('akh-morn')).length, 2)
      for (const first of [plan.job, plan.with!]) {
        const p4 = selected(plan.job, plan.with!, route, 'first', first).phases[3].mechanics
        for (const [i, row] of p4.filter(m => m.after?.includes('akh-morn')).entries()) {
          const solo = (plan.job === first) === (i === 0)
          assert.equal(row.actions.every(a => Boolean(a.buddy)), !solo)
          assert.equal(row.tag?.startsWith('Solo'), solo)
        }
      }
    }
  }
})

test('FRU second-hit TBN and buddy mits stay distinct from first-hit presses', () => {
  for (const plan of plans) {
    const p5 = selectTankRoute(plan, tankChoices(plan, {}, 'MT'), 'MT').phases[4]
    for (const row of p5.mechanics) {
      const second = row.tag === 'Second hit'
      if (second) {
        assert.ok(['1:01', '2:59'].includes(row.time!))
        assert.ok(row.actions.every(a => a.buddy || a.name === 'The Blackest Night'))
      }
      else assert.ok(row.actions.every(a => !a.buddy && a.name !== 'The Blackest Night'))
    }
  }
  const drk = selected('DRK', 'WAR', 'war-opens').phases[4].mechanics
  const personal = drk.find(m => m.time === '1:01')!
  assert.equal(personal.actions[0].name, 'The Blackest Night')
  assert.ok(!personal.actions[0].buddy)
  assert.ok(drk.find(m => m.time === '2:59')!.actions.every(a => a.buddy))
})

test('tank choices recover stale preferences and reject malformed catalog conditions', () => {
  const plan = planFor('WAR', 'GNB')
  assert.equal(tankChoices(plan, { route: 'obsolete', powder: 'invalid' }, 'OT').route, undefined)
  assert.equal(tankChoices(plan, {}, 'OT').powder, 'first')
  const files = structuredClone(readFightFiles())
  const path = Object.keys(files).find(p => p.endsWith('fru/sheets/mitbutgood.json'))!
  const raw = files[path] as { tankMits: { plans: typeof plans } }
  raw.tankMits.plans[0].phases[0].mechanics[0].when = { route: 'unknown-route' }
  assert.throws(() => validateCatalog(files, {}, { jobs: loadCatalog().jobs }), /Unknown tank choice/)
})

test('FRU seats determine opening duties and expose only applicable strategies', () => {
  for (const plan of plans) assert.ok(!availableTankChoices(plan, 'MT').some(c => c.id === 'route'))
  const gnb = planFor('GNB', 'DRK')
  for (const seat of ['MT', 'OT']) {
    const rows = selectTankRoute(gnb, {}, seat).phases.flatMap(p => p.mechanics)
    assert.equal(rows.some(r => r.after === 'p1-powder-mark-trail-1' && r.actions.some(a => a.name === 'Superbolide')), seat === 'MT')
    assert.equal(rows.some(r => r.after === 'p2-quadruple-slap-1' && r.actions.some(a => a.name === 'Superbolide')), seat === 'OT')
  }

})

test('FRU strategy controls follow phase order and require a 7/1 order', () => {
  for (const plan of plans) {
    assert.deepEqual(plan.choices!.map(c => c.id), ['powder', 'akh'])
    const akh = plan.choices!.find(c => c.id === 'akh')!
    assert.deepEqual(new Set(akh.options.map(o => o.id)), new Set([plan.job, plan.with]))
    assert.ok(akh.options.some(o => o.id === akh.default))
  }
})
