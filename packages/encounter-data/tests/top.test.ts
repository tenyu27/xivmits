import assert from 'node:assert/strict'
import test from 'node:test'
import { readFileSync } from 'node:fs'
import { loadCatalog, readFightFiles } from '@xivmits/encounter-data'
import type { MitSheet } from '@xivmits/core'

const catalog = loadCatalog()
const fight = catalog.fights.find(f => f.id === 'top')!
const sheet = Object.entries(readFightFiles()).find(([path]) => path.endsWith('/top/sheets/topmitty.json'))![1] as MitSheet

test('TOP phase starts retain the longest observed phase lengths from the slow-clear audit', () => {
  // P2's 145.123s is from J3P84vzxT6YDhwGq/1; P3's 193.547s is
  // from yMTqNwFRLacJWvx7/8. Neither is the longest total clear.
  assert.deepEqual(fight.phases.map(p => p.start), ['0:00', '2:11', '4:36', '7:50', '9:01', '13:48'])
})

test('TOP retains every source assignment with Blind Faith at its P5 cast cue', () => {
  assert.deepEqual(sheet.phases.map(p => p.mechanics.length), [5, 1, 6, 7, 7, 11])
  assert.deepEqual(sheet.phases.map(p => p.mechanics.reduce((n, m) =>
    n + Object.values(m.assignments).reduce((sum, actions) => sum + actions.length, 0), 0)),
  [32, 24, 39, 21, 57, 79])
  assert.equal(sheet.phases[4].mechanics.at(-1)!.mechanicId, 'p5-blind-faith-1')
  const cue = fight.phases[4].mechanics.find(m => m.id === 'p5-blind-faith-1')!
  assert.equal(cue.time, '4:35')
  assert.ok(!cue.minor)
  assert.ok(!sheet.phases[5].mechanics.some(m => m.mechanicId === 'p6-blind-faith-1'))
  const blind = fight.phases[5].mechanics[0]
  assert.equal(blind.id, 'p6-blind-faith-1')
  assert.equal(blind.time, '0:00')
  assert.deepEqual(blind.fflogs?.abilityIds, [32626])
})

test('TOP P2 groups the numeric source row at Meteor instead of Party Synergy', () => {
  const rows = sheet.phases[1].mechanics
  assert.equal(rows.length, 1)
  assert.equal(rows[0].mechanicId, 'p2-optimized-meteor-1')
  assert.equal(rows[0].note, 'Mitigation for Optimized Meteor and Cosmo Memory.')
  const mechanics = fight.phases[1].mechanics
  assert.equal(mechanics.find(m => m.id === 'p2-party-synergy-1')!.minor, true)
  assert.ok(!mechanics.find(m => m.id === 'p2-optimized-meteor-1')!.minor)
  assert.ok(!mechanics.find(m => m.id === 'p2-cosmo-memory-1')!.minor)
})

test('TOP tank plans use the actual buster name and damage time', () => {
  assert.equal(sheet.tankMits!.plans.length, 12)
  const expectedCounts = [35, 37, 35, 30, 37, 43, 32, 42, 38, 42, 38, 50]
  assert.deepEqual(sheet.tankMits!.plans.map(plan => plan.phases.reduce((n, p) =>
    n + p.mechanics.reduce((sum, m) => sum + m.actions.length, 0), 0)), expectedCounts)
  for (const plan of sheet.tankMits!.plans) {
    for (const phase of plan.phases) {
      const mechanics = fight.phases.find(p => p.id === phase.id)!.mechanics
      for (const row of phase.mechanics) {
        if (!row.after) {
          assert.equal(row.name, 'Prepull')
          continue
        }
        const canonical = mechanics.find(m => m.id === row.after)!
        assert.equal(row.name, canonical.name)
        assert.equal(row.time, canonical.time)
      }
    }
    const p2 = plan.phases.find(p => p.id === 'p2')!
    assert.ok(p2.mechanics.some(m => m.after === 'p2-solar-ray-1'))
    assert.ok(p2.mechanics.some(m => m.after === 'p2-optimized-bladedance-1'))
  }
  assert.ok(sheet.tankMits!.plans.some(plan => plan.phases.some(phase =>
    phase.mechanics.some(m => m.after === 'p3-oversampled-wave-cannon-1'))))
})

test('TOP distinguishes repeated hits without duplicating the sheet presses', () => {
  const blasters = fight.phases[0].mechanics.filter(m => m.id.startsWith('p1-blaster-'))
  assert.deepEqual(blasters.map(m => m.fflogs?.abilityIds), [
    [31495, 31496, 31498], [31496, 31498], [31496, 31498], [31497, 31498],
  ])
  const p1 = fight.phases[0].mechanics.filter(m => m.id.startsWith('p1-diffuse-wave-cannon-kyrios-'))
  assert.deepEqual(p1.map(m => m.time), ['1:49', '1:51', '1:53', '1:55', '1:57'])
  assert.equal(p1.filter(m => !m.minor).length, 1)
  const p3 = fight.phases[2].mechanics.find(m => m.id === 'p3-oversampled-wave-cannon-1')!
  assert.equal(p3.roles, undefined, 'P3 monitors damage all roles')
  const p5 = sheet.phases[4].mechanics
  assert.ok(p5.some(m => m.mechanicId === 'p5-hello-distant-world-3'))
  assert.ok(!p5.some(m => m.mechanicId === 'p5-hello-distant-world-4'))
  const p6 = sheet.phases[5].mechanics
  assert.ok(p6.some(m => m.mechanicId === 'p6-wave-cannon-1'))
  assert.ok(!p6.some(m => m.mechanicId === 'p6-wave-cannon-2'))
})


