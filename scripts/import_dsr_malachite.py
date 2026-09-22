"""Import Malachite Laurent's DSR party grid and all six tank pairings.

python3 scripts/import_dsr_malachite.py [--xlsx /path/to/reviewed.xlsx]
Default input is the live workbook. Never writes encounter.json.
Explicit row bindings exclude duplicate Eyes blocks and leftover TOP templates.
"""
import argparse
import json
import re
import zipfile
from pathlib import Path

import workbook
from import_fru_mitbutgood import read_cells, COLUMNS, HEALERS, ROLES, extras
from normalize_sheet import bind_sheet, load_encounter, snap_tank_times

ROOT = Path(__file__).resolve().parents[1]
SHEET_ID = '1sUEuFDGa_Qg4SYHo4y7b4oEvUGvmhkUMn2rPdXdWEo0'
SOURCE = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit?gid=1960553822#gid=1960553822'
PARTY = {
    'Thordan': [
        (15, 'Strength of the Ward', 'p2-strength-of-the-ward-1'),
        (17, 'Ancient Quaga', 'p2-ancient-quaga-1'),
        (19, 'Sanctity of the Ward', 'p2-sanctity-of-the-ward-1'),
        (21, 'Ultimate End', 'p2-ultimate-end-1'),
        (23, 'Final Chorus (Transition)', 'p2-final-chorus-1'),
    ],
    'NidhoggEyes': [
        (10, 'First Stack', 'p3-eye-of-the-tyrant-1'),
        (12, 'Second Stack', 'p3-eye-of-the-tyrant-2'),
        (14, 'Soul Tether', 'p3-soul-tether-1'),
        (999, 'Resentment', 'p4-resentment-1'),
        (1001, 'Orb Pops', 'p4-flare-nova-1'),
        (1003, 'Dives', 'p4-mirage-dive-1'),
        (1005, 'Steep in Rage', 'p4-steep-in-rage-1'),
    ],
    'RewindDark Thordan': [
        (10, 'Healers', 'rewind-brightwing-1'),
        (12, 'Melee', 'rewind-brightwing-2'),
        (14, 'Range', 'rewind-brightwing-3'),
        (16, 'Tank', 'rewind-brightwing-4'),
        (18, 'Pure of Heart', 'rewind-pure-of-heart-1'),
        (31, 'Wrath of the Heavens', 'p5-wrath-of-the-heavens-1'),
        (33, 'Ancient Quaga', 'p5-ancient-quaga-1'),
        (35, 'Death of the Heavens', 'p5-death-of-the-heavens-1'),
        (37, 'Ancient Quaga', 'p5-ancient-quaga-2'),
    ],
    'Double Dragons': [
        (11, 'Wyrmsbreath 1', 'p6-great-wyrmsbreath-1'),
        (13, 'Akh Afah', 'p6-akh-afah-1'),
        (15, 'Wroth Flames', 'p6-wroth-flames-1'),
        (17, 'Akh Afah', 'p6-akh-afah-2'),
        (19, 'Wyrmsbreath 2', 'p6-great-wyrmsbreath-2'),
        (21, 'Cauterize', 'p6-cauterize-2'),
    ],
    'Dragon King Thordan': [
        (11, 'Transition', 'p7-alternative-end-1'),
        (13, 'Akh Morn 1', 'p7-akh-morn-s-edge-1'),
        (15, 'Gigaflare 1', 'p7-gigaflare-s-edge-1'),
        (17, 'Akh Morn 2', 'p7-akh-morn-s-edge-2'),
        (19, 'Gigaflare 2', 'p7-gigaflare-s-edge-2'),
        (21, 'Akh Morn 3', 'p7-akh-morn-s-edge-3'),
    ],
}
ABILITY = {
    'Rep': 'Reprisal', 'Expedient': 'Expedient', 'Seraph': 'Summon Seraph',
    'EukProg': 'Eukrasian Prognosis', 'ZoeEukProg': 'Zoe + Eukrasian Prognosis',
    'ZoeEukrpog': 'Zoe + Eukrasian Prognosis', 'ZoeProg': 'Zoe + Eukrasian Prognosis',
    'Neutral': 'Neutral Sect', 'Horo': 'Horoscope', 'Soil': 'Sacred Soil',
    'CU': 'Collective Unconscious', 'Spread-Lo': 'Deployment Tactics',
    'Spreadlo': 'Deployment Tactics', 'Bell': 'Liturgy of the Bell',
    'Macro': 'Macrocosmos', 'Fey Illum': 'Fey Illumination',
    'Fey Ilum': 'Fey Illumination', 'Physis': 'Physis II',
    'Thrill': 'Thrill of Battle', 'Shadowwall': 'Shadow Wall',
    'TBN': 'The Blackest Night', 'Nascent': 'Nascent Flash',
    'HOC': 'Heart of Corundum', 'HoC': 'Heart of Corundum',
    'Heart of Corrundum': 'Heart of Corundum', 'Sheltron': 'Holy Sheltron',
    'Camoflauge': 'Camouflage', 'Camoflauce': 'Camouflage',
    'Sentinal': 'Sentinel', 'Bulward': 'Bulwark',
    'Rerprisal': 'Reprisal', 'Equalibrium': 'Equilibrium',
}
KNOWN = set(json.loads((ROOT / 'packages/encounter-data/abilities.json').read_text())['names']) | {'Nebula', 'Equilibrium'}
PAIRS = ['WARDRK', 'WARGNB', 'WARPLD', 'GNBDRK', 'GNBPLD', 'PLDDRK']
TANK_ANCHORS = {
    'p2': ["Ascalon's Might 1", 'Strength of the Ward', "Ascalon's Might 2"],
    'p3': ['Soul Tether'],
    'p5': ["Ascalon's Might 1", "Ascalon's Might 2"],
    'p6': ['Wyrmsbreath 1', 'Hallowed Wing 1', 'Hallowed Wing 2', 'Wyrmsbreath 2', 'Cauterize'],
    'p7': ['Ahk Morn 1', 'Ahk Morn 2', 'Ahk Morn 3'],
}
TANK_IDS = {
    'p2': ['p2-ascalon-s-might-1', 'p2-holy-shield-bash-1', 'p2-heavenly-heel-1'],
    'p3': ['p3-soul-tether-1'],
    'p5': ['p5-heavenly-heel-1', 'p5-heavenly-heel-2'],
    'p6': ['p6-great-wyrmsbreath-1', 'p6-hallowed-wings-1', 'p6-hallowed-wings-2',
           'p6-great-wyrmsbreath-2', 'p6-cauterize-2'],
    'p7': [f'p7-akh-morn-s-edge-{i}' for i in range(1, 4)],
}


