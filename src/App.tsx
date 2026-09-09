import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import {
  Alert, Anchor, Box, Button, Container, Group, MantineProvider, NativeSelect,
  Input, SegmentedControl, Stack, Switch, Text, Title, Tooltip, localStorageColorSchemeManager,
  useComputedColorScheme, useMantineColorScheme,
} from '@mantine/core'
import {
  IconAlertCircle, IconArrowRight, IconBrandX, IconCoffee, IconDeviceDesktop, IconExternalLink,
  IconInfoCircle, IconLayoutGrid, IconMoon, IconPictureInPicture, IconSun,
} from '@tabler/icons-react'
import catalog from './data/catalog'
import { jobsForRole, jobsForSeat, positionsForSheet, slotIdFor } from './data/resolve'
import MitView, { type Display, type Layout } from './components/MitView'
import { theme } from './theme'
import { initialSelection, readMap, readStored, sheetKey, sheetPath, storeMap, storeValue } from './state'
import { usePip } from './usePip'
import './App.css'

// Icon-only, so each option carries its own accessible name - a sun glyph alone
// does not say "light theme" to a screen reader, and `title` gives sighted
// users the same word on hover.
const themeOption = (value: string, name: string, Icon: typeof IconSun) => ({
  value,
  label: <span role="img" aria-label={name} title={name} style={{ display: 'flex' }}>
    <Icon size={16} aria-hidden />
  </span>,
})

function ThemeControl() {
  const { colorScheme, setColorScheme } = useMantineColorScheme()
  return <SegmentedControl
    className="display-picker" aria-label="Theme" size="xs" value={colorScheme}
    onChange={value => setColorScheme(value as 'auto' | 'light' | 'dark')}
    data={[
      themeOption('auto', 'System theme', IconDeviceDesktop),
      themeOption('light', 'Light theme', IconSun),
      themeOption('dark', 'Dark theme', IconMoon),
    ]}
  />
}

const DISPLAY_OPTIONS = [
  { value: 'both', label: 'Icon + text' },
  { value: 'icon', label: 'Icon' },
  { value: 'text', label: 'Text' },
]

const isDisplay = (value: string): value is Display => ['both', 'icon', 'text'].includes(value)

const LAYOUT_OPTIONS = [
  { value: 'tabs', label: 'By phase' },
  { value: 'list', label: 'All phases' },
]

// `grid` (the cheatsheet) is not a picked layout - it is forced by the
// `?view=cheatsheet` tab that the Cheatsheet button opens.
const isLayout = (value: string): value is Layout => value === 'tabs' || value === 'list'

// Read once at mount - the cheatsheet tab is a fixed, read-only view and does
// not renavigate within itself.
const query = new URLSearchParams(window.location.search)
const cheatsheet = query.get('view') === 'cheatsheet'

