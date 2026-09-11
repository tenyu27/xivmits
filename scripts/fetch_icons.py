"""Resolve mit-sheet action names to FFXIV action icons via XIVAPI, once.

Usage: python3 scripts/fetch_icons.py [--force]

This runs maintainer-side, like the spreadsheet converters. The site never
touches XIVAPI at runtime - icons are downloaded into apps/web/public/icons/ and the
name -> file map is written to packages/encounter-data/icons.json, both committed to the repo.
See AGENTS.md: no third-party network requests after load.

Icons are property of SQUARE ENIX; see README for attribution.
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ICON_DIR = ROOT / 'apps/web/public/icons'
MAP_FILE = ROOT / 'packages/encounter-data/icons.json'
ABILITY_FILE = ROOT / 'packages/encounter-data/abilities.json'
SEARCH = 'https://v2.xivapi.com/api/search'
ASSET = 'https://v2.xivapi.com/api/asset'

# Sheet shorthand that is not the in-game action name.
ALIASES = {
    'Seraph': 'Summon Seraph',
    "Seraph's Veil": 'Summon Seraph',
    'Spreadlo': 'Deployment Tactics',
    'Zoe Shields': 'Zoe',
    # Every job's level 3 limit break shares one icon in the game data, so the
    # sheet's generic "LB3" - and TOP Mitty's "Tank LB" / "Healer LB" - resolve
    # to it without naming a per-job ability.
    'LB3': 'Last Bastion',
    'Tank LB': 'Last Bastion',
    'Healer LB': 'Last Bastion',
    # TOP Mitty's tank-pairing tabs write pre-7.0 / shorthand names.
    'Vengeance': 'Damnation',
}

# Names that describe a decision, not a single ability. These intentionally get
# no icon - the text carries the whole meaning.
NO_ICON = {
    'Assist Tanks', 'Avoid HP-restoring abilities', 'Manage Accretion healing',
    # TOP Mitty tank tabs: "press your whole kit" / "cover your co-tank" / a
    # cue, not one button.
    'Kitchen Sink', 'Buddy Mit', 'Voke after Buster',
    # LPDU writes a couple of calls as prose: a bundle of AST cooldowns, a
    # babysitting instruction, and the enrage marker.
    'All single-target mit', 'Card mits', 'Babysit the beam tank', 'Enrage',
}

# AST cards have no Action row - they are drawn and played through Play I/II/III
# - so the card art lives in the Status sheet instead. Resolved by name there.
STATUS_ICONS = {'The Balance', 'The Bole', 'The Arrow', 'The Spear', 'The Ewer', 'The Spire'}

# Generic names resolved per job from packages/encounter-data/jobs.json instead of by search.
# 'Party Mit' means a different button for every job standing in that slot.
JOB_GENERIC = {'Party Mit', 'Extra', 'Short Mit', '90s Mit', '120s Mit', 'Invuln'}

# Real, castable actions the game data flags IsPlayerAction=false because they
# are granted by a stance (SGE's Eukrasia) rather than slotted on a hotbar.
NONPLAYER_OK = {'Eukrasian Prognosis', 'Eukrasian Prognosis II', 'Eukrasian Diagnosis'}

# The placeholder icon unused Action rows point at.
PLACEHOLDER = '000000/000405'


def get(url, params):
    request = urllib.request.Request(
        f'{url}?{urllib.parse.urlencode(params)}',
        headers={'User-Agent': 'xivmits-icon-import/1.0 (+https://xivmits.com)'},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def slug(name):
    """Stable id for an ability, so sheets stop referring to it by prose."""
    return re.sub(r'(^-|-$)', '', re.sub(r'[^a-z0-9]+', '-', name.lower()))


def candidate(name):
    """Sheet names carry qualifiers - 'Feint (Chaos)', 'Sun Sign (7-8th Set)'.
    The parenthetical says when to press it, not what it is."""
    base = re.sub(r'\s*\([^)]*\)\s*$', '', name).strip()
    return ALIASES.get(base, ALIASES.get(name, base))


def resolve_status(name):
    """Return (action_id, icon_id, icon_path, status_name) for a Status-sheet icon.

    Status rows are not castable actions, so there is no action id; the card
    icons this covers are cosmetic anyway.
    """
    payload = json.loads(get(SEARCH, {
        'sheets': 'Status', 'query': f'Name="{name}"', 'fields': 'Name,Icon.path,Icon.id', 'limit': 5,
    }))
    for row in payload.get('results', []):
        icon = row['fields'].get('Icon') or {}
        if icon.get('path') and PLACEHOLDER not in icon['path']:
            return None, icon['id'], icon['path'], row['fields']['Name']
    return None


def resolve(name):
    """Return (action_id, icon_id, icon_path, action_name) for a player action.

    `action_id` is the Action sheet row id, which is the same number FFLogs
    reports as `abilityGameID` for a player cast - the anchor a future parse
    needs to match a logged press back to the mit a sheet recorded.
    """
    if name in STATUS_ICONS:
        return resolve_status(name)
    payload = json.loads(get(SEARCH, {
        'sheets': 'Action',
        'query': f'Name="{name}"',
        'fields': 'Name,Icon.path,Icon.id,IsPlayerAction,ClassJobLevel,ActionCategory.Name',
        'limit': 10,
    }))
    usable = []
    for row in payload.get('results', []):
        fields = row['fields']
        icon = fields.get('Icon') or {}
        path = icon.get('path', '')
        category = ((fields.get('ActionCategory') or {}).get('fields') or {}).get('Name')
        # Limit breaks are not player actions and carry no job level, but they
        # are real, castable, and named per job - they just share one icon.
        player = fields.get('IsPlayerAction') and fields.get('ClassJobLevel')
        if not player and category != 'Limit Break' and fields['Name'] not in NONPLAYER_OK:
            continue
        if PLACEHOLDER in path:
            continue
        usable.append((row['row_id'], icon['id'], path, fields['Name']))
    if not usable:
        return None
    # Lowest row id is the original action; later rows are re-releases.
    action_id, icon_id, path, action = min(usable)
    return action_id, icon_id, path, action


def main(force=False):
    ICON_DIR.mkdir(parents=True, exist_ok=True)
    names = set()
    for path in sorted((ROOT / 'packages/encounter-data/fights').rglob('*.json')):
        # Encounters carry the canonical mechanic timeline; only sheets under
        # sheets/ carry assignments and tankMits.
        if path.name in ('fight.json', 'encounter.json'):
            continue
        sheet = json.loads(path.read_text())
        for phase in sheet['phases']:
            for mechanic in phase['mechanics']:
                for actions in mechanic['assignments'].values():
                    names.update(action['name'] for action in actions)
        # Tank personal-mit plans carry their own mechanic/action lists.
        for plan in sheet.get('tankMits', {}).get('plans', []):
            for phase in plan['phases']:
                for mechanic in phase['mechanics']:
                    names.update(action['name'] for action in mechanic['actions'])

    # Every per-job ability a sheet can resolve a generic name to.
    jobs = json.loads((ROOT / 'packages/encounter-data/jobs.json').read_text())['jobs']
    for job in jobs:
        names.update(job.get('abilities', {}).values())

    # Two maps: the ability registry, keyed by an id derived from the real game
    # name so every way a sheet writes an ability collapses onto one entry, and
    # `names`, which records what each sheet wrote so an importer can resolve it.
    mapping, unresolved, failed, abilities, by_name = {}, [], [], {}, {}
    for name in sorted(names):
        base = candidate(name)
        if base in JOB_GENERIC:
            # "Party Mit" is a slot, not a button: jobs.json says which action
            # each job presses for it, so there is nothing to anchor here. The
            # qualifier a sheet adds ("Party Mit (GNB/DRK)") scopes who presses
            # it, so it belongs on the reference, not on a separate ability.
            ability_id = slug(base)
            abilities.setdefault(ability_id, {'name': base, 'kind': 'generic'})
            by_name[name] = ability_id
            continue
        if name in NO_ICON:
            # Prose the sheet writes in an action cell ("Avoid HP-restoring
            # abilities"): a cue to the reader, with no action behind it.
            ability_id = slug(name)
            abilities[ability_id] = {'name': name, 'kind': 'note'}
            by_name[name] = ability_id
            continue
        query = candidate(name)
        try:
            found = resolve(query)
        except Exception as error:  # network or schema change - never half-write
            print(f'  ERROR {name!r} ({query!r}): {error}', file=sys.stderr)
            failed.append(name)
            continue
        if not found:
            unresolved.append(name)
            abilities[slug(name)] = {'name': name, 'kind': 'note'}
            by_name[name] = slug(name)
            print(f'  no match: {name!r} (searched {query!r})')
            continue
        action_id, icon_id, icon_path, action = found
        filename = f'{icon_id:06d}.png'
        target = ICON_DIR / filename
        if force or not target.exists():
            target.write_bytes(get(ASSET, {'path': icon_path, 'format': 'png'}))
            time.sleep(0.15)
        mapping[name] = filename
        # Keyed by the real game name, so 'Feint' and 'Feint (Chaos)' - and
        # 'Zoe Shields', 'Spreadlo', 'Vengeance' - land on one ability.
        ability_id = slug(action)
        entry = {'name': action, 'kind': 'action' if action_id else 'status', 'icon': filename}
        if action_id is not None:
            # Same number FFLogs reports as abilityGameID for this cast.
            entry['action'] = action_id
        abilities.setdefault(ability_id, entry)
        by_name[name] = ability_id
        print(f'  {name:32} -> {action:24} {filename}  action={action_id}')

    if failed:
        raise SystemExit('Icon refresh failed; existing map and icons were left unchanged: ' + ', '.join(sorted(failed)))

    MAP_FILE.write_text(json.dumps(dict(sorted(mapping.items())), indent=2) + '\n')
    ABILITY_FILE.write_text(json.dumps(
        {'abilities': dict(sorted(abilities.items())), 'names': dict(sorted(by_name.items()))},
        indent=2, ensure_ascii=False) + '\n')
    used = {f for f in mapping.values()}
    for stale in ICON_DIR.glob('*.png'):
        if stale.name not in used:
            stale.unlink()
            print(f'  removed unused icon {stale.name}')
    kinds = {}
    for entry in abilities.values():
        kinds[entry['kind']] = kinds.get(entry['kind'], 0) + 1
    anchored = sum(1 for e in abilities.values() if e.get('action'))
    print(f"\n{len(abilities)} abilities recorded ({kinds}), {anchored} anchored to a game action id")
    print(f'\n{len(mapping)} names mapped to {len(used)} icons, '
          f'{len(unresolved) + len(names & NO_ICON)} intentionally or unavoidably text-only')
    if unresolved:
        print('Unresolved (text-only, which must still read correctly): ' + ', '.join(sorted(unresolved)))


if __name__ == '__main__':
    main(force='--force' in sys.argv)