def clean(value):
    return ' '.join(value.split())


def add_note(action, text):
    if text:
        action['note'] = ' '.join(filter(None, [action.get('note'), clean(text)]))


def parse_actions(raw):
    """Read actual buttons strictly; preserve buddy scope and source qualifiers."""
    actions = []
    for line in raw.splitlines():
        line = clean(line)
        if not line:
            continue
        buddy = line.startswith('Buddy Mit:')
        if buddy:
            line = line.split(':', 1)[1].strip()
        line = line.replace('Rampart Thrill', 'Rampart, Thrill')
        for token in re.split(r'[,/]', line):
            token = token.strip().lstrip('*')
            notes = re.findall(r'\(([^)]+)\)', token)
            token = re.sub(r'\s*\([^)]*\)', '', token).strip()
            expanded = ABILITY.get(token, token).split(' + ')
            for name in expanded:
                if name not in KNOWN:
                    raise ValueError(f'Unknown DSR action {name!r} in {raw!r}')
                action = {'name': name}
                for note in notes:
                    add_note(action, note)
                if buddy:
                    action['buddy'] = True
                    add_note(action, 'On your co-tank.')
                actions.append(action)
    return actions


def party_actions(raw):
    personal = re.fullmatch(r'Personals on Melee ([12])', clean(raw))
    if personal:
        return [{'name': 'Buddy Mit', 'buddy': True, 'note': f'On M{personal[1]}.'},
                {'name': 'Oblation (DRK)', 'buddy': True, 'note': f'On M{personal[1]}.'}]
    if clean(raw) == '*Can Feint Hallowed Plume':
        return [{'name': 'Feint', 'note': 'Optional; use on Hallowed Plume.'}]
    return parse_actions(raw)


def continuation(actions, raw):
    """The second grid line can contain an extra button or a scoped note."""
    text = clean(raw)
    if not text:
        return
    if text == 'Rep':
        actions.extend(parse_actions(text))
    elif text in ['(Spreadlo Optional)', '(Holos Optional)']:
        name = 'Deployment Tactics' if 'Spreadlo' in text else 'Holos'
        actions.append({'name': name, 'note': f'{name} is optional.'})
    elif text in ['2nd GCD Soil', '2nd GCD Kerachole', 'Early Soil (After 2nd Melee Auto)',
                  'Early Kera (After 2nd Melee Auto)']:
        name = 'Sacred Soil' if 'Soil' in text else 'Kerachole'
        matching = next((a for a in actions if a['name'] == name), None)
        if matching is None:
            matching = {'name': name}
            actions.append(matching)
        add_note(matching, f'Use {name} on the second GCD.' if text.startswith('2nd')
                 else f'Use {name} early, after the second melee auto.')
    elif text == '(Single Target Shield Rot Melee)':
        actions.append({'name': 'Adloquium' if any(a['name'] == 'Succor' for a in actions) else 'Eukrasian Diagnosis',
                        'note': 'Single-target shield on the melee with Mortal Vow.'})
    elif text == '(Early)':
        for action in actions:
            add_note(action, 'Use early.')
    else:
        raise ValueError(f'Unreviewed continuation {raw!r}')


