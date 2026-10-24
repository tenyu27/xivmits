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
  // Oblation is the action's name. An identity mapping stripped the (DRK)
  // qualifier the sheet uses to say whose press it is.
  assert.equal(job('DRK').abilities?.Oblation, undefined)
  const resolved = resolveAction('Oblation (DRK)', job('DRK'), catalog.icons)
  assert.equal(resolved.applies && resolved.label, 'Oblation (DRK)')
  assert.equal(resolved.applies && resolved.icon, catalog.icons['Oblation (DRK)'])
})
