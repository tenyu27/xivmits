import { Fragment, useId, useRef, useEffect } from 'react'
import type { ReactNode } from 'react'
import { Anchor, Box, Group, Text, UnstyledButton } from '@mantine/core'
import { IconArrowForward, IconExternalLink } from '@tabler/icons-react'
import { resolveAction, type Resolved } from '../data/resolve'
import type { Fight, Job, Sheet, TankMitPlan } from '../data/schema'

type Action = { name: string; note?: string; carryOver?: boolean; buddy?: boolean; noteLink?: string }
type ResolvedActions = { action: Action; resolved: Extract<Resolved, { applies: true }> }[]
type Entry = {
  mechanic: { id: string; name: string; time?: string }
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
// scrolling column with a sticky splitter between each.
export type Layout = 'tabs' | 'list'

export default function MitView({ fight, sheet, roleId, phaseId, onPhase, job, personalPlan, display = 'both', notes = true, compact = false, layout = 'tabs', phaseAction }: {
  fight: Fight; sheet: Sheet; roleId: string; phaseId: string; onPhase: (id: string) => void
  job?: Job; personalPlan?: TankMitPlan; display?: Display; notes?: boolean; compact?: boolean; layout?: Layout; phaseAction?: ReactNode
}) {
  const prefix = useId()
  const tabs = useRef<HTMLElement>(null)
  const sections = useRef(new Map<string, HTMLElement | null>())
  const list = layout === 'list'
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
    const data = sheet.phases.find(p => p.id === id)
    const party: Entry[] = (data?.mechanics ?? []).map(mechanic => ({
      mechanic, actions: resolveActions(mechanic.assignments[roleId] ?? []),
    }))

    const plan = personalPlan?.phases.find(p => p.id === id)
    if (!plan) return { data, entries: party }

    const front: Entry[] = []
    const byAnchor = new Map<string, Entry[]>()
    for (const mechanic of plan.mechanics) {
      // When a personal row names the same mechanic as the party row it sits
      // under, drop the repeated heading - the accent edge already says it is a
      // separate, personal line.
      const anchorName = mechanic.after ? party.find(pe => pe.mechanic.id === mechanic.after)?.mechanic.name : undefined
      const sameName = !mechanic.time && anchorName === mechanic.name
      const entry: Entry = {
        mechanic: sameName ? { ...mechanic, name: '' } : mechanic,
        personal: sameName ? 'bar' : 'plain', note: mechanic.note,
        actions: resolveActions(mechanic.actions),
        alts: mechanic.alts?.map(alt => ({ label: alt.label, actions: resolveActions(alt.actions) })),
      }
      if (!mechanic.after) front.push(entry)
      else byAnchor.set(mechanic.after, [...(byAnchor.get(mechanic.after) ?? []), entry])
    }
    const noteRow: Entry | undefined = plan.note
      ? { mechanic: { id: `${id}-personal-note`, name: '' }, personal: 'bar', note: plan.note, actions: [] }
      : undefined

    const entries: Entry[] = [...front]
    if (noteRow && !plan.noteAfter) entries.unshift(noteRow)
    for (const pe of party) {
      entries.push(pe)
      for (const spliced of byAnchor.get(pe.mechanic.id) ?? []) entries.push(spliced)
      if (noteRow && plan.noteAfter === pe.mechanic.id) entries.push(noteRow)
    }
    return { data: data ?? { id, note: undefined as string | undefined, mechanics: [] }, entries }
  }

  // Keep the active tab in view inside its own horizontal strip. Scroll the
  // strip only - `scrollIntoView` here would also yank the whole page in list
  // mode, where the tab bar is not pinned.
  useEffect(() => {
    const strip = tabs.current
    const active = strip?.querySelector<HTMLElement>('[aria-selected="true"]')
    if (strip && active) strip.scrollTo({ left: active.offsetLeft - strip.clientWidth / 2 + active.clientWidth / 2 })
  }, [phaseId])

  // Entering the single list, land on the phase you were last reading rather
  // than at the top - the tab bar still points there.
  useEffect(() => {
    if (list) sections.current.get(phaseId)?.scrollIntoView()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [list])

  // Icons carry no meaning of their own in `both` mode - the name is beside
  // them. Alone, they are the only label left, so they take the name as alt.
  const iconFor = (file: string | undefined, name: string, carryOver?: boolean) => {
    if (!file) return null
    const label = carryOver ? `${name} (still active)` : name
    return <img
      className={carryOver ? 'action-icon faded' : 'action-icon'}
      src={`${import.meta.env.BASE_URL}icons/${file}`}
      width={iconSize} height={iconSize} loading="lazy" decoding="async"
      alt={display === 'icon' ? label : ''} aria-hidden={display !== 'icon'}
      title={display === 'icon' ? label : undefined}
    />
  }

  const goToPhase = (id: string) => {
    onPhase(id)
    if (list) sections.current.get(id)?.scrollIntoView({ block: 'start' })
  }

  // A mit that is an alternative or a co-tank cover, not a primary press:
  // rendered small and inline with the notes - a label, then shrunk icon + name
  // per entry.
  const miniActions = (list: ResolvedActions, label: string, keyed: string) => list.length > 0 && (
    <Box className="aside" key={keyed}>
      <Text span className="aside-label" fz={compact ? 'xs' : 'sm'} fw={700} c="dimmed">{label}</Text>
      {list.map(({ resolved: { label: name, icon } }, index) => <Text
        span key={`${keyed}-${index}`} className="aside-item" fz={compact ? 'xs' : 'sm'} fw={500} c="dimmed"
      >
        {display !== 'text' && icon && <img
          className="aside-icon" src={`${import.meta.env.BASE_URL}icons/${icon}`}
          width={compact ? 14 : 16} height={compact ? 14 : 16}
          alt={display === 'icon' ? name : ''} aria-hidden={display !== 'icon'}
          title={display === 'icon' ? name : undefined}
        />}
        {(display !== 'icon' || !icon) && name}
      </Text>)}
    </Box>
  )

  const actionList = (all: ResolvedActions, keyed: string, trailingNote?: string) => {
    const actions = all.filter(entry => !entry.action.buddy)
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
    : <Box component="ul" className={display === 'text' ? 'actions actions-flow separated' : 'actions actions-flow'}>
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
      {miniActions(buddies, 'Buddy:', `${keyed}-buddy`)}
    </>
  }

  const mechanics =(data: ReturnType<typeof entriesFor>['data'], entries: ReturnType<typeof entriesFor>['entries']) => {
    if (!data) return <Text ta="center" c="dimmed" py="xl">No mitigation data available for this phase.</Text>
    // A phase-wide aside sits above the mechanic list.
    const note = data.note && <Text c="dimmed" fz={compact ? 'xs' : 'sm'} mb="sm" maw="62ch">{data.note}</Text>
    if (!entries?.length) return note || <Text ta="center" c="dimmed" py="xl">No mechanics listed for this phase.</Text>
    // One row shape for every entry: a party mechanic, a spliced personal
    // mechanic ('plain' - same shape, accent rule), or a personal continuation
    // of the row above ('bar' - no heading, joined to it). `alts` and the
    // mechanic-level `note` only ever come from personal entries.
    return <>{note}<Box component="ol" className="assignments">
      {entries.map(({ mechanic, actions, personal, note: rowNote, alts }) => <Box
        component="li" key={mechanic.id}
        className={`assignment${personal ? ` personal personal-${personal}` : ''}${!personal && !actions.length ? ' unassigned' : ''}`}
      >
        {/* The cast leads the entry - larger than the abilities, a step down in
            contrast and warm where they are cool, so the two never read as the
            same kind of text. A 'bar' personal row would only repeat the name
            of the row above, so it has no heading. */}
        {mechanic.name && <Group className="mechanic-heading" justify="space-between" align="center" gap="sm" wrap="nowrap">
          <Text component="h3" className="mechanic-name" fz={compact ? '0.875rem' : '0.9375rem'} fw={700} lh={1.3}>{mechanic.name}</Text>
          {mechanic.time && <Text className="timestamp" component="span" ff="monospace" fz={compact ? 'xs' : 'sm'} fw={700}>
            {mechanic.time}
          </Text>}
        </Group>}

        {personal
          ? <Box className="personal-body">
            {(actions.length > 0 || (rowNote && showNotes)) && actionList(actions, mechanic.id, rowNote)}
            {alts?.map(alt => miniActions(alt.actions, alt.label, `${mechanic.id}-alt-${alt.label}`))}
          </Box>
          : actions.length > 0 && actionList(actions, mechanic.id)}
      </Box>)}
    </Box></>
  }

  const tab = entriesFor(phase.id)

  return <Box component="section" className={`mit-view${compact ? ' compact' : ''}${list ? ' list' : ''}`}>
    <Group className="phase-bar" gap="sm" wrap="nowrap">
      {compact && <Text fz="sm" fw={700}>{slot?.job ?? slot?.id}</Text>}
      <Box component="nav" ref={tabs} className="phase-tabs" role="tablist" aria-label="Encounter phases">
        {fight.phases.map((p, index) => <UnstyledButton
          key={p.id} type="button" role="tab" id={`${prefix}-${p.id}`}
          aria-controls={list ? `${prefix}-panel-${p.id}` : `${prefix}-panel`} aria-selected={p.id === phase.id}
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
      {phaseAction}
    </Group>

    {list
      ? <Box className="phase-list">
        {fight.phases.map(p => {
          const { data, entries } = entriesFor(p.id)
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
            {mechanics(data, entries)}
          </Box>
        })}
      </Box>
      : <Box id={`${prefix}-panel`} role="tabpanel" aria-labelledby={`${prefix}-${phase.id}`} aria-live="polite" tabIndex={0}>
        {!compact && <Text component="h2" fz="lg" fw={600} lh={1.2} mt="md" mb="xs" style={{ overflowWrap: 'anywhere' }}>
          {phase.name ?? phase.label}
        </Text>}
        {mechanics(tab.data, tab.entries)}
      </Box>}
  </Box>
}
