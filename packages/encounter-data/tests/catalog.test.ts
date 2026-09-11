import assert from 'node:assert/strict'
import test from 'node:test'
import { loadCatalog, readFightFiles } from '@xivmits/encounter-data'

test('validates the repository catalog and keeps reconciled phases anchored to FFLogs', () => {
  const paths = Object.keys(readFightFiles())
  const catalog = loadCatalog()

  const encounterCount = paths.filter(path => path.endsWith('encounter.json')).length
  const sheetCount = paths.filter(path => path.includes('/sheets/')).length
  assert.equal(catalog.fights.length, encounterCount)
  assert.equal(catalog.sheets.length, sheetCount)
  for (const fight of catalog.fights) {
    // Encounter ids are resolved (FFLogs worldData); mechanic ability ids are
    // not yet - filling them is what ties a mechanic to real log events.
    assert.ok(fight.fflogs?.encounterIds.length, `${fight.id} has no FFLogs encounter id`)
    const mechanics = fight.phases.flatMap(phase => phase.mechanics)
    const unnumberedNames = mechanics
      .map(mechanic => mechanic.name)
      .filter(name => !/\(\d+\)$|\b\d+(?:st|nd|rd|th)?\b/i.test(name))
    assert.equal(new Set(unnumberedNames).size, unnumberedNames.length)
    for (const mechanic of mechanics) {
      assert.ok(mechanic.fflogs, `${fight.id}/${mechanic.id} lost its fflogs block`)
    }
  }

  // Phases already reconciled against real logs must stay anchored: every
  // mechanic carries at least one ability id, and a time to go with it. Add a
  // phase to this list as it is reconciled - the rest are still sheet-derived.
  const anchored = [['dmu', 'p1'], ['dmu', 'p2'], ['dmu', 'p3'], ['dmu', 'p4'], ['dmu', 'p5']]
  for (const [fightId, phaseId] of anchored) {
    const phase = catalog.fights.find(f => f.id === fightId)!.phases.find(p => p.id === phaseId)!
    for (const mechanic of phase.mechanics) {
      assert.ok(mechanic.time, `${fightId}/${mechanic.id} has no time`)
      assert.ok(mechanic.fflogs!.abilityIds.length, `${fightId}/${mechanic.id} has no ability id`)
    }
  }
})