def validate_party_rows(tab, cells, bindings):
    # Phase ownership comes from the workbook section above a row, not
    # FFLogs' transition labels. In particular, Final Chorus closes P2.
    headers = sorted((int(ref[1:]), 'rewind' if value.startswith('Rewind') else 'p' + value[1])
                     for ref, value in cells.items()
                     if re.fullmatch(r'D\d+', ref) and re.match(r'^(P[2-7]:|Rewind)', value))
    for row, _, anchor in bindings:
        phase = next((pid for header, pid in reversed(headers) if header < row), None)
        if phase != anchor.split('-')[0]:
            raise ValueError(f'{tab}/B{row}: source phase {phase} does not match {anchor}')
    expected = {row: title for row, title, _ in bindings}
    if tab == 'NidhoggEyes':
        expected.update({row + 974: expected[row] for row in [999, 1001, 1003, 1005]})
    if tab == 'RewindDark Thordan':
        expected[39] = 'Notes'
    if tab in ['Double Dragons', 'Dragon King Thordan']:
        expected.update(dict(zip(range(1004, 1015, 2), [
            'Cosmo Memory', 'Cosmo Dive 1', 'Wave Cannon 1', 'Wave Cannon 2', 'Cosmo Dive 2', 'Cosmo Meteor'])))
    actual = {int(ref[1:]): clean(value) for ref, value in cells.items()
              if re.fullmatch(r'B\d+', ref) and clean(value)}
    if actual != expected:
        raise ValueError(f'{tab}: mechanic rows changed; review the workbook layout')


def import_tanks(archive, encounter):
    strings = workbook.shared_strings(archive)
    mechanics = {m['id']: m for p in encounter['phases'] for m in p['mechanics']}
    plans = []
    for tab in PAIRS:
        cells, _ = read_cells(archive, strings, workbook.worksheet(archive, tab))
        headers = sorted((int(ref[1:]), 'p' + value.strip()[1]) for ref, value in cells.items()
                         if re.fullmatch(r'C\d+', ref) and re.match(r'^P[23567]:', value.strip()))
        if [pid for _, pid in headers] != list(TANK_ANCHORS):
            raise ValueError(f'{tab}: tank phase headers changed')
        for col, job, other in [('C', tab[:3], tab[3:]), ('G', tab[3:], tab[:3])]:
            plan = {'job': job, 'with': other, 'phases': []}
            for hi, (header, pid) in enumerate(headers):
                # Stop at the next phase; for P7 stop after its three real rows.
                end = headers[hi + 1][0] if hi + 1 < len(headers) else header + 17
                rows = sorted(int(ref[1:]) for ref, value in cells.items()
                              if re.fullmatch(r'B\d+', ref) and header < int(ref[1:]) < end
                              and clean(value) != 'Notes')
                expected = TANK_ANCHORS[pid]
                actual = [clean(cells[f'B{r}']).replace('Wymsbreath', 'Wyrmsbreath') for r in rows]
                if actual != expected:
                    raise ValueError(f'{tab}/{pid}: expected {expected}, got {actual}')
                note_row = next((r for r in range(rows[-1] + 1, end)
                                 if cells.get(f'B{r}') == 'Notes'), None)
                note = ' '.join(clean(cells.get(f'{col}{r}', '')) for r in range(note_row or end, end)).strip()
                # Two PLD columns have a copied GNB cooldown name. The same
                # row explicitly assigns Sentinel; preserve the timing for it.
                if job == 'PLD':
                    note = note.replace('Nebula', 'Sentinel')
                phase = {'id': pid, 'mechanics': []}
                if note and pid == 'p3':
                    phase['note'] = note.lstrip('*')
                for row, anchor in zip(rows, TANK_IDS[pid]):
                    raw = '\n'.join(filter(None, [cells.get(f'{col}{row}', ''), cells.get(f'{col}{row+1}', '')]))
                    actions = parse_actions(raw)
                    # A cell's parenthetical target applies to the whole run.
                    target = re.search(r'\(Take (Heel|Slashes)\)', raw)
                    if target:
                        for action in actions:
                            if not action.get('buddy') and 'Take ' not in action.get('note', ''):
                                add_note(action, 'Take ' + target[1])
                    if not actions:
                        continue
                    m = mechanics[anchor]
                    phase['mechanics'].append({'id': anchor + '-personal', 'after': anchor,
                                               'name': m['name'], 'actions': actions})
                if note and pid != 'p3':
                    anchor = {'p2': TANK_IDS['p2'][0], 'p5': TANK_IDS['p5'][1],
                              'p6': TANK_IDS['p6'][3], 'p7': TANK_IDS['p7'][0]}[pid]
                    target_row = next((m for m in phase['mechanics'] if m['after'] == anchor), None)
                    if target_row is None:
                        raise ValueError(f'{tab}/{job}/{pid}: note has no assigned mechanic')
                    # The shared P5 mechanic already carries the healer directive.
                    scoped = note.lstrip('*').replace('Camoflauge', 'Camouflage')
                    if pid == 'p5':
                        scoped = scoped.replace('Healers need to mit tanks for 2nd buster', '').strip()
                    if scoped:
                        target_row['note'] = scoped
                plan['phases'].append(phase)
            plans.append(plan)
    return {'note': 'Tank personal plans follow the selected job pairing. Coordinate the indicated Heel, Slashes, and invulnerability duties with your co-tank.',
            'plans': plans}


