import type { Abilities, Encounter, Icons, Job, MitSheet, ResolvedSheet } from '@xivmits/core'
import index from 'virtual:mit-index'
import { loadFight as loadFightChunk } from 'virtual:mit-load'

// What the selection screen, prerender, and SEO need. Mechanics and assignments
// stay in the per-fight chunk so the home page does not download every sheet.
export type FightSummary = Pick<Encounter, 'id' | 'name' | 'shortName' | 'released' | 'type' | 'syncLevel'> & {
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

/** The fight chunk, or null when the load rejects, the id is unknown, or the
 *  chunk is for a different fight. Callers render that null as an error. */
export async function readFight(
  id: string,
  load: (id: string) => Promise<FightBundle | null> = loadFight,
): Promise<FightBundle | null> {
  try {
    const bundle = await load(id)
    return bundle?.fight.id === id ? bundle : null
  } catch {
    return null
  }
}
