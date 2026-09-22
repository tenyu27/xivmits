import assert from 'node:assert/strict'
import test from 'node:test'
import { validateCatalog } from '@xivmits/core/schema'

const encounter = {
  id: 'test', name: 'Test encounter', type: 'Other',
  released: '2022-04-26',
  fflogs: { encounterIds: [] },
  phases: [{
    id: 'p1', label: 'P1', start: '0:00',
    mechanics: [{
      id: 'p1-raidwide-1', name: 'Raidwide', time: '0:18',
      fflogs: { abilityIds: [] },
    }],
  }],
}

const sheet = {
  id: 'plan', fightId: 'test', name: 'Plan', updated: '2026-09-08',
  slots: [{ id: 'MT', role: 'tank' }],
  phases: [{
    id: 'p1',
    mechanics: [{
      mechanicId: 'p1-raidwide-1',
      assignments: { MT: [{ name: 'Reprisal' }] },
    }],
  }],
}

const files = (sheetValue: unknown = sheet) => ({
  '/repo/data/fights/test/encounter.json': encounter,
  '/repo/data/fights/test/sheets/plan.json': sheetValue,
})
const jobs = { jobs: [{ id: 'GNB', name: 'Gunbreaker', role: 'tank' }] }

test('orders fights by original release date, newest first, independently of file order', () => {
  const newer = { ...encounter, id: 'newer', released: '2024-11-26' }
  const catalog = validateCatalog({
    ...files(), '/repo/data/fights/newer/encounter.json': newer,
  }, {}, jobs)
  assert.deepEqual(catalog.fights.map(f => f.id), ['newer', 'test'])
})

test('requires a valid encounter release date', () => {
  for (const released of [undefined, '2024-02-30', 'yesterday']) {
    assert.throws(() => validateCatalog({
      ...files(), '/repo/data/fights/test/encounter.json': { ...encounter, released },
    }, {}, jobs))
  }
})

test('resolves canonical mechanic data with sheet assignments', () => {
  const catalog = validateCatalog(files(), {}, jobs)
  assert.deepEqual(catalog.sheets[0].phases[0].mechanics[0], {
    id: 'p1-raidwide-1', name: 'Raidwide', time: '0:18',
    fflogs: { abilityIds: [] }, assignments: { MT: [{ name: 'Reprisal' }] },
    note: undefined,
  })
})

test('rejects an action with no ability in the registry', () => {
  // Non-empty, so the check runs, but it has never heard of Reprisal.
  const registry = {
    abilities: { feint: { name: 'Feint', kind: 'action', action: 7549 } },
    names: { Feint: 'feint' },
  }
  assert.throws(() => validateCatalog(files(), {}, jobs, registry), /Reprisal/)
})

test('accepts a catalog whose actions all resolve', () => {
  const sheetActions = new Set<string>()
  for (const phase of sheet.phases) {
    for (const mechanic of phase.mechanics) {
      for (const actions of Object.values(mechanic.assignments)) {
        for (const action of actions) sheetActions.add((action as { name: string }).name)
      }
    }
  }
  const registry = {
    abilities: Object.fromEntries([...sheetActions].map(n => [
      n.toLowerCase().replace(/[^a-z0-9]+/g, '-'), { name: n, kind: 'action' as const }])),
    names: Object.fromEntries([...sheetActions].map(n => [n, n.toLowerCase().replace(/[^a-z0-9]+/g, '-')])),
  }
  const catalog = validateCatalog(files(), {}, jobs, registry)
  assert.equal(Object.keys(catalog.abilities.abilities).length, sheetActions.size)
})

test('rejects a sheet reference missing from its encounter', () => {
  const invalid = structuredClone(sheet)
  invalid.phases[0].mechanics[0].mechanicId = 'p1-missing-1'
  assert.throws(() => validateCatalog(files(invalid), {}, jobs), /Unknown mechanic p1-missing-1/)
})

test('rejects duplicate canonical mechanic IDs', () => {
  const duplicate = structuredClone(encounter)
  duplicate.phases[0].mechanics.push(structuredClone(duplicate.phases[0].mechanics[0]))
  assert.throws(() => validateCatalog({
    '/repo/data/fights/test/encounter.json': duplicate,
    '/repo/data/fights/test/sheets/plan.json': sheet,
  }, {}, jobs), /Duplicate canonical mechanic IDs/)
})

test('carries a role-scoped mechanic through to the resolved sheet', () => {
  const scoped = structuredClone(encounter)
  scoped.phases[0].mechanics[0] = { ...scoped.phases[0].mechanics[0], roles: ['tank'] }
  const catalog = validateCatalog({
    '/repo/data/fights/test/encounter.json': scoped,
    '/repo/data/fights/test/sheets/plan.json': sheet,
  }, {}, jobs)
  assert.deepEqual(catalog.sheets[0].phases[0].mechanics[0].roles, ['tank'])
})

test('carries a minor mechanic through to the resolved sheet', () => {
  const quiet = structuredClone(encounter)
  quiet.phases[0].mechanics[0] = { ...quiet.phases[0].mechanics[0], minor: true }
  const catalog = validateCatalog({
    '/repo/data/fights/test/encounter.json': quiet,
    '/repo/data/fights/test/sheets/plan.json': sheet,
  }, {}, jobs)
  assert.equal(catalog.sheets[0].phases[0].mechanics[0].minor, true)
})

