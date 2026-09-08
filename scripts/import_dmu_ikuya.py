"""Convert the Ikuya DMU P1–P5 workbook tabs, plus the Omnitank tab (tank
personal-mit -> `tankMits`), into reviewed repo JSON.

Usage: python3 scripts/import_dmu_ikuya.py '/path/to/Ikuya Mitty (DMU).xlsx'
Uses Python's standard library. The site never reads Excel at runtime.
"""
import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
COLUMNS = {'F': 'MT', 'H': 'OT', 'J': 'WHM', 'L': 'AST', 'N': 'SCH', 'P': 'SGE', 'R': 'M1', 'T': 'M2', 'V': 'P', 'X': 'C'}
HEALERS = ['WHM', 'AST', 'SCH', 'SGE']
# Which jobs may stand in each slot. Healer slots name a job outright; the tank
# and DPS slots are positions, so the viewer picks the job themselves -- but each
# DPS slot only admits jobs of its kind (M1/M2 melee, P ranged, C caster).
ROLES = {'MT': 'tank', 'OT': 'tank', 'M1': 'melee', 'M2': 'melee', 'P': 'ranged', 'C': 'caster',
         **{job: 'healer' for job in HEALERS}}
MARKERS = '⁰¹²³⁴⁵⁶⁷⁸⁹'
MARKER = rf'[{MARKERS}]+'
PHASE_NAMES = ['Kefka', 'Forsaken Kefka', 'Exdeath & Chaos', 'Kefka Says', 'Kefka Reimagined']


def clean(value):
    # Correct spelling errors only; preserve the source's terminology.
    for typo, corrected in {'Serpah': 'Seraph', 'Illumuniation': 'Illumination', 'Scared Soil': 'Sacred Soil', 'Embrance': 'Embrace'}.items():
        value = value.replace(typo, corrected)
    return ' '.join(value.split())


def add_note(action, note):
    note = clean(note)
    if note and note not in action.get('note', ''):
        action['note'] = (action.get('note', '') + ' ' + note).strip()


def column_number(column):
    result = 0
    for c in column:
        result = result * 26 + ord(c) - 64
    return result


# Omnitank tab -> tankMits. Two assignment columns per row. P1/P2/P4 columns are
# MT / OT (rows get a `seat`); P3/P5 columns are a job-priority order, and for a
# pairing the tank higher in PRIO_ORDER reads the left column. Every ordered pair
# of the four tanks is one plan. Cells use shorthand, expanded per job below.

TANKS = ['PLD', 'WAR', 'DRK', 'GNB']
PRIO_ORDER = ['WAR', 'DRK', 'GNB', 'PLD']  # left-header order, same in P3 and P5

INVULN = {'WAR': 'Holmgang', 'PLD': 'Hallowed Ground', 'DRK': 'Living Dead', 'GNB': 'Superbolide'}
MIT_40 = {'WAR': 'Damnation', 'PLD': 'Guardian', 'DRK': 'Shadowed Vigil', 'GNB': 'Great Nebula'}
MIT_90 = {'WAR': 'Thrill of Battle', 'PLD': 'Bulwark', 'DRK': 'Dark Mind', 'GNB': 'Camouflage'}
SHORT_MIT = {'WAR': 'Nascent Flash', 'PLD': 'Holy Sheltron', 'DRK': 'Oblation', 'GNB': 'Heart of Corundum'}
SHORTHAND = {'Invulnerability': INVULN, '40%': MIT_40, '90s': MIT_90, 'Short Mit': SHORT_MIT, 'Short': SHORT_MIT}
BUDDY_MIT = {'WAR': ['Nascent Flash'], 'PLD': ['Intervention'], 'DRK': ['The Blackest Night', 'Oblation'], 'GNB': ['Heart of Corundum']}
# Rampart + 40% + 90s + short mit, pressed together. The short-mit slot is the
# personal button, not the ally-targeted one SHORT_MIT names for the "Short Mit"
# shorthand: WAR spends Bloodwhetting here, not Nascent Flash. DRK also adds TBN.
KITCHEN_SINK_SHORT = dict(SHORT_MIT, WAR='Bloodwhetting')
KITCHEN_SINK = {job: ['Rampart', MIT_40[job], MIT_90[job], KITCHEN_SINK_SHORT[job]] for job in TANKS}
KITCHEN_SINK['DRK'].append('The Blackest Night')
KNOWN_TOKENS = {'Kitchen Sink', 'Buddy Mit', 'Rampart', 'Invulnerability', '40%', '90s', 'Short Mit', 'Short', 'Provoke'}

