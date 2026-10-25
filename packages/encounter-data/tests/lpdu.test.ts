import assert from 'node:assert/strict'
import test from 'node:test'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { loadCatalog } from '@xivmits/encounter-data'
import type { MitSheet } from '@xivmits/core'

const sheetPath = fileURLToPath(new URL('../fights/dmu/sheets/lpdu.json', import.meta.url))
const raw = JSON.parse(readFileSync(sheetPath, 'utf8')) as MitSheet
const catalog = loadCatalog()
const resolved = catalog.sheets.find(s => s.fightId === 'dmu' && s.id === 'lpdu')!

test('LPDU P3 keeps the compile row order and the viewer follows the encounter clock', () => {
  // Two boss tracks share the grid. The compile writes Exdeath's Thunder III
  // and Stack/Roles rows above the beam rows the clock places earlier:
  // Thunder III (5th Set) is 3:29 and Black Holes 2nd Set is 3:19; Stack/Roles
  // 3 is 4:09 and Black Holes 3rd Set is 3:43. The sheet JSON keeps that row
  // order. resolveSheet displays the encounter's timed order.
  const source = raw.phases.find(p => p.id === 'p3')!.mechanics.map(m => m.mechanicId)
  assert.ok(source.indexOf('p3-thunder-iii-5') < source.indexOf('p3-black-hole-5'))
  assert.ok(source.indexOf('p3-shocking-impact-3') < source.indexOf('p3-black-hole-6'))

  const viewed = resolved.phases.find(p => p.id === 'p3')!.mechanics.map(m => m.id)
  assert.ok(viewed.indexOf('p3-black-hole-5') < viewed.indexOf('p3-thunder-iii-5'))
  assert.ok(viewed.indexOf('p3-black-hole-6') < viewed.indexOf('p3-shocking-impact-3'))
})

test('LPDU ranged party mit and Scholar shields use the level-100 names', () => {
  const names = raw.phases.flatMap(phase => phase.mechanics.flatMap(mechanic =>
    Object.entries(mechanic.assignments).flatMap(([slot, actions]) =>
      actions.map(action => `${slot}:${action.name}`))))
  assert.equal(names.filter(name => name === 'P:90s Mit').length, 0)
  assert.ok(names.includes('P:Party Mit'))
  assert.equal(names.filter(name => name.endsWith(':Succor')).length, 0)
  assert.ok(names.some(name => name.endsWith(':Concitation')))
})

test('LPDU arcana use the level-30 action rows', () => {
  // The Balance, Arrow, Spear and Spire still exist (37023-37026) and no sheet
  // names them. The Bole and the Ewer are actions 37027 and 37028. Other
  // actions can start with "The " (TEA's The Blackest Night); this is the arcana.
  const names = new Set(catalog.sheets.flatMap(sheet => sheet.phases.flatMap(phase =>
    phase.mechanics.flatMap(mechanic => Object.values(mechanic.assignments).flatMap(actions =>
      actions.map(action => action.name))))))
  const arcana = [...names].filter(name => /^(The )?(Balance|Bole|Arrow|Spear|Ewer|Spire)$/.test(name)).sort()
  assert.deepEqual(arcana, ['The Bole', 'The Ewer'])
  for (const [name, action] of [['The Bole', 37027], ['The Ewer', 37028]] as const) {
    const ability = catalog.abilities.abilities[catalog.abilities.names[name]]
    assert.equal(ability.kind, 'action', name)
    assert.equal(ability.action, action, name)
    assert.equal(catalog.icons[name], ability.icon, name)
  }
})
