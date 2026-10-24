import type { Abilities, Encounter, Icons, Job, MitSheet, ResolvedSheet } from '@xivmits/core'
import index from 'virtual:mit-index'
import { loadFight as loadFightChunk } from 'virtual:mit-load'

// What the selection screen, prerender, and SEO need. Mechanics and assignments
// stay in the per-fight chunk so the home page does not download every sheet.
export type FightSummary = Pick<Encounter, 'id' | 'name' | 'shortName' | 'released' | 'type' | 'level'> & {
  phases: Array<Pick<Encounter['phases'][number], 'id' | 'label' | 'name' | 'start'>>
}
export type SheetSummary = Pick<MitSheet, 'id' | 'fightId' | 'name' | 'updated' | 'author' | 'description' | 'source' | 'slots'>
export type MitIndex = {
  fights: FightSummary[]
  sheets: SheetSummary[]
  jobs: Job[]
  icons: Icons
  abilities: Abilities
}
export type FightBundle = { fight: Encounter; sheets: ResolvedSheet[] }

const catalog = index as MitIndex
export default catalog

export function loadFight(id: string): Promise<FightBundle | null> {
  return loadFightChunk(id)
}
