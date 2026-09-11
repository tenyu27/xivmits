import { Fragment, useId, useRef, useEffect } from 'react'
import type { ReactNode } from 'react'
import { Anchor, Box, Group, Text, UnstyledButton } from '@mantine/core'
import { IconArrowForward, IconExternalLink, IconInfoCircle, IconUser, IconUsers } from '@tabler/icons-react'
import { resolveAction, type Resolved } from '../data/resolve'
import type { Fight, Job, Sheet, TankMitPlan } from '@xivmits/core'

const clockSecs = (t: string) => { const [m, s] = t.split(':').map(Number); return m * 60 + s }
const fmtClock = (secs: number) => `${Math.floor(secs / 60)}:${String(secs % 60).padStart(2, '0')}`
// Pull-clock time for a phase-relative m:ss. Undefined with no phase start, or
// when it starts at 0:00 and the two clocks would match.
const absClock = (start: string | undefined, rel: string) => {
  if (!start || clockSecs(start) === 0) return undefined
  return fmtClock(clockSecs(start) + clockSecs(rel))
}

type Action = { name: string; note?: string; noteJobs?: string[]; carryOver?: boolean; buddy?: boolean; noteLink?: string }
type ResolvedActions = { action: Action; resolved: Extract<Resolved, { applies: true }> }[]

// A buddy press whose only note names the melee it covers ("On M1.") carries
// its target in that note. When every press in a run names the *same* melee,
// that target becomes the run's label instead of a note repeated under it.
// Mixed targets have no single label, so the notes stay where they are.
const BUDDY_TARGET = /^On (M\d)\.$/
const buddyTarget = (list: ResolvedActions): string | undefined => {
  const targets = new Set(list.map(e => e.action.note?.match(BUDDY_TARGET)?.[1]))
  const [only] = targets
  return list.length > 0 && targets.size === 1 && only ? only : undefined
}
type Entry = {
  mechanic: { id: string; name: string; time?: string; tag?: string }
  actions: ResolvedActions
  // 'plain' - a personal row that adds a mechanic the party timeline does not
  // have; renders exactly like a party row. 'bar' - a personal row that repeats
  // the party mechanic above it; heading dropped, marked only by an accent left
  // edge and no divider.
  personal?: 'plain' | 'bar'
  note?: string
  alts?: { label: string; actions: ResolvedActions }[]
}

export type Display = 'both' | 'icon' | 'text'
// `tabs` shows one phase at a time; `list` stacks every phase into one
// scrolling column with a sticky splitter between each; `grid` is the
// one-screen cheatsheet - one condensed row per phase, icons only.
export type Layout = 'tabs' | 'list' | 'grid'

