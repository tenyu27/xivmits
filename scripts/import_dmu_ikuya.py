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
import workbook
from normalize_sheet import bind_sheet, load_encounter

NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
SHEET_ID = '10C3ytfH3irHqkb45rchIq5oqdAs-v_OKTj57M-Twi3k'
PHASE_TABS = ['P1 | Kefka', 'P2 | Forsaken Kefka', 'P3 | Chaos & Exdeath',
              'P4 | Kefka Says', 'P5 | Kefka Reimagined']
OMNITANK_TAB = 'Omnitank'
COLUMNS = {'F': 'MT', 'H': 'OT', 'J': 'WHM', 'L': 'AST', 'N': 'SCH', 'P': 'SGE', 'R': 'M1', 'T': 'M2', 'V': 'P', 'X': 'C'}
HEALERS = ['WHM', 'AST', 'SCH', 'SGE']
# Which jobs may stand in each slot. Healer slots name a job outright; the tank
# and DPS slots are positions, so the viewer picks the job themselves -- but each
# DPS slot only admits jobs of its kind (M1/M2 melee, P ranged, C caster).
ROLES = {'MT': 'tank', 'OT': 'tank', 'M1': 'melee', 'M2': 'melee', 'P': 'ranged', 'C': 'caster',
         **{job: 'healer' for job in HEALERS}}
MARKERS = '⁰¹²³⁴⁵⁶⁷⁸⁹'
MARKER = rf'[{MARKERS}]+'
# Workbook row name -> encounter mechanic name, where the two differ. The
# encounter re-cut the black-hole tethers into sets of beams and renumbered
# Fell Forces in fight order; the workbook still uses Ikuya's own wording.
# Actions the workbook parks on one row but that really belong to later rows.
# Ikuya writes "Sun Sign (7-8th Set)" on the 6th black-hole beam because their
# sheet has no row for beams 7 and 8; the encounter does, so the press moves to
# its own rows. It is pressed on beam 6 and is still running for 7 and 8, so the
# later rows carry over rather than re-press.
SPREAD_SUFFIX = ' (7-8th Set)'
SPREAD_ONTO = {'p3-black-hole-6': ['p3-black-hole-7', 'p3-black-hole-8']}


# The Omnitank tab names and times its rows on its own clock, in its own
# wording. Once the encounter is reconciled against logs, those disagree with
# the party rows they render beside - "Thunder III" sitting next to "Thunder III
# (2nd Set)", at a time several seconds off. These map a tank row's wording onto
# the encounter mechanic family it describes, so the row can adopt that
# mechanic's name and time.
TANK_FAMILIES = {
    'Fell Forces (3x)': 'Fell Forces',
    'Fell Forces (2x)': 'Fell Forces',
    'Fell Forces I': 'Fell Forces',
    'Fell Forces II': 'Fell Forces',
    'Fell Forces III': 'Fell Forces',
    'Revolting Ruin III': 'Revolting Ruin',
    'Hyperdrive (3x)': 'Hyperdrive',
    'Thunder III': 'Thunder III',
    'Ultimate Embrace': 'Ultimate Embrace',
    'Wings of Destruction': 'Wings of Destruction',
    'Maddening Orchestra': 'Maddening Orchestra',
    'Flare/Holy': 'Flare/Holy',
    'Black Holes IV (10th Tether Set)': 'Black Holes 4th Set (Beam 2)',
}
# Rows that are the tank's own business, not a mechanic the encounter carries:
# a sub-hit of one mechanic, or a cue like "Autos". They keep their wording and
# take only their anchor's time.
# 'Autos' is a phase-top cue rather than a mechanic, so it keeps its wording.
TANK_KEEP_NAME = {'Autos'}

# The three autos inside one Fell Forces are one encounter mechanic; the call
# that distinguishes them belongs in the row's tag, not in a name the fight does
# not have.
TANK_ROW_TAGS = {'Fell Forces III': 'Share 3rd hit'}

# The workbook's bare "Solo" means the invuln eats two of the autos on its own -
# on the 3x it covers two and the third is shared. Say how many.
TANK_TAG_TEXT = {'Solo': 'Solo 2 hits'}


