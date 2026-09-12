"""Convert the "FRU Mit but Good" party-mit workbook into reviewed repo JSON.

Usage: python3 scripts/import_fru_mitbutgood.py
Uses Python's standard library. The site never reads Excel at runtime.

Scope (this pass): the five party-wide mitigation grids -- Fatebreaker /
Shiva / Gaia / Light and Dark / Pandora. The six per-tank-pairing tabs
(WARGNB, WARPLD, ...) and the healer-specific tabs are NOT imported yet.

Layout, per phase tab:
  * a header row with "Tank 1" in column C, then columns C..M are
    Tank 1 / Tank 2 / Scholar / Sage / White Mage / Astro / Melee 1 /
    Melee 2 / Phys Range / Caster / Extras
  * mechanic rows every other row: B is the cast name, C..M the assignments
  * a "Notes" row (B == "Notes") ends the block; column C holds footnotes,
    one per line, each prefixed with *, ** or ***
  * the Shiva tab stacks two blocks (Diamond Dust set, then Light Rampant
    set); both are P2

Cells are shorthand ("Rep", "Concit/Soil", "EukProg/Kera"); ABILITY expands
each token to the in-game action name so the text reads on its own and
scripts/fetch_icons.py can resolve an icon. "/" in a cell means press all of
them for that mechanic. A trailing *, ** or *** is a footnote ref; a leading
"(Early)" / "(Late)" or a trailing "(Gaia)" / "(Shiva)" is a timing/target
note. The source's column-A timestamps are deliberately dropped -- their
reference clock is inconsistent between tabs.
"""
import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
import workbook
from normalize_sheet import bind_sheet, load_encounter

NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
SHEET_ID = '1M1LHe4mpb1lyxkLWJxrDwe_JH897nickG3XLTtwnI90'

# Grid column -> slot ID. Healer columns name a job outright; the tank and DPS
# columns are positions, so the viewer picks the job -- but each DPS column only
# admits jobs of its kind (Melee 1/2 -> M1/M2, Phys Range -> P, Caster -> C).
# "M" (Extras) is not a slot -- see extras() below.
COLUMNS = {'C': 'T1', 'D': 'T2', 'E': 'SCH', 'F': 'SGE', 'G': 'WHM', 'H': 'AST',
           'I': 'M1', 'J': 'M2', 'K': 'P', 'L': 'C'}
HEALERS = ['SCH', 'SGE', 'WHM', 'AST']
ROLES = {'T1': 'tank', 'T2': 'tank', **{j: 'healer' for j in HEALERS},
         'M1': 'melee', 'M2': 'melee', 'P': 'ranged', 'C': 'caster'}

# phase ID -> tab name. The Shiva tab holds two "Tank 1" blocks; both are P2.
PHASE_TAB = {'p1': 'Fatebreaker', 'p2': 'Shiva', 'p3': 'Gaia',
             'p4': 'Light and Dark', 'p5': 'Pandora'}

# The sheet groups Fall of Faith's four resolutions into pairs.
# Bind each pair's presses to its
# first hit; do not invent extra presses on the second hit. See docs/FRU.md.
MECHANIC_ALIASES = {
    'Fall of Faith (1/2)': 'Fall of Faith 1',
    'Fall of Faith (3/4)': 'Fall of Faith 3',
    'Sinbound Holy': 'Sinbound Holy 1',
    'Mirror Mirror': 'Mirror, Mirror',
    'House of Light': 'The House of Light 4',
    'Junction (Transition)': 'Junction',
}

FIGHT = {
    'id': 'fru', 'name': 'Futures Rewritten (Ultimate)', 'shortName': 'FRU', 'type': 'Ultimate',
    'phases': [
        {'id': 'p1', 'label': 'P1', 'name': 'Fatebreaker'},
        {'id': 'p2', 'label': 'P2', 'name': 'Usurper of Frost'},
        {'id': 'p3', 'label': 'P3', 'name': 'Oracle of Darkness'},
        {'id': 'p4', 'label': 'P4', 'name': 'Light and Dark'},
        {'id': 'p5', 'label': 'P5', 'name': 'Pandora'},
    ],
}

# Whole-cell fixups applied before splitting on "/". The source writes
# "Seraphism" as "Seraph/ism" in two cells; without this the "/" split would
# turn it into "Seraph" + "ism".
CELL_FIXUPS = {'Seraph/ism': 'Seraphism'}

