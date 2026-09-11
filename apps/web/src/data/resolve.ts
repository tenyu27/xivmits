/** Catalog-bound wrappers over the pure resolvers in @xivmits/core.
 *
 * Core stays runtime-agnostic - it takes the icon map and job list as
 * arguments - so this app binds them once here and the views keep calling
 * `resolveAction(name, job)`. */
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

export const resolveAction = (name: string, job?: Job) => resolveActionWith(name, job, catalog.icons)
export const jobsForRole = (role?: string) => jobsForRoleIn(catalog.jobs, role)
export const jobsForSeat = (
  sheet: { slots: { id: string; job?: string; role?: string; jobs?: string[] }[] },
  position?: Position,
) => jobsForSeatIn(catalog.jobs, sheet, position)
