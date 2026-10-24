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
    'Seraph Veil': 'Seraphic Veil',
    'Spreadlo': 'Deployment Tactics',
    'Zoe Shields': 'Zoe',
    # Every job's level 3 limit break shares one icon in the game data, so the
    # sheet's generic "LB3" - and TOP Mitty's "Tank LB" / "Healer LB" - resolve
    # to it without naming a per-job ability.
    'LB3': 'Last Bastion',
    'Tank LB': 'Last Bastion',
    'Healer LB': 'Last Bastion',
}

# A trait replaces the action at `level`. The old button stays its own registry
# entry so a sheet can still name it for a fight synced below that level, and
# sync.test.ts rejects it once the duty's sync level has caught up. Levels are
# the Trait sheet's Level on v2.xivapi.com. The extra level-96 upgrade found
# beside the healer shields is Requiescat Mastery (trait 565) → Imperator.
REPLACED_BY = {
    'Succor': ('Concitation', 96),                 # trait 628 Succor Mastery
    'Eukrasian Prognosis': ('Eukrasian Prognosis II', 96),  # trait 637
    'Aspected Helios': ('Helios Conjunction', 96),  # trait 633
    'Medica II': ('Medica III', 96),               # trait 624 Medica Mastery
    'Requiescat': ('Imperator', 96),               # trait 565 Requiescat Mastery
    'Sentinel': ('Guardian', 92),                  # trait 564 Sentinel Mastery
    'Vengeance': ('Damnation', 92),                # trait 567 Vengeance Mastery
    'Shadow Wall': ('Shadowed Vigil', 92),         # trait 571 Shadow Wall Mastery
    'Nebula': ('Great Nebula', 92),                # trait 574 Nebula Mastery
}

# Effect lengths that change with level, ascending, keyed by the game's action
# name. The tooltip states the unsynced length (15s). Enhanced Reprisal (trait
# 640), Enhanced Feint (641) and Enhanced Addle (643) are the level 98 traits
# that extend these from 10s to 15s, so a fight that syncs below 98 — TOP and
# DSR at 90 — still has the 10s version. The first step is that base length.
DURATIONS = {name: [{'level': 1, 'seconds': 10}, {'level': 98, 'seconds': 15}]
             for name in ('Reprisal', 'Feint', 'Addle')}

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

# Damage reduction, in percent, ascending by the level the step starts. The
# action text shows the post-trait 15%. The level-98 traits are the change
# from 10% to 15%; the level-88 traits only cut the recast to 90s. Same step
# convention as DURATIONS.
POTENCIES = {
    'Troubadour': [{'level': 62, 'percent': 10}, {'level': 98, 'percent': 15}],    # action 7405, trait 601
    'Tactician': [{'level': 56, 'percent': 10}, {'level': 98, 'percent': 15}],     # action 16889, trait 607
    'Shield Samba': [{'level': 56, 'percent': 10}, {'level': 98, 'percent': 15}],  # action 16012, trait 611
}

# Real, castable actions the game data flags IsPlayerAction=false. They are not
# slotted on a hotbar of their own: Sage's Eukrasia grants Eukrasian Diagnosis
# (level 30, action 24291), Eukrasian Prognosis (level 30, action 24292) and
# Eukrasian Prognosis II (level 96, action 37034), and Seraph grants Seraphic
# Veil (level 80, action 16548). Sheets name those presses, so they belong in
# the registry.
#
# Each name also has later rows — placeholder icons 000405 / 000784, and for
# Seraphic Veil a non-placeholder copy (row 29240) — none of which carry a
# ClassJobLevel. Only a row that has one is the action a player learns. Require
# that level here, then keep the lowest row id: a later re-release of the same
# name must not replace the original. Dropping either rule records a copy.
NONPLAYER_OK = {'Eukrasian Prognosis', 'Eukrasian Prognosis II', 'Eukrasian Diagnosis',
                'Seraphic Veil'}  # TOP also names Seraph's automatic shield.

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
    """Return (action_id, icon_id, icon_path, status_name, level) for a Status icon.

    Status rows are not castable actions, so there is no action id and no job
    level; the card icons this covers are cosmetic anyway.
    """
    payload = json.loads(get(SEARCH, {
        'sheets': 'Status', 'query': f'Name="{name}"', 'fields': 'Name,Icon.path,Icon.id', 'limit': 5,
    }))
    for row in payload.get('results', []):
        icon = row['fields'].get('Icon') or {}
        if icon.get('path') and PLACEHOLDER not in icon['path']:
            return None, icon['id'], icon['path'], row['fields']['Name'], None
    return None