function Shell() {
  const [selection, setSelection] = useState(initialSelection)
  const [display, setDisplay] = useState<Display>(() => {
    const stored = readStored('display')
    return isDisplay(stored) ? stored : 'both'
  })
  const [notes, setNotes] = useState(() => readStored('notes') !== 'off')
  const [personalMits, setPersonalMits] = useState(() => readStored('personalMits') !== 'off')
  const [layout, setLayout] = useState<Layout>(() => {
    const stored = readStored('layout')
    return isLayout(stored) ? stored : 'tabs'
  })
  // The cheatsheet tab carries the reader's job and tank branch in its URL so it
  // resolves the same plan as the tab that opened it, without touching storage.
  const [jobId, setJobId] = useState(() => query.get('job') ?? readStored('lastJob'))
  const [otherTankId, setOtherTankId] = useState(() => query.get('otherTank') ?? readStored('lastOtherTank'))
  const [p3BossId, setP3BossId] = useState(() => query.get('p3Boss') ?? readStored('lastP3Boss'))
  const [invulnId, setInvulnId] = useState(() => query.get('invuln') ?? readStored('lastInvulnOrder'))
  const resolvedScheme = useComputedColorScheme('dark')
  const pip = usePip(resolvedScheme)
  const fight = catalog.fights.find(f => f.id === selection.fightId)
  const sheets = catalog.sheets.filter(s => s.fightId === fight?.id)
  const sheet = sheets.find(s => s.id === selection.sheetId)
  const key = sheet ? sheetKey(sheet.fightId, sheet.id) : ''
  const viewing = selection.viewing && fight && sheet && selection.roleId
  const positions = sheet ? positionsForSheet(sheet) : []
  const position = positions.find(p => p.id === selection.roleId)
  const jobOptions = sheet ? jobsForSeat(sheet, position) : jobsForRole(position?.role)
  // Keep the viewer's job when the new seat can still take it, otherwise clear
  // it rather than silently showing another role's plan.
  const job = jobOptions.find(j => j.id === jobId)
  const slotId = sheet ? slotIdFor(sheet, position, job?.id) : ''
  // Melee mitigation is the same for every melee job, so that seat carries no
  // generic lines to resolve - the job selector is disabled and no job needed.
  const jobFree = position?.role === 'melee'
  // Otherwise a job is always required: without it a generic line like "Party
  // Mit" cannot become a real ability, and job-qualified lines cannot be
  // filtered at all.
  const needsJob = Boolean(position && !jobFree && (!job || !slotId))

  // Tank personal mit: once a tank seat has a job, that job's plan splices into
  // the party timeline (MitView `personalPlan`). A sheet keys these two ways.
  // TOP pairs the two tanks - each partner is a whole plan, chosen by "Other
  // tank". DMU keys by job alone and its rows branch on the viewer's own P3
  // boss and P5 invuln choices, chosen here and passed to MitView.
  const tankPlans = position?.role === 'tank' && job ? sheet?.tankMits?.plans.filter(p => p.job === job.id) ?? [] : []
  const paired = tankPlans.some(p => p.with)
  const otherTankOptions = tankPlans.map(p => p.with).filter((w): w is string => Boolean(w))
  // A co-tank must be picked on a paired sheet - no blank/"hide" option. Until
  // one is, `otherTank` is '' (a "Choose tank" placeholder) and "View mits" is
  // blocked. Hiding the personal rows once viewing is the "Party" mits toggle.
  const otherTank = otherTankOptions.includes(otherTankId) ? otherTankId : ''
  const priorities = sheet?.tankMits?.priorities
  // A stored choice wins; otherwise default by seat - MT holds Exdeath and
  // takes the 2nd invuln, OT holds Chaos and goes 1st.
  const p3Boss: 'Chaos' | 'Exdeath' = p3BossId === 'Chaos' || p3BossId === 'Exdeath'
    ? p3BossId : selection.roleId === 'OT' ? 'Chaos' : 'Exdeath'
  const invulnOrder: 1 | 2 = invulnId === '1' || invulnId === '2'
    ? (Number(invulnId) as 1 | 2) : selection.roleId === 'OT' ? 1 : 2
  // A tank can hide the personal rows entirely - some raiders only want the
  // party grid. Off means no plan is spliced, and its branch selects go away.
  const tankPlan = !personalMits ? undefined
    : paired ? tankPlans.find(p => p.with === otherTank)
    : tankPlans[0]

  useEffect(() => {
    const onPop = () => setSelection(initialSelection())
    window.addEventListener('popstate', onPop)
    return () => window.removeEventListener('popstate', onPop)
  }, [])
  useEffect(() => {
    document.title = viewing
      ? `${fight.name} · ${selection.roleId}${cheatsheet ? ' · Cheatsheet' : ''} | XIVMits`
      : 'XIVMits · FFXIV raid mits'
  }, [viewing, fight, selection.roleId])

  function pickSheet(id: string, fightId = selection.fightId) {
    const next = catalog.sheets.find(s => s.id === id && s.fightId === fightId)
    const nextFight = catalog.fights.find(f => f.id === fightId)
    const nextKey = sheetKey(fightId, id)
    const savedRole = readMap('lastRoleBySheet')[nextKey]
    const savedPhase = readMap('lastPhaseBySheet')[nextKey]
    setSelection({
      fightId, sheetId: id,
      roleId: next?.slots.some(s => s.id === savedRole) ? savedRole : '',
      phaseId: nextFight?.phases.some(p => p.id === savedPhase) ? savedPhase : nextFight?.phases[0].id ?? '',
      viewing: false, error: '',
    })
  }
  function clearQuery() {
    if (window.location.search) window.history.replaceState(null, '', sheetPath(selection.fightId, selection.sheetId))
  }
  function changePhase(phaseId: string) {
    setSelection(previous => ({ ...previous, phaseId }))
    storeMap('lastPhaseBySheet', key, phaseId)
    clearQuery()
  }
  function changeRole(roleId: string) {
    setSelection(previous => ({ ...previous, roleId }))
    storeMap('lastRoleBySheet', key, roleId)
    if (viewing) clearQuery()
  }
  function view() {
    if (!fight || !sheet || !selection.roleId) return
    storeValue('lastFight', fight.id)
    storeMap('lastSheetByFight', fight.id, sheet.id)
    storeMap('lastRoleBySheet', key, selection.roleId)
    storeMap('lastPhaseBySheet', key, selection.phaseId)
    window.history.pushState(null, '', sheetPath(fight.id, sheet.id))
    setSelection(previous => ({ ...previous, viewing: true, error: '' }))
  }
  function changeDisplay(value: string) {
    if (!isDisplay(value)) return
    setDisplay(value)
    storeValue('display', value)
  }
  function changeNotes(value: boolean) {
    setNotes(value)
    storeValue('notes', value ? 'on' : 'off')
  }
  function changePersonalMits(value: boolean) {
    setPersonalMits(value)
    storeValue('personalMits', value ? 'on' : 'off')
  }
  function changeLayout(value: string) {
    if (!isLayout(value)) return
    setLayout(value)
    storeValue('layout', value)
  }
  function changeJob(value: string) {
    setJobId(value)
    storeValue('lastJob', value)
  }
  function changeOtherTank(value: string) {
    setOtherTankId(value)
    storeValue('lastOtherTank', value)
  }
  function changeP3Boss(value: string) {
    setP3BossId(value)
    storeValue('lastP3Boss', value)
  }
  function changeInvuln(value: string) {
    setInvulnId(value)
    storeValue('lastInvulnOrder', value)
  }
  function reset() {
    window.history.replaceState(null, '', import.meta.env.BASE_URL)
    setSelection({ fightId: '', sheetId: '', roleId: '', phaseId: '', viewing: false, error: '' })
  }

  // Full width on the selection screen; the focused view caps it via its wrapper.
  const roleSelect = <NativeSelect
    label="Role" value={selection.roleId} disabled={!sheet}
    onChange={event => changeRole(event.currentTarget.value)}
    data={[
      ...(viewing ? [] : [{ value: '', label: sheet ? 'Choose role' : 'Pick a sheet first' }]),
      ...positions.map(p => ({ value: p.id, label: p.id })),
    ]}
  />
  const jobSelect = <NativeSelect
    label="Job" value={jobFree ? '' : job?.id ?? ''} disabled={!position || jobFree}
    onChange={event => changeJob(event.currentTarget.value)}
    // The placeholder exists only while nothing is chosen. Dropping it once a
    // job is set keeps the closed select narrow and stops it offering a state
    // the app no longer accepts. Raiders read abbreviations faster than names,
    // and they match what the sheets themselves write. A melee seat needs no
    // job at all, so it just shows "--".
    data={jobFree
      ? [{ value: '', label: '--' }]
      : [
        ...(job ? [] : [{ value: '', label: position ? 'Choose job' : 'Pick a role first' }]),
        ...jobOptions.map(j => ({ value: j.id, label: j.id })),
      ]}
  />
  // A small info tooltip by a branch toggle: the sheet's suggested job order for
  // each side, the viewer's own job pulled out in accent so they can see where
  // they sit. `keyLabel` prettifies the invuln keys ("1" -> "1st").
  const priorityTip = (orders: Record<string, string[]> | undefined, keyLabel: (k: string) => string) => {
    if (!orders || !Object.keys(orders).length) return null
    return <Tooltip
      withArrow position="top" events={{ hover: true, focus: true, touch: true }}
      label={<Box>
        {Object.entries(orders).map(([opt, jobs]) => <Text key={opt} fz="sm" style={{ whiteSpace: 'nowrap', lineHeight: 1.7 }}>
          <Text span inherit fw={700}>{keyLabel(opt)}:</Text>{'  '}
          {jobs.flatMap((j, i) => [
            i > 0 ? <Text span inherit key={`s${i}`} c="var(--text-muted)">{' > '}</Text> : null,
            <Text span inherit key={j} fw={job?.id === j ? 700 : 400} c={job?.id === j ? 'var(--accent)' : undefined}>{j}</Text>,
          ])}
        </Text>)}
      </Box>}
    >
      <IconInfoCircle size={12} style={{ verticalAlign: 'text-bottom', opacity: 0.5, cursor: 'help' }} tabIndex={0} aria-label="Suggested job order" />
    </Tooltip>
  }
  // On the mits page a co-tank can still be unset (stale storage, a shared URL);
  // flag it beside the label so the missing personal rows are explained, not
  // just absent.
  const otherTankWarning = paired && !otherTank ? <Tooltip
    withArrow position="top" events={{ hover: true, focus: true, touch: true }}
    label="Must be selected to see personal mits."
  >
    <IconAlertCircle
      size={13} color="var(--mantine-color-red-6)" tabIndex={0}
      style={{ cursor: 'help' }}
      aria-label="Must be selected to see personal mits."
    />
  </Tooltip> : null
  // "Other tank" picks the co-tank on a paired sheet (TOP) - each partner is a
  // whole plan. A "Choose tank" placeholder until one is set, then dropped, like
  // Job. Rendered in the selection screen's grow row and the mits control row;
  // `labelExtra` hangs the missing-co-tank warning off the label there.
  const otherTankSelect = (labelExtra: React.ReactNode = null) => paired ? <Input.Wrapper
    labelElement="div"
    label={<Group gap={4} align="center" wrap="nowrap">Other tank{labelExtra}</Group>}
  >
    <NativeSelect
      value={otherTank}
      onChange={event => changeOtherTank(event.currentTarget.value)}
      data={[
        ...(otherTank ? [] : [{ value: '', label: 'Choose tank' }]),
        ...otherTankOptions.map(id => ({ value: id, label: id })),
      ]}
    />
  </Input.Wrapper> : null
  // P3 boss / P5 invuln branch toggles for a job-keyed sheet whose rows really
  // do branch (ikuya). A sheet may key by job and still not branch - LPDU fixes
  // both bosses and both invulns by seat - and then there is nothing to toggle.
  const branches = tankPlans.some(p => p.phases.some(ph => ph.mechanics.some(m => m.boss || m.invuln)))
  const tankBranchToggles = tankPlans.length === 0 || paired || !branches ? null
    : <>
      <Input.Wrapper
        label={<Group gap={4} align="center" wrap="nowrap">P3 boss{priorityTip(priorities?.p3Boss, k => k)}</Group>}
        labelElement="div"
      >
        <SegmentedControl
          className="display-picker" size="sm" value={p3Boss} onChange={changeP3Boss}
          data={[{ value: 'Chaos', label: 'Chaos' }, { value: 'Exdeath', label: 'Exdeath' }]}
        />
      </Input.Wrapper>
      <Input.Wrapper
        label={<Group gap={4} align="center" wrap="nowrap">P5 invuln{priorityTip(priorities?.invuln, k => k === '1' ? '1st' : k === '2' ? '2nd' : k)}</Group>}
        labelElement="div"
      >
        <SegmentedControl
          className="display-picker" size="sm" value={String(invulnOrder)} onChange={changeInvuln}
          data={[{ value: '1', label: '1st' }, { value: '2', label: '2nd' }]}
        />
      </Input.Wrapper>
    </>
  const tankControls = tankPlans.length === 0 ? null : <>
    <Input.Wrapper label="Mits" labelElement="div">
      <SegmentedControl
        className="display-picker" size="sm" aria-label="Show personal tank mitigation"
        value={personalMits ? 'both' : 'party'}
        onChange={value => changePersonalMits(value === 'both')}
        data={[{ value: 'both', label: 'All' }, { value: 'party', label: 'Party' }]}
      />
    </Input.Wrapper>
    {personalMits && (paired
      ? <Box flex="0 0 128px">{otherTankSelect(otherTankWarning)}</Box>
      : tankBranchToggles)}
  </>

  // The cheatsheet is its own bare layout (same tab, `?view=cheatsheet`): no
  // site header/footer, no 720px reading column, no phase tab bar - every
  // pixel goes to fitting all phase columns across with the least wrapping.
  if (cheatsheet) {
    return <Box px="md" py="sm" h="100dvh" style={{ display: 'flex', flexDirection: 'column' }}>
      {viewing && fight && sheet ? <>
        <Group justify="space-between" align="center" wrap="wrap" gap="sm" mb="sm" style={{ flex: '0 0 auto' }}>
          <Text fz="sm" c="dimmed" style={{ overflowWrap: 'anywhere' }}>
            {fight.name} · {selection.roleId}{job ? ` ${job.id}` : ''} · {sheet.name}
          </Text>
          <Button
            component="a" href={sheetPath(fight.id, sheet.id)} variant="default" size="compact-sm"
            leftSection={<IconArrowRight size={14} aria-hidden style={{ transform: 'rotate(180deg)' }} />}
          >
            Full view
          </Button>
        </Group>
        {needsJob
          ? <Text ta="center" c="dimmed" py="xl">Choose a job to see this role's assignments.</Text>
          : <Box flex={1} mih={0} style={{ display: 'flex', flexDirection: 'column' }}>
            <MitView
              hideTabs fight={fight} sheet={sheet} roleId={slotId} phaseId={selection.phaseId}
              onPhase={changePhase} job={jobFree ? undefined : job} personalPlan={tankPlan}
              p3Boss={p3Boss} invulnOrder={invulnOrder} display="icon" notes={false} layout="grid"
            />
          </Box>}
      </> : <Text ta="center" c="dimmed" py="xl">
        Mit sheet not found. <Anchor href={import.meta.env.BASE_URL}>Start over</Anchor>.
      </Text>}
    </Box>
  }

  // Link to this same sheet/role/job forced to the cheatsheet layout (same
  // tab). The reader's job and tank branch ride the query so the view resolves
  // the same plan without reading storage.
  const cheatsheetHref = (() => {
    if (!fight || !sheet) return undefined
    // No `phase` - the cheatsheet shows every phase at once.
    const q = new URLSearchParams({ view: 'cheatsheet' })
    if (selection.roleId) q.set('role', selection.roleId)
    if (job) q.set('job', job.id)
    if (tankPlans.length) {
      if (paired) { if (otherTank) q.set('otherTank', otherTank) }
      else { q.set('p3Boss', p3Boss); q.set('invuln', String(invulnOrder)) }
    }
    return `${sheetPath(fight.id, sheet.id)}?${q}`
  })()

  return <Container size={720} px="md" mih="100dvh" display="flex" style={{ flexDirection: 'column' }}>
    <Group component="header" justify="space-between" wrap="nowrap" pt="sm" pb="lg" style={{ borderBottom: '1px solid var(--border)' }}>
      <Anchor href={import.meta.env.BASE_URL} underline="never" c="var(--text)" fz="xl" fw={750} lts="-0.04em" style={{ whiteSpace: 'nowrap' }}>
        XIV<Text span inherit fw={450}>Mits</Text>
      </Anchor>
      <ThemeControl />
    </Group>

    <Box component="main" flex={1} miw={0} py="xl">
      {viewing ? <>
        {/* Fight name on its own line; the fight/sheet actions always sit as a
            row beneath it rather than floating to its right. */}
        <Stack gap="xs">
          <Box miw={0}>
            <Text fz="sm" c="dimmed">{fight.type} · {sheet.name}</Text>
            <Title order={1} fz="xl" lts="-0.035em" style={{ overflowWrap: 'anywhere' }}>{fight.name}</Title>
          </Box>
          <Group gap="sm" wrap="wrap">
            {sheet.source && <Button
              component="a" href={sheet.source.url} target="_blank" rel="noreferrer"
              variant="default" leftSection={<IconExternalLink size={16} aria-hidden />}
            >
              Source
            </Button>}
            {cheatsheetHref && <Button
              component="a" href={cheatsheetHref}
              variant="default" leftSection={<IconLayoutGrid size={16} aria-hidden />}
            >
              Cheatsheet
            </Button>}
            <Button variant="outline" onClick={() => { pip.close(); setSelection(previous => ({ ...previous, viewing: false })); window.history.pushState(null, '', import.meta.env.BASE_URL) }}>
              Change fight/sheet
            </Button>
          </Group>
        </Stack>

        {/* Two fixed rows, one gap between every control. Row 1 - what you are
            reading: role, job, the plan controls. Row 2 - how the page is
            drawn: display, layout, notes. Same label style, height, and bottom
            alignment throughout; each row wraps only if it runs out of width. */}
        <Stack gap="sm" my="md">
          <Group className="control-row" align="flex-end" gap="sm" wrap="wrap">
            <Box flex="0 0 88px" miw={76}>{roleSelect}</Box>
            <Box flex="0 0 128px">{jobSelect}</Box>
            {tankControls}
          </Group>
          <Group className="control-row" align="flex-end" gap="sm" wrap="wrap">
            <Input.Wrapper label="Display" labelElement="div">
              <SegmentedControl
                className="display-picker" aria-label="Show icons, text, or both"
                size="sm" value={display} onChange={changeDisplay} data={DISPLAY_OPTIONS}
              />
            </Input.Wrapper>
            <Input.Wrapper label="Layout" labelElement="div">
              <SegmentedControl
                className="display-picker" aria-label="Show one phase or every phase in one list"
                size="sm" value={layout} onChange={changeLayout} data={LAYOUT_OPTIONS}
              />
            </Input.Wrapper>
            <Input.Wrapper label="Notes" labelElement="div">
              <Switch
                aria-label="Show action notes" size="md" checked={notes}
                disabled={display === 'icon'}
                onChange={event => changeNotes(event.currentTarget.checked)}
              />
            </Input.Wrapper>
          </Group>
        </Stack>
        {pip.error && <Alert color="red" variant="light" mb="md" role="alert">{pip.error}</Alert>}

        {needsJob
          ? <Text ta="center" c="dimmed" py="xl">Choose a job to see this role's assignments.</Text>
          : <MitView
            fight={fight} sheet={sheet} roleId={slotId} phaseId={selection.phaseId}
            onPhase={changePhase} job={jobFree ? undefined : job} personalPlan={tankPlan}
            p3Boss={p3Boss} invulnOrder={invulnOrder}
            display={display} notes={notes} layout={layout}
            phaseAction={pip.supported && <Button
              variant="outline" size="sm" leftSection={<IconPictureInPicture size={18} aria-hidden />}
              onClick={pip.open}
            >
              {pip.pipWindow ? 'Focus window' : 'Pop out'}
            </Button>}
          />}

        {pip.pipWindow && createPortal(
          <MitView compact fight={fight} sheet={sheet} roleId={slotId} phaseId={selection.phaseId} onPhase={changePhase} job={job} personalPlan={tankPlan} p3Boss={p3Boss} invulnOrder={invulnOrder} display={display} notes={notes} layout={layout} />,
          pip.pipWindow.document.body,
        )}
      </> : <Box maw={480} mx="auto">
        <Title order={1}>What do I mit?</Title>
        <Text c="dimmed" mt="sm">Easy focus on your own mit without distraction.</Text>

        {selection.error && <Alert color="red" variant="light" mt="md" role="alert">
          <Stack gap="xs" align="flex-start">
            <Text fz="sm">{selection.error}</Text>
            <Button variant="subtle" color="gray" size="compact-sm" onClick={reset}>Change fight/sheet</Button>
          </Stack>
        </Alert>}

        <Stack component="form" gap="lg" mt="xl" onSubmit={(event: React.FormEvent) => { event.preventDefault(); view() }}>
          <NativeSelect
            label="Fight" value={selection.fightId}
            onChange={event => {
              const fightId = event.currentTarget.value
              const saved = readMap('lastSheetByFight')[fightId]
              pickSheet(catalog.sheets.some(s => s.id === saved && s.fightId === fightId) ? saved : '', fightId)
            }}
            data={[{ value: '', label: 'Choose fight' }, ...catalog.fights.map(f => ({ value: f.id, label: f.name }))]}
          />
          <NativeSelect
            label="Mit sheet" value={selection.sheetId} disabled={!fight}
            onChange={event => pickSheet(event.currentTarget.value)}
            data={[
              { value: '', label: fight ? sheets.length ? 'Choose sheet' : 'No sheets available' : 'Pick a fight first' },
              ...sheets.map(s => ({ value: s.id, label: s.name })),
            ]}
          />
          <Group grow align="flex-start" gap="sm">{roleSelect}{jobSelect}{otherTankSelect()}</Group>
          <Button type="submit" rightSection={<IconArrowRight size={18} aria-hidden />} disabled={!fight || !sheet || !selection.roleId || (!job && !jobFree) || (paired && !otherTank)}>
            View mits
          </Button>
        </Stack>
      </Box>}
    </Box>

    <Stack component="footer" gap="sm" pt="lg" pb="md" style={{ borderTop: '1px solid var(--border)' }}>
      <Group justify="space-between" align="center" gap="sm" wrap="wrap">
        <Group gap="xs" align="center">
          <Text fz="sm" c="dimmed">Made by tenyu</Text>
          <Text fz="sm" c="dimmed" aria-hidden>·</Text>
          {/* Icon-only, so the accessible name has to come from aria-label - see
              DESIGN.md §7. `title` gives sighted users the same words. */}
          <Tooltip label="Support on Ko-fi" position="top" withArrow>
            <Anchor
              href="https://ko-fi.com/tenyu" target="_blank" rel="noreferrer noopener"
              aria-label="Support tenyu on Ko-fi"
              c="dimmed" display="inline-flex" className="kofi-link"
            >
              <IconCoffee size={18} aria-hidden />
            </Anchor>
          </Tooltip>
          <Tooltip label="@tenyu27 on X" position="top" withArrow>
            <Anchor
              href="https://x.com/tenyu27" target="_blank" rel="noreferrer noopener"
              aria-label="tenyu on X"
              c="dimmed" display="inline-flex"
            >
              <IconBrandX size={18} aria-hidden />
            </Anchor>
          </Tooltip>
        </Group>
        <Anchor href="https://forms.gle/hATqhVSkM93NoCWy9" target="_blank" rel="noreferrer noopener" fz="sm">
          Have a question or feedback?
        </Anchor>
      </Group>
      {/* Required attribution for using Square Enix game assets - see README. */}
      <Text fz="xs" c="var(--text-faint)">
        FINAL FANTASY is a registered trademark of Square Enix Holdings Co., Ltd.
        FINAL FANTASY XIV © SQUARE ENIX
      </Text>
    </Stack>
  </Container>
}

// Key must match the pre-paint script in index.html.
const colorSchemeManager = localStorageColorSchemeManager({ key: 'xivmits-color-scheme' })

export default function App() {
  return <MantineProvider theme={theme} defaultColorScheme="auto" colorSchemeManager={colorSchemeManager}>
    <Shell />
  </MantineProvider>
}