# phase -> (data rows, mode). Left column is E, right is I, time D.
OMNI_BLOCKS = [
    (1, [8, 10, 12, 14], 'seat'),
    (2, [27, 29, 31], 'seat'),
    (3, [45, 47, 49, 51, 53, 55], 'prio'),
    (4, [69], 'seat'),
    (5, [81, 83, 85, 87, 89, 91, 93, 95, 97, 99], 'prio'),
]


def omni_seconds(value):
    """Seconds from an Omnitank D-cell: a stored time fraction, or '12:13+'."""
    try:
        return round(float(value) * 1440)
    except (TypeError, ValueError):
        match = re.search(r'(\d+):(\d+)', str(value))
        return int(match.group(1)) * 60 + int(match.group(2)) if match else 0


def expand_token(name, job, carry):
    """One shorthand token -> a list of action dicts for this job."""
    if name.startswith('Provoke'):
        action = {'name': 'Provoke'}
        rest = name[len('Provoke'):].strip()
        if rest:
            action['note'] = rest.rstrip('.') + '.'
        if carry:
            action['carryOver'] = True
        return [action]
    if name == 'Kitchen Sink':
        names, buddy = KITCHEN_SINK[job], False
    elif name == 'Buddy Mit':
        names, buddy = BUDDY_MIT[job], True
    elif name in SHORTHAND:
        names, buddy = [SHORTHAND[name][job]], False
    else:
        names, buddy = [name], False  # Rampart, or a literal
    out = []
    for ability in names:
        action = {'name': ability}
        if buddy:
            action['buddy'] = True
        if carry:
            action['carryOver'] = True
        out.append(action)
    return out


def parse_omni_cell(text, job, notes):
    """Cell text -> (actions, extra_notes). '➔' lines carry over. A bare label
    line and a '(Solo/Close/Far)' suffix become notes. A '(PLD/DRK)' suffix
    scopes its token to those jobs."""
    actions, extra = [], []
    for raw_line in text.split('\n'):
        line = raw_line.strip()
        if not line:
            continue
        carry = '➔' in line
        line = line.replace('➔', '').strip()
        tokens = [t.strip() for t in line.split('+') if t.strip()]
        cleaned = []
        for token in tokens:
            suffix = re.search(r'\(([^)]+)\)\s*$', token)
            scope = None
            if suffix:
                tag = suffix.group(1)
                if tag in ('Solo', 'Close', 'Far'):
                    extra.append({'Solo': 'Solo this hit.', 'Close': 'Close.', 'Far': 'Far.'}[tag])
                    token = token[:suffix.start()].strip()
                elif re.match(r'^[A-Z]{3}(/[A-Z]{3})*$', tag):
                    scope = tag.split('/')
                    token = token[:suffix.start()].strip()
            markers = re.findall(MARKER, token)
            base = clean(re.sub(MARKER, '', token))
            cleaned.append((base, markers, scope))
        recognised = [c for c in cleaned if c[0] in KNOWN_TOKENS or c[0].startswith('Provoke')]
        if not recognised and len(cleaned) == 1 and cleaned[0][0]:
            label = cleaned[0][0]
            extra.append(label if label.endswith('.') else label + '.')
            continue
        for base, markers, scope in cleaned:
            if not base:
                continue
            if base not in KNOWN_TOKENS and not base.startswith('Provoke'):
                raise ValueError(f'Unknown Omnitank token {base!r} in cell {text!r}')
            if scope and job not in scope:
                continue
            for action in expand_token(base, job, carry):
                for marker in markers:
                    if marker in notes:
                        add_note(action, notes[marker])
                actions.append(action)
    return actions, extra


