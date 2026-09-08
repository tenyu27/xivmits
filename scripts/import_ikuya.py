"""Convert only the Ikuya DMU P1–P5 workbook tabs into reviewed repo JSON.

Usage: python3 scripts/import_ikuya.py '/path/to/Ikuya Mitty (DMU).xlsx'
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
    for phase_number in range(1, 6):
        root = ET.fromstring(archive.read(f'xl/worksheets/sheet{phase_number + 5}.xml'))
        cells = {}
        for cell in root.findall('.//s:sheetData/s:row/s:c', NS):
            value = cell.find('s:v', NS)
            if value is None or not value.text:
                continue
            cells[cell.get('r')] = strings[int(value.text)] if cell.get('t') == 's' else value.text
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
    output = Path(__file__).resolve().parents[1] / 'data/fights/dmu'
    output.mkdir(parents=True, exist_ok=True)
    fight = {'id': 'dmu', 'name': 'Dancing Mad (Ultimate)', 'shortName': 'DMU', 'type': 'Ultimate', 'phases': [{'id': f'p{i}', 'label': f'P{i}', 'name': name} for i, name in enumerate(PHASE_NAMES, 1)]}
    for filename, data in [('fight.json', fight), ('ikuya.json', sheet)]:
        (output / filename).write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
    print([(p['id'], len(p['mechanics']), sum(len(a) for m in p['mechanics'] for a in m['assignments'].values())) for p in sheet['phases']])


if __name__ == '__main__':
    convert(sys.argv[1])