# Shorthand token -> in-game action name. A value with " + " is two buttons and
# becomes two actions. Anything not here and not in PASSTHROUGH raises.
ABILITY = {
    # Scholar
    'Concit': 'Concitation', 'Recit': 'Recitation',
    'Recit Concit': 'Recitation + Concitation',
    'Soil': 'Sacred Soil', 'Exp': 'Expedient', 'Exped': 'Expedient',
    'Fey': 'Fey Illumination', 'Consolation': 'Consolation',
    'Seraph': 'Summon Seraph', 'Seraphism': 'Seraphism',
    'Spread-Lo': 'Deployment Tactics',
    # Sage
    'EukProg': 'Eukrasian Prognosis II',
    'Zoe EukProg': 'Zoe + Eukrasian Prognosis II',
    'Kera': 'Kerachole', 'Holos': 'Holos', 'Panhaima': 'Panhaima', 'Zoe': 'Zoe',
    'Philosophia': 'Philosophia', 'Sophia': 'Philosophia',
    # White Mage
    'Temp': 'Temperance', 'Caress': 'Divine Caress', 'Bell': 'Liturgy of the Bell',
    'Confession': 'Plenary Indulgence',
    # Astrologian
    'CU': 'Collective Unconscious', 'Macro': 'Macrocosmos',
    'Neutral': 'Neutral Sect', 'Sun': 'Sun Sign',
    # Tanks
    'Rep': 'Reprisal', 'Veil': 'Divine Veil', 'Shake': 'Shake It Off',
    'TANK LB': 'Tank LB',
}
# Tokens kept verbatim. "Party Mit" is generic and resolves per job (jobs.json);
# Feint / Addle are role-universal.
PASSTHROUGH = {'Party Mit', 'Feint', 'Addle', 'Tank LB'}

TIMING = {'(Early)': 'Use early.', '(Late)': 'Use late.'}
TARGET = {'(Gaia)': 'On Gaia.', '(Shiva)': 'On Shiva.'}
SHORT_TANK_MIT = re.compile(r'^Short CD on (M[12])$')

# A footnote that only holds for some of the jobs a generic ability ("Party
# Mit") resolves to gets a noteJobs scope, so the viewer sees it only on the
# job it is about. Keyed by a substring of the footnote text.
NOTE_JOBS = {'Shake/Veil can be used prepull': ['WAR', 'PLD']}


def clean(value):
    return ' '.join(str(value).split())


def add_note(action, note):
    note = clean(note)
    if note and note not in action.get('note', ''):
        action['note'] = (action.get('note', '') + ' ' + note).strip()


def expand(token):
    """Shorthand -> list of action names."""
    name = ABILITY.get(token, token)
    if name not in ABILITY.values() and name not in PASSTHROUGH:
        raise ValueError(f'Unknown token {token!r}')
    return [part.strip() for part in name.split(' + ')]


def cell_actions(raw, footnotes):
    """One grid cell -> list of action dicts."""
    out = []
    for line in str(raw).splitlines():
        line = clean(line)
        if not line:
            continue
        short = SHORT_TANK_MIT.match(line)
        if short:
            # A tank spends its buddy-mit on a named melee (rendered small,
            # inline). "Buddy Mit" resolves per tank job via jobs.json
            # (Nascent Flash / Intervention / TBN / Heart of Corundum); DRK
            # also uses Oblation, which the (DRK) constraint drops for the
            # rest. Only occurs once, on P2 Banish III.
            target = f'On {short.group(1)}.'
            out.append({'name': 'Buddy Mit', 'note': target, 'buddy': True})
            out.append({'name': 'Oblation (DRK)', 'note': target, 'buddy': True})
            continue
        for fixed, replacement in CELL_FIXUPS.items():
            line = line.replace(fixed, replacement)
        for token in line.split('/'):
            token = token.strip()
            if not token:
                continue
            notes = []
            for prefix, text in TIMING.items():
                if token.startswith(prefix):
                    token = token[len(prefix):].strip()
                    notes.append(text)
            for suffix, text in TARGET.items():
                if token.endswith(suffix):
                    token = token[:-len(suffix)].strip()
                    notes.append(text)
            marker = re.search(r'\*+$', token)
            if marker:
                token = token[:marker.start()].strip()
                key = marker.group(0)
                if key not in footnotes:
                    raise ValueError(f'Unresolved footnote {key!r} for {token!r}')
                notes.append(footnotes[key])
            for name in expand(token):
                action = {'name': name}
                for note in notes:
                    add_note(action, note)
                for fragment, jobs in NOTE_JOBS.items():
                    if fragment in action.get('note', ''):
                        action['noteJobs'] = jobs
                out.append(action)
    return out


def extras(raw):
    """The Extras column is the extra raid mit only RDM (Magick Barrier) and MCH
    (Dismantle) bring -- so it lands on the caster and physical-ranged seats
    only. Returns (slot, action name) pairs."""
    tokens = {t.strip() for t in re.split(r'[+/]', str(raw)) if t.strip()}
    out = []
    if 'Barrier' in tokens:
        out.append(('C', 'Extra (RDM)'))
    if 'Dismantle' in tokens:
        out.append(('P', 'Extra (MCH)'))
    return out