def align_tank_rows(sheet, encounter):
    """Give each tank row the name and time of the mechanic it belongs to.

    Rows arrive in MT/OT pairs sharing a name and time, so a pair resolves once
    and both halves land on the same mechanic.
    """
    by_phase = {p['id']: p['mechanics'] for p in encounter['phases']}
    for plan in sheet.get('tankMits', {}).get('plans', []):
        for phase in plan['phases']:
            mechanics = by_phase[phase['id']]
            resolved, taken = {}, set()
            for row in phase['mechanics']:
                # Not keyed on seat: an MT and an OT row of the same mechanic are
                # one moment and must land on the same one. Keyed on the row's
                # original anchor as well, because two pairs can share a name and
                # carry no time of their own and still be different moments.
                key = (row['name'], row.get('time'), row.get('after'))
                if key not in resolved:
                    family = TANK_FAMILIES.get(row['name'])
                    match = None
                    if family:
                        def in_family(m):
                            return m['name'] == family or m['name'].startswith(family + ' ')
                        # An anchor that already points at the right mechanic is
                        # kept, and does not consume it: the three autos inside
                        # one Fell Forces all belong to that same mechanic.
                        current = next((m for m in mechanics if m['id'] == row.get('after')), None)
                        if current is not None and in_family(current):
                            match = current
                        else:
                            for mechanic in mechanics:
                                if mechanic['id'] not in taken and in_family(mechanic):
                                    match = mechanic
                                    taken.add(mechanic['id'])
                                    break
                    resolved[key] = match
                match = resolved[key]
                if match is not None:
                    if row['name'] in TANK_ROW_TAGS:
                        row['tag'] = TANK_ROW_TAGS[row['name']]
                if row.get('tag') in TANK_TAG_TEXT:
                    row['tag'] = TANK_TAG_TEXT[row['tag']]
                    row['after'] = match['id']
                    row['time'] = match['time']
                    if row['name'] not in TANK_KEEP_NAME:
                        row['name'] = match['name']
                elif row.get('after'):
                    # No mechanic of its own: sit on its anchor's clock rather
                    # than the workbook's.
                    anchored = next((m for m in mechanics if m['id'] == row['after']), None)
                    if anchored and anchored.get('time'):
                        row['time'] = anchored['time']
            # Folding sub-rows onto one mechanic can leave two rows saying
            # exactly the same thing - the 1st and 2nd auto of a Fell Forces are
            # both a bare "Avoid" once they stop carrying distinct names.
            seen, kept = set(), []
            for row in phase['mechanics']:
                fingerprint = (row['name'], row.get('tag'), row.get('seat'), row.get('boss'),
                               row.get('invuln'), row.get('after'), row.get('note'),
                               tuple((a['name'], a.get('carryOver'), a.get('note')) for a in row['actions']))
                if fingerprint in seen:
                    continue
                seen.add(fingerprint)
                kept.append(row)
            phase['mechanics'] = kept
    return sheet


def spread_parked_actions(sheet):
    """Move `<action> (7-8th Set)` off its parked row onto the rows it names."""
    rows = {m['mechanicId']: m for phase in sheet['phases'] for m in phase['mechanics']}
    for phase in sheet['phases']:
        extra = []
        for mechanic in phase['mechanics']:
            targets = SPREAD_ONTO.get(mechanic['mechanicId'])
            if not targets:
                continue
            for slot, actions in list(mechanic['assignments'].items()):
                parked = [a for a in actions if a['name'].endswith(SPREAD_SUFFIX)]
                if not parked:
                    continue
                mechanic['assignments'][slot] = [a for a in actions if a not in parked]
                for target in targets:
                    row = rows.get(target) or next(
                        (e for e in extra if e['mechanicId'] == target), None)
                    if row is None:
                        row = {'mechanicId': target, 'assignments': {}}
                        extra.append(row)
                    row['assignments'].setdefault(slot, []).extend(
                        {'name': a['name'][:-len(SPREAD_SUFFIX)], 'carryOver': True} for a in parked)
        if extra:
            order = [m['mechanicId'] for m in phase['mechanics']] + [e['mechanicId'] for e in extra]
            phase['mechanics'] = sorted(phase['mechanics'] + extra,
                                        key=lambda m: ORDER.get(m['mechanicId'], order.index(m['mechanicId'])))
    return sheet


