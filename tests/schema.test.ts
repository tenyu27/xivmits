import assert from 'node:assert/strict'
import { readFileSync, readdirSync } from 'node:fs'
import test from 'node:test'
import { validateCatalog } from '../src/data/schema.ts'

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

test('rejects a mechanic scoped to something that is not a role', () => {
  const scoped = structuredClone(encounter)
  scoped.phases[0].mechanics[0] = { ...scoped.phases[0].mechanics[0], roles: ['MT'] }
  assert.throws(() => validateCatalog({
    '/repo/data/fights/test/encounter.json': scoped,
    '/repo/data/fights/test/sheets/plan.json': sheet,
  }, {}, jobs))
})

test('validates the repository catalog and keeps FFLogs placeholders empty', () => {
  const root = new URL('../data/fights/', import.meta.url)
  const dataFiles = readdirSync(root, { recursive: true, encoding: 'utf8' })
    .filter(path => path.endsWith('.json'))
  const catalog = validateCatalog(
    Object.fromEntries(dataFiles.map(path => [`/repo/data/fights/${path}`, JSON.parse(readFileSync(new URL(path, root), 'utf8'))])),
    JSON.parse(readFileSync(new URL('../data/icons.json', import.meta.url), 'utf8')),
    JSON.parse(readFileSync(new URL('../data/jobs.json', import.meta.url), 'utf8')),
  )

  const encounterCount = dataFiles.filter(path => path.endsWith('encounter.json')).length
  const sheetCount = dataFiles.filter(path => path.includes('/sheets/')).length
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