def read_cells(archive, strings, worksheet):
    root = ET.fromstring(archive.read(worksheet))
    cells, maxrow = {}, 0
    for cell in root.findall('.//s:sheetData/s:row/s:c', NS):
        ref = cell.get('r')
        if cell.get('t') == 'inlineStr':
            node = cell.find('s:is', NS)
            text = ''.join(node.itertext()) if node is not None else ''
        else:
            value = cell.find('s:v', NS)
            if value is None or not value.text:
                continue
            text = strings[int(value.text)] if cell.get('t') == 's' else value.text
        cells[ref] = text
        maxrow = max(maxrow, int(re.sub(r'\D', '', ref)))
    return cells, maxrow


def parse_footnotes(raw):
    """A Notes cell -> ({'*': text, '**': text, ...}, [unreferenced lines])."""
    refs, loose = {}, []
    for line in str(raw).splitlines():
        line = clean(line)
        if not line:
            continue
        match = re.match(r'^(\*+)\s*(.*)', line)
        if match:
            refs[match.group(1)] = match.group(2).strip()
        else:
            loose.append(line)
    return refs, loose


def parse_block(cells, header_row, block_end, phase_id):
    """One 'Tank 1' block -> (mechanics, phase-note lines).

    The block's footnotes live on its Notes row, below every mechanic, so read
    that first and hand the resolved refs to cell_actions.
    """
    rows = list(range(header_row + 2, block_end, 2))
    stop = next((r for r in rows if clean(cells.get(f'B{r}', '')) == 'Notes'
                 or re.match(r'^P\d+:', clean(cells.get(f'B{r}', '')))), None)
    footnotes, notes = ({}, [])
    if stop is not None:
        footnotes, notes = parse_footnotes(cells.get(f'C{stop}', ''))
        rows = rows[:rows.index(stop)]

    mechanics = []
    for row in rows:
        title = clean(cells.get(f'B{row}', ''))
        if not title:
            continue
        mechanic = {'id': f'{phase_id}-r{row}', 'name': title, 'assignments': {}}
        for column, slot in COLUMNS.items():
            actions = cell_actions(cells.get(f'{column}{row}', ''), footnotes)
            if actions:
                mechanic['assignments'][slot] = actions
        for slot, name in extras(cells.get(f'M{row}', '')):
            mechanic['assignments'].setdefault(slot, []).append({'name': name})
        mechanics.append(mechanic)
    return mechanics, notes


def convert():
    archive = workbook.fetch(SHEET_ID)
    strings = workbook.shared_strings(archive)

    tab_sheet = workbook.tabs(archive)

    sheet = {
        'id': 'mitbutgood', 'fightId': 'fru', 'name': 'FRU Mit but Good',
        'author': 'Fae Nightwolf & Valiaa Masume', 'updated': '2026-09-08',
        'sourceVersion': '3/2',
        'source': {'name': 'FRU Mit but Good spreadsheet',
                   'url': 'https://docs.google.com/spreadsheets/d/1M1LHe4mpb1lyxkLWJxrDwe_JH897nickG3XLTtwnI90/edit'},
        'description': "Party mitigation for FRU from Fae Nightwolf & Valiaa Masume's plan. "
                       'Pick a tank position, a healer job, or a DPS position.',
        'slots': [{'id': slot, **({'job': slot} if slot in HEALERS else {}), 'role': ROLES[slot]}
                  for slot in COLUMNS.values()],
        'phases': [],
    }

    for phase_id, tab in PHASE_TAB.items():
        cells, maxrow = read_cells(archive, strings, tab_sheet[tab])
        headers = sorted(int(ref[1:]) for ref, value in cells.items()
                         if ref.startswith('C') and value == 'Tank 1')
        mechanics, notes = [], []
        for index, header in enumerate(headers):
            end = headers[index + 1] if index + 1 < len(headers) else maxrow + 1
            block_mechs, block_notes = parse_block(cells, header, end, phase_id)
            mechanics.extend(block_mechs)
            notes.extend(block_notes)
        phase = {'id': phase_id, 'mechanics': mechanics}
        if notes:
            phase['note'] = ' '.join(dict.fromkeys(notes))
        sheet['phases'].append(phase)

    # The encounter is the fight's source of truth and is never written here;
    # the workbook's rows bind onto the mechanics already on file.
    sheet = bind_sheet(sheet, load_encounter('fru'), MECHANIC_ALIASES)
    out = Path(__file__).resolve().parents[1] / 'packages/encounter-data/fights/fru/sheets/mitbutgood.json'
    out.write_text(json.dumps(sheet, indent=2, ensure_ascii=False) + '\n')
    print([(p['id'], len(p['mechanics']),
            sum(len(a) for m in p['mechanics'] for a in m['assignments'].values()))
           for p in sheet['phases']])


if __name__ == '__main__':
    convert()
