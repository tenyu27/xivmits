import assert from 'node:assert/strict'
import test from 'node:test'
import { loadCatalog } from '@xivmits/encounter-data'

const catalog = loadCatalog()
const fight = catalog.fights.find(f => f.id === 'dsr')!
const sheet = catalog.sheets.find(s => s.fightId === 'dsr')!

test('DSR tank footnotes stay with their source mechanic and job pairing', () => {
  for (const plan of sheet.tankMits!.plans) {
    for (const phase of plan.phases) {
      if (phase.note) assert.equal(phase.id, 'p3', 'Only the autos instruction applies throughout a phase')
      for (const row of phase.mechanics) {
        if (row.note?.startsWith('WB2:')) assert.equal(row.after, 'p6-great-wyrmsbreath-2')
        if (row.note?.startsWith('AM1:')) assert.equal(row.after, 'p7-akh-morn-s-edge-1')
        if (row.note?.startsWith('Rep from')) assert.equal(row.after, 'p2-ascalon-s-might-1')
        if (row.note?.includes('Feint is free')) assert.equal(row.after, 'p5-heavenly-heel-2')
      }
    }
    assert.ok(plan.phases.find(p => p.id === 'p7')!.mechanics[0].note?.startsWith('AM1:'))
    if (plan.job !== 'WAR') {
      assert.ok(plan.phases.find(p => p.id === 'p6')!.mechanics
        .find(m => m.after === 'p6-great-wyrmsbreath-2')!.note?.startsWith('WB2:'))
    }
  }
})

test('DSR party rows follow every workbook section and its row order', () => {
  const sourceRows = {
    p2: ['strength-of-the-ward-1', 'ancient-quaga-1', 'sanctity-of-the-ward-1', 'ultimate-end-1', 'final-chorus-1'],
    p3: ['eye-of-the-tyrant-1', 'eye-of-the-tyrant-2', 'soul-tether-1'],
    p4: ['resentment-1', 'flare-nova-1', 'mirage-dive-1', 'steep-in-rage-1'],
    rewind: ['brightwing-1', 'brightwing-2', 'brightwing-3', 'brightwing-4', 'pure-of-heart-1'],
    p5: ['wrath-of-the-heavens-1', 'ancient-quaga-1', 'death-of-the-heavens-1', 'ancient-quaga-2', 'heavenly-heel-2'],
    p6: ['great-wyrmsbreath-1', 'akh-afah-1', 'wroth-flames-1', 'akh-afah-2', 'great-wyrmsbreath-2', 'cauterize-2'],
    p7: ['alternative-end-1', 'akh-morn-s-edge-1', 'gigaflare-s-edge-1', 'akh-morn-s-edge-2', 'gigaflare-s-edge-2', 'akh-morn-s-edge-3'],
  }
  for (const [pid, rows] of Object.entries(sourceRows)) {
    const actual = sheet.phases.find(p => p.id === pid)!.mechanics
      .filter(m => Object.keys(m.assignments).length || m.id === 'rewind-brightwing-4')
    assert.deepEqual(actual.map(m => m.id), rows.map(id => `${pid}-${id}`), pid)
  }
})

test('fight selection follows original release order', () => {
  assert.deepEqual(catalog.fights.map(f => f.id), ['dmu', 'fru', 'top', 'dsr'])
})

test('DSR uses longest observed phase lengths and keeps checkpoint and transition clocks distinct', () => {
  assert.deepEqual(fight.phases.map(p => [p.id, p.start]), [
    ['p2', '0:00'], ['p3', '3:26'], ['p4', '5:40'], ['rewind', '6:57'],
    ['p5', '8:21'], ['p6', '11:29'], ['p7', '15:15'],
  ])
  for (const phase of fight.phases) {
    for (const mechanic of phase.mechanics) {
      assert.ok(mechanic.time && mechanic.fflogs?.abilityIds.length, mechanic.id)
    }
  }
  const chorus = sheet.phases.find(p => p.id === 'p2')!.mechanics.at(-1)!
  assert.equal(chorus.id, 'p2-final-chorus-1')
  assert.equal(chorus.time, '3:23')
  assert.ok(chorus.assignments.OT.some(a => a.name === 'Party Mit'))
  const transition = sheet.phases.find(p => p.id === 'p7')!.mechanics[0]
  assert.equal(transition.id, 'p7-alternative-end-1')
  assert.equal(transition.time, '0:00')
  assert.ok(transition.assignments.SCH.some(a => a.name === 'Deployment Tactics'))
})

test('DSR retains source continuations and every pairing without importing duplicate or TOP template rows', () => {
  assert.deepEqual(sheet.phases.map(p => Object.values(p.mechanics).reduce((n, m) =>
    n + Object.values(m.assignments).flat().length, 0)), [48, 20, 25, 26, 34, 50, 65])
  assert.equal(sheet.tankMits!.plans.length, 12)
  for (const job of ['WAR', 'DRK', 'GNB', 'PLD']) {
    assert.equal(sheet.tankMits!.plans.filter(p => p.job === job).length, 3)
  }
  for (const plan of sheet.tankMits!.plans) {
    assert.deepEqual(plan.phases.map(p => p.id), ['p2', 'p3', 'p5', 'p6', 'p7'])
    for (const phase of plan.phases) for (const row of phase.mechanics) {
      const anchor = fight.phases.find(p => p.id === phase.id)!.mechanics.find(m => m.id === row.after)!
      assert.ok(anchor, row.id)
      assert.equal(row.time, anchor.time)
      assert.equal(row.name, anchor.name)
    }
  }
  assert.ok(!JSON.stringify(sheet).match(/Cosmo|Wave Cannon|Under Construction/))
  const heel = sheet.phases.find(p => p.id === 'p5')!.mechanics.find(m => m.id === 'p5-heavenly-heel-2')!
  assert.deepEqual(heel.assignments.M1, [{ name: 'Feint' }])
  assert.equal(heel.note, undefined)
  for (const job of ['SCH', 'SGE', 'WHM', 'AST'])
    assert.ok(heel.assignments[job][0].note?.includes('Healers'))
  const rewind = sheet.phases.find(p => p.id === 'rewind')!.mechanics.find(m => m.id === 'rewind-brightwing-2')!
  assert.ok(rewind.assignments.OT.some(a => a.name === 'Reprisal'))
})