def convert(archive=None):
    archive = archive or workbook.fetch(SHEET_ID)
    strings = workbook.shared_strings(archive)
    encounter = load_encounter('dsr')
    mechanics = {m['id']: m for p in encounter['phases'] for m in p['mechanics']}
    phases = {p['id']: {'id': p['id'], 'mechanics': []} for p in encounter['phases']}
    for tab, bindings in PARTY.items():
        cells, _ = read_cells(archive, strings, workbook.worksheet(archive, tab))
        validate_party_rows(tab, cells, bindings)
        for row, title, anchor in bindings:
            if clean(cells.get(f'B{row}', '')) != title:
                raise ValueError(f'{tab}/B{row}: expected {title!r}')
            assignments = {}
            for col, slot in COLUMNS.items():
                actions = party_actions(cells.get(f'{col}{row}', ''))
                continuation(actions, cells.get(f'{col}{row+1}', ''))
                if actions:
                    assignments[slot] = actions
            for slot, name in extras(cells.get(f'M{row}', '')):
                assignments.setdefault(slot, []).append({'name': name})
            phase = phases[anchor.split('-')[0]]
            phase['mechanics'].append({'id': anchor, 'name': mechanics[anchor]['name'], 'assignments': assignments})
        if tab == 'NidhoggEyes':
            # The second Eyes block is a duplicate template, not another phase.
            for original in [999, 1001, 1003, 1005]:
                for col in ['B', *COLUMNS, 'M']:
                    first = clean(cells.get(f'{col}{original}', '')).replace(' (early)', '')
                    second = clean(cells.get(f'{col}{original+974}', ''))
                    if first != second:
                        raise ValueError('Duplicate Eyes block changed; review before importing')
        if tab == 'RewindDark Thordan':
            if clean(cells.get('C39', '')) != 'M1 Feint 2nd Heavenly Heel':
                raise ValueError('Dark Thordan Feint note changed')
            if clean(cells.get('C40', '')) != 'Healers need to mit tanks for 2nd buster':
                raise ValueError('Dark Thordan healer note changed')
            m = mechanics['p5-heavenly-heel-2']
            phases['p5']['mechanics'].append({'id': m['id'], 'name': m['name'],
                'note': 'Healers need to mitigate tanks for this buster.',
                'assignments': {'M1': [{'name': 'Feint'}],
                                **{job: [{'name': 'Assist Tanks'}] for job in HEALERS}}})
    phases['p2']['note'] = 'Times start at the Thordan checkpoint. This sheet does not assign the P1 door boss.'
    phases['rewind']['note'] = 'Brightwing bait order: healers, melee, ranged, tanks. Use the assigned shields before the first bait.'
    sheet = {'id': 'dsrmitty', 'fightId': 'dsr', 'name': 'DSR Mitty',
             'author': 'Malachite Laurent', 'updated': '2026-09-17',
             'source': {'name': 'DSR Mitty spreadsheet', 'url': SOURCE},
             'description': 'Party mitigation and all six tank pairings, from the Thordan checkpoint through Dragon King Thordan.',
             'slots': [{'id': slot, 'role': ROLES[slot], **({'job': slot} if slot in HEALERS else {})}
                       for slot in COLUMNS.values()], 'phases': list(phases.values())}
    sheet = bind_sheet(sheet, encounter)
    sheet['tankMits'] = import_tanks(archive, encounter)
    snap_tank_times(sheet, encounter)
    output = ROOT / 'packages/encounter-data/fights/dsr/sheets/dsrmitty.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(sheet, indent=2, ensure_ascii=False) + '\n')
    print([(p['id'], len(p['mechanics']), sum(len(a) for m in p['mechanics'] for a in m['assignments'].values()))
           for p in sheet['phases']])
    return sheet


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--xlsx', type=Path)
    args = parser.parse_args()
    convert(zipfile.ZipFile(args.xlsx) if args.xlsx else None)