def convert_omnitank(archive, strings, party_phases, phase_starts):
    root = ET.fromstring(archive.read('xl/worksheets/sheet15.xml'))
    cells = {}
    for cell in root.findall('.//s:sheetData/s:row/s:c', NS):
        value = cell.find('s:v', NS)
        if value is None or not value.text:
            continue
        cells[cell.get('r')] = strings[int(value.text)] if cell.get('t') == 's' else value.text

    # Footnotes: one dict per phase block, keyed by superscript marker.
    block_notes = {}
    for phase_number, rows, _ in OMNI_BLOCKS:
        raw = cells.get(f'D{rows[-1] + 2}', '')
        block_notes[phase_number] = {m[0]: clean(m[1]) for m in re.findall(rf'({MARKER})\s+(.*?)(?=\n{MARKER}\s|$)', raw, re.S)}

    def party_lookup(phase_number):
        mechs = party_phases[phase_number - 1]['mechanics']
        timed = [(m['id'], m['name'], clock_seconds(m['time'])) for m in mechs if 'time' in m]
        return timed

    def anchor_for(timed, rel):
        chosen = None
        for mid, name, secs in timed:
            if secs <= rel:
                chosen = (mid, name)
        return chosen

    plans = []
    for job in TANKS:
        for other in TANKS:
            if job == other:
                continue
            higher = PRIO_ORDER.index(job) < PRIO_ORDER.index(other)
            phases_out = []
            for phase_number, rows, mode in OMNI_BLOCKS:
                start = phase_starts[phase_number - 1]
                timed = party_lookup(phase_number)
                notes = block_notes[phase_number]
                out_mechs = []
                for row in rows:
                    title = cells.get(f'B{row}', '')
                    name = clean(re.sub(MARKER, '', title))
                    title_markers = re.findall(MARKER, title)
                    rel = max(0, omni_seconds(cells.get(f'D{row}')) - start)
                    rel_str = f'{rel // 60}:{rel % 60:02}'
                    anchor = anchor_for(timed, rel)
                    seats = [('MT', 'E'), ('OT', 'I')] if mode == 'seat' else \
                            [(None, 'E' if higher else 'I')]
                    for seat, column in seats:
                        actions, extra = parse_omni_cell(cells.get(f'{column}{row}', ''), job, notes)
                        note_parts = [notes[m] for m in title_markers if m in notes] + extra
                        alts = omni_alt(phase_number, row, seat, job)
                        same = bool(anchor) and anchor[1] == name
                        # Drop an empty row that only repeats a party mechanic
                        # already on the timeline; keep empty markers for busters
                        # with no party row (Revolting Ruin, Hyperdrive, Autos).
                        if same and not actions and not alts and not note_parts:
                            continue
                        collapse = same and bool(actions) and not alts
                        mid = f'{job}{other}-p{phase_number}-r{row}'.lower() + (f'-{seat.lower()}' if seat else '')
                        mech = {'id': mid, 'name': name}
                        if not collapse:
                            mech['time'] = rel_str
                        if anchor:
                            mech['after'] = anchor[0]
                        if seat:
                            mech['seat'] = seat
                        if note_parts:
                            mech['note'] = ' '.join(dict.fromkeys(note_parts))
                        mech['actions'] = actions
                        if alts:
                            mech['alts'] = alts
                        out_mechs.append(mech)
                phase_out = {'id': f'p{phase_number}', 'mechanics': out_mechs}
                if phase_number == 5 and mode == 'prio' and not higher:
                    phase_out['note'] = 'You start with the boss. Hold aggro at the phase start so your co-tank does not get the Holy debuff.'
                phases_out.append(phase_out)
            plans.append({'job': job, 'with': other, 'phases': phases_out})
    return {'plans': plans}


def omni_alt(phase_number, row, seat, job):
    """WAR's one contingency: keep the P1 invuln, spend it on the first P2
    Ultimate Embrace instead."""
    if job != 'WAR' or seat != 'MT':
        return None
    if phase_number == 1 and row == 14:
        return [{'label': 'Alt: kitchen sink', 'actions': [{'name': n} for n in KITCHEN_SINK['WAR']]}]
    if phase_number == 2 and row == 27:
        return [{'label': 'Alt: Holmgang (if saved from P1)', 'actions': [{'name': 'Holmgang'}]}]
    return None


def clock_seconds(text):
    minutes, seconds = text.split(':')
    return int(minutes) * 60 + int(seconds)


