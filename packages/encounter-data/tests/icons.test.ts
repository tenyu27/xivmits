import assert from 'node:assert/strict'
import test from 'node:test'
import { loadCatalog } from '@xivmits/encounter-data'

const catalog = loadCatalog()

test('icons.json matches the registry icon for every wording', () => {
  for (const [wording, id] of Object.entries(catalog.abilities.names)) {
    const ability = catalog.abilities.abilities[id]
    if (!ability.icon) {
      assert.equal(catalog.icons[wording], undefined, wording)
      continue
    }
    assert.equal(catalog.icons[wording], ability.icon, wording)
  }
  for (const wording of Object.keys(catalog.icons)) {
    assert.ok(catalog.abilities.names[wording], wording)
  }
})
