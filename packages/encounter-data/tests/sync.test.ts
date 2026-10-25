import assert from 'node:assert/strict'
import test from 'node:test'
import { abilityAtLevel, durationAtLevel, potencyAtLevel } from '@xivmits/core'
import { loadCatalog } from '@xivmits/encounter-data'
import type { Job } from '@xivmits/core'

const catalog = loadCatalog()
const byGameName = new Map(Object.values(catalog.abilities.abilities).map(entry => [entry.name, entry]))

/** A sheet wording, or the in-game name a generic slot resolved to. */
function entryFor(name: string) {
  const id = catalog.abilities.names[name]
  return (id && catalog.abilities.abilities[id]) || byGameName.get(name)
}

const baseName = (name: string) => name.replace(/\s*\([^)]*\)\s*$/, '').trim()

test('every fight records the level it syncs to', () => {
  assert.deepEqual(
    Object.fromEntries(catalog.fights.map(fight => [fight.id, fight.syncLevel])),
    { dmu: 100, dsr: 90, fru: 100, tea: 80, top: 90 },
  )
})

test('no sheet assigns an action its fight has not unlocked at the sync level', () => {
  const jobsForSlot = (slots: { id: string; job?: string; role?: string; jobs?: string[] }[], slotId: string): Job[] => {
    const slot = slots.find(candidate => candidate.id === slotId)
    if (!slot) return []
    if (slot.job) {
      const job = catalog.jobs.find(candidate => candidate.id === slot.job)
      return job ? [job] : []
    }
    return catalog.jobs.filter(job => job.role === slot.role && (!slot.jobs || slot.jobs.includes(job.id)))
  }

  const check = (name: string, sync: number, where: string, jobs: Job[]) => {
    const written = entryFor(name)
    if (written?.level !== undefined) {
      assert.ok(written.level <= sync, `${where}: ${name} is level ${written.level}, above sync ${sync}`)
    }
    const slot = baseName(name)
    for (const job of jobs) {
      const resolved = abilityAtLevel(job, slot, sync)
      if (!resolved) continue
      const concrete = entryFor(resolved)
      if (concrete?.level !== undefined) {
        assert.ok(
          concrete.level <= sync,
          `${where}: ${job.id} ${name} resolves to ${resolved} (level ${concrete.level}), above sync ${sync}`,
        )
      }
    }
  }

  for (const sheet of catalog.sheets) {
    const sync = catalog.fights.find(fight => fight.id === sheet.fightId)?.syncLevel
    assert.equal(typeof sync, 'number', `${sheet.fightId} has no sync level`)
    for (const phase of sheet.phases) for (const mechanic of phase.mechanics) {
      for (const [slotId, actions] of Object.entries(mechanic.assignments)) {
        for (const action of actions) check(action.name, sync!, `${sheet.id} ${mechanic.id} ${slotId}`, jobsForSlot(sheet.slots, slotId))
      }
    }
    for (const plan of sheet.tankMits?.plans ?? []) {
      const job = catalog.jobs.find(candidate => candidate.id === plan.job)
      assert.ok(job, plan.job)
      for (const phase of plan.phases) for (const mechanic of phase.mechanics) {
        for (const action of mechanic.actions) check(action.name, sync!, `${sheet.id} ${plan.job} ${mechanic.id}`, [job])
        for (const alt of mechanic.alts ?? []) {
          for (const action of alt.actions) check(action.name, sync!, `${sheet.id} ${plan.job} ${mechanic.id} alt`, [job])
        }
      }
    }
  }
})

