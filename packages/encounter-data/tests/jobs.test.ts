import assert from 'node:assert/strict'
import test from 'node:test'
import { loadCatalog } from '@xivmits/encounter-data'
import { resolveAction } from '@xivmits/core'

const catalog = loadCatalog()
const job = (id: string) => catalog.jobs.find(candidate => candidate.id === id)!

test('job mappings stay limited to generics a sheet can actually assign', () => {
  for (const id of ['WHM', 'SCH', 'AST', 'SGE']) {
    assert.equal(job(id).abilities?.['Party Mit'], undefined, id)
  }
  // No caster seat is assigned Party Mit. RDM's party mit is Magick Barrier,
  // the same button Extra (RDM) already names. PCT's Tempera Grassa was only
  // reachable through an unused Party Mit mapping.
  assert.equal(job('RDM').abilities?.['Party Mit'], 'Magick Barrier')
  assert.equal(job('RDM').abilities?.Extra, 'Magick Barrier')
  assert.equal(job('PCT').abilities?.['Party Mit'], undefined)
  assert.equal(catalog.abilities.names['Tempera Grassa'], undefined)
  // "Oblation (DRK)" is the sheet's way of saying the DRK presses Oblation.
  // The mapping strips the qualifier so the row reads the button name.
  assert.equal(job('DRK').abilities?.Oblation, 'Oblation')
  const rows: [string, string, string][] = [
    ['dsr', 'dsrmitty', 'rewind-brightwing-2'],
    ['fru', 'fmbg', 'p2-banish-iii-1'],
  ]
  for (const [fightId, sheetId, mechanicId] of rows) {
    const fight = catalog.fights.find(candidate => candidate.id === fightId)!
    const sheet = catalog.sheets.find(candidate => candidate.fightId === fightId && candidate.id === sheetId)!
    const mechanic = sheet.phases.flatMap(phase => phase.mechanics).find(candidate => candidate.id === mechanicId)!
    const names = Object.values(mechanic.assignments).flat().map(action => action.name).filter(name => name.includes('Oblation'))
    assert.ok(names.length > 0, mechanicId)
    for (const name of names) {
      const resolved = resolveAction(name, job('DRK'), catalog.icons, fight.syncLevel)
      assert.equal(resolved.applies && resolved.label, 'Oblation', `${fightId} ${mechanicId} ${name}`)
      assert.equal(resolved.applies && resolved.icon, catalog.icons.Oblation, name)
    }
  }
})
