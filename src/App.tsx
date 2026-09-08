import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import {
  Alert, Anchor, Box, Button, Container, Group, MantineProvider, NativeSelect,
  Input, SegmentedControl, Stack, Switch, Text, Title, Tooltip, localStorageColorSchemeManager,
  useComputedColorScheme, useMantineColorScheme,
} from '@mantine/core'
import {
  IconArrowRight, IconBrandX, IconCoffee, IconDeviceDesktop, IconExternalLink, IconMoon,
  IconPictureInPicture, IconSun,
} from '@tabler/icons-react'
import catalog from './data/catalog'
import { jobsForRole, positionsForSheet, slotIdFor } from './data/resolve'
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

const isLayout = (value: string): value is Layout => value === 'tabs' || value === 'list'

function Shell() {
  const [selection, setSelection] = useState(initialSelection)
  const [display, setDisplay] = useState<Display>(() => {
    const stored = readStored('display')
    return isDisplay(stored) ? stored : 'both'
  })
  const [notes, setNotes] = useState(() => readStored('notes') !== 'off')
  const [layout, setLayout] = useState<Layout>(() => {
    const stored = readStored('layout')
    return isLayout(stored) ? stored : 'tabs'
  })
  const [jobId, setJobId] = useState(() => readStored('lastJob'))
  const [otherTankId, setOtherTankId] = useState(() => readStored('lastOtherTank'))
  const resolvedScheme = useComputedColorScheme('dark')
  const pip = usePip(resolvedScheme)
  const fight = catalog.fights.find(f => f.id === selection.fightId)
  const sheets = catalog.sheets.filter(s => s.fightId === fight?.id)
  const sheet = sheets.find(s => s.id === selection.sheetId)
  const key = sheet ? sheetKey(sheet.fightId, sheet.id) : ''
  const viewing = selection.viewing && fight && sheet && selection.roleId
  const positions = sheet ? positionsForSheet(sheet) : []
  const position = positions.find(p => p.id === selection.roleId)
  const jobOptions = jobsForRole(position?.role)
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

  // Tank personal mit: when a tank seat picks a job and a co-tank, that
  // pairing's rows splice into the party timeline (MitView `personalPlan`).
  // Buddy-mit targets and invuln order change with the co-tank.
  const tankPlans = position?.role === 'tank' && job ? sheet?.tankMits?.plans.filter(p => p.job === job.id) ?? [] : []
  const otherTankOptions = tankPlans.map(p => p.with)
  const otherTank = otherTankOptions.includes(otherTankId) ? otherTankId : ''
  const tankPlan = tankPlans.find(p => p.with === otherTank)

  useEffect(() => {
    const onPop = () => setSelection(initialSelection())
    window.addEventListener('popstate', onPop)
    return () => window.removeEventListener('popstate', onPop)
  }, [])
  useEffect(() => {
    document.title = viewing ? `${fight.name} · ${selection.roleId} | XIVMits` : 'XIVMits · FFXIV raid mits'
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
  function reset() {
    window.history.replaceState(null, '', import.meta.env.BASE_URL)
    setSelection({ fightId: '', sheetId: '', roleId: '', phaseId: '', viewing: false, error: '' })
  }

  // Full width on the selection screen; the focused view caps it via its wrapper.
  const roleSelect = <NativeSelect
    label="Role" value={selection.roleId} disabled={!sheet}
    onChange={event => changeRole(event.currentTarget.value)}
    data={[
      ...(viewing ? [] : [{ value: '', label: sheet ? 'Choose your role' : 'Pick a sheet first' }]),
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
        ...(job ? [] : [{ value: '', label: position ? 'Choose your job' : 'Pick a role first' }]),
        ...jobOptions.map(j => ({ value: j.id, label: j.id })),
      ]}
  />
  // Only appears once a tank seat has a job and the sheet ships tank plans
  // (TOP). Picking a co-tank splices that pairing's personal-mit rows into the
  // timeline; shown on the selection screen and in the focused view's controls.
  const otherTankSelect = tankPlans.length > 0 ? <NativeSelect
    label="Other tank" value={otherTank}
    onChange={event => changeOtherTank(event.currentTarget.value)}
    data={[{ value: '', label: 'Hide' }, ...otherTankOptions.map(id => ({ value: id, label: id }))]}
  /> : null

  return <Container size={720} px="md" mih="100dvh" display="flex" style={{ flexDirection: 'column' }}>
    <Group component="header" justify="space-between" wrap="nowrap" pt="sm" pb="lg" style={{ borderBottom: '1px solid var(--border)' }}>
      <Anchor href={import.meta.env.BASE_URL} underline="never" c="var(--text)" fz="xl" fw={750} lts="-0.04em" style={{ whiteSpace: 'nowrap' }}>
        XIV<Text span inherit fw={450}>Mits</Text>
      </Anchor>
      <ThemeControl />
    </Group>

    <Box component="main" flex={1} miw={0} py="xl">
      {viewing ? <>
        <Group justify="space-between" align="flex-start" wrap="wrap" gap="sm">
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
            <Button variant="outline" onClick={() => { pip.close(); setSelection(previous => ({ ...previous, viewing: false })); window.history.pushState(null, '', import.meta.env.BASE_URL) }}>
              Change fight/sheet
            </Button>
          </Group>
        </Group>

        {/* Every control here gets the same treatment: label above in the same
            style, one shared height, bottom-aligned. Mixing label positions and
            sizes made this row read as five unrelated widgets. */}
        <Group className="control-row" align="flex-end" gap="sm" my="md" wrap="wrap">
          <Box flex="0 1 88px" miw={76}>{roleSelect}</Box>
          {/* Job and Other tank keep one fixed width so the row never reflows
              as their value text changes. */}
          <Box flex="0 0 128px">{jobSelect}</Box>
          {otherTankSelect && <Box flex="0 0 128px">{otherTankSelect}</Box>}
          <Input.Wrapper label="Show" labelElement="div">
            <SegmentedControl
              className="display-picker" aria-label="Show icons, text, or both"
              size="sm" value={display} onChange={changeDisplay} data={DISPLAY_OPTIONS}
            />
          </Input.Wrapper>
          <Input.Wrapper label="Notes" labelElement="div">
            <Switch
              aria-label="Show action notes" size="md" checked={notes}
              disabled={display === 'icon'}
              onChange={event => changeNotes(event.currentTarget.checked)}
            />
          </Input.Wrapper>
          <Input.Wrapper label="Layout" labelElement="div">
            <SegmentedControl
              className="display-picker" aria-label="Show one phase or every phase in one list"
              size="sm" value={layout} onChange={changeLayout} data={LAYOUT_OPTIONS}
            />
          </Input.Wrapper>
        </Group>
        {pip.error && <Alert color="red" variant="light" mb="md" role="alert">{pip.error}</Alert>}

        {needsJob
          ? <Text ta="center" c="dimmed" py="xl">Choose your job to see this role's assignments.</Text>
          : <MitView
            fight={fight} sheet={sheet} roleId={slotId} phaseId={selection.phaseId}
            onPhase={changePhase} job={jobFree ? undefined : job} personalPlan={tankPlan}
            display={display} notes={notes} layout={layout}
            phaseAction={pip.supported && <Button
              variant="outline" size="sm" leftSection={<IconPictureInPicture size={18} aria-hidden />}
              onClick={pip.open}
            >
              {pip.pipWindow ? 'Focus window' : 'Pop out'}
            </Button>}
          />}

        {pip.pipWindow && createPortal(
          <MitView compact fight={fight} sheet={sheet} roleId={slotId} phaseId={selection.phaseId} onPhase={changePhase} job={job} personalPlan={tankPlan} display={display} notes={notes} layout={layout} />,
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
            data={[{ value: '', label: 'Choose a fight' }, ...catalog.fights.map(f => ({ value: f.id, label: f.name }))]}
          />
          <NativeSelect
            label="Mit sheet" value={selection.sheetId} disabled={!fight}
            onChange={event => pickSheet(event.currentTarget.value)}
            data={[
              { value: '', label: fight ? sheets.length ? 'Choose a sheet' : 'No sheets available' : 'Pick a fight first' },
              ...sheets.map(s => ({ value: s.id, label: s.name })),
            ]}
          />
          <Group grow align="flex-start" gap="sm">{roleSelect}{jobSelect}{otherTankSelect}</Group>
          <Button type="submit" rightSection={<IconArrowRight size={18} aria-hidden />} disabled={!fight || !sheet || !selection.roleId || (!job && !jobFree)}>
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
