import assert from 'node:assert/strict'
import { mkdtempSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { after, before, test } from 'node:test'
import { createElement as h } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { MantineProvider } from '@mantine/core'
import { createServer } from 'vite'
import { resolveAction } from '@xivmits/core'
import { loadCatalog } from '@xivmits/encounter-data'

const catalog = loadCatalog()
const fight = catalog.fights.find(candidate => candidate.id === 'tea')
const sheet = catalog.sheets.find(candidate => candidate.fightId === 'tea')
const job = id => catalog.jobs.find(candidate => candidate.id === id)

let server, MitView, meleeSharesKit, meleeJobFree, cacheDir
before(async () => {
  cacheDir = mkdtempSync(join(tmpdir(), 'xivmits-tea-view-'))
  server = await createServer({ cacheDir, server: { middlewareMode: true, hmr: false, ws: false }, appType: 'custom' })
  MitView = (await server.ssrLoadModule('/src/components/MitView.tsx')).default
  const resolve = await server.ssrLoadModule('/src/data/resolve.ts')
  meleeSharesKit = resolve.meleeSharesKit
  meleeJobFree = resolve.meleeJobFree
})
after(async () => {
  try { await server?.close() } finally {
    if (cacheDir) rmSync(cacheDir, { recursive: true, force: true })
  }
})

const SLOT_JOBS = {
  MT: ['PLD', 'WAR', 'DRK', 'GNB'],
  OT: ['PLD', 'WAR', 'DRK', 'GNB'],
  SCH: ['SCH'], SGE: ['SGE'], WHM: ['WHM'], AST: ['AST'],
  M1: ['MNK', 'DRG', 'NIN', 'SAM', 'RPR', 'VPR'],
  M2: ['MNK', 'DRG', 'NIN', 'SAM', 'RPR', 'VPR'],
  P: ['BRD', 'MCH', 'DNC'],
  C: ['BLM', 'SMN', 'RDM', 'PCT'],
}
const PHASES = ['p1', 'lc', 'p2', 'p3', 'p4']
const POST80 = ['Holy Sheltron', 'Bloodwhetting', 'Heart of Corundum', 'Oblation', 'Aquaveil', 'Liturgy of the Bell', 'Exaltation', 'Expedient', 'Magick Barrier', 'Macrocosmos', 'Concitation', 'Medica III', 'Helios Conjunction', 'Eukrasian Prognosis II', 'Krasis', 'Pneuma', 'Protraction', 'Divine Caress']

const decode = value => value
  .replaceAll('&amp;', '&').replaceAll('&lt;', '<').replaceAll('&gt;', '>')
  .replaceAll('&quot;', '"').replaceAll('&#x27;', "'").replaceAll('&apos;', "'")

function render(slot, player, options) {
  return renderToStaticMarkup(h(MantineProvider, {}, h(MitView, {
    fight, sheet, roleId: slot, onPhase: () => {}, job: player, phaseId: 'p1', ...options,
  })))
}

function expectedRows(slot, player, phaseId) {
  const rows = []
  for (const phase of sheet.phases) {
    if (phaseId && phase.id !== phaseId) continue
    for (const mechanic of phase.mechanics) {
      const assigned = (mechanic.assignments[slot]?.length ?? 0) > 0
      const roleOk = !mechanic.roles || mechanic.roles.includes(player.role)
      if (!assigned && (mechanic.minor || !roleOk)) continue
      const actions = (mechanic.assignments[slot] ?? [])
        .map(action => ({ action, resolved: resolveAction(action.name, player, catalog.icons, fight.syncLevel) }))
        .filter(item => item.resolved.applies)
      const notes = []
      for (const item of actions) {
        if (item.action.note && !notes.includes(item.action.note)) notes.push(item.action.note)
      }
      if (mechanic.note && (!mechanic.noteRoles || mechanic.noteRoles.includes(player.role) || mechanic.noteRoles.includes(player.id)))
        notes.push(mechanic.note)
      rows.push({
        id: mechanic.id,
        time: mechanic.time,
        actions: actions.map(item => item.resolved.label),
        notes,
      })
    }
  }
  return rows
}

function rowsFrom(html) {
  return html.split(/<li\b[^>]*\bassignment\b/).slice(1).map(chunk => {
    const time = chunk.match(/\btimestamp\b[^>]*>([^<]+)/)?.[1]?.trim()
    const actions = [...chunk.matchAll(/\baction-name\b[^>]*>([^<]*)/g)].map(match => decode(match[1].trim()))
    const notes = [...chunk.matchAll(/\baction-note\b[\s\S]*?<\/li>/g)]
      .map(match => decode(match[0].replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim()))
    return { time, actions, notes }
  })
}

function assertRows(html, slot, player, phaseId) {
  const got = rowsFrom(html)
  const want = expectedRows(slot, player, phaseId)
  const where = `${player.id} ${slot} ${phaseId ?? 'all'}`
  assert.equal(got.length, want.length, `${where}: ${got.length} rows, expected ${want.length}`)
  for (let index = 0; index < want.length; index++) {
    assert.deepEqual(got[index].actions, want[index].actions, `${where} ${want[index].id}`)
    assert.equal(got[index].time, want[index].time, `${where} ${want[index].id}`)
    for (const note of want[index].notes)
      assert.ok(got[index].notes.some(text => text.includes(note)), `${where} ${want[index].id} missing ${note}`)
  }
  const durations = [...html.matchAll(/\baction-duration\b[^>]*>([^<]+)/g)].map(match => match[1])
  assert.ok(durations.every(value => value === '10s'), `${where} durations ${durations.join(',')}`)
  for (const retired of POST80) assert.equal(html.includes(retired), false, `${where} ${retired}`)
  assert.equal(/\baction-name\b[^>]*>Physis</.test(html), false, where)
}

function cheatLabels(html) {
  const labels = []
  for (const match of html.matchAll(/\balt="([^"]*)"|\bcheat-abils\b[^>]*>([^<]*)/g)) {
    const label = decode((match[1] ?? match[2]).trim())
    if (label) labels.push(label)
  }
  return labels
}

