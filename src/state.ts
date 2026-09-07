import catalog from './data/catalog'
import { isKnownPosition } from './data/resolve'

export function readStored(key: string): string {
  try { return localStorage.getItem(key) ?? '' } catch { return '' }
}
export function storeValue(key: string, value: string) {
  try { localStorage.setItem(key, value) } catch { /* The viewer also works without storage. */ }
}
export function readMap(key: string): Record<string, string> {
  try {
    const value: unknown = JSON.parse(readStored(key))
    if (value && typeof value === 'object' && !Array.isArray(value)) {
      return Object.fromEntries(Object.entries(value).filter((entry): entry is [string, string] => typeof entry[1] === 'string'))
    }
  } catch { /* Ignore corrupt preferences. */ }
  return {}
}
export function storeMap(key: string, id: string, value: string) {
  storeValue(key, JSON.stringify({ ...readMap(key), [id]: value }))
}
export const sheetKey = (fight: string, sheet: string) => `${fight}/${sheet}`
export const sheetPath = (fight: string, sheet: string) => `${import.meta.env.BASE_URL}${fight}/${sheet}/`

export function initialSelection() {
  const base = import.meta.env.BASE_URL
  const path = window.location.pathname.startsWith(base) ? window.location.pathname.slice(base.length) : window.location.pathname
  const parts = path.split('/').filter(Boolean)
  const linked = parts.length > 0
  const fight = catalog.fights.find(f => f.id === (linked ? parts[0] : readStored('lastFight')))
  const sheet = fight && catalog.sheets.find(s => s.fightId === fight.id && s.id === (linked ? parts[1] : readMap('lastSheetByFight')[fight.id]))
  const key = sheet ? sheetKey(sheet.fightId, sheet.id) : ''
  const query = new URLSearchParams(window.location.search)
  const role = query.get('role') ?? readMap('lastRoleBySheet')[key]
  const phase = query.get('phase') ?? readMap('lastPhaseBySheet')[key]
  // `role` is a seat (MT, H2, D3), which may be a synthesized position rather
  // than a literal slot id - see positionsForSheet.
  const validRole = sheet && role && isKnownPosition(sheet, role) ? role : ''
  const validPhase = fight?.phases.find(p => p.id.toLowerCase() === phase?.toLowerCase())?.id ?? fight?.phases[0].id ?? ''
  return {
    fightId: fight?.id ?? '', sheetId: sheet?.id ?? '', roleId: validRole,
    // The root is always the selection screen, prepopulated from storage.
    // A sheet path is the explicit signal to open the focused view.
    phaseId: validPhase, viewing: Boolean(linked && sheet && validRole && parts.length === 2),
    error: linked && (!fight || !sheet || parts.length > 2) ? 'Mit sheet not found.' : '',
  }
}