test('TOP P5 groups every event after each raidwide and before its next Solar Ray', () => {
  const canonical = fight.phases[4].mechanics
  const resolved = catalog.sheets.find(s => s.fightId === 'top')!.phases[4].mechanics
  const seconds = (time: string) => time.split(':').map(Number).reduce((m, s) => m * 60 + s)
  for (const [i, version] of ['Delta', 'Sigma', 'Omega'].entries()) {
    const row = resolved.find(m => m.name === `${version} Mech`)!
    const start = canonical.find(m => m.id === `p5-run-mi-${version.toLowerCase()}-version-1`)!
    const end = canonical.find(m => m.id === `p5-solar-ray-${i * 2 + 3}`)!
    assert.equal(row.time, ['0:26', '1:49', '3:18'][i])
    assert.equal(seconds(row.time!), seconds(start.time!) + 1)
    const members = canonical.filter(m => seconds(m.time!) >= seconds(row.time!) && seconds(m.time!) < seconds(end.time!))
    assert.deepEqual(row.coveredMechanicIds, members.map(m => m.id))
    assert.deepEqual(row.fflogs?.abilityIds, [...new Set(members.flatMap(m => m.fflogs!.abilityIds))])
    assert.ok(resolved.some(m => m.id === end.id), 'Solar Ray remains outside the group')
    assert.ok(members.every(m => m.id === row.id || !resolved.some(r => r.id === m.id)))
    assert.ok(!row.minor)
  }
  assert.ok(resolved.find(m => m.name === 'Omega Mech')!.coveredMechanicIds!.includes('p5-hello-distant-world-4'))
  assert.equal(canonical.find(m => m.id === 'p5-hello-distant-world-3')!.time, '3:52')
  const blind = resolved.find(m => m.id === 'p5-blind-faith-1')!
  assert.equal(Object.values(blind.assignments).flat().length, 5)
})


test('TOP preserves reviewed source guidance outside tank-only plans', () => {
  assert.match(sheet.phases[1].note!, /After Playstation: Feint \/ Addle/)
  assert.match(sheet.phases[4].note!, /15s party mit.*second hit/)
  assert.match(sheet.phases[4].note!, /10s party mit.*start of the raidwide cast/)
  assert.match(sheet.phases[4].note!, /WAR\/PLD, GNB\/DRK, GNB\/PLD, PLD\/DRK: Healers must/)
  assert.equal(sheet.phases[5].note, undefined)
  for (const id of ['p6-wave-cannon-3', 'p6-wave-cannon-6'])
    assert.match(sheet.phases[5].mechanics.find(m => m.mechanicId === id)!.note!, /after the 1st set of proteans/)
  assert.match(sheet.phases[5].mechanics.find(m => m.mechanicId === 'p6-cosmo-memory-1')!.assignments.T1.find(a => a.name === 'Tank LB')!.note!, /WAR > DRK > PLD/)
  for (const plan of sheet.tankMits!.plans) {
    const phase = plan.phases.find(p => p.id === 'p6')!
    const note = phase.note ?? ''
    const paired = [plan.job, plan.with].sort().join('/') === 'DRK/GNB'
    assert.equal(note.includes('Cosmo Memory instead of Cosmo Dive 1'), paired)
    if (paired) assert.equal(phase.noteAfter, 'p6-cosmo-memory-1')
    assert.match(phase.mechanics.find(m => m.after === 'p6-cosmo-dive-1')!.note!, /Rampart after/)
    if (plan.job === 'DRK') assert.match(phase.mechanics.find(m => m.after === 'p6-wave-cannon-6')!.note!, /Save MP/)
  }
  const p6 = sheet.phases[5].mechanics
  assert.ok(!p6.find(m => m.mechanicId === 'p6-cosmo-memory-1')!.assignments.T1.some(a => a.name === 'Party Mit'))
  assert.ok(p6.find(m => m.mechanicId === 'p6-cosmo-dive-1')!.assignments.T1.some(a => a.name === 'Party Mit'))
  const sch = sheet.phases.flatMap(p => p.mechanics.flatMap(m => m.assignments.SCH ?? []))
  assert.ok(sch.some(a => a.name === 'Seraph Veil'))
  assert.ok(!sch.some(a => a.name === "Seraph's Veil" || a.name === 'Seraph'))
  const ability = catalog.abilities.abilities[catalog.abilities.names['Seraph Veil']]
  assert.equal(ability.name, 'Seraphic Veil')
  assert.equal(ability.action, 16548)
})


test('TOP evidence documentation agrees with every canonical time and visibility flag', () => {
  const doc = readFileSync(new URL('../../../docs/TOP.md', import.meta.url), 'utf8')
  const mechanics = fight.phases.flatMap(p => p.mechanics)
  const rows = [...doc.matchAll(/^\| `(p\d-[^`]+)` \| (\d+:\d+) \| (?:damage|cast|begincast) \|.*\| (hidden|tank-only|all) \|$/gm)]
  assert.equal(rows.length, mechanics.length)
  assert.equal(new Set(rows.map(r => r[1])).size, mechanics.length)
  for (const [, id, time, visibility] of rows) {
    const mechanic = mechanics.find(m => m.id === id)!
    assert.equal(time, mechanic.time, id)
    assert.equal(visibility, mechanic.minor ? 'hidden' : mechanic.roles?.includes('tank') ? 'tank-only' : 'all', id)
  }
})