ALIASES = {
    'Black Holes II (3rd Tether Set)': 'Black Holes 2nd Set (Beam 1)',
    'Black Holes II (4th Tether Set)': 'Black Holes 2nd Set (Beam 2)',
    'Black Holes II (5th Tether Set)': 'Black Holes 2nd Set (Beam 3)',
    'Black Holes III (6th Tether Set)': 'Black Holes 3rd Set (Beam 1)',
    'Fell Forces (3x) 1': 'Fell Forces 1 (3x)',
    'Fell Forces (2x) 1': 'Fell Forces 2 (2x)',
    'Fell Forces (2x) 2': 'Fell Forces 3 (2x)',
    'Fell Forces (3x) 2': 'Fell Forces 4 (3x)',
}

# Rules the source repeats on every row of a phase tab. Hoisted to the phase
# note (shown once, one rule per line) instead of stamped onto each action, so a
# mit's own note stays short and specific. One list per phase number.
# Note fragments that scope the whole note to certain jobs (import stamps
# `noteJobs` on any action whose note contains the fragment).
NOTE_JOBS = {
    'if playing WAR': ['WAR'],
}

# Short per-row calls the Omnitank cells write as a bare label line ("Close",
# "First Hit"). Pulled off the note into a `tag` badge on the row.
POSITION_TAGS = {
    'Close.': 'Close hit', 'Far.': 'Far hit', 'Solo this hit.': 'Solo',
    'First Hit.': '1st hit', 'Second Hit.': '2nd hit',
}

# Targeted mitigation (Reprisal / Addle / Feint / Dismantle). The caveat about
# what it does in a given phase is a phase-top `scopedNote` - shown only to a
# seat that brings one of these abilities, and hidden by the notes toggle.
TARGETED_MIT = ('Reprisal', 'Addle', 'Feint', 'Dismantle')
TARGETED_NOTE = {
    3: 'Target your firewalled boss while the firewall is up. Targeted mitigation mostly covers '
       'tank autos and busters in this phase, not raidwides.',
    4: 'Targeted mitigation only works on Ultima Upsurge; other uses cover tank autos.',
}

PHASE_RULES = {
    1: [],
    2: [],
    3: [],
    4: [],
    5: [],
}


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


# Omnitank tab -> tankMits. Two assignment columns per row, one plan per tank
# job. P1/P2/P4 columns are MT / OT and rows get a `seat`. P3/P5 columns are the
# two sides of a split the viewer picks directly: left (E) is Chaos in P3 / 1st
# invuln in P5, right (I) the mirror. The sheet's header writes a job-priority
# order to *suggest* which side each job takes, but we do not apply it - the
# player chooses via the P3 boss / P5 invuln toggle - so both sides are emitted
# and tagged `boss` / `invuln`. Cells use shorthand, expanded per job below.

TANKS = ['PLD', 'WAR', 'DRK', 'GNB']

INVULN = {'WAR': 'Holmgang', 'PLD': 'Hallowed Ground', 'DRK': 'Living Dead', 'GNB': 'Superbolide'}
MIT_40 = {'WAR': 'Damnation', 'PLD': 'Guardian', 'DRK': 'Shadowed Vigil', 'GNB': 'Great Nebula'}
MIT_90 = {'WAR': 'Thrill of Battle', 'PLD': 'Bulwark', 'DRK': 'Dark Mind', 'GNB': 'Camouflage'}
# The short personal mitigation each tank presses on itself. A value may be a
# list (DRK stacks TBN + Oblation). WAR's is Bloodwhetting, not the ally-only
# Nascent Flash -- that one is the "Buddy Mit" below.
SHORT_MIT = {'WAR': 'Bloodwhetting', 'PLD': 'Holy Sheltron',
             'DRK': ['The Blackest Night', 'Oblation'], 'GNB': 'Heart of Corundum'}
SHORTHAND = {'Invulnerability': INVULN, '40%': MIT_40, '90s': MIT_90, 'Short Mit': SHORT_MIT, 'Short': SHORT_MIT}
BUDDY_MIT = {'WAR': ['Nascent Flash'], 'PLD': ['Intervention'], 'DRK': ['The Blackest Night', 'Oblation'], 'GNB': ['Heart of Corundum']}


def as_list(value):
    return list(value) if isinstance(value, list) else [value]


# Rampart + 40% + 90s + short mit, pressed together.
KITCHEN_SINK = {job: ['Rampart', MIT_40[job], MIT_90[job], *as_list(SHORT_MIT[job])] for job in TANKS}
KNOWN_TOKENS = {'Kitchen Sink', 'Buddy Mit', 'Rampart', 'Invulnerability', '40%', '90s', 'Short Mit', 'Short', 'Provoke'}

