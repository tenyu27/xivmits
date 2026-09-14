import assert from 'node:assert/strict'
import test from 'node:test'
import { loadCatalog } from '@xivmits/encounter-data'

// Reviewed against Ikuya v6.0's active Omnitank tab. The party tab omits
// Thunder III sets 2–4, so its preceding row cannot identify those busters.
const anchors: Record<string, Array<string | undefined>> = {
  p1: ['p1-revolting-ruin-iii-1', 'p1-hyperdrive-1', 'p1-revolting-ruin-iii-2', 'p1-hyperdrive-2'],
  p2: ['p2-ultimate-embrace-1', 'p2-wings-of-destruction-1', 'p2-ultimate-embrace-2'],
  p3: [1, 2, 3, 4, 5].map(n => `p3-thunder-iii-${n}`).concat('p3-black-hole-10'),
  p4: [undefined],
  p5: ['p5-fell-forces-1', 'p5-maddening-orchestra-1', 'p5-flare-1',
    'p5-fell-forces-2', 'p5-fell-forces-3', 'p5-maddening-orchestra-2',
    'p5-flare-2', 'p5-fell-forces-4', 'p5-fell-forces-4'],
}
const invulns = {
  PLD: 'Hallowed Ground', WAR: 'Holmgang', DRK: 'Living Dead', GNB: 'Superbolide',
}

test('every Ikuya tank branch keeps its reviewed mechanic occurrence and time', () => {
  const catalog = loadCatalog()
  const sheet = catalog.sheets.find(s => s.fightId === 'dmu' && s.id === 'ikuya')!
  const fight = catalog.fights.find(f => f.id === 'dmu')!
  const plans = sheet.tankMits!.plans
  assert.deepEqual(plans.map(p => p.job).sort(), Object.keys(invulns).sort())
  for (const plan of plans) {
    assert.deepEqual(plan.phases.map(p => p.id), Object.keys(anchors))
    for (const phase of plan.phases) {
      const label = `${plan.job}/${phase.id}`
      assert.deepEqual(phase.mechanics.map(m => m.after),
        anchors[phase.id].flatMap(anchor => [anchor, anchor]), label)
      const canonical = fight.phases.find(p => p.id === phase.id)!.mechanics
      for (const row of phase.mechanics) {
        if (!row.after) continue
        const mechanic = canonical.find(m => m.id === row.after)!
        assert.equal(row.name, mechanic.name, `${label}/${row.id} name`)
        assert.equal(row.time, mechanic.time, `${label}/${row.id} time`)
      }
    }
  }
})

test('all four Ikuya tanks invuln P3 set 2 on Chaos and set 4 on Exdeath, independent of seat', () => {
  const sheet = loadCatalog().sheets.find(s => s.fightId === 'dmu' && s.id === 'ikuya')!
  for (const [job, invuln] of Object.entries(invulns)) {
    const phase = sheet.tankMits!.plans.find(p => p.job === job)!.phases.find(p => p.id === 'p3')!
    for (const seat of ['MT', 'OT']) {
      for (const [boss, after, time] of [
        ['Chaos', 'p3-thunder-iii-2', '1:49'],
        ['Exdeath', 'p3-thunder-iii-4', '2:48'],
      ]) {
        const rows = phase.mechanics.filter(m => (!m.seat || m.seat === seat)
          && (!m.boss || m.boss === boss) && m.actions.some(a => a.name === invuln))
        assert.deepEqual(rows.map(m => ({ after: m.after, time: m.time })),
          [{ after, time }], `${seat}/${job}/${boss}`)
      }
    }
  }
})
