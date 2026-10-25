import assert from 'node:assert/strict'
import test from 'node:test'
import { abilityAtLevel } from '@xivmits/core'
import { loadCatalog } from '@xivmits/encounter-data'

const catalog = loadCatalog()
const fight = catalog.fights.find(f => f.id === 'tea')!
const sheet = catalog.sheets.find(s => s.fightId === 'tea')!
const mechanic = (id: string) => sheet.phases.flatMap(phase => phase.mechanics).find(row => row.id === id)!
const names = (id: string, slot: string) => mechanic(id).assignments[slot]?.map(action => action.name) ?? []

test('TEA syncs to 80 and credits the NAUR sheet', () => {
  assert.equal(fight.syncLevel, 80)
  assert.equal(fight.shortName, 'TEA')
  assert.equal(fight.released, '2019-11-12')
  assert.deepEqual(fight.phases.map(phase => phase.id), ['p1', 'lc', 'p2', 'p3', 'p4'])
  assert.equal(fight.phases[0].start, '0:00')
  assert.equal(fight.phases[1].start, undefined)
  assert.equal(sheet.name, 'NAUR')
  assert.match(sheet.author ?? '', /@sounox \(LPDU\/NAUR\)/)
  assert.match(sheet.author ?? '', /Jamie Jams @ Faerie/)
  assert.match(sheet.description ?? '', /11\/21\/2025/)
  assert.match(sheet.description ?? '', /NAUR staff/)
  assert.equal(sheet.updated, '2025-11-21')
  assert.match(sheet.source?.url ?? '', /1A58RflNeNq9mesuvSEcQzIvQ3MwOGyvPRi5khNACrc8/)
})

test('level 80 generics and the NAUR rows resolve to the buttons that level has', () => {
  const pld = catalog.jobs.find(job => job.id === 'PLD')!
  assert.equal(abilityAtLevel(pld, 'Short Mit', fight.syncLevel), 'Sheltron')
  assert.deepEqual(names('p1-fluid-swing-1', 'MT'), ['90s Mit', 'Short Mit', 'Reprisal'])
  assert.deepEqual(names('p1-cascade-1', 'SGE'), ['Physis II', 'Ixochole'])
  assert.ok(names('p1-cascade-1', 'MT').includes('Passage of Arms (PLD)'))
  assert.ok(names('p1-cascade-1', 'OT').includes('Passage of Arms (PLD)'))
  assert.deepEqual(names('p1-jagd-dolls-1', 'P'), ['Party Mit', "Nature's Minne (BRD)"])
  assert.ok(names('p1-splash-1', 'P').includes('Extra (MCH)'))
  assert.equal(mechanic('p1-cascade-1').time, '0:20')
  assert.equal(mechanic('lc-limit-cut-1').time, '0:07')
  assert.equal(mechanic('p3-j-wave-0').note, 'Covers J Waves 0 through 3.')
  assert.match(sheet.phases.find(phase => phase.id === 'p1')!.note ?? '', /Shade Shift/)
  const written = JSON.stringify(sheet)
  for (const retired of ['Holy Sheltron', 'Bloodwhetting', 'Heart of Corundum', 'Oblation', 'Aquaveil', 'Expedient', 'Magick Barrier', 'Macrocosmos']) {
    assert.equal(written.includes(retired), false, retired)
  }
})