# phase -> (data rows, mode). Left column is E, right is I, time D. 'seat' rows
# split by MT / OT; 'split' rows split by the P3-boss / P5-invuln choice.
OMNI_BLOCKS = [
    (1, [8, 10, 12, 14], 'seat'),
    (2, [27, 29, 31], 'seat'),
    (3, [45, 47, 49, 51, 53, 55], 'split'),
    (4, [69], 'seat'),
    (5, [81, 83, 85, 87, 89, 91, 93, 95, 97, 99], 'split'),
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
        names, buddy = as_list(SHORTHAND[name][job]), False
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
    root = ET.fromstring(archive.read(workbook.worksheet(archive, OMNITANK_TAB)))
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

    # One plan per job. Seat-mode phases (P1/P2/P4) emit an MT and an OT row.
    # Split-mode phases (P3/P5) emit both source columns, each tagged with the
    # side it belongs to -- P3 by which boss you hold (E Chaos, I Exdeath), P5 by
    # invuln order (E 1st, I 2nd) -- and the viewer's toggle selects between
    # them. The sheet's priority list is not applied; the player picks.
    START_WITH_BOSS = ('You start with the boss. Hold aggro at the phase start '
                       'so your co-tank does not get the Holy debuff.')
    plans = []
    for job in TANKS:
        phases_out = []
        for phase_number, rows, mode in OMNI_BLOCKS:
            start = phase_starts[phase_number - 1]
            timed = party_lookup(phase_number)
            notes = block_notes[phase_number]
            out_mechs = []
            for row in rows:
                row_mechs = []
                title = cells.get(f'B{row}', '')
                name = clean(re.sub(MARKER, '', title))
                title_markers = re.findall(MARKER, title)
                rel = max(0, omni_seconds(cells.get(f'D{row}')) - start)
                rel_str = f'{rel // 60}:{rel % 60:02}'
                anchor = anchor_for(timed, rel)
                if mode == 'seat':
                    variants = [('E', {'seat': 'MT'}, 'mt'), ('I', {'seat': 'OT'}, 'ot')]
                elif phase_number == 3:
                    variants = [('E', {'boss': 'Chaos'}, 'chaos'), ('I', {'boss': 'Exdeath'}, 'exdeath')]
                else:
                    variants = [('E', {'invuln': 1}, 'inv1'), ('I', {'invuln': 2}, 'inv2')]
                for column, tag, suffix in variants:
                    actions, extra = parse_omni_cell(cells.get(f'{column}{row}', ''), job, notes)
                    note_parts = [notes[m] for m in title_markers if m in notes] + extra
                    alts = omni_alt(phase_number, row, tag.get('seat'), job)
                    # WAR's kitchen-sink alternative lives in the `alts` sub-row
                    # on its own rows; the source also repeats it as a footnote
                    # that lands on every job and row (title markers -> note_parts,
                    # inline markers -> action notes), so scrub that prose copy.
                    drop = 'alternatively kitchen sink'
                    note_parts = [n for n in note_parts if drop not in n.lower()]
                    for a in actions:
                        if a.get('note') and drop in a['note'].lower():
                            a['note'] = ' '.join(
                                s for s in re.split(r'(?<=\.)\s+', a['note']) if drop not in s.lower()
                            ).strip()
                            if not a['note']:
                                del a['note']
                    same = bool(anchor) and anchor[1] == name
                    # Drop an empty row that only repeats a party mechanic
                    # already on the timeline; keep empty markers for busters
                    # with no party row (Revolting Ruin, Hyperdrive, Autos).
                    if same and not actions and not alts and not note_parts:
                        continue
                    collapse = same and bool(actions) and not alts
                    mech = {'id': f'{job}-p{phase_number}-r{row}-{suffix}'.lower(), 'name': name}
                    if not collapse:
                        mech['time'] = rel_str
                    if anchor:
                        mech['after'] = anchor[0]
                    mech.update(tag)
                    # A positional call ("Close." / "Far." / "Solo this hit.")
                    # reads as a badge, not a trailing sentence fragment.
                    for frag, tag_val in POSITION_TAGS.items():
                        if frag in note_parts:
                            mech['tag'] = tag_val
                            note_parts = [n for n in note_parts if n != frag]
                    if note_parts:
                        mech['note'] = ' '.join(dict.fromkeys(note_parts))
                    mech['actions'] = actions
                    if alts:
                        mech['alts'] = alts
                    out_mechs.append(mech)
                    row_mechs.append(mech)
                # If one invuln variant of this row is the Solo hit, the co-tank
                # solos on the other - mark that side "Avoid" so this tank holds,
                # synthesising a marker row when the sheet left it blank.
                solo = next((m for m in row_mechs if m.get('tag') == 'Solo' and 'invuln' in m), None)
                if solo:
                    other = 1 if solo['invuln'] == 2 else 2
                    sib = next((m for m in row_mechs if m.get('invuln') == other), None)
                    if sib:
                        sib['tag'] = 'Avoid'
                        sib['actions'] = []
                    else:
                        marker = {'id': f'{job}-p{phase_number}-r{row}-inv{other}'.lower(),
                                  'name': solo['name'], 'invuln': other, 'tag': 'Avoid', 'actions': []}
                        if 'after' in solo:
                            marker['after'] = solo['after']
                        out_mechs.append(marker)
            phase_out = {'id': f'p{phase_number}', 'mechanics': out_mechs}
            # "You start with the boss" applies to the whole of P5 for the 2nd
            # invuln - a phase-top personal note, not a per-row one.
            if phase_number == 5:
                phase_out['note'] = START_WITH_BOSS
                phase_out['noteInvuln'] = 2
            phases_out.append(phase_out)
        plans.append({'job': job, 'phases': phases_out})

    # Suggested job order per side, from the split-block column headers:
    # "Chaos (WAR > DRK > GNB > PLD)" / "Exdeath (...)" for P3, and the bare
    # "WAR > DRK > GNB > PLD" / "PLD > GNB > DRK > WAR (Start With Boss)" for P5.
    def order_list(text):
        stripped = re.sub(r'\([^)]*\)', '', re.sub(MARKER, '', text))
        return [j for j in (p.strip() for p in stripped.split('>')) if j in TANKS]

    p3_pri = {}
    for cell in (cells.get('E43', ''), cells.get('I43', '')):
        m = re.match(r'\s*([A-Za-z]+)\s*\((.*)\)', cell)
        if m:
            p3_pri[m.group(1)] = order_list(m.group(2))
    invuln_pri = {k: order_list(cells.get(c, '')) for k, c in (('1', 'E79'), ('2', 'I79'))}
    priorities = {}
    if all(len(v) == len(TANKS) for v in p3_pri.values()) and len(p3_pri) == 2:
        priorities['p3Boss'] = p3_pri
    if all(len(v) == len(TANKS) for v in invuln_pri.values()):
        priorities['invuln'] = invuln_pri

    result = {'plans': plans}
    if priorities:
        result['priorities'] = priorities
    return result


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


def convert():
    archive = workbook.fetch(SHEET_ID)
    strings = workbook.shared_strings(archive)
    sheet = {
        'id': 'ikuya', 'fightId': 'dmu', 'name': 'Ikuya Mitty',
        'author': 'Ikuya Kirishima', 'updated': '2026-09-07',
        'sourceVersion': '6.0 (1 Sep)',
        'source': {'name': 'Ikuya Mitty spreadsheet',
                   'url': 'https://docs.google.com/spreadsheets/d/10C3ytfH3irHqkb45rchIq5oqdAs-v_OKTj57M-Twi3k/edit'},
        'description': 'P1–P5 from Ikuya Kirishima’s mitigation plan. Choose a tank position, healer job, or DPS position.',
        'slots': [{'id': slot, **({'job': slot} if slot in HEALERS else {}), 'role': ROLES[slot]} for slot in COLUMNS.values()],
        'phases': [],
    }
    phase_starts = []
    for phase_number in range(1, 6):
        root = ET.fromstring(archive.read(workbook.worksheet(archive, PHASE_TABS[phase_number - 1])))
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
        # "All mechanics require shields" only matters to the shield healers, so
        # it rides the first SCH / SGE action of the phase rather than the
        # phase note (which every role sees).
        shields_done = set()
        prev_extras_row = None
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
            # On back-to-back checked rows one press (Magick Barrier / Dismantle,
            # ~10s) covers both, so the later ones are carry-overs.
            if cells.get(f'Z{row}') == '✔':
                # RDM is a caster, MCH a physical ranged - so the extra raid mit
                # only belongs on those two seats, never on melee.
                extra = {'name': 'Extra (RDM/MCH)'}
                if prev_extras_row == row - 2:
                    extra['carryOver'] = True
                for slot in ['P', 'C']:
                    mechanic['assignments'].setdefault(slot, []).append(dict(extra))
                prev_extras_row = row
            if phase_number == 3 and row == 24:
                mechanic['note'] = notes['⁴']
                for slot in COLUMNS.values():
                    name = 'Manage Accretion healing' if slot in HEALERS else 'Avoid HP-restoring abilities'
                    mechanic['assignments'][slot] = [{'name': name}]
            # Mechanic footnotes and unnumbered timing rules belong beside the
            # affected actions. Phase-wide rules live in the phase note instead
            # (see PHASE_RULES) - only genuinely local notes are added here.
            for slot, actions in mechanic['assignments'].items():
                if slot in ('SCH', 'SGE') and slot not in shields_done:
                    add_note(actions[0], 'All mechanics require shields.')
                    shields_done.add(slot)
                if slot in HEALERS and '¹⁰' in title_notes:
                    add_note(actions[0], notes['¹⁰'])
                # The "monitor the tanks / burst-heal after invuln" note only
                # matters for the Fell Forces (3x) after the second Maddening
                # Orchestra (row 28), not every P5 healer row.
                if slot in HEALERS and phase_number == 5 and row == 28:
                    add_note(actions[0], notes['²'])
                for action in actions:
                    if phase_number == 1 and row == 8 and action['name'] == 'Party Mit (GNB/DRK)':
                        add_note(action, 'Time this to carry over through Wave Cannon and the first Double-Trouble Trap.')
                    # A note that only holds for some of the jobs a generic
                    # ability covers gets a `noteJobs` scope so the viewer only
                    # sees it on the job it is about.
                    for frag, jobs in NOTE_JOBS.items():
                        if frag in action.get('note', ''):
                            action['noteJobs'] = jobs
            # Timing rules that apply to a whole mechanic, every role.
            if phase_number == 1 and row == 14:
                mechanic['note'] = 'Use late into the castbar so it also covers Hyperdrive.'
            if phase_number == 5 and row == 32:
                mechanic['note'] = 'Use any timed mitigation as late as possible.'
            if phase_number == 5 and row == 40:
                mechanic['note'] = ('It is important that the new round of mitigation for the 5th hit '
                                    'are applied as the first round of mitigation will fall off.')
            mechanics.append(mechanic)
        phase = {'id': f'p{phase_number}', 'mechanics': mechanics}
        if PHASE_RULES[phase_number]:
            phase['note'] = '\n'.join(PHASE_RULES[phase_number])
        # The targeted-mit caveat: a phase-top note shown only to a seat that
        # brings one of those abilities this phase, and toggleable.
        if phase_number in TARGETED_NOTE:
            phase['scopedNote'] = {'text': TARGETED_NOTE[phase_number], 'abilities': list(TARGETED_MIT)}
        sheet['phases'].append(phase)
    sheet['tankMits'] = convert_omnitank(archive, strings, sheet['phases'], phase_starts)
    # The encounter is log-reconciled and read-only here: the workbook only says
    # who presses what, so its rows bind onto the mechanics already on file.
    encounter = load_encounter('dmu')
    global ORDER
    # Encounter order, so rows added for parked actions land in the right place.
    ORDER = {m['id']: i for phase in encounter['phases']
             for i, m in enumerate(phase['mechanics'])}
    sheet = align_tank_rows(spread_parked_actions(bind_sheet(sheet, encounter, ALIASES)), encounter)
    out = Path(__file__).resolve().parents[1] / 'packages/encounter-data/fights/dmu/sheets/ikuya.json'
    out.write_text(json.dumps(sheet, indent=2, ensure_ascii=False) + '\n')
    print([(p['id'], len(p['mechanics']), sum(len(a) for m in p['mechanics'] for a in m['assignments'].values())) for p in sheet['phases']])
    print([(p['job'], sum(len(m['actions']) for ph in p['phases'] for m in ph['mechanics'])) for p in sheet['tankMits']['plans']])


if __name__ == '__main__':
    convert()