def convert(path):
    archive = zipfile.ZipFile(path)
    strings = [''.join(si.itertext()) for si in ET.fromstring(archive.read('xl/sharedStrings.xml'))]
    sheet = {
        'id': 'ikuya', 'fightId': 'dmu', 'name': 'Ikuya Mitty',
        'author': 'Ikuya Kirishima', 'updated': '2026-09-07',
        'sourceFile': Path(path).name, 'sourceVersion': '6.0 (1 Sep)',
        'source': {'name': 'Ikuya Mitty spreadsheet',
                   'url': 'https://docs.google.com/spreadsheets/d/10C3ytfH3irHqkb45rchIq5oqdAs-v_OKTj57M-Twi3k/edit'},
        'description': 'P1–P5 from Ikuya Kirishima’s mitigation plan. Choose a tank position, healer job, or DPS position.',
        'slots': [{'id': slot, **({'job': slot} if slot in HEALERS else {}), 'role': ROLES[slot]} for slot in COLUMNS.values()],
        'phases': [],
    }
    phase_starts = []
    for phase_number in range(1, 6):
        root = ET.fromstring(archive.read(f'xl/worksheets/sheet{phase_number + 5}.xml'))
        cells = {}
        for cell in root.findall('.//s:sheetData/s:row/s:c', NS):
            value = cell.find('s:v', NS)
            if value is None or not value.text:
                continue
            cells[cell.get('r')] = strings[int(value.text)] if cell.get('t') == 's' else value.text
        # D is absolute pull time, E is phase-relative; their difference on the
        # first row is when the phase starts.
        d8, e8 = cells.get('D8'), cells.get('E8')
        phase_starts.append(round(float(d8) * 1440) - round(float(e8) * 1440) if d8 and e8 else 0)
        notes_row = next(int(ref[1:]) for ref, value in cells.items() if ref.startswith('B') and value == 'Notes')
        raw_notes = cells[f'D{notes_row}']
        notes = {match[0]: clean(match[1]) for match in re.findall(rf'({MARKER})\s+(.*?)(?=\n{MARKER}\s|$)', raw_notes, re.S)}
        merged = [m.get('ref') for m in root.findall('s:mergeCells/s:mergeCell', NS)]
        mechanics = []
        for row in range(8, notes_row, 2):
            title = cells.get(f'B{row}', '')
            if not title or (phase_number == 5 and row == 30):
                continue
            title_notes = re.findall(MARKER, title)
            mechanic = {'id': f'p{phase_number}-r{row}', 'name': clean(re.sub(MARKER, '', title)), 'assignments': {}}
            time = cells.get(f'E{row}', '')
            if time:
                # Excel h:mm stores the source's m:ss display as hours/minutes.
                seconds = round(float(time) * 24 * 60)
                mechanic['time'] = f'{seconds // 60}:{seconds % 60:02}'
            for column, slot in COLUMNS.items():
                raw = cells.get(f'{column}{row}', '')
                shared = False
                vertical_carry = False
                if not raw:
                    for merge in merged:
                        start_col, start_row, end_col, end_row = re.match(r'([A-Z]+)(\d+):([A-Z]+)(\d+)', merge).groups()
                        if int(start_row) <= row <= int(end_row) and column_number(start_col) <= column_number(column) <= column_number(end_col) and start_col in COLUMNS:
                            raw = cells.get(f'{start_col}{start_row}', '')
                            shared = start_col != column
                            vertical_carry = int(start_row) < row
                            break
                if not raw or raw == 'Enrage!':
                    continue
                actions = []
                carry = False
                for line in raw.strip().splitlines():
                    line = line.strip()
                    carry = '➔' in line or vertical_carry or (line.startswith('+') and carry)
                    for part in line.replace('➔', '').split('+'):
                        markers = re.findall(MARKER, part)
                        name = clean(re.sub(MARKER, '', part))
                        if not name:
                            continue
                        action = {'name': name}
                        if carry:
                            action['carryOver'] = True
                        for marker in markers:
                            if marker not in notes:
                                raise ValueError(f'Unresolved footnote {marker} in P{phase_number} {column}{row}')
                            add_note(action, notes[marker])
                            if phase_number == 5 and marker == '¹':
                                action['noteLink'] = 'https://www.twitch.tv/kizuwah/clip/PeppyModernSamosaArsonNoSexy-s6G3BH_VonLSpdI2'
                        if phase_number == 3 and row == 38 and slot in ['MT', 'OT']:
                            add_note(action, 'Shared MT/OT assignment in the source; coordinate which tank uses Reprisal.')
                        actions.append(action)
                if actions:
                    mechanic['assignments'][slot] = actions
            # The source's checked Extras column calls for the additional raid
            # mitigation available only to RDM and MCH. Add it to every DPS
            # seat; the job qualifier makes the viewer hide it for other jobs.
            if cells.get(f'Z{row}') == '✔':
                # RDM is a caster, MCH a physical ranged - so the extra raid mit
                # only belongs on those two seats, never on melee.
                for slot in ['P', 'C']:
                    mechanic['assignments'].setdefault(slot, []).append({'name': 'Extra (RDM/MCH)'})
            if phase_number == 3 and row == 24:
                for slot in COLUMNS.values():
                    name = 'Manage Accretion healing' if slot in HEALERS else 'Avoid HP-restoring abilities'
                    mechanic['assignments'][slot] = [{'name': name, 'note': notes['⁴']}]
            # Mechanic footnotes and unnumbered timing rules belong beside the affected actions.
            for slot, actions in mechanic['assignments'].items():
                if slot in HEALERS and '¹⁰' in title_notes:
                    add_note(actions[0], notes['¹⁰'])
                if slot in HEALERS and phase_number == 5 and (row in [14, 16, 26, 28]):
                    if notes['²'] not in actions[0].get('note', ''):
                        add_note(actions[0], notes['²'])
                for action in actions:
                    name = action['name']
                    if slot in HEALERS and not action.get('carryOver') and ('Shield' in name or name == 'Spreadlo'):
                        add_note(action, 'All mechanics require shields.')
                    if phase_number == 1 and mechanic['name'].startswith('Light of Judg') and not action.get('carryOver'):
                        add_note(action, 'Use late into the castbar so it also covers Hyperdrive.')
                    if phase_number == 1 and row == 8 and name == 'Party Mit (GNB/DRK)':
                        add_note(action, 'Time this to carry over through Wave Cannon and the first Double-Trouble Trap.')
                    if phase_number == 3 and any(ability in name for ability in ['Reprisal', 'Feint', 'Addle']):
                        add_note(action, 'Target your firewalled boss while the firewall is up. Targeted mitigation mostly covers tank autos and busters in this phase, not raidwides.')
                    if phase_number == 4 and any(ability in name for ability in ['Reprisal', 'Feint', 'Addle']):
                        add_note(action, 'Targeted mitigation only works on Ultima Upsurge; other uses cover tank autos.')
                    if phase_number == 5 and row >= 32 and not action.get('carryOver'):
                        add_note(action, 'For Forsaken, use any timed mitigation as late as possible unless otherwise noted.')
                        if row == 40:
                            add_note(action, 'It is important that the new round of mitigation for the 5th hit are applied as the first round of mitigation will fall off.')
            mechanics.append(mechanic)
        sheet['phases'].append({'id': f'p{phase_number}', 'mechanics': mechanics})
    sheet['tankMits'] = convert_omnitank(archive, strings, sheet['phases'], phase_starts)
    output = Path(__file__).resolve().parents[1] / 'data/fights/dmu'
    output.mkdir(parents=True, exist_ok=True)
    fight = {'id': 'dmu', 'name': 'Dancing Mad (Ultimate)', 'shortName': 'DMU', 'type': 'Ultimate',
             'phases': [{'id': f'p{i}', 'label': f'P{i}', 'name': name,
                         'start': f'{phase_starts[i - 1] // 60}:{phase_starts[i - 1] % 60:02}'}
                        for i, name in enumerate(PHASE_NAMES, 1)]}
    for filename, data in [('fight.json', fight), ('ikuya.json', sheet)]:
        (output / filename).write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
    print([(p['id'], len(p['mechanics']), sum(len(a) for m in p['mechanics'] for a in m['assignments'].values())) for p in sheet['phases']])
    print([(f"{p['job']}+{p['with']}", sum(len(m['actions']) for ph in p['phases'] for m in ph['mechanics'])) for p in sheet['tankMits']['plans']])


if __name__ == '__main__':
    convert(sys.argv[1])
