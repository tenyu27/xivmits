import { z } from 'zod'

const text = z.string().trim().min(1)
const id = text.regex(/^[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)*$/)
const slug = text.regex(/^[a-z0-9]+(?:-[a-z0-9]+)*$/)
const jobId = text.regex(/^[A-Z]{3}$/)
// `start` is when the phase begins on the pull clock (m:ss), so a mechanic's
// phase-relative `time` can also show as an absolute time.
const time = text.regex(/^\d+:[0-5]\d$/)
const encounterMechanicSchema = z.object({
  id, name: text, time: time.optional(),
  fflogs: z.object({ abilityIds: z.array(z.number().int().positive()) }).strict().optional(),
}).strict()
const encounterPhaseSchema = z.object({
  id, label: text, name: text.optional(), start: time.optional(),
  mechanics: z.array(encounterMechanicSchema),
}).strict()
const action = z.object({
  name: text, note: text.optional(), carryOver: z.boolean().optional(),
  // Restrict `note` to these jobs - a caveat that only applies to some of the
  // jobs the generic ability resolves to ("if playing WAR"). The action still
  // renders for everyone; only its note is hidden off-list. Shown when no job
  // is picked, like a job-list name constraint.
  noteJobs: z.array(jobId).optional(),
  // A "cover your co-tank" press (a tank's buddy-mit): rendered small and
  // inline with the notes, not as a full action.
  buddy: z.boolean().optional(),
  noteLink: z.url().refine(value => /^https?:\/\//.test(value)).optional(),
}).strict()
const encounterSchema = z.object({
  id: slug, name: text, shortName: text.optional(),
  type: z.enum(['Savage', 'Ultimate', 'Criterion', 'Other']),
  fflogs: z.object({ encounterIds: z.array(z.number().int().positive()) }).strict().optional(),
  phases: z.array(encounterPhaseSchema).min(1),
}).strict()
const sheetSchema = z.object({
  id: slug, fightId: slug, name: text, updated: z.iso.date(),
  author: text.optional(), description: text.optional(), sourceFile: text.optional(), sourceVersion: text.optional(),
  source: z.object({ name: text, url: z.url().refine(value => /^https?:\/\//.test(value), 'Use an HTTP(S) source URL') }).strict().optional(),
  // `role` says which jobs may stand in this slot, so a generic assignment
  // ("Party Mit") can be resolved to the job the viewer actually plays.
  slots: z.array(z.object({ id, job: text.optional(), role: z.enum(['tank', 'healer', 'melee', 'ranged', 'caster']).optional() }).strict()).min(1),
  phases: z.array(z.object({
    id,
    // A phase-wide aside that is not tied to any one mechanic - "personal mit
    // is free for autos this phase". Renders under the phase heading.
    note: text.optional(),
    // Also under the phase heading, but only for a viewer whose role presses
    // one of `abilities` this phase (targeted mit: Reprisal / Addle / …), and
    // hidden by the notes toggle like an action note.
    scopedNote: z.object({ text, abilities: z.array(text).min(1) }).strict().optional(),
    mechanics: z.array(z.object({
      mechanicId: id,
      // An aside for the whole mechanic, every role - "avoid HP-restoring
      // abilities here". Renders once under the cast, above the abilities,
      // whether or not this viewer presses anything.
      note: text.optional(),
      assignments: z.record(id, z.array(action).min(1)),
    }).strict()),
  }).strict()),
  // Optional tank personal-mit plans. The party grid says what a tank does *for
  // the group*; this says what each tank does for *itself*, and it branches on
  // choices the party grid does not carry - buddy-mit targets, which boss you
  // hold, invuln order. Rows splice into the party timeline right below the
  // party mechanic each one names in `after`.
  //
  // Two ways a plan is keyed. With `with`, it is a co-tank *pairing* (TOP): the
  // whole plan changes with the partner. Without `with`, it is keyed by `job`
  // alone (DMU) and its rows self-select on the viewer's own branch choices via
  // `boss` (which boss in P3) and `invuln` (invuln order in P5) - a sheet whose
  // pairing only ever mattered to fix those two bits.
  tankMits: z.object({
    note: text.optional(),
    // Suggested job order for each side of a branch, straight from the sheet's
    // header. Not applied - the player still picks - but shown in a tooltip by
    // the P3 boss / P5 invuln toggle so they can see where their job sits.
    // Keyed by the toggle value (`Chaos`/`Exdeath`, `1`/`2`).
    priorities: z.object({
      p3Boss: z.record(text, z.array(jobId)).optional(),
      invuln: z.record(text, z.array(jobId)).optional(),
    }).strict().optional(),
    plans: z.array(z.object({
      job: jobId, with: jobId.optional(),
      phases: z.array(z.object({
        id,
        // A phase-wide aside; `noteAfter` is the party mechanic id it renders
        // below (phase top when absent). `noteInvuln` restricts it to one P5
        // invuln order (e.g. "you start with the boss" is only for the 2nd).
        note: text.optional(), noteAfter: id.optional(),
        noteInvuln: z.union([z.literal(1), z.literal(2)]).optional(),
        mechanics: z.array(z.object({
          id, name: text, time: time.optional(),
          // Party mechanic id, same phase, this row renders below. Phase top
          // when absent.
          after: id.optional(),
          // Show this row only for this party seat, hidden for the other. For a
          // plan keyed by job pair whose rows still split by MT/OT (DMU).
          seat: z.enum(['MT', 'OT']).optional(),
          // Branch tags for a job-keyed plan (no `with`): show this row only
          // when the viewer holds this boss in P3 / takes this invuln slot in
          // P5. Untagged rows show for every choice.
          boss: z.enum(['Chaos', 'Exdeath']).optional(),
          invuln: z.union([z.literal(1), z.literal(2)]).optional(),
          // An aside tied to this row (folded in from a phase note).
          note: text.optional(),
          // A short positional call for this row - "Close", "Far", "Solo" -
          // pulled out of the note so it reads as a badge by the mechanic name
          // rather than a sentence fragment at the end.
          tag: text.optional(),
          // May be empty: a marker row that only says the buster happened here.
          actions: z.array(action),
          // "An alternative way to mit this" - e.g. the double-invuln
          // contingency line. Rendered as a labelled sub-row.
          alts: z.array(z.object({ label: text, actions: z.array(action).min(1) }).strict()).optional(),
        }).strict()),
      }).strict()).min(1),
    }).strict()).min(1),
  }).strict().optional(),
}).strict()

// Action name -> icon filename in public/icons. Generated by
// scripts/fetch_icons.py; an action with no entry renders text-only.
const iconsSchema = z.record(text, text.regex(/^\d{6}\.png$/, 'Icon must be a six-digit PNG filename'))

// Jobs, and what a sheet's generic ability names mean for each one.
const jobSchema = z.object({
  id: text.regex(/^[A-Z]{3}$/), name: text, role: z.enum(['tank', 'healer', 'melee', 'ranged', 'caster']),
  abilities: z.record(text, text).optional(),
}).strict()
const jobsSchema = z.object({ jobs: z.array(jobSchema).min(1) }).strict()

export type EncounterMechanic = z.infer<typeof encounterMechanicSchema>
export type EncounterPhase = z.infer<typeof encounterPhaseSchema>
export type Encounter = z.infer<typeof encounterSchema>
export type MitSheet = z.infer<typeof sheetSchema>
export type MitSheetMechanicReference = MitSheet['phases'][number]['mechanics'][number]
export type ResolvedMechanic = EncounterMechanic & Omit<MitSheetMechanicReference, 'mechanicId'>
export type ResolvedSheet = Omit<MitSheet, 'phases'> & {
  phases: Array<Omit<MitSheet['phases'][number], 'mechanics'> & { mechanics: ResolvedMechanic[] }>
}
// Runtime names retained because the UI consumes the resolved view, not the
// persisted formats. They are aliases, not compatibility parsing paths.
export type Fight = Encounter
export type Sheet = ResolvedSheet
export type TankMitPlan = NonNullable<Sheet['tankMits']>['plans'][number]
export type Icons = z.infer<typeof iconsSchema>
export type Job = z.infer<typeof jobSchema>
export type Catalog = { fights: Encounter[]; sheets: ResolvedSheet[]; icons: Icons; jobs: Job[] }

function unique(values: string[], label: string) {
  if (new Set(values).size !== values.length) throw new Error(`Duplicate ${label}`)
}

/** Join normalized source data into the view model consumed by React. */
export function resolveSheet(encounter: Encounter, sheet: MitSheet): ResolvedSheet {
  return {
    ...sheet,
    phases: sheet.phases.map(phase => {
      const encounterPhase = encounter.phases.find(candidate => candidate.id === phase.id)!
      const overlays = new Map(phase.mechanics.map(mechanic => [mechanic.mechanicId, mechanic]))
      return {
        ...phase,
        mechanics: encounterPhase.mechanics.map(mechanic => {
          const overlay = overlays.get(mechanic.id)
          return { ...mechanic, note: overlay?.note, assignments: overlay?.assignments ?? {} }
        }),
      }
    }),
  }
}

export function validateCatalog(files: Record<string, unknown>, rawIcons: unknown = {}, rawJobs: unknown = { jobs: [] }): Catalog {
  const icons = iconsSchema.parse(rawIcons)
  const { jobs } = jobsSchema.parse(rawJobs)
  unique(jobs.map(j => j.id), 'job IDs')
  const fights: Encounter[] = []
  const rawSheets: MitSheet[] = []
  for (const [path, value] of Object.entries(files)) {
    try {
      if (path.endsWith('/encounter.json')) {
        const fight = encounterSchema.parse(value)
        if (!path.endsWith(`/${fight.id}/encounter.json`)) throw new Error('Encounter ID must match its directory')
        unique(fight.phases.map(p => p.id), 'phase IDs')
        unique(fight.phases.flatMap(p => p.mechanics.map(m => m.id)), 'canonical mechanic IDs')
        fights.push(fight)
      } else if (path.includes('/sheets/')) {
        const sheet = sheetSchema.parse(value)
        if (!path.endsWith(`/${sheet.fightId}/sheets/${sheet.id}.json`)) throw new Error('Sheet IDs must match its path')
        unique(sheet.slots.map(s => s.id), 'slot IDs')
        unique(sheet.phases.map(p => p.id), 'sheet phase IDs')
        unique(sheet.phases.flatMap(p => p.mechanics.map(m => m.mechanicId)), 'sheet mechanic references')
        if (sheet.tankMits) {
          unique(sheet.tankMits.plans.map(p => `${p.job}+${p.with ?? ''}`), `tank plans in ${sheet.id}`)
          for (const plan of sheet.tankMits.plans) {
            const label = `${plan.job}+${plan.with ?? ''}`
            if (plan.job === plan.with) throw new Error(`Tank plan pairs ${plan.job} with itself in ${sheet.id}`)
            // Branch tags (`boss`/`invuln`) belong to job-keyed plans; a pairing
            // already fixes those bits, so mixing the two is a data error.
            if (plan.with && plan.phases.some(p => p.mechanics.some(m => m.boss || m.invuln)))
              throw new Error(`Tank plan ${label} in ${sheet.id} has both a co-tank and boss/invuln branch tags`)
            unique(plan.phases.map(p => p.id), `tank plan ${label} phase IDs`)
            unique(plan.phases.flatMap(p => p.mechanics.map(m => m.id)), `tank plan ${label} mechanic IDs`)
          }
        }
        rawSheets.push(sheet)
      } else {
        throw new Error('Expected encounter.json or a JSON file under sheets/')
      }
    } catch (error) { throw new Error(`${path}: ${String(error)}`) }
  }
  if (!fights.length) throw new Error('At least one fight is required')
  unique(fights.map(f => f.id), 'fight IDs')
  unique(rawSheets.map(s => `${s.fightId}/${s.id}`), 'sheet IDs')
  const sheets: ResolvedSheet[] = []
  for (const sheet of rawSheets) {
    const fight = fights.find(f => f.id === sheet.fightId)
    if (!fight) throw new Error(`Unknown fight ${sheet.fightId}`)
    for (const phase of sheet.phases) {
      if (!fight.phases.some(p => p.id === phase.id)) throw new Error(`Unknown phase ${phase.id} in ${sheet.id}`)
      for (const mechanic of phase.mechanics) {
        const canonical = fight.phases.flatMap(candidate => candidate.mechanics).find(candidate => candidate.id === mechanic.mechanicId)
        if (!canonical) throw new Error(`Unknown mechanic ${mechanic.mechanicId} in ${sheet.id}`)
        if (!fight.phases.find(candidate => candidate.id === phase.id)?.mechanics.some(candidate => candidate.id === mechanic.mechanicId))
          throw new Error(`Mechanic ${mechanic.mechanicId} is not in phase ${phase.id} of ${sheet.id}`)
        for (const slot of Object.keys(mechanic.assignments)) {
          if (!sheet.slots.some(s => s.id === slot)) throw new Error(`Unknown slot ${slot} in ${mechanic.mechanicId}`)
        }
      }
    }
    for (const plan of sheet.tankMits?.plans ?? []) {
      for (const phase of plan.phases) {
        if (!fight.phases.some(p => p.id === phase.id)) throw new Error(`Unknown phase ${phase.id} in tank plan ${plan.job}+${plan.with ?? ''} of ${sheet.id}`)
        // `after` / `noteAfter` anchor a personal row to a party mechanic in
        // the same phase, so the splice has somewhere to land.
        const anchors = new Set(sheet.phases.find(p => p.id === phase.id)?.mechanics.map(m => m.mechanicId))
        for (const mechanic of phase.mechanics) {
          if (mechanic.after && !anchors.has(mechanic.after)) throw new Error(`Tank plan ${plan.job}+${plan.with ?? ''} ${mechanic.id}: unknown anchor ${mechanic.after}`)
        }
        if (phase.noteAfter && !anchors.has(phase.noteAfter)) throw new Error(`Tank plan ${plan.job}+${plan.with ?? ''} ${phase.id}: unknown noteAfter ${phase.noteAfter}`)
      }
      plan.phases.sort((a, b) => fight.phases.findIndex(p => p.id === a.id) - fight.phases.findIndex(p => p.id === b.id))
    }
    sheet.phases.sort((a, b) => fight.phases.findIndex(p => p.id === a.id) - fight.phases.findIndex(p => p.id === b.id))
    sheets.push(resolveSheet(fight, sheet))
  }
  return { fights, sheets, icons, jobs }
}
