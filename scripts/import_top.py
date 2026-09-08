"""Convert Malachite Laurent's TOP party-mit workbook into reviewed repo JSON.

Usage: python3 scripts/import_top.py '/path/to/TOP Mitty.xlsx'
Uses Python's standard library. The site never reads Excel at runtime.

Scope: the five party-wide mitigation grids (Beetle / MF / Final Omega /
Dynamis / Alpha Omega). The workbook's per-tank-job pairing tabs (WARDRK,
GNBPLD, ...) and its side notes, images, and video links are not imported.
Tank 1 / Tank 2 become the seats T1 / T2 -- there is no MT / OT split here.
"""
import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

# Grid column -> slot ID. The healer columns name a job outright; the tank and
# DPS columns are positions, so the viewer picks the job -- but each DPS column
# only admits jobs of its kind: Melee 1/2 -> M1/M2, Phys Range -> PHY, Caster ->
# CAS. 'M' (Extras) is not a slot -- see the RDM/MCH handling below.
COLUMNS = {'C': 'T1', 'D': 'T2', 'E': 'SCH', 'F': 'SGE', 'G': 'WHM', 'H': 'AST',
           'I': 'M1', 'J': 'M2', 'K': 'P', 'L': 'C'}
HEALERS = ['SCH', 'SGE', 'WHM', 'AST']
ROLES = {'T1': 'tank', 'T2': 'tank', **{j: 'healer' for j in HEALERS},
         'M1': 'melee', 'M2': 'melee', 'P': 'ranged', 'C': 'caster'}

# (phase ID, worksheet number). The workbook has no P4 Blue Screen grid.
PHASES = [('p1', 2), ('p2', 3), ('p3', 4), ('p5', 5), ('p6', 6)]

# The sheet writes healer mit in shorthand; expand to the in-game action name so
# the text reads on its own and scripts/fetch_icons.py can resolve an icon.
ABILITY = {
    'Soil': 'Sacred Soil', 'Fey': 'Fey Illumination', 'Expedience': 'Expedient',
    'Seraph': "Seraph's Veil", 'Spread-Lo': 'Deployment Tactics',
    'EukProg': 'Eukrasian Prognosis', 'Eukprog': 'Eukrasian Prognosis',
    'CU': 'Collective Unconscious', 'Star': 'Earthly Star', 'Bell': 'Liturgy of the Bell',
    'Zoe EukProg': 'Zoe + Eukrasian Prognosis',  # two buttons, so two actions
}

# "Everything" means press the whole kit. Level 90, raid-mitigation only.
EVERYTHING = {
    'SCH': ['Sacred Soil', 'Fey Illumination', 'Expedient', "Seraph's Veil",
            'Deployment Tactics', 'Whispering Dawn'],
    'SGE': ['Kerachole', 'Holos', 'Panhaima', 'Eukrasian Prognosis', 'Physis II'],
    'WHM': ['Temperance', 'Liturgy of the Bell', 'Plenary Indulgence', 'Asylum'],
    'AST': ['Collective Unconscious', 'Neutral Sect', 'Earthly Star', 'Macrocosmos', 'Horoscope'],
}

FIGHT = {
    'id': 'top', 'name': 'The Omega Protocol (Ultimate)', 'shortName': 'TOP', 'type': 'Ultimate',
    'phases': [
        {'id': 'p1', 'label': 'P1', 'name': 'Omega'},
        {'id': 'p2', 'label': 'P2', 'name': 'Omega M/F'},
        {'id': 'p3', 'label': 'P3', 'name': 'Omega Reconfigured'},
        {'id': 'p4', 'label': 'P4', 'name': 'Blue Screen'},
        {'id': 'p5', 'label': 'P5', 'name': 'Run: Dynamis'},
        {'id': 'p6', 'label': 'P6', 'name': 'Alpha Omega'},
    ],
}


def clean(value):
    value = ' '.join(str(value).split())
    # Correct the source's spelling; keep its terminology and shorthand.
    for typo, fixed in {'Pantrokrator': 'Pantokrator', 'ZoeEukProg': 'Zoe EukProg'}.items():
        value = value.replace(typo, fixed)
    # A stray number sits where P2's mechanic name belongs; the mechanic is Party Synergy.
    return 'Party Synergy' if re.fullmatch(r'\d+(\.0+)?', value) else value


