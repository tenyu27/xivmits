import catalog from './catalog'
import type { Job } from './schema'

/** A trailing "(...)" on an action name is either a job list saying who presses
 *  it - "Party Mit (GNB/DRK)" - or timing - "Sun Sign (7-8th Set)". */
const QUALIFIER = /\s*\(([^)]*)\)\s*$/
const JOB_LIST = /^[A-Z]{3}(\/[A-Z]{3})*$/

/** `applies: false` means this line belongs to a different job and should not
 *  be rendered at all - see resolveAction. */
export type Resolved =
  | { applies: true; label: string; icon?: string; from?: string }
  | { applies: false }

/**
 * Turn a sheet's action name into what this player actually presses.
 *
 * Sheets write generic names because a plan is written once for whoever stands
 * in the slot: "Party Mit" is Heart of Light for a GNB and Shake It Off for a
 * WAR. Knowing the job turns that into a real ability - and therefore an icon.
 */
export function resolveAction(name: string, job?: Job): Resolved {
  const qualifier = name.match(QUALIFIER)?.[1]
  const base = name.replace(QUALIFIER, '').trim()

  // A job list is a constraint, not a hint. "Party Mit (GNB/DRK)" is an
  // instruction to whoever is the GNB or DRK - so for anyone else it is not an
  // assignment at all, and the view shows only what *you* press (PRD section 5).
  // With no job chosen we cannot judge, so the line stays.
  if (qualifier && JOB_LIST.test(qualifier) && job && !qualifier.split('/').includes(job.id)) {
    return { applies: false }
  }

  const ability = job?.abilities?.[base]
  if (ability) {
    // A timing qualifier still applies to the resolved ability, so keep it.
    const label = qualifier && !JOB_LIST.test(qualifier) ? `${ability} (${qualifier})` : ability
    return { applies: true, label, icon: catalog.icons[ability], from: base }
  }

  return { applies: true, label: name, icon: catalog.icons[name] ?? catalog.icons[base] }
}

/** A seat in the party: MT, H2, D3. Distinct from the job standing in it. */
export type Position = { id: string; role: string; slotId?: string }

// A full party, so a sheet that assigns by job still offers real seats.
const SEATS: Record<string, string[]> = {
  tank: ['MT', 'OT'], healer: ['H1', 'H2'], dps: ['D1', 'D2', 'D3', 'D4'],
}
const ROLES = ['tank', 'healer', 'dps']

/**
 * The seats a sheet offers.
 *
 * Sheets divide the party two ways. Most name positions - `MT`, `D3` - and the
 * job is the viewer's to pick. Some name jobs instead, because that role's plan
 * genuinely differs per job (every healer kit mitigates differently). For those
 * the seat is just a label and the *job* selects which column to read, so we
 * offer standard seats and resolve the column from the job.
 */
export function positionsForSheet(sheet: { slots: { id: string; job?: string; role?: string }[] }): Position[] {
  const positions: Position[] = []
  for (const role of ROLES) {
    const slots = sheet.slots.filter(s => s.role === role)
    if (!slots.length) continue
    if (slots.every(s => s.job)) positions.push(...(SEATS[role] ?? []).map(id => ({ id, role })))
    else positions.push(...slots.map(s => ({ id: s.id, role, slotId: s.id })))
  }
  // A sheet that declares no roles keeps its slots exactly as written.
  positions.push(...sheet.slots.filter(s => !s.role).map(s => ({ id: s.id, role: '', slotId: s.id })))
  return positions
}

/** The data column to read for a seat + job. Empty when the job is still unset
 *  on a job-keyed role - there is genuinely no column to show yet. */
export function slotIdFor(sheet: { slots: { id: string; job?: string; role?: string }[] }, position?: Position, jobId?: string) {
  if (!position) return ''
  if (position.slotId) return position.slotId
  return sheet.slots.find(s => s.role === position.role && s.job === jobId)?.id ?? ''
}

export const jobsForRole = (role?: string) =>
  role ? catalog.jobs.filter(j => j.role === role) : catalog.jobs

export const isKnownPosition = (sheet: { slots: { id: string; job?: string; role?: string }[] }, id: string) =>
  positionsForSheet(sheet).some(p => p.id === id)
