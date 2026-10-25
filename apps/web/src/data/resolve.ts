/** Catalog-bound wrappers over the pure resolvers in @xivmits/core.
 *
 * Core stays runtime-agnostic - it takes the icon map and job list as
 * arguments - so this app binds them once here and the views keep calling
 * `resolveAction(name, job, syncLevel)`. `syncLevel` is the fight's synced
 * level, so a generic slot can resolve to the button that level has learned. */
import catalog from './catalog'
import {
  resolveAction as resolveActionWith,
  jobsForRole as jobsForRoleIn,
  jobsForSeat as jobsForSeatIn,
  type Job,
  type Position,
} from '@xivmits/core'

export { positionsForSheet, slotIdFor, isKnownPosition } from '@xivmits/core'
export type { Resolved, Position } from '@xivmits/core'

export const resolveAction = (name: string, job?: Job, syncLevel?: number) =>
  resolveActionWith(name, job, catalog.icons, syncLevel)

/** A trailing "(PLD/WAR)" is a job list. Timing qualifiers such as "(7-8th Set)" are not. */
const JOB_LIST = /\(([A-Z]{3}(?:\/[A-Z]{3})*)\)\s*$/

type KitSheet = {
  phases: { mechanics: { assignments: Record<string, { name: string }[] | undefined> }[] }[]
}

/** True when every melee standing in this seat presses the same buttons.
 *  A job-qualified line (Mantra (MNK)) means the seat has to know the job,
 *  or that line cannot be dropped for everyone else. An unloaded sheet
 *  still shares a kit, so the picker does not demand a job before the data arrives. */
export function meleeSharesKit(sheet: KitSheet | undefined, slotId?: string) {
  if (!sheet || !slotId) return true
  return !sheet.phases.some(phase => phase.mechanics.some(mechanic =>
    (mechanic.assignments[slotId] ?? []).some(action => JOB_LIST.test(action.name))))
}

/** The melee job picker stays disabled only while the seat shares one kit. */
export function meleeJobFree(role: string | undefined, sheet: KitSheet | undefined, slotId?: string) {
  return role === 'melee' && meleeSharesKit(sheet, slotId)
}
export const jobsForRole = (role?: string) => jobsForRoleIn(catalog.jobs, role)
export const jobsForSeat = (
  sheet: { slots: { id: string; job?: string; role?: string; jobs?: string[] }[] },
  position?: Position,
) => jobsForSeatIn(catalog.jobs, sheet, position)