test('a job slot resolves to the button its level has, and the unsynced answer is the last step', () => {
  for (const job of catalog.jobs) {
    for (const [slot, steps] of Object.entries(job.levels ?? {})) {
      assert.equal(steps.at(-1)!.name, job.abilities![slot], `${job.id} ${slot}: last step must match abilities`)
      assert.deepEqual(steps.map(step => step.level), [...steps.map(step => step.level)].sort((a, b) => a - b))
      for (const step of steps) {
        const ability = entryFor(step.name)
        assert.ok(ability, `${job.id}: ${step.name} has no ability entry`)
        assert.equal(ability.level, step.level, `${job.id} ${slot}: ${step.name}`)
      }
    }
  }
  const slot = (id: string, sync?: number) => abilityAtLevel(catalog.jobs.find(job => job.id === id), '120s Mit', sync)
  assert.deepEqual(
    ['PLD', 'WAR', 'DRK', 'GNB'].map(id => slot(id, 90)),
    ['Sentinel', 'Vengeance', 'Shadow Wall', 'Nebula'],
  )
  assert.deepEqual(
    ['PLD', 'WAR', 'DRK', 'GNB'].map(id => slot(id, 91)),
    ['Sentinel', 'Vengeance', 'Shadow Wall', 'Nebula'],
  )
  assert.deepEqual(
    ['PLD', 'WAR', 'DRK', 'GNB'].map(id => slot(id, 92)),
    ['Guardian', 'Damnation', 'Shadowed Vigil', 'Great Nebula'],
  )
  assert.deepEqual(
    ['PLD', 'WAR', 'DRK', 'GNB'].map(id => slot(id, 100)),
    ['Guardian', 'Damnation', 'Shadowed Vigil', 'Great Nebula'],
  )
  assert.deepEqual(
    ['PLD', 'WAR', 'DRK', 'GNB'].map(id => slot(id)),
    ['Guardian', 'Damnation', 'Shadowed Vigil', 'Great Nebula'],
  )
  const at = (id: string, name: string, sync?: number) =>
    abilityAtLevel(catalog.jobs.find(job => job.id === id), name, sync)
  assert.deepEqual(
    ['PLD', 'WAR', 'DRK', 'GNB'].map(id => at(id, 'Short Mit', 80)),
    ['Sheltron', 'Raw Intuition', 'The Blackest Night', 'Heart of Stone'],
  )
  assert.deepEqual(
    ['PLD', 'WAR', 'DRK', 'GNB'].map(id => at(id, 'Short Mit', 82)),
    ['Holy Sheltron', 'Bloodwhetting', 'The Blackest Night', 'Heart of Corundum'],
  )
  assert.equal(at('GNB', 'Buddy Mit', 80), 'Heart of Stone')
  assert.equal(at('GNB', 'Buddy Mit', 90), 'Heart of Corundum')
  assert.equal(at('WAR', 'Buddy Mit', 80), 'Nascent Flash')
  assert.deepEqual(
    ['PLD', 'WAR', 'DRK', 'GNB'].map(id => at(id, '120s Mit', 80)),
    ['Sentinel', 'Vengeance', 'Shadow Wall', 'Nebula'],
  )
})

test('Vengeance is its own action, not Damnation', () => {
  const vengeance = entryFor('Vengeance')
  const damnation = entryFor('Damnation')
  assert.ok(vengeance && damnation)
  assert.equal(vengeance.name, 'Vengeance')
  assert.equal(vengeance.action, 44)
  assert.equal(vengeance.level, 38)
  assert.equal(vengeance.icon, '000267.png')
  assert.equal(catalog.icons.Vengeance, '000267.png')
  assert.equal(damnation.action, 36923)
  assert.equal(damnation.level, 92)
  assert.notEqual(vengeance.action, damnation.action)
  assert.notEqual(vengeance.icon, damnation.icon)
  assert.notEqual(catalog.abilities.names.Vengeance, catalog.abilities.names.Damnation)
})

test('Reprisal, Feint and Addle last 10s until the level 98 trait', () => {
  for (const name of ['Reprisal', 'Feint', 'Addle']) {
    const durations = entryFor(name)?.durations
    assert.ok(durations, name)
    assert.deepEqual(durations.map(step => step.level), [...durations.map(step => step.level)].sort((a, b) => a - b))
    assert.equal(durationAtLevel(durations, 80), 10, name)
    assert.equal(durationAtLevel(durations, 90), 10, name)
    assert.equal(durationAtLevel(durations, 97), 10, name)
    assert.equal(durationAtLevel(durations, 98), 15, name)
    assert.equal(durationAtLevel(durations, 100), 15, name)
    assert.equal(durationAtLevel(durations), 15, name)
  }
})

test('non-hotbar rows the sheets name stay anchored to their real game rows', () => {
  // IsPlayerAction=false in the game data. They are still the actions a player
  // learns: Eukrasia grants the three Sage spells, and Seraph grants its veil.
  const expected: Record<string, [number, number]> = {
    'Eukrasian Diagnosis': [24291, 30],
    'Eukrasian Prognosis': [24292, 30],
    'Eukrasian Prognosis II': [37034, 96],
    'Seraphic Veil': [16548, 80],
  }
  for (const [name, [action, level]] of Object.entries(expected)) {
    const entry = byGameName.get(name)
    assert.ok(entry, name)
    assert.equal(entry.action, action, name)
    assert.equal(entry.level, level, name)
    assert.ok(entry.icon && entry.icon !== '000405.png' && entry.icon !== '000784.png', `${name} fell back to a placeholder icon`)
  }
})

