"""Convert Malachite Laurent's TOP party-mit workbook into reviewed repo JSON.

Usage: python3 scripts/import_top_topmitty.py '/path/to/TOP Mitty.xlsx'
Uses Python's standard library. The site never reads Excel at runtime.

Scope: the five party-wide mitigation grids (Beetle / MF / Final Omega /
Dynamis / Alpha Omega), plus the six per-tank-job pairing tabs (WARDRK,
GNBPLD, ...) which become `tankMits` -- personal mit per tank per co-tank,
shown below the party view. Side notes, images, and video links are not
imported. Tank 1 / Tank 2 become the seats T1 / T2 in the party grid --
there is no MT / OT split here.
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

# Per-pairing tabs -> (job A, job B, worksheet number). Column C is job A,
# column G is job B; each tab yields two plans (A paired with B, B with A).
TANK_TABS = [('WAR', 'DRK', 7), ('WAR', 'GNB', 8), ('WAR', 'PLD', 9),
             ('GNB', 'DRK', 10), ('GNB', 'PLD', 11), ('PLD', 'DRK', 12)]
TANK_FULLNAME = {'WARRIOR': 'WAR', 'DARK KNIGHT': 'DRK', 'GUNBREAKER': 'GNB', 'PALADIN': 'PLD'}

# The pairing tabs write mit in shorthand and with a few typos; expand to the
# in-game action name so the text reads on its own and fetch_icons can resolve
# an icon. Names already spelled the game's way pass through untouched.
# "Kitchen Sink" (press your whole kit) stays as written - a decision, not a
# single button, like "Party Mit (GNB/DRK)" in the party grid.
TANK_ABILITY = {
    'Thril': 'Thrill of Battle', 'Thrill': 'Thrill of Battle', 'Vengence': 'Vengeance',
    'Bolide': 'Superbolide', 'Camo': 'Camouflage', 'HOC': 'Heart of Corundum',
    'Nebula': 'Great Nebula', 'TBN': 'The Blackest Night', 'Sheltron': 'Holy Sheltron',
    'Sentinal': 'Sentinel', 'Nascent': 'Nascent Flash', 'Intervention': 'Intervention',
}

# The one ally-targeted mitigation each tank brings ("Buddy Mit" with no skill
# named means this one). "Buddy Mit: <skill>" names it explicitly.
# DRK brings two ally-targetable mits and the sheet means both; the rest bring one.
TANK_BUDDY = {'WAR': 'Nascent Flash', 'PLD': 'Intervention',
              'GNB': 'Heart of Corundum', 'DRK': ['The Blackest Night', 'Oblation']}

# "Kitchen Sink" means press the whole personal-mit kit. Raid mitigation only,
# level 100 - invulns (Holmgang / Hallowed Ground / Living Dead / Superbolide)
# are their own line in the sheet, not part of the sink.
TANK_EVERYTHING = {
    'WAR': ['Rampart', 'Vengeance', 'Thrill of Battle', 'Bloodwhetting'],
    'PLD': ['Rampart', 'Sentinel', 'Holy Sheltron', 'Bulwark'],
    'DRK': ['Rampart', 'Shadow Wall', 'Dark Mind', 'The Blackest Night', 'Oblation'],
    'GNB': ['Rampart', 'Great Nebula', 'Camouflage', 'Heart of Corundum'],
}

# Tank-tab phase headers sit in column C: "P1: Beetle Omega", "P5: Dynamis".
TANK_PHASE = re.compile(r'^P(\d):')

# Where each personal-mit row lands in the party-mit timeline: phase -> personal
# mechanic name -> the party mechanic it renders *below* (None = phase top).
# Hand-mapped against the party grid; re-check when either sheet's rows move.
PERSONAL_ANCHOR = {
    'p1': {'Prepull': None, 'Diffuse Wave Cannon': 'Stack 4'},
    'p2': {'Solar Ray': None, 'Tank Tethers': 'Party Synergy'},
    'p3': {'Patch 1': '1st Patch Set', 'Patch 2': '2nd Patch Set',
           'Patch 3': '3rd Patch Set', 'Patch 4': '4th Patch Set',
           'Critical Error': 'Critical Error', 'Monitors': 'Critical Error'},
    'p5': {'Delta Solar Ray': None, 'Sigma Solar Ray': 'Delta Mech',
           'Omega Solar Ray': 'Sigma Mech', 'Final Buster': 'Omega Mech'},
    'p6': {'Cosmo Dive 1': 'Cosmo Dive 1', 'Wave Cannon 1': 'Wave Cannon 1',
           'Wave Cannon 2': 'Wave Cannon 2', 'Cosmo Dive 2': 'Cosmo Dive 2'},
}

# How each phase's "Notes" row is placed:
#   ('mechanic', name)  -> becomes that personal row's aside (folded in)
#   ('alt', name)       -> "<label>: <abilities> on X" -> a labelled alt line
#   ('row', partyName)  -> a standalone personal note row after that party row
PERSONAL_NOTE = {
    'p1': ('mechanic', 'Diffuse Wave Cannon'),
    'p2': ('alt', 'Solar Ray'),
    'p3': ('row', 'Hello World'),
    'p5': ('mechanic', 'Sigma Solar Ray'),
}

# P4 Blue Screen is invuln-note only and has no party grid - skip it.
DROP_TANK_PHASES = {'p4'}

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


def read_cells(archive, strings, worksheet):
    # Flatten one worksheet to {cell ref: text}, plus the highest row seen.
    root = ET.fromstring(archive.read(f'xl/worksheets/sheet{worksheet}.xml'))
    cells, maxrow = {}, 0
    for cell in root.findall('.//s:sheetData/s:row/s:c', NS):
        value = cell.find('s:v', NS)
        if value is None or not value.text:
            continue
        ref = cell.get('r')
        cells[ref] = strings[int(value.text)] if cell.get('t') == 's' else value.text
        maxrow = max(maxrow, int(re.sub(r'\D', '', ref)))
    return cells, maxrow


def buddy_actions(text, job):
    # "Buddy Mit" / "Buddy Mit: <skill>" -> the ally-targeted mit(s), flagged so
    # the site renders them small and inline, not as a primary press. A job may
    # bring more than one (DRK: TBN + Oblation).
    match = re.match(r'^Buddy Mit(?::\s*(.+))?$', str(text).strip())
    if not match:
        return None
    skill = match.group(1)
    if skill:
        names = [TANK_ABILITY.get(skill.strip(), skill.strip())]
    else:
        default = TANK_BUDDY.get(job)
        names = default if isinstance(default, list) else [default] if default else []
    return [{'name': n, 'buddy': True} for n in names] or None


def tank_actions(raw, job):
    # Pairing-tab cells list mit comma-separated ("Rampart, Camo, HOC"); "+" and
    # "/" also mean "press both". A trailing "(...)" is a when-note kept on the
    # action, so expand the word before it, not the whole string.
    out = []
    for line in str(raw).splitlines():
        buddy = buddy_actions(line, job)
        if buddy:
            out.extend(buddy)
            continue
        for part in re.split(r'[,+/]', line):
            part = clean(part)
            if not part:
                continue
            base, suffix = re.match(r'^(.*?)\s*(\([^)]*\))?$', part).groups()
            base = base.strip()
            if base == 'Kitchen Sink' and job in TANK_EVERYTHING:
                out.extend({'name': n} for n in TANK_EVERYTHING[job])
                continue
            name = TANK_ABILITY.get(base, base)
            out.append({'name': f'{name} {suffix}' if suffix else name})
    return out


def place_personal(plan, party_phases):
    # Splice each personal row into the party timeline: resolve its `after`
    # anchor and fold the phase "Notes" row where PERSONAL_NOTE says.
    name_to_id = {p['id']: {m['name']: m['id'] for m in reversed(p['mechanics'])}
                  for p in party_phases}
    kept = []
    for phase in plan['phases']:
        pid = phase['id']
        if pid in DROP_TANK_PHASES:
            continue
        ids = name_to_id.get(pid, {})
        anchors = PERSONAL_ANCHOR.get(pid, {})
        by_name = {m['name']: m for m in phase['mechanics']}
        for mechanic in phase['mechanics']:
            if mechanic['name'] not in anchors:
                raise SystemExit(f"unmapped personal mechanic {pid}/{mechanic['name']!r} "
                                 f"in {plan['job']}+{plan['with']} - add it to PERSONAL_ANCHOR")
            target = anchors[mechanic['name']]
            if target:
                mechanic['after'] = ids[target]
        note = phase.pop('note', None)
        directive = PERSONAL_NOTE.get(pid)
        if note and directive:
            kind, where = directive
            if kind == 'row':
                phase['note'], phase['noteAfter'] = note, ids[where]
            elif kind == 'mechanic':
                host = by_name.get(where)
                if host is None:  # combo has no such row - keep the note as its own
                    host = {'id': f"{plan['job']}{plan['with']}-{pid}-note".lower(),
                            'name': where, 'actions': []}
                    if anchors.get(where):
                        host['after'] = ids[anchors[where]]
                    phase['mechanics'].append(host)
                host['note'] = note
            elif kind == 'alt':
                match = re.match(r'^(?P<label>.+?):\s*(?P<abilities>.+?)\s+on\s+.+$', note)
                host = by_name[where]
                if match:
                    host.setdefault('alts', []).append(
                        {'label': match['label'].strip(),
                         'actions': tank_actions(match['abilities'], plan['job'])})
                else:
                    host['note'] = note
        elif note:
            phase['note'] = note
        if phase['mechanics'] or phase.get('note'):
            kept.append(phase)
    plan['phases'] = kept
    return plan


def convert_tank_tabs(archive, strings, party_phases):
    # Each pairing tab is two stacked columns (C = job A, G = job B) of the same
    # phase blocks. Turn it into two plans: A-with-B reads column C, B-with-A
    # reads column G. The plan changes with the co-tank -- buddy-mit targets and
    # invuln order do.
    plans = []
    for job_a, job_b, worksheet in TANK_TABS:
        cells, maxrow = read_cells(archive, strings, worksheet)
        headers = sorted((int(ref[1:]), TANK_PHASE.match(str(val)).group(1))
                         for ref, val in cells.items()
                         if ref.startswith('C') and ref[1:].isdigit() and TANK_PHASE.match(str(val)))
        phases_a, phases_b = [], []
        for index, (header_row, number) in enumerate(headers):
            end = headers[index + 1][0] if index + 1 < len(headers) else maxrow + 1
            phase_id = f'p{number}'
            job_row = next((r for r in range(header_row + 1, end)
                            if str(cells.get(f'C{r}', '')).strip().upper() in TANK_FULLNAME), None)
            if job_row is None:
                continue
            phase_a = {'id': phase_id, 'mechanics': []}
            phase_b = {'id': phase_id, 'mechanics': []}
            current_a = current_b = None
            for row in range(job_row + 1, end):
                title = str(cells.get(f'B{row}', '')).strip()
                c_raw, g_raw = cells.get(f'C{row}', ''), cells.get(f'G{row}', '')
                if title == 'Notes':
                    if c_raw:
                        phase_a['note'] = clean(c_raw)
                    if g_raw:
                        phase_b['note'] = clean(g_raw)
                    break
                if title:
                    current_a = {'id': f'{job_a}{job_b}-{phase_id}-r{row}'.lower(),
                                 'name': clean(title), 'actions': tank_actions(c_raw, job_a)}
                    current_b = {'id': f'{job_b}{job_a}-{phase_id}-r{row}'.lower(),
                                 'name': clean(title), 'actions': tank_actions(g_raw, job_b)}
                    if current_a['actions']:
                        phase_a['mechanics'].append(current_a)
                    if current_b['actions']:
                        phase_b['mechanics'].append(current_b)
                else:
                    # A sub-row under a mechanic: a "Buddy Mit: ..." line becomes
                    # a flagged buddy action on it, anything else a note on the
                    # last action.
                    for raw, job, current, phase in (
                        (c_raw, job_a, current_a, phase_a), (g_raw, job_b, current_b, phase_b)
                    ):
                        if not raw or not current:
                            continue
                        buddy = buddy_actions(raw, job)
                        if buddy:
                            current['actions'].extend(buddy)
                            if not any(m is current for m in phase['mechanics']):
                                phase['mechanics'].append(current)
                        elif current['actions']:
                            current['actions'][-1].setdefault('note', clean(raw))
            phases_a.append(phase_a)
            phases_b.append(phase_b)
        plans.append(place_personal({'job': job_a, 'with': job_b, 'phases': phases_a}, party_phases))
        plans.append(place_personal({'job': job_b, 'with': job_a, 'phases': phases_b}, party_phases))
    return {'plans': plans}


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
    sheet['tankMits'] = convert_tank_tabs(archive, strings, sheet['phases'])
    output = Path(__file__).resolve().parents[1] / 'data/fights/top'
    output.mkdir(parents=True, exist_ok=True)
    for filename, data in [('fight.json', FIGHT), ('topmitty.json', sheet)]:
        (output / filename).write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
    print([(p['id'], len(p['mechanics']),
            sum(len(a) for m in p['mechanics'] for a in m['assignments'].values())) for p in sheet['phases']])
    print([(f"{p['job']}+{p['with']}", sum(len(m['actions']) for ph in p['phases'] for m in ph['mechanics']))
           for p in sheet['tankMits']['plans']])


if __name__ == '__main__':
    convert(sys.argv[1])