export default function MitView({ fight, sheet, roleId, phaseId, onPhase, job, personalPlan, p3Boss, invulnOrder, display = 'both', notes = true, compact = false, layout = 'tabs', hideTabs = false }: {
  fight: Fight; sheet: Sheet; roleId: string; phaseId: string; onPhase: (id: string) => void
  job?: Job; personalPlan?: TankMitPlan; p3Boss?: 'Chaos' | 'Exdeath'; invulnOrder?: 1 | 2
  display?: Display; notes?: boolean; compact?: boolean; layout?: Layout
  // Drop the phase tab bar entirely - the cheatsheet tab shows every phase at
  // once, so the jump-nav only costs vertical space.
  hideTabs?: boolean
}) {
  const prefix = useId()
  const tabs = useRef<HTMLElement>(null)
  const sections = useRef(new Map<string, HTMLElement | null>())
  const list = layout === 'list'
  const grid = layout === 'grid'
  // Both stacked layouts turn the phase tabs into jump-nav and give every
  // phase its own panel.
  const stacked = list || grid
  const phase = fight.phases.find(p => p.id === phaseId) ?? fight.phases[0]
  const slot = sheet.slots.find(s => s.id === roleId)
  const iconSize = compact ? 26 : 32
  const showNotes = notes && display !== 'icon'

  const resolveActions = (list: readonly Action[]): ResolvedActions => list
    .map(action => ({ action, resolved: resolveAction(action.name, job) }))
    .filter((entry): entry is ResolvedActions[number] => entry.resolved.applies)

  // Every mechanic in the phase, assigned or not. A phase repeats names -
  // "Light of Judgment" twice, "Double-Trouble Trap" three times - so dropping
  // the unassigned ones makes it ambiguous *which* one you are meant to cover.
  // Lines belonging to another job are still dropped; the mechanic stays, blank.
  //
  // When a co-tank is picked, that pairing's personal-mit rows splice into this
  // list right below the party mechanic each one names in `after` (phase top
  // when it names none).
  const entriesFor = (id: string) => {
    const start = fight.phases.find(p => p.id === id)?.start
    const data = sheet.phases.find(p => p.id === id)
    const party: Entry[] = (data?.mechanics ?? [])
      // A role-scoped mechanic (a tank buster) keeps its blank row only for the
      // roles it is about, and a `minor` one - chip damage the encounter records
      // for completeness - keeps none at all. Anyone the sheet actually assigns
      // still sees it: LPDU has the healers mitigating the same busters ikuya
      // leaves to the tanks, so either flag hides an empty row, never an
      // assignment.
      .filter(mechanic => (mechanic.assignments[roleId]?.length ?? 0) > 0
        || (!mechanic.minor
          && (!mechanic.roles || !slot?.role || mechanic.roles.includes(slot.role))))
      .map(mechanic => ({
        mechanic, actions: resolveActions(mechanic.assignments[roleId] ?? []),
        note: mechanic.note,
      }))

    const plan = personalPlan?.phases.find(p => p.id === id)
    if (!plan) return { data, entries: party, start, personalNote: undefined as string | undefined }

    const front: Entry[] = []
    const byAnchor = new Map<string, Entry[]>()
    for (const mechanic of plan.mechanics) {
      // A row tagged with a seat belongs only to that seat's viewer.
      if (mechanic.seat && mechanic.seat !== roleId) continue
      // Branch tags on a job-keyed plan: the row is for one boss / invuln slot
      // only. Untagged rows always show; a tagged row needs the matching choice.
      if (mechanic.boss && mechanic.boss !== p3Boss) continue
      if (mechanic.invuln && mechanic.invuln !== invulnOrder) continue
      // When a personal row names the same mechanic as the party row it sits
      // under, drop the repeated heading - the accent edge already says it is a
      // separate, personal line. "Same" also covers a qualified party variant:
      // a personal "Thunder III" folds into "Thunder III (1st Set)" and an
      // "Ultimate Embrace" into the timeline's "Ultimate Embrace 2", and the
      // party row's own timestamp then stands for both.
      //
      // A personal row carries its anchor's time once the importer puts it on
      // the encounter's clock, so a time of its own no longer argues against
      // the fold - only a time that disagrees with the anchor does, which means
      // the row is about a different moment.
      const anchor = mechanic.after ? party.find(pe => pe.mechanic.id === mechanic.after) : undefined
      const anchorName = anchor?.mechanic.name
      const qualified = anchorName && anchorName.startsWith(`${mechanic.name} `)
        && /^(\(.*\)|\d+)$/.test(anchorName.slice(mechanic.name.length + 1))
      const sameMoment = !mechanic.time || mechanic.time === anchor?.mechanic.time
      const sameName = Boolean(anchorName && sameMoment && (anchorName === mechanic.name || qualified))
      // A bar row drops its heading, so its `tag` has nowhere to sit there; it
      // renders beside the Personal label instead, and may be hoisted onto the
      // party mechanic below. A plain row keeps its tag in its own heading.
      const entry: Entry = {
        mechanic: sameName ? { ...mechanic, name: '' } : mechanic,
        personal: sameName ? 'bar' : 'plain', note: mechanic.note,
        actions: resolveActions(mechanic.actions),
        alts: mechanic.alts?.map(alt => ({ label: alt.label, actions: resolveActions(alt.actions) })),
      }
      if (!mechanic.after) front.push(entry)
      else byAnchor.set(mechanic.after, [...(byAnchor.get(mechanic.after) ?? []), entry])
    }
    // The plan's phase note. Anchored (`noteAfter`) it rides the timeline as an
    // edged personal row; unanchored it reads like any other phase note, at the
    // top, so `personalNote` carries it out to `mechanics()`.
    const showPlanNote = plan.note && (!plan.noteInvuln || plan.noteInvuln === invulnOrder)
    const personalNote = showPlanNote && !plan.noteAfter ? plan.note : undefined
    const noteRow: Entry | undefined = showPlanNote && plan.noteAfter
      ? { mechanic: { id: `${id}-personal-note`, name: '' }, personal: 'bar', note: plan.note, actions: [] }
      : undefined

    // A bar row keeps its own tag, beside the Personal label: the call belongs
    // with the press it describes, and several rows under one mechanic - the
    // Solo line and the Share-3rd-hit line of the same Fell Forces - each need
    // their own. A row is dropped only when it holds nothing at all: no actions,
    // no tag, no note. One that holds only carried-over actions still says
    // something - that cooldown covers this mechanic - and stays.
    const hasBody = (e: Entry) => e.personal !== 'bar' || e.actions.length > 0
      || Boolean(e.mechanic.tag) || Boolean(e.note) || Boolean(e.alts?.length)
    for (const [anchorId, group] of byAnchor) byAnchor.set(anchorId, group.filter(hasBody))

    const entries: Entry[] = [...front]
    for (const pe of party) {
      entries.push(pe)
      for (const spliced of byAnchor.get(pe.mechanic.id) ?? []) entries.push(spliced)
      if (noteRow && plan.noteAfter === pe.mechanic.id) entries.push(noteRow)
    }
    return { data: data ?? { id, note: undefined as string | undefined, mechanics: [] }, entries, start, personalNote }
  }

  // Keep the active tab in view inside its own horizontal strip. Scroll the
  // strip only - `scrollIntoView` here would also yank the whole page in list
  // mode, where the tab bar is not pinned.
  useEffect(() => {
    const strip = tabs.current
    const active = strip?.querySelector<HTMLElement>('[aria-selected="true"]')
    if (strip && active) strip.scrollTo({ left: active.offsetLeft - strip.clientWidth / 2 + active.clientWidth / 2 })
  }, [phaseId])

  // Switching to the single list does not scroll: the page stays where it is
  // and the tab bar still marks which phase you were on. Jumping the viewport
  // on a layout toggle is more disorienting than a manual scroll.

  // Icons carry no meaning of their own in `both` mode - the name is beside
  // them. Alone, they are the only label left, so they take the name as alt.
  const iconFor = (file: string | undefined, name: string, carryOver?: boolean, opts?: { size?: number; labelled?: boolean }) => {
    if (!file) return null
    const label = carryOver ? `${name} (still active)` : name
    const size = opts?.size ?? iconSize
    // Grid cells have no text beside the icon, so it takes the name as alt even
    // in `both` mode - same rule as the icon-only display, just forced per call.
    const named = opts?.labelled || display === 'icon'
    return <img
      className={carryOver ? 'action-icon faded' : 'action-icon'}
      src={`${import.meta.env.BASE_URL}icons/${file}`}
      width={size} height={size} loading="lazy" decoding="async"
      alt={named ? label : ''} aria-hidden={!named}
      title={named ? label : undefined}
    />
  }

  const goToPhase = (id: string) => {
    onPhase(id)
    if (stacked) sections.current.get(id)?.scrollIntoView({ block: 'start' })
  }

  // A mit that is an alternative or a co-tank cover, not a primary press:
  // rendered small and inline with the notes - a label, then shrunk icon + name
  // per entry, joined by "+" (they are pressed together), with any distinct
  // notes folded in after.
  const miniActions = (list: ResolvedActions, label: string, keyed: string) => {
    if (!list.length) return false
    const notes = showNotes
      ? Array.from(new Set(list.map(e => e.action.note).filter((n): n is string => Boolean(n))))
      : []
    return <Box className="aside" key={keyed}>
      <Text span className="aside-label" fz={compact ? 'xs' : 'sm'} fw={700} c="dimmed">{label}</Text>
      {list.map(({ resolved: { label: name, icon } }, index) => <Fragment key={`${keyed}-${index}`}>
        {index > 0 && <Text span className="aside-plus" fz={compact ? 'xs' : 'sm'} c="dimmed" aria-hidden>+</Text>}
        <Text span className="aside-item" fz={compact ? 'xs' : 'sm'} fw={500} c="dimmed">
          {display !== 'text' && icon && <img
            className="aside-icon" src={`${import.meta.env.BASE_URL}icons/${icon}`}
            width={compact ? 14 : 16} height={compact ? 14 : 16}
            alt={display === 'icon' ? name : ''} aria-hidden={display !== 'icon'}
            title={display === 'icon' ? name : undefined}
          />}
          {(display !== 'icon' || !icon) && name}
        </Text>
      </Fragment>)}
      {notes.map((note, index) => <Text
        span key={`${keyed}-note-${index}`} className="aside-note" fz={compact ? 'xs' : 'sm'} fw={400} c="dimmed"
      >{note}</Text>)}
    </Box>
  }

  const actionList = (all: ResolvedActions, keyed: string, trailingNote?: string) => {
    const kept = all.filter(entry => !entry.action.buddy)
    // Press-now first, carry-overs after, whatever order the data had them in -
    // the "Still active" break assumes every carry-over trails the fresh casts.
    const actions = [...kept.filter(e => !e.action.carryOver), ...kept.filter(e => e.action.carryOver)]
    const buddies = all.filter(entry => entry.action.buddy)
    const withNotes = display !== 'icon' && showNotes
      && (Boolean(trailingNote) || actions.some(entry => entry.action.note))
    return <>
      {(actions.length > 0 || withNotes) && (display === 'icon'
    ? <Group component="ul" className="actions actions-icons" gap={6} wrap="wrap">
      {actions.map(({ action, resolved: { label, icon } }, index) => {
        const startsCarryOverRow = action.carryOver && !actions[index - 1]?.action.carryOver
        return <Fragment key={`${keyed}-${action.name}-${index}`}>
          {startsCarryOverRow && <>
            <Box component="li" className="action-break" aria-hidden />
            <Box component="li" className="carry-over-marker" aria-hidden>
              <IconArrowForward size={15} />
            </Box>
          </>}
          <Box component="li" className="action-chip">
            {iconFor(icon, label, action.carryOver)
              ?? <Text span fz={compact ? 'sm' : 'md'} fw={600} c={action.carryOver ? 'dimmed' : undefined}>{label}</Text>}
          </Box>
        </Fragment>
      })}
    </Group>
    : <Box component="ul" className="actions actions-flow">
      {actions.map(({ action, resolved: { label, icon } }, index) => {
        const startsCarryOverRow = action.carryOver && !actions[index - 1]?.action.carryOver
        return <Fragment key={`${keyed}-${action.name}-${index}`}>
          {startsCarryOverRow && <>
            <Box component="li" className="action-break" aria-hidden />
            <Group component="li" className="carry-over-marker" gap={4} align="center">
              <IconArrowForward size={15} aria-hidden />
              <Text span fz="xs" c="dimmed" fw={400}>Still active</Text>
            </Group>
          </>}
          {/* "+" joins abilities pressed together for the same cast. Its own
              flex item, so it wraps with the name that follows and a stranded
              leading "+ Foo" still reads right. Not before the first, and not
              across the carry-over break (the arrow marks that instead). */}
          {index > 0 && !startsCarryOverRow && <Box component="li" className="action-plus" aria-hidden>+</Box>}
          <Box component="li" className="action-item">
            <Group gap="xs" align="center" wrap="nowrap">
              {display === 'both' && iconFor(icon, label, action.carryOver)}
              <Text span className="action-name" fz={compact ? '1rem' : '1.125rem'} fw={action.carryOver ? 500 : 600} c={action.carryOver ? 'dimmed' : undefined} style={{ overflowWrap: 'anywhere' }}>
                {label}
              </Text>
            </Group>
          </Box>
        </Fragment>
      })}
      {showNotes && actions.map(({ action }, index) => {
        const note = action.note
        // A note scoped to certain jobs is dropped for anyone else; with no job
        // chosen it stays, since we cannot yet judge.
        if (action.noteJobs && job && !action.noteJobs.includes(job.id)) return null
        if (!note || actions.some(({ action: other }, otherIndex) =>
          otherIndex !== index && other.noteLink === action.noteLink &&
          (other.note === note ? otherIndex < index : Boolean(other.note?.includes(note))))) return null
        return <Box component="li" className="action-note" key={`note-${keyed}-${action.name}-${index}`}>
          <Text fz="sm" fw={400} c="dimmed" maw="62ch">
            {note}
            {!compact && action.noteLink && <> <Anchor href={action.noteLink} target="_blank" rel="noreferrer" fz="sm" style={{ whiteSpace: 'nowrap' }}>
              Timing example <IconExternalLink size={12} aria-hidden style={{ verticalAlign: 'middle' }} />
            </Anchor></>}
          </Text>
        </Box>
      })}
      {showNotes && trailingNote && <Box component="li" className="action-note" key={`note-${keyed}-trailing`}>
        <Text fz="sm" fw={400} c="dimmed" maw="62ch">{trailingNote}</Text>
      </Box>}
    </Box>)}
      {(() => {
        const target = buddyTarget(buddies)
        return miniActions(
          target ? buddies.map(e => ({ ...e, action: { ...e.action, note: undefined } })) : buddies,
          target ? `${target}:` : 'Buddy:',
          `${keyed}-buddy`,
        )
      })()}
    </>
  }

  const mechanics =(data: ReturnType<typeof entriesFor>['data'], entries: ReturnType<typeof entriesFor>['entries'], phaseStart?: string, personalNote?: string) => {
    if (!data) return <Text ta="center" c="dimmed" py="xl">No mitigation data available for this phase.</Text>
    // A phase-wide aside sits above the mechanic list: the rules the sheet
    // repeats every row (shields, targeted-mit caveats) collected here once,
    // one per line, so a mit's own note carries only what is specific to it.
    const phaseNote = (body: string, key?: string) => <Group key={key} className="phase-note" gap={6} align="flex-start" wrap="nowrap" mb="sm" maw="64ch">
      <IconInfoCircle size={compact ? 14 : 16} className="phase-note-icon" aria-hidden />
      <Text c="dimmed" fz={compact ? 'xs' : 'sm'} style={{ whiteSpace: 'pre-line' }}>{body}</Text>
    </Group>
    const note = data.note && showNotes && phaseNote(data.note)
    // The plan's unanchored phase note - "you start with the boss" - reads like
    // any other phase note, not an edged personal row. Still notes-toggle gated.
    const personal = personalNote && showNotes ? phaseNote(personalNote, 'personal') : null
    // Shown only when this viewer's seat actually presses one of the abilities
    // the note is about (targeted mit), and only with notes on.
    const scoped = data.scopedNote && showNotes
      && (entries ?? []).some(e => e.actions.some(a =>
        data.scopedNote!.abilities.some(ab => a.action.name.includes(ab) || a.resolved.label.includes(ab))))
      ? phaseNote(data.scopedNote.text, 'scoped') : null
    // A phase with no mechanics for this viewer can still carry notes: a
    // phase-wide party aside, or a tank pairing's own phase note.
    if (!entries?.length) return note || personal || scoped
      ? <>{note}{personal}{scoped}</>
      : <Text ta="center" c="dimmed" py="xl">No mechanics listed for this phase.</Text>
    // One row shape for every entry: a party mechanic, a spliced personal
    // mechanic ('plain' - same shape, accent rule), or a personal continuation
    // of the row above ('bar' - no heading, joined to it). A `note` is the
    // mechanic's all-role aside (party) or a personal row's own note; `alts`
    // only ever come from personal entries.
    return <>{note}{personal}{scoped}<Box component="ol" className="assignments">
      {entries.map(({ mechanic, actions, personal, note: rowNote, alts }) => <Box
        component="li" key={mechanic.id}
        className={`assignment${personal ? ` personal personal-${personal}` : ''}${!personal && !actions.length ? ' unassigned' : ''}`}
      >
        {/* The cast leads the entry - larger than the abilities, a step down in
            contrast and warm where they are cool, so the two never read as the
            same kind of text. A 'bar' personal row would only repeat the name
            of the row above, so it has no heading. */}
        {mechanic.name && <Group className="mechanic-heading" justify="space-between" align="center" gap="sm" wrap="nowrap">
          <Group gap={6} align="center" wrap="nowrap" miw={0}>
            <Text component="h3" className="mechanic-name" fz={compact ? '0.875rem' : '0.9375rem'} fw={700} lh={1.3}>{mechanic.name}</Text>
            {mechanic.tag && <Text span className="mechanic-tag" fz={compact ? '0.5rem' : '0.625rem'} fw={700}>{mechanic.tag}</Text>}
          </Group>
          {mechanic.time && <Text className="timestamp" component="span" ff="monospace" fz={compact ? 'xs' : 'sm'} fw={700}>
            {absClock(phaseStart, mechanic.time) ?? mechanic.time}
            {absClock(phaseStart, mechanic.time) && <Text component="span" fz="inherit" c="dimmed" fw={500}>{' '}{mechanic.time}</Text>}
          </Text>}
        </Group>}

        {personal
          ? <Box className="personal-body">
            {/* Names the block as this tank's own cooldowns, so a personal row
                is not just "a party row with a differently coloured rule". */}
            <Group gap={6} align="center" wrap="nowrap">
              <Text span className="personal-tag" fz={compact ? '0.5rem' : '0.625rem'} fw={700}>
                <IconUser size={compact ? 9 : 11} aria-hidden />Personal
              </Text>
              {/* A bar row has no heading to hold its tag - the call that tells
                  it apart from its siblings sits here instead. */}
              {personal === 'bar' && mechanic.tag
                && <Text span className="mechanic-tag" fz={compact ? '0.5rem' : '0.625rem'} fw={700}>{mechanic.tag}</Text>}
            </Group>
            {(actions.length > 0 || (rowNote && showNotes)) && actionList(actions, mechanic.id, rowNote)}
            {alts?.map(alt => miniActions(alt.actions, alt.label, `${mechanic.id}-alt-${alt.label}`))}
          </Box>
          : (actions.length > 0 || (rowNote && showNotes)) && actionList(actions, mechanic.id, rowNote)}
      </Box>)}
    </Box></>
  }

  // The cheatsheet condenses a phase to one row of mechanic cells: name on top,
  // icons below (icons only, always - it is the densest view). Personal tank
  // mit and carry-overs never take their own cell - they sit in the mechanic's
  // cell after a splitter (accent-hued + person glyph for personal, plain for
  // carry-over). A standalone personal mechanic renders the same, just with no
  // party icons before the glyph.
  const cheatIconSize = compact ? 16 : 20
  // One run of actions: press-now first, then - after a splitter and the same
  // forward arrow the other views use - any carry-overs, dimmed.
  const cheatIcons = (all: ResolvedActions, key: string) => {
    const fresh = all.filter(a => !a.action.carryOver)
    const carried = all.filter(a => a.action.carryOver)
    const run = (group: ResolvedActions, tag: string) => group.map((a, index) => <Fragment key={`${key}-${tag}-${index}`}>
      {iconFor(a.resolved.icon, a.resolved.label, a.action.carryOver, { size: cheatIconSize, labelled: true })
        ?? <Text span className="cheat-abils" fz="xs" fw={600}>{a.resolved.label}</Text>}
    </Fragment>)
    return <>
      {fresh.length > 0 && run(fresh, 'now')}
      {carried.length > 0 && <>
        <Box className="cheat-split" aria-hidden />
        <IconArrowForward className="cheat-carry-arrow" size={compact ? 12 : 14} aria-label="still active" />
        {run(carried, 'carry')}
      </>}
    </>
  }
  // One run of icons, buddy-mit presses split off behind their own marker so
  // they never read as an on-self press. `lead` is whatever opens the run (the
  // divider + person glyph for a personal run, nothing for party); it renders
  // for a buddy-only run too, or that run would merge into the one before it.
  const cheatRun = (actions: ResolvedActions, key: string, lead: ReactNode) => {
    const main = actions.filter(a => !a.action.buddy)
    const buddies = actions.filter(a => a.action.buddy)
    if (main.length === 0 && buddies.length === 0) return null
    const buddyLabel = buddyTarget(buddies) ?? 'Buddy'
    return <>
      {lead}
      {main.length > 0 && cheatIcons(main, `${key}-m`)}
      {buddies.length > 0 && <>
        {main.length > 0 && <Box className="cheat-split cheat-split-personal" aria-hidden />}
        <Text span className="cheat-buddy" fz={compact ? '0.5rem' : '0.625rem'} fw={700} aria-label={`buddy mit on ${buddyLabel}`}>
          <IconUsers size={compact ? 9 : 11} aria-hidden />{buddyLabel}
        </Text>
        {cheatIcons(buddies, `${key}-b`)}
      </>}
    </>
  }
  const cheatCell = (entry: Entry, partyActions: ResolvedActions, personalRuns: ResolvedActions[], key: string) => {
    const { mechanic } = entry
    const name = mechanic.name || (entry.personal ? 'Personal' : '')
    const empty = partyActions.length === 0 && personalRuns.length === 0
    return <Box component="li" key={key} className={`cheat-mech${empty ? ' unassigned' : ''}`}>
      <Box className="cheat-head">
        {name && <Text span className="cheat-name" fz="xs" fw={700}>{name}</Text>}
        {mechanic.tag && <Text span className="mechanic-tag cheat-tag" fz="0.5rem" fw={700}>{mechanic.tag}</Text>}
      </Box>
      {/* A mechanic this viewer covers nothing at is just its name - no empty
          icon row, like the unassigned rows in the other layouts. */}
      {!empty && <Box className="cheat-icons">
        {cheatRun(partyActions, `${key}-p`, null)}
        {personalRuns.map((runActions, index) => <Fragment key={`${key}-x-${index}`}>
          {cheatRun(runActions, `${key}-x-${index}`, <>
            <Box className="cheat-split cheat-split-personal" aria-hidden />
            <IconUser className="cheat-personal" size={compact ? 9 : 11} aria-label="personal mit" />
          </>)}
        </Fragment>)}
      </Box>}
    </Box>
  }
  // Personal mit never takes its own cell: a `bar` row folds into the cell
  // before it, a `plain` personal mechanic keeps its name but renders its icons
  // through the same glyph + splitter path (with no party icons ahead of it).
  // A `bar` row with no actions is a personal phase note - nothing to show.
  const cheatCells = (entries: Entry[]) => {
    const cells: { entry: Entry; partyActions: ResolvedActions; personalRuns: ResolvedActions[] }[] = []
    for (const entry of entries) {
      if (entry.personal === 'bar') {
        if (entry.actions.length && cells.length) cells[cells.length - 1].personalRuns.push(entry.actions)
        continue
      }
      if (entry.personal === 'plain') {
        cells.push({ entry, partyActions: [], personalRuns: entry.actions.length ? [entry.actions] : [] })
        continue
      }
      cells.push({ entry, partyActions: entry.actions, personalRuns: [] })
    }
    return cells
  }

  const tab = entriesFor(phase.id)

  return <Box component="section" className={`mit-view${compact ? ' compact' : ''}${list ? ' list' : ''}${grid ? ' grid' : ''}`}>
    {!hideTabs && <Group className="phase-bar" gap="sm" wrap="nowrap">
      {compact && <Text fz="sm" fw={700}>{slot?.job ?? slot?.id}</Text>}
      <Box component="nav" ref={tabs} className="phase-tabs" role="tablist" aria-label="Encounter phases">
        {fight.phases.map((p, index) => <UnstyledButton
          key={p.id} type="button" role="tab" id={`${prefix}-${p.id}`}
          aria-controls={stacked ? `${prefix}-panel-${p.id}` : `${prefix}-panel`} aria-selected={p.id === phase.id}
          aria-current={p.id === phase.id ? 'true' : undefined} tabIndex={p.id === phase.id ? 0 : -1}
          onClick={() => goToPhase(p.id)}
          onKeyDown={event => {
            let next = index
            if (event.key === 'ArrowRight') next = (index + 1) % fight.phases.length
            else if (event.key === 'ArrowLeft') next = (index - 1 + fight.phases.length) % fight.phases.length
            else if (event.key === 'Home') next = 0
            else if (event.key === 'End') next = fight.phases.length - 1
            else return
            event.preventDefault()
            goToPhase(fight.phases[next].id)
            tabs.current?.querySelectorAll<HTMLButtonElement>('button')[next].focus()
          }}
        >{p.label}</UnstyledButton>)}
      </Box>
    </Group>}

    {grid
      ? <Box className="cheatsheet">
        {fight.phases.map(p => {
          const { entries } = entriesFor(p.id)
          const cells = cheatCells(entries)
          return <Box
            key={p.id} component="section" className="cheat-col"
            id={hideTabs ? undefined : `${prefix}-panel-${p.id}`}
            role={hideTabs ? undefined : 'tabpanel'}
            aria-labelledby={hideTabs ? undefined : `${prefix}-${p.id}`}
            aria-label={hideTabs ? (p.name ?? p.label) : undefined}
            ref={el => { sections.current.set(p.id, el) }}
          >
            <Text className="cheat-col-head" fw={700} fz={compact ? 'xs' : 'sm'}>
              {p.label}{p.name && p.name !== p.label && <Text span c="dimmed" fw={500} fz="inherit"> {p.name}</Text>}
            </Text>
            {cells.length === 0
              ? <Text className="cheat-empty" c="dimmed" fz="xs">—</Text>
              : <Box component="ol" className="cheat-col-list">
                {cells.map(({ entry, partyActions, personalRuns }, index) =>
                  cheatCell(entry, partyActions, personalRuns, `${p.id}-${entry.mechanic.id}-${index}`))}
              </Box>}
          </Box>
        })}
      </Box>
      : list
      ? <Box className="phase-list">
        {fight.phases.map(p => {
          const { data, entries, start, personalNote } = entriesFor(p.id)
          return <Box
            key={p.id} component="section"
            id={`${prefix}-panel-${p.id}`} role="tabpanel" aria-labelledby={`${prefix}-${p.id}`}
            ref={el => { sections.current.set(p.id, el) }}
          >
            <Box className="phase-splitter">
              <Text className="phase-splitter-label" fw={700} fz={compact ? 'xs' : 'sm'}>{p.label}</Text>
              {p.name && p.name !== p.label && <Text className="phase-splitter-name" c="dimmed" fz={compact ? 'xs' : 'sm'} style={{ overflowWrap: 'anywhere' }}>
                {p.name}
              </Text>}
            </Box>
            {mechanics(data, entries, start, personalNote)}
          </Box>
        })}
      </Box>
      : <Box id={`${prefix}-panel`} role="tabpanel" aria-labelledby={`${prefix}-${phase.id}`} aria-live="polite" tabIndex={0}>
        {!compact && <Text component="h2" fz="lg" fw={600} lh={1.2} mt="md" mb="xs" style={{ overflowWrap: 'anywhere' }}>
          {phase.name ?? phase.label}
        </Text>}
        {mechanics(tab.data, tab.entries, tab.start, tab.personalNote)}
      </Box>}
  </Box>
}