// Trait levels from v2.xivapi.com. The level-96 set is every "Upgrades X to Y"
// trait from 96 through 100; the tanks are the level-92 masteries the sheets use.
const replacements: [string, string, number][] = [
  ['Succor', 'Concitation', 96],
  ['Eukrasian Prognosis', 'Eukrasian Prognosis II', 96],
  ['Aspected Helios', 'Helios Conjunction', 96],
  ['Medica II', 'Medica III', 96],
  ['Requiescat', 'Imperator', 96],
  ['Sentinel', 'Guardian', 92],
  ['Vengeance', 'Damnation', 92],
  ['Shadow Wall', 'Shadowed Vigil', 92],
  ['Nebula', 'Great Nebula', 92],
  ['Sheltron', 'Holy Sheltron', 82],
  ['Raw Intuition', 'Bloodwhetting', 82],
  ['Heart of Stone', 'Heart of Corundum', 82],
  ['Physis', 'Physis II', 60],
]

test('retired actions record the trait that replaces them', () => {
  for (const [name, replacement, level] of replacements) {
    assert.deepEqual(entryFor(name)?.replacedBy, { name: replacement, level }, name)
    assert.equal(entryFor(replacement)?.name, replacement)
  }
})

function jobsForSlot(slots: { id: string; job?: string; role?: string; jobs?: string[] }[], slotId: string): Job[] {
  const slot = slots.find(candidate => candidate.id === slotId)
  if (!slot) return []
  if (slot.job) {
    const job = catalog.jobs.find(candidate => candidate.id === slot.job)
    return job ? [job] : []
  }
  return catalog.jobs.filter(job => job.role === slot.role && (!slot.jobs || slot.jobs.includes(job.id)))
}

/** A written name, and whatever a generic slot resolves to at this sync. */
function retiredAt(name: string, sync: number, where: string, jobs: Job[]): string[] {
  const found: string[] = []
  const written = entryFor(name)?.replacedBy
  if (written && written.level <= sync) found.push(`${where}: ${name} → ${written.name} at ${written.level} (sync ${sync})`)
  for (const job of jobs) {
    const resolved = abilityAtLevel(job, baseName(name), sync)
    if (!resolved) continue
    const replacedBy = entryFor(resolved)?.replacedBy
    if (replacedBy && replacedBy.level <= sync) {
      found.push(`${where}: ${job.id} ${name} resolves to ${resolved}, replaced by ${replacedBy.name} at ${replacedBy.level} (sync ${sync})`)
    }
  }
  return found
}

test('no sheet assigns an action that the fight sync level has already replaced', () => {
  const retired: string[] = []
  for (const sheet of catalog.sheets) {
    const sync = catalog.fights.find(fight => fight.id === sheet.fightId)!.syncLevel!
    for (const phase of sheet.phases) for (const mechanic of phase.mechanics) {
      for (const [slotId, actions] of Object.entries(mechanic.assignments)) {
        for (const action of actions) {
          retired.push(...retiredAt(action.name, sync, `${sheet.fightId}/${sheet.id} ${mechanic.id} ${slotId}`, jobsForSlot(sheet.slots, slotId)))
        }
      }
    }
    for (const plan of sheet.tankMits?.plans ?? []) {
      const job = catalog.jobs.find(candidate => candidate.id === plan.job)
      assert.ok(job, plan.job)
      for (const phase of plan.phases) for (const mechanic of phase.mechanics) {
        for (const action of mechanic.actions) retired.push(...retiredAt(action.name, sync, `${sheet.fightId}/${sheet.id} ${plan.job} ${mechanic.id}`, [job]))
        for (const alt of mechanic.alts ?? []) {
          for (const action of alt.actions) retired.push(...retiredAt(action.name, sync, `${sheet.fightId}/${sheet.id} ${plan.job} ${mechanic.id} alt`, [job]))
        }
      }
    }
  }
  assert.deepEqual(retired, [])
})

test('party mits record the level 98 potency step', () => {
  const potencies: [string, number][] = [['Troubadour', 62], ['Tactician', 56], ['Shield Samba', 56]]
  const dsr = catalog.fights.find(fight => fight.id === 'dsr')!.syncLevel
  const dmu = catalog.fights.find(fight => fight.id === 'dmu')!.syncLevel
  assert.equal(dsr, 90)
  assert.equal(dmu, 100)
  for (const [name, learned] of potencies) {
    const steps = entryFor(name)?.potencies
    assert.deepEqual(steps, [{ level: learned, percent: 10 }, { level: 98, percent: 15 }], name)
    assert.equal(potencyAtLevel(steps, catalog.fights.find(fight => fight.id === 'tea')!.syncLevel), 10, name)
    assert.equal(potencyAtLevel(steps, dsr), 10, name)
    assert.equal(potencyAtLevel(steps, dmu), 15, name)
    assert.equal(potencyAtLevel(steps), 15, name)
  }
})