def actions_from(raw, slot):
    # "/" in a cell means the same as "+": press both.
    out = []
    for line in str(raw).splitlines():
        for part in re.split(r'[+/]', line):
            name = clean(part)
            if not name:
                continue
            if name == 'Everything' and slot in EVERYTHING:
                out.extend({'name': n} for n in EVERYTHING[slot])
                continue
            expanded = ABILITY.get(name, name)
            out.extend({'name': n.strip()} for n in expanded.split('+'))
    return out


def extras(raw):
    # The Extras column is the extra raid mit only RDM (Magick Barrier) and MCH
    # (Dismantle) bring - so it lands on the caster and physical-ranged seats
    # only, never on melee. Returns (slot, action name) pairs.
    tokens = {t.strip() for t in re.split(r'[+/]', str(raw)) if t.strip()}
    out = []
    if 'Barrier' in tokens:
        out.append(('C', 'Extra (RDM)'))
    if 'Dismantle' in tokens:
        out.append(('P', 'Extra (MCH)'))
    return out


def convert(path):
    archive = zipfile.ZipFile(path)
    strings = [''.join(si.itertext()) for si in ET.fromstring(archive.read('xl/sharedStrings.xml'))]
    sheet = {
        'id': 'topmitty', 'fightId': 'top', 'name': 'TOP Mitty',
        'author': 'Malachite Laurent', 'updated': '2026-09-07',
        'sourceFile': Path(path).name,
        'source': {'name': 'TOP Mitty spreadsheet',
                   'url': 'https://docs.google.com/spreadsheets/d/1ROErvG1BhTuNvXqPGcR6ZyyhJ7uNTZdf2WzKyVj9hh4/edit'},
        'description': "Party mitigation for TOP from Malachite Laurent's plan. "
                       'Pick a tank position, a healer job, or a DPS position. '
                       'P4 Blue Screen has no party-wide assignments.',
        'slots': [{'id': slot, **({'job': slot} if slot in HEALERS else {}), 'role': ROLES[slot]}
                  for slot in COLUMNS.values()],
        'phases': [],
    }
    for phase_id, worksheet in PHASES:
        root = ET.fromstring(archive.read(f'xl/worksheets/sheet{worksheet}.xml'))
        cells = {}
        for cell in root.findall('.//s:sheetData/s:row/s:c', NS):
            value = cell.find('s:v', NS)
            if value is None or not value.text:
                continue
            cells[cell.get('r')] = strings[int(value.text)] if cell.get('t') == 's' else value.text
        header = next(int(ref[1:]) for ref, value in cells.items() if ref.startswith('C') and value == 'Tank 1')
        mechanics = []
        for row in range(header + 2, header + 200, 2):
            title = cells.get(f'B{row}', '')
            if not title or title == 'Notes' or re.match(r'^P\d+:', title):
                if title == 'Notes' or re.match(r'^P\d+:', title):
                    break
                continue
            mechanic = {'id': f'{phase_id}-r{row}', 'name': clean(title), 'assignments': {}}
            for column, slot in COLUMNS.items():
                actions = actions_from(cells.get(f'{column}{row}', ''), slot)
                note = cells.get(f'{column}{row + 1}', '')  # sub-row beneath the mechanic
                if note and actions:
                    actions[-1]['note'] = clean(note)
                if actions:
                    mechanic['assignments'][slot] = actions
            for slot, name in extras(cells.get(f'M{row}', '')):
                mechanic['assignments'].setdefault(slot, []).append({'name': name})
            mechanics.append(mechanic)
        sheet['phases'].append({'id': phase_id, 'mechanics': mechanics})
    output = Path(__file__).resolve().parents[1] / 'data/fights/top'
    output.mkdir(parents=True, exist_ok=True)
    for filename, data in [('fight.json', FIGHT), ('topmitty.json', sheet)]:
        (output / filename).write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
    print([(p['id'], len(p['mechanics']),
            sum(len(a) for m in p['mechanics'] for a in m['assignments'].values())) for p in sheet['phases']])


if __name__ == '__main__':
    convert(sys.argv[1])
