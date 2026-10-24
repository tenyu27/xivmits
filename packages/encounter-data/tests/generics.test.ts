import assert from 'node:assert/strict'
import test from 'node:test'
import { loadCatalog } from '@xivmits/encounter-data'
import { resolveAction } from '@xivmits/core'

const catalog = loadCatalog()

// jobs.json already maps these per tank. They have to be registry abilities
// too, or a sheet that writes the generic fails validation before the job
// can turn it into a button.
const generics = ['120s Mit', 'Short Mit', 'Invuln', '90s Mit', 'Party Mit', 'Extra', 'Buddy Mit'] as const

test('tank generics are registry abilities and resolve on a real fight', () => {
  const fight = catalog.fights.find(f => f.id === 'dmu')!
  const sheet = catalog.sheets.find(s => s.fightId === fight.id && s.id === 'lpdu')!
  assert.equal(fight.syncLevel, 100)
  assert.ok(sheet.slots.some(slot => slot.role === 'tank'))
  const gnb = catalog.jobs.find(job => job.id === 'GNB')!
  const expected = {
    '120s Mit': 'Great Nebula',
    'Short Mit': 'Heart of Corundum',
    'Invuln': 'Superbolide',
    '90s Mit': 'Camouflage',
    'Party Mit': 'Heart of Light',
    'Buddy Mit': 'Heart of Corundum',
  }
  for (const name of generics) {
    const id = catalog.abilities.names[name]
    assert.equal(catalog.abilities.abilities[id]?.kind, 'generic', name)
  }
  for (const [name, button] of Object.entries(expected)) {
    const resolved = resolveAction(name, gnb, catalog.icons)
    assert.equal(resolved.applies && resolved.label, button, name)
    assert.equal(resolved.applies && resolved.icon, catalog.icons[button], name)
  }
  const healerLb = catalog.abilities.abilities[catalog.abilities.names['Healer LB']]
  assert.equal(healerLb.name, 'Pulse of Life')
  assert.equal(healerLb.action, 208)
  assert.notEqual(catalog.abilities.names['Healer LB'], catalog.abilities.names['Tank LB'])
  assert.equal(catalog.icons['Healer LB'], healerLb.icon)
})