def resolve(name):
    """Return (action_id, icon_id, icon_path, action_name, level) for a player action.

    `action_id` is the Action sheet row id, which is the same number FFLogs
    reports as `abilityGameID` for a player cast - the anchor a future parse
    needs to match a logged press back to the mit a sheet recorded. `level` is
    ClassJobLevel, when the job learns it.
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
        level = fields.get('ClassJobLevel') or None
        # Limit breaks are not player actions and carry no job level, but they
        # are real, castable, and named per job - they just share one icon.
        # NONPLAYER_OK rows are real too, but only the copy that has a level:
        # the others are placeholders or duplicates. See NONPLAYER_OK.
        player = fields.get('IsPlayerAction') and level
        named = fields['Name'] in NONPLAYER_OK and level
        if not player and category != 'Limit Break' and not named:
            continue
        if PLACEHOLDER in path:
            continue
        usable.append((row['row_id'], icon['id'], path, fields['Name'], level))
    if not usable:
        return None
    # Lowest row id is the original action; later rows are re-releases.
    return min(usable)


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
        # Lower-level forms of a slot ("120s Mit" is Vengeance before Damnation)
        # have to be in the registry even when no current sheet writes them.
        for steps in job.get('levels', {}).values():
            names.update(step['name'] for step in steps)

    # A sheet may name a generic no current fight uses. Register every one,
    # the same way Party Mit and 90s Mit are registered, so "120s Mit",
    # "Short Mit" and "Invuln" are valid abilities rather than unknown wording.
    names.update(JOB_GENERIC)

    # Keep retired actions and their replacements in the registry even when no
    # current sheet names them, so the next regeneration does not drop replacedBy.
    names.update(REPLACED_BY)
    names.update(replacement for replacement, _level in REPLACED_BY.values())

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
        action_id, icon_id, icon_path, action, level = found
        filename = f'{icon_id:06d}.png'
        target = ICON_DIR / filename
        if force or not target.exists():
            target.write_bytes(get(ASSET, {'path': icon_path, 'format': 'png'}))
            time.sleep(0.15)
        mapping[name] = filename
        # Keyed by the real game name, so 'Feint' and 'Feint (Chaos)' - and
        # 'Zoe Shields', 'Spreadlo', 'Seraph Veil' - land on one ability.
        # Vengeance does not: it is action 44, and Damnation replaces it at 92.
        ability_id = slug(action)
        entry = {'name': action, 'kind': 'action' if action_id else 'status', 'icon': filename}
        if action_id is not None:
            # Same number FFLogs reports as abilityGameID for this cast.
            entry['action'] = action_id
        if level:
            entry['level'] = level  # ClassJobLevel: when the job learns it
        if action in DURATIONS:
            entry['durations'] = DURATIONS[action]
        if action in POTENCIES:
            entry['potencies'] = POTENCIES[action]
        replacement = REPLACED_BY.get(action)
        if replacement:
            entry['replacedBy'] = {'name': replacement[0], 'level': replacement[1]}
        abilities.setdefault(ability_id, entry)
        by_name[name] = ability_id
        print(f'  {name:32} -> {action:24} {filename}  action={action_id} level={level}')

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