test('rejects a mechanic scoped to something that is not a role', () => {
  const scoped = structuredClone(encounter)
  scoped.phases[0].mechanics[0] = { ...scoped.phases[0].mechanics[0], roles: ['MT'] }
  assert.throws(() => validateCatalog({
    '/repo/data/fights/test/encounter.json': scoped,
    '/repo/data/fights/test/sheets/plan.json': sheet,
  }, {}, jobs))
})

test('accepts a seat restricted to some of its role\'s jobs', () => {
  const restricted = structuredClone(sheet)
  restricted.slots[0] = { ...restricted.slots[0], jobs: ['WAR', 'DRK', 'GNB'] }
  const catalog = validateCatalog(files(restricted), {}, jobs)
  assert.deepEqual(catalog.sheets[0].slots[0].jobs, ['WAR', 'DRK', 'GNB'])
})

test('rejects a seat restriction that is not a job ID', () => {
  const restricted = structuredClone(sheet)
  restricted.slots[0] = { ...restricted.slots[0], jobs: ['Warrior'] }
  assert.throws(() => validateCatalog(files(restricted), {}, jobs))
})


function groupedFiles() {
  const groupEncounter = structuredClone(encounter)
  groupEncounter.phases[0].mechanics.push(
    { id: 'p1-hit-1', name: 'Hit 1', time: '0:25', fflogs: { abilityIds: [1] } },
    { id: 'p1-hit-2', name: 'Hit 2', time: '0:35', fflogs: { abilityIds: [2] } },
    { id: 'p1-buster-1', name: 'Buster', time: '0:45', fflogs: { abilityIds: [3] } },
  )
  const groupSheet = {
    ...structuredClone(sheet),
    phases: [{ id: 'p1', mechanics: [{
      mechanicId: 'p1-hit-1',
      group: { name: 'Sequence', after: 'p1-raidwide-1', before: 'p1-buster-1' },
      assignments: { MT: [{ name: 'Reprisal' }] },
    }] }],
  }
  return {
    '/repo/data/fights/test/encounter.json': groupEncounter,
    '/repo/data/fights/test/sheets/plan.json': groupSheet,
  }
}

test('groups a sequence at its start without mutating logged events or duplicating presses', () => {
  const input = groupedFiles()
  const original = structuredClone(input)
  const catalog = validateCatalog(input, {}, jobs)
  const rows = catalog.sheets[0].phases[0].mechanics
  assert.deepEqual(rows.map(m => [m.name, m.time]), [
    ['Raidwide', '0:18'], ['Sequence', '0:19'], ['Buster', '0:45'],
  ])
  assert.deepEqual(rows[1].coveredMechanicIds, ['p1-hit-1', 'p1-hit-2'])
  assert.deepEqual(rows[1].fflogs?.abilityIds, [1, 2])
  assert.equal(rows.flatMap(m => Object.values(m.assignments).flat()).length, 1)
  assert.deepEqual(input, original)
})

test('rejects missing, reversed, and out-of-window group references', () => {
  for (const [field, value, error] of [
    ['after', 'p1-missing-1', /must have times/],
    ['before', 'p1-missing-1', /must have times/],
    ['after', 'p1-buster-1', /invalid interval/],
    ['after', 'p1-hit-1', /reference must be inside/],
  ] as const) {
    const input = groupedFiles()
    input['/repo/data/fights/test/sheets/plan.json'].phases[0].mechanics[0].group[field] = value
    assert.throws(() => validateCatalog(input, {}, jobs), error)
  }
})

test('rejects overlapping groups and separate overlays they would hide', () => {
  const input = groupedFiles()
  const rows = input['/repo/data/fights/test/sheets/plan.json'].phases[0].mechanics
  rows.push({ ...structuredClone(rows[0]), mechanicId: 'p1-hit-2' })
  assert.throws(() => validateCatalog(input, {}, jobs), /separate overlay.*would be hidden/)

  const overlap = groupedFiles()
  const first = overlap['/repo/data/fights/test/sheets/plan.json'].phases[0].mechanics[0]
  first.group.before = 'p1-hit-2'
  overlap['/repo/data/fights/test/sheets/plan.json'].phases[0].mechanics.push({
    mechanicId: 'p1-hit-2', group: { name: 'Overlapping', after: 'p1-raidwide-1', before: 'p1-buster-1' },
    assignments: { MT: [{ name: 'Reprisal' }] },
  })
  assert.throws(() => validateCatalog(overlap, {}, jobs), /overlapping intervals/)
})

test('rejects grouping that would hide a tank personal anchor or note', () => {
  for (const note of [false, true]) {
    const input = groupedFiles()
    const source = input['/repo/data/fights/test/sheets/plan.json']
    const withTank = { ...source, tankMits: { plans: [{ job: 'GNB', phases: [{
      id: 'p1', ...(note ? { note: 'Tank note', noteAfter: 'p1-hit-2' } : {}),
      mechanics: note ? [] : [{ id: 'personal', name: 'Tank mit', after: 'p1-hit-2', actions: [{ name: 'Rampart' }] }],
    }] }] } }
    assert.throws(() => validateCatalog({ ...input, '/repo/data/fights/test/sheets/plan.json': withTank }, {}, jobs), /tank anchor.*would be hidden/)
  }
})
