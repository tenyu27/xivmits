import assert from 'node:assert/strict'
import test from 'node:test'
import { validateCatalog } from '@xivmits/core/schema'

const encounter = {
  id: 'test', name: 'Test encounter', type: 'Other',
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

test('resolves canonical mechanic data with sheet assignments', () => {
  const catalog = validateCatalog(files(), {}, jobs)
  assert.deepEqual(catalog.sheets[0].phases[0].mechanics[0], {
    id: 'p1-raidwide-1', name: 'Raidwide', time: '0:18',
    fflogs: { abilityIds: [] }, assignments: { MT: [{ name: 'Reprisal' }] },
    note: undefined,
  })
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
