import assert from 'node:assert/strict'
import test from 'node:test'
import { loadCatalog, readFightFiles } from '@xivmits/encounter-data'

test('validates the repository catalog and keeps FFLogs placeholders empty', () => {
  const paths = Object.keys(readFightFiles())
  const catalog = loadCatalog()

  const encounterCount = paths.filter(path => path.endsWith('encounter.json')).length
  const sheetCount = paths.filter(path => path.includes('/sheets/')).length
  assert.equal(catalog.fights.length, encounterCount)
  assert.equal(catalog.sheets.length, sheetCount)
  for (const fight of catalog.fights) {
    assert.deepEqual(fight.fflogs?.encounterIds, [])
    const mechanics = fight.phases.flatMap(phase => phase.mechanics)
    const unnumberedNames = mechanics
      .map(mechanic => mechanic.name)
      .filter(name => !/\(\d+\)$|\b\d+(?:st|nd|rd|th)?\b/i.test(name))
    assert.equal(new Set(unnumberedNames).size, unnumberedNames.length)
    for (const mechanic of mechanics) {
      assert.deepEqual(mechanic.fflogs?.abilityIds, [])
    }
  }
})