test('only TEA melee seats qualify a press by job', () => {
  for (const candidate of catalog.sheets) for (const slot of candidate.slots.filter(item => item.role === 'melee')) {
    const shares = meleeSharesKit(candidate, slot.id)
    assert.equal(shares, candidate.fightId !== 'tea', `${candidate.fightId}/${slot.id}`)
    assert.equal(meleeJobFree('melee', candidate, slot.id), shares)
  }
  assert.equal(meleeJobFree('melee', undefined, 'M1'), true)
  assert.equal(meleeJobFree('tank', sheet, 'MT'), false)
  assert.equal(meleeSharesKit(sheet, 'M1'), false)
  assert.equal(meleeSharesKit(sheet, 'M2'), false)
})

test('every TEA job matches the sheet in By phase, All phases, the cheatsheet, and the pop-out', () => {
  for (const [slot, ids] of Object.entries(SLOT_JOBS)) for (const id of ids) {
    const player = job(id)
    const list = render(slot, player, { layout: 'list' })
    assertRows(list, slot, player)
    for (const phaseId of PHASES) {
      const tabs = render(slot, player, { layout: 'tabs', phaseId })
      assertRows(tabs, slot, player, phaseId)
      assert.match(tabs, new RegExp(`>${fight.phases.find(phase => phase.id === phaseId).label}<`))
    }
    const popout = render(slot, player, { layout: 'tabs', phaseId: 'p4', compact: true })
    assertRows(popout, slot, player, 'p4')
    assert.match(popout, /\bcompact\b/)

    const grid = render(slot, player, { layout: 'grid', display: 'icon', notes: false, hideTabs: true })
    const want = expectedRows(slot, player).flatMap(row => row.actions)
    assert.deepEqual(cheatLabels(grid), want, `${id} ${slot} cheatsheet`)
    assert.equal(grid.includes('action-note'), false, `${id} cheatsheet notes`)
    assert.equal(grid.includes('action-duration'), false, `${id} cheatsheet duration`)
    assert.equal(grid.includes('Press it when Enumeration'), false, id)
    assert.equal(grid.includes('8 seconds before'), false, id)
    for (const retired of POST80) assert.equal(grid.includes(retired), false, `${id} ${retired}`)
  }
})

test('TEA phase notes stay with the role they address', () => {
  const tank = render('MT', job('PLD'), { layout: 'list' })
  const healer = render('SCH', job('SCH'), { layout: 'list' })
  assert.equal(tank.includes('water debuff'), false)
  assert.ok(healer.includes('water debuff'))
  assert.ok(tank.includes('If a Warrior is in the party'))
  assert.equal(healer.includes('If a Warrior is in the party'), false)
  assert.equal(tank.includes('Press Holos'), false)
  assert.ok(healer.includes('Press Holos'))
  assert.ok(tank.includes('Shade Shift'))
  assert.ok(healer.includes('Shade Shift'))
})

test('Doll Feeds party mit and Mantra resolve to the job the sheet names', () => {
  const mch = rowsFrom(render('P', job('MCH'), { layout: 'tabs', phaseId: 'p1' }))
  const dolls = expectedRows('P', job('MCH'), 'p1').findIndex(row => row.id === 'p1-jagd-dolls-1')
  assert.deepEqual(mch[dolls].actions, ['Tactician'])
  assert.ok(mch[dolls].notes.some(note => note.includes('Optional.')))
  const brd = rowsFrom(render('P', job('BRD'), { layout: 'tabs', phaseId: 'p1' }))
  assert.deepEqual(brd[dolls].actions, ["Nature's Minne (BRD)"])
  const dnc = rowsFrom(render('P', job('DNC'), { layout: 'tabs', phaseId: 'p1' }))
  assert.deepEqual(dnc[dolls].actions, [])
  for (const id of ['MNK', 'DRG', 'NIN', 'SAM', 'RPR', 'VPR']) {
    const html = render('M1', job(id), { layout: 'list' })
    assert.equal(html.includes('Mantra'), id === 'MNK', id)
    assert.ok(html.includes('Feint'), id)
  }
})
