import assert from 'node:assert/strict'
import test from 'node:test'
import { abilityAtLevel, durationAtLevel, resolveAction } from '@xivmits/core'
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
  assert.deepEqual(names('p1-jagd-dolls-1', 'P'), ['Party Mit (MCH)', "Nature's Minne (BRD)"])
  assert.equal(mechanic('p1-jagd-dolls-1').assignments.P?.[0]?.note, 'Optional.')
  assert.ok(names('p1-splash-1', 'P').includes('Extra (MCH)'))
  assert.equal(mechanic('p1-cascade-1').time, '0:20')
  assert.equal(mechanic('lc-limit-cut-1').time, '0:07')
  assert.equal(mechanic('p3-j-wave-0').note, 'Covers J Waves 0 through 3.')
  assert.match(sheet.phases.find(phase => phase.id === 'p1')!.note ?? '', /Shade Shift/)
  const written = JSON.stringify(sheet)
  for (const retired of ['Holy Sheltron', 'Bloodwhetting', 'Heart of Corundum', 'Oblation', 'Aquaveil', 'Expedient', 'Magick Barrier', 'Macrocosmos', 'If playing MCH']) {
    assert.equal(written.includes(retired), false, retired)
  }
})

const job = (id: string) => catalog.jobs.find(candidate => candidate.id === id)!
const SLOT_JOBS = {
  MT: ['PLD', 'WAR', 'DRK', 'GNB'],
  OT: ['PLD', 'WAR', 'DRK', 'GNB'],
  SCH: ['SCH'], SGE: ['SGE'], WHM: ['WHM'], AST: ['AST'],
  M1: ['MNK', 'DRG', 'NIN', 'SAM', 'RPR', 'VPR'],
  M2: ['MNK', 'DRG', 'NIN', 'SAM', 'RPR', 'VPR'],
  P: ['BRD', 'MCH', 'DNC'],
  C: ['BLM', 'SMN', 'RDM', 'PCT'],
}
const POST80 = [
  'Holy Sheltron', 'Bloodwhetting', 'Heart of Corundum', 'Oblation', 'Aquaveil',
  'Liturgy of the Bell', 'Exaltation', 'Expedient', 'Magick Barrier', 'Macrocosmos',
  'Concitation', 'Medica III', 'Helios Conjunction', 'Eukrasian Prognosis II',
  'Krasis', 'Pneuma', 'Protraction', 'Divine Caress', 'Physis',
]
const UNRESOLVED = /^(?:Party Mit|Short Mit|90s Mit|120s Mit|Invuln|Extra|Buddy Mit)(?: \([A-Z]{3}(?:\/[A-Z]{3})*\))?$/

test('every TEA clock is monotonic inside its phase', () => {
  const toSeconds = (time: string) => {
    const [minutes, secs] = time.split(':').map(Number)
    return minutes * 60 + secs
  }
  for (const phase of fight.phases) {
    let prev = -1
    for (const row of phase.mechanics) {
      assert.match(row.time ?? '', /^\d+:[0-5]\d$/, `${phase.id} ${row.id}`)
      const secs = toSeconds(row.time!)
      assert.ok(secs >= prev, `${phase.id} ${row.id} ${row.time} follows ${prev}`)
      prev = secs
    }
  }
})

test('every TEA assignment resolves at 80 for every job that can stand in the slot', () => {
  const dolls = mechanic('p1-jagd-dolls-1')
  assert.equal(resolveAction('Party Mit (MCH)', job('MCH'), catalog.icons, 80).applies && resolveAction('Party Mit (MCH)', job('MCH'), catalog.icons, 80).label, 'Tactician')
  for (const id of ['BRD', 'DNC']) assert.equal(resolveAction('Party Mit (MCH)', job(id), catalog.icons, 80).applies, false, id)
  assert.equal(resolveAction("Nature's Minne (BRD)", job('BRD'), catalog.icons, 80).applies && resolveAction("Nature's Minne (BRD)", job('BRD'), catalog.icons, 80).label, "Nature's Minne (BRD)")
  for (const id of ['MCH', 'DNC']) assert.equal(resolveAction("Nature's Minne (BRD)", job(id), catalog.icons, 80).applies, false, id)
  for (const slot of ['M1', 'M2']) {
    assert.ok(dolls.assignments[slot]?.some(action => action.name === 'Mantra (MNK)'))
    for (const id of SLOT_JOBS.M1) {
      const resolved = resolveAction('Mantra (MNK)', job(id), catalog.icons, 80)
      assert.equal(resolved.applies, id === 'MNK', `${slot} ${id}`)
      if (resolved.applies) assert.equal(resolved.label, 'Mantra (MNK)')
    }
  }

  for (const [slot, ids] of Object.entries(SLOT_JOBS)) {
    for (const id of ids) {
      const player = job(id)
      for (const phase of sheet.phases) for (const row of phase.mechanics) {
        for (const action of row.assignments[slot] ?? []) {
          const resolved = resolveAction(action.name, player, catalog.icons, fight.syncLevel)
          if (!resolved.applies) continue
          assert.equal(UNRESOLVED.test(resolved.label), false, `${id} ${row.id} ${action.name} -> ${resolved.label}`)
          assert.equal(POST80.includes(resolved.label), false, `${id} ${row.id} ${resolved.label}`)
          const abilityId = catalog.abilities.names[resolved.label]
          const durations = abilityId ? catalog.abilities.abilities[abilityId]?.durations : undefined
          if (durations) assert.equal(durationAtLevel(durations, fight.syncLevel), 10, `${id} ${resolved.label}`)
        }
      }
    }
  }
})
