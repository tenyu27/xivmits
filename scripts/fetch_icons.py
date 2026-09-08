"""Resolve mit-sheet action names to FFXIV action icons via XIVAPI, once.

Usage: python3 scripts/fetch_icons.py [--force]

This runs maintainer-side, like the spreadsheet converters. The site never
touches XIVAPI at runtime - icons are downloaded into public/icons/ and the
name -> file map is written to data/icons.json, both committed to the repo.
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
ICON_DIR = ROOT / 'public/icons'
MAP_FILE = ROOT / 'data/icons.json'
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
}

# Generic names resolved per job from data/jobs.json instead of by search.
# 'Party Mit' means a different button for every job standing in that slot.
JOB_GENERIC = {'Party Mit', 'Extra'}

# Real, castable actions the game data flags IsPlayerAction=false because they
# are granted by a stance (SGE's Eukrasia) rather than slotted on a hotbar.
NONPLAYER_OK = {'Eukrasian Prognosis'}

# The placeholder icon unused Action rows point at.
PLACEHOLDER = '000000/000405'


def get(url, params):
    request = urllib.request.Request(
        f'{url}?{urllib.parse.urlencode(params)}',
        headers={'User-Agent': 'xivmits-icon-import/1.0 (+https://xivmits.com)'},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def candidate(name):
    """Sheet names carry qualifiers - 'Feint (Chaos)', 'Sun Sign (7-8th Set)'.
    The parenthetical says when to press it, not what it is."""
    base = re.sub(r'\s*\([^)]*\)\s*$', '', name).strip()
    return ALIASES.get(base, ALIASES.get(name, base))


def resolve(name):
    """Return (icon_id, icon_path, action_name) for the real player action."""
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
    _, icon_id, path, action = min(usable)
    return icon_id, path, action


def main(force=False):
    ICON_DIR.mkdir(parents=True, exist_ok=True)
    names = set()
    for path in sorted((ROOT / 'data/fights').rglob('*.json')):
        if path.name == 'fight.json':
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
    jobs = json.loads((ROOT / 'data/jobs.json').read_text())['jobs']
    for job in jobs:
        names.update(job.get('abilities', {}).values())

    mapping, unresolved, failed = {}, [], []
    for name in sorted(names):
        if name in NO_ICON or candidate(name) in JOB_GENERIC:
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
            print(f'  no match: {name!r} (searched {query!r})')
            continue
        icon_id, icon_path, action = found
        filename = f'{icon_id:06d}.png'
        target = ICON_DIR / filename
        if force or not target.exists():
            target.write_bytes(get(ASSET, {'path': icon_path, 'format': 'png'}))
            time.sleep(0.15)
        mapping[name] = filename
        print(f'  {name:32} -> {action:24} {filename}')

    if failed:
        raise SystemExit('Icon refresh failed; existing map and icons were left unchanged: ' + ', '.join(sorted(failed)))

    MAP_FILE.write_text(json.dumps(dict(sorted(mapping.items())), indent=2) + '\n')
    used = {f for f in mapping.values()}
    for stale in ICON_DIR.glob('*.png'):
        if stale.name not in used:
            stale.unlink()
            print(f'  removed unused icon {stale.name}')
    print(f'\n{len(mapping)} names mapped to {len(used)} icons, '
          f'{len(unresolved) + len(names & NO_ICON)} intentionally or unavoidably text-only')
    if unresolved:
        print('Unresolved (text-only, which must still read correctly): ' + ', '.join(sorted(unresolved)))


if __name__ == '__main__':
    main(force='--force' in sys.argv)
