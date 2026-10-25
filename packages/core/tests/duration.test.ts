import assert from 'node:assert/strict'
import test from 'node:test'
import { durationAtLevel, potencyAtLevel } from '@xivmits/core'

const reprisal = [{ level: 22, seconds: 10 }, { level: 98, seconds: 15 }]
const troubadour = [{ level: 62, percent: 10 }, { level: 98, percent: 15 }]

test('duration and potency use the highest step the sync has reached', () => {
  assert.equal(durationAtLevel(reprisal, 90), 10)
  assert.equal(durationAtLevel(reprisal, 98), 15)
  assert.equal(durationAtLevel(reprisal, 100), 15)
  assert.equal(durationAtLevel(reprisal, 21), undefined)
  assert.equal(durationAtLevel(reprisal), 15)
  assert.equal(durationAtLevel(undefined, 100), undefined)
  assert.equal(potencyAtLevel(troubadour, 90), 10)
  assert.equal(potencyAtLevel(troubadour, 100), 15)
  assert.equal(potencyAtLevel(troubadour), 15)
  assert.equal(potencyAtLevel(undefined, 100), undefined)
})
