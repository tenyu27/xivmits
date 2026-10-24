"""Convert Malachite Laurent's TOP party-mit workbook into reviewed repo JSON.

Usage: python3 scripts/import_top_topmitty.py
Uses Python's standard library. The site never reads Excel at runtime.

Scope: the five party-wide mitigation grids (Beetle / MF / Final Omega /
Dynamis / Alpha Omega), plus the six per-tank-job pairing tabs (WARDRK,
GNBPLD, ...) which become `tankMits` -- personal mit per tank per co-tank,
shown below the party view. Reviewed source notes are imported; images and
video links are not. Tank 1 / Tank 2 become the seats T1 / T2 in the party grid --
there is no MT / OT split here.
"""
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
import workbook
from normalize_sheet import bind_sheet, load_encounter

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

# (phase ID, worksheet number, which "Tank 1" header block in that sheet). Every
# party grid is its own worksheet except "Final Omega" (sheet 4), which stacks
# two: "P3: Final Omega" then, far below, "P4: Blue Screen".
SHEET_ID = '1ROErvG1BhTuNvXqPGcR6ZyyhJ7uNTZdf2WzKyVj9hh4'
PHASES = [('p1', 'Beetle', 1), ('p2', 'MF', 1), ('p3', 'Final Omega', 1),
          ('p4', 'Final Omega', 2), ('p5', 'Dynamis', 1), ('p6', 'Alpha Omega', 1)]

# The sheet writes healer mit in shorthand; expand to the in-game action name so
# the text reads on its own and scripts/fetch_icons.py can resolve an icon.
ABILITY = {
    'Soil': 'Sacred Soil', 'Fey': 'Fey Illumination', 'Expedience': 'Expedient',
    'Seraph': 'Seraph Veil', 'Spread-Lo': 'Deployment Tactics',
    'EukProg': 'Eukrasian Prognosis', 'Eukprog': 'Eukrasian Prognosis',
    'Euk Prog': 'Eukrasian Prognosis', 'Kera': 'Kerachole',
    'CU': 'Collective Unconscious', 'Star': 'Earthly Star', 'Bell': 'Liturgy of the Bell',
    'Zoe EukProg': 'Zoe + Eukrasian Prognosis',  # two buttons, so two actions
}

# "Everything" means press the whole kit. Level 90, raid-mitigation only.
EVERYTHING = {
    'SCH': ['Sacred Soil', 'Fey Illumination', 'Expedient', 'Seraph Veil',
            'Deployment Tactics', 'Whispering Dawn'],
    'SGE': ['Kerachole', 'Holos', 'Panhaima', 'Eukrasian Prognosis', 'Physis II'],
    'WHM': ['Temperance', 'Liturgy of the Bell', 'Plenary Indulgence', 'Asylum'],
    'AST': ['Collective Unconscious', 'Neutral Sect', 'Earthly Star', 'Macrocosmos', 'Horoscope'],
}

# Per-pairing tabs -> (job A, job B, worksheet number). Column C is job A,
# column G is job B; each tab yields two plans (A paired with B, B with A).
TANK_TABS = [('WAR', 'DRK', 'WARDRK'), ('WAR', 'GNB', 'WARGNB'), ('WAR', 'PLD', 'WARPLD'),
             ('GNB', 'DRK', 'GNBDRK'), ('GNB', 'PLD', 'GNBPLD'), ('PLD', 'DRK', 'PLDDRK')]
TANK_FULLNAME = {'WARRIOR': 'WAR', 'DARK KNIGHT': 'DRK', 'GUNBREAKER': 'GNB', 'PALADIN': 'PLD'}

# The pairing tabs write mit in shorthand and with a few typos; expand to the
# in-game action name so the text reads on its own and fetch_icons can resolve
# an icon. Names already spelled the game's way pass through untouched. TOP
# syncs to level 90, so the sheet's "Nebula" is GNB's level 38 Nebula — Great
# Nebula only replaces it at 92 — and must not be expanded to the newer name.
# "Kitchen Sink" (press your whole kit) stays as written - a decision, not a
# single button, like "Party Mit (GNB/DRK)" in the party grid.
TANK_ABILITY = {
    'Thril': 'Thrill of Battle', 'Thrill': 'Thrill of Battle', 'Vengence': 'Vengeance',
    'Bolide': 'Superbolide', 'Camo': 'Camouflage', 'HOC': 'Heart of Corundum',
    'TBN': 'The Blackest Night', 'Sheltron': 'Holy Sheltron',
    'Sentinal': 'Sentinel', 'Nascent': 'Nascent Flash', 'Intervention': 'Intervention',
}

# The one ally-targeted mitigation each tank brings ("Buddy Mit" with no skill
# named means this one). "Buddy Mit: <skill>" names it explicitly.
# DRK brings two ally-targetable mits and the sheet means both; the rest bring one.
TANK_BUDDY = {'WAR': 'Nascent Flash', 'PLD': 'Intervention',
              'GNB': 'Heart of Corundum', 'DRK': ['The Blackest Night', 'Oblation']}

# "Kitchen Sink" means press the whole personal-mit kit. Raid mitigation only,
# at TOP's level 90 sync — invulns (Holmgang / Hallowed Ground / Living Dead /
# Superbolide) are their own line in the sheet, not part of the sink. GNB's
# 120s button here is Nebula; Great Nebula is level 92.
TANK_EVERYTHING = {
    'WAR': ['Rampart', 'Vengeance', 'Thrill of Battle', 'Bloodwhetting'],
    'PLD': ['Rampart', 'Sentinel', 'Holy Sheltron', 'Bulwark'],
    'DRK': ['Rampart', 'Shadow Wall', 'Dark Mind', 'The Blackest Night', 'Oblation'],
    'GNB': ['Rampart', 'Nebula', 'Camouflage', 'Heart of Corundum'],
}

# Tank-tab phase headers sit in column C: "P1: Beetle Omega", "P5: Dynamis".
TANK_PHASE = re.compile(r'^P(\d):')

# Workbook wording -> log-derived mechanic. The encounter owns names and times.
PARTY_MECHANICS = {
    'p1': {'Pantokrator': 'p1-pantokrator-1',
           **{f'Stack {n}': f'p1-condensed-wave-cannon-kyrios-{n}' for n in range(1, 5)}},
    'p2': {'Optimized Meteor / Cosmo Memory': 'p2-optimized-meteor-1'},
    'p3': {'Hello World': 'p3-hello-world-1', 'Critical Error': 'p3-critical-error-1',
           **{f'{n}{suffix} Patch Set': f'p3-latent-defect-{n}'
              for n, suffix in [(1, 'st'), (2, 'nd'), (3, 'rd'), (4, 'th')]}},
    'p4': {**{f'Protean {n}': f'p4-wave-cannon-{2*n-1}' for n in range(1, 4)},
           **{f'Stack {n}': f'p4-wave-cannon-{2*n}' for n in range(1, 4)},
           'Blue Screen': 'p4-blue-screen-1'},
    'p5': {'Delta Cast': 'p5-run-mi-delta-version-1', 'Delta Mech': 'p5-hello-distant-world-1',
           'Sigma Cast': 'p5-run-mi-sigma-version-1', 'Sigma Mech': 'p5-hello-distant-world-2',
           'Omega Cast': 'p5-run-mi-omega-version-1', 'Omega Mech': 'p5-hello-distant-world-3',
           'Blind Faith': 'p5-blind-faith-1'},
    'p6': {'Cosmo Memory': 'p6-cosmo-memory-1',
           'Cosmo Dive 1': 'p6-cosmo-dive-1', 'Cosmo Dive 2': 'p6-cosmo-dive-2',
           'Protean 1': 'p6-wave-cannon-1', 'Protean 2': 'p6-wave-cannon-4',
           'Wave Cannon 1': 'p6-wave-cannon-3', 'Wave Cannon 2': 'p6-wave-cannon-6',
           'Cosmo Meteor': 'p6-cosmo-meteor-1', 'Flares': 'p6-cosmo-meteor-3',
           'Magic Number 1': 'p6-magic-number-1', 'Magic Number 2': 'p6-magic-number-2'},
}

# A personal row anchors directly to its mechanic, including busters absent
# from the party grid. Prepull alone remains an unanchored instruction.
PERSONAL_ANCHOR = {
    'p1': {'Prepull': None, 'Diffuse Wave Cannon': 'p1-diffuse-wave-cannon-kyrios-1'},
    'p2': {'Solar Ray': 'p2-solar-ray-1', 'Tank Tethers': 'p2-optimized-bladedance-1'},
    'p3': {**{f'Patch {n}': f'p3-latent-defect-{n}' for n in range(1, 5)},
           'Critical Error': 'p3-critical-error-1', 'Monitors': 'p3-oversampled-wave-cannon-1'},
    'p5': {'Delta Solar Ray': 'p5-solar-ray-1', 'Sigma Solar Ray': 'p5-solar-ray-3',
           'Omega Solar Ray': 'p5-solar-ray-5', 'Final Buster': 'p5-solar-ray-7'},
    'p6': {'Cosmo Dive 1': 'p6-cosmo-dive-1', 'Wave Cannon 1': 'p6-wave-cannon-3',
           'Wave Cannon 2': 'p6-wave-cannon-6', 'Cosmo Dive 2': 'p6-cosmo-dive-2'},
}

# How each phase's "Notes" row is placed:
#   ('mechanic', name)  -> becomes that personal row's aside (folded in)
#   ('alt', name)       -> "<label>: <abilities> on X" -> a labelled alt line
#   ('row', mechanicId) -> a standalone personal note row after that mechanic
PERSONAL_NOTE = {
    'p1': ('mechanic', 'Diffuse Wave Cannon'),
    'p2': ('alt', 'Solar Ray'),
    'p3': ('row', 'p3-hello-world-1'),
    'p5': ('mechanic', 'Omega Solar Ray'),
}


def bind_party(sheet, encounter):
    phases = {p['id']: p for p in sheet['phases']}
    # Keep the workbook's mitigation at the P5 cast cue, ahead of P6 damage.
    blind = [m for m in phases['p5']['mechanics'] if m['name'] == 'Blind Faith']
    if len(blind) != 1:
        raise SystemExit('Expected exactly one P5 Blind Faith source row')
    canonical = {p['id']: {m['id']: m for m in p['mechanics']} for p in encounter['phases']}
    for phase in sheet['phases']:
        seen = {}
        for mechanic in phase['mechanics']:
            name = mechanic['name']
            seen[name] = seen.get(name, 0) + 1
            key = f'{name} {seen[name]}' if name == 'Magic Number' else name
            target = PARTY_MECHANICS[phase['id']].get(key)
            if target is None:
                raise SystemExit(f"Unmapped TOP party mechanic {phase['id']}/{name!r}")
            if phase['id'] == 'p2' and key == 'Optimized Meteor / Cosmo Memory':
                mechanic['note'] = 'Mitigation for Optimized Meteor and Cosmo Memory.'
            mechanic['name'] = canonical[phase['id']][target]['name']
    sheet = bind_sheet(sheet, encounter)
    for mechanic in phases['p5']['mechanics']:
        for number, version in enumerate(('Delta', 'Sigma', 'Omega'), 1):
            if mechanic['mechanicId'] == f'p5-hello-distant-world-{number}':
                mechanic['group'] = {
                    'name': f'{version} Mech',
                    'after': f'p5-run-mi-{version.lower()}-version-1',
                    'before': f'p5-solar-ray-{number * 2 + 1}',
                }
    return sheet


def clean(value):
    value = ' '.join(str(value).split())
    # Correct the source's spelling; keep its terminology and shorthand.
    for typo, fixed in {'Pantrokrator': 'Pantokrator', 'ZoeEukProg': 'Zoe EukProg'}.items():
        value = value.replace(typo, fixed)
    return value


def join_notes(lines):
    return ' '.join(text if text.endswith(('.', '!', '?')) else text + '.'
                    for line in lines if (text := clean(line)))


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
    root = ET.fromstring(archive.read(workbook.worksheet(archive, worksheet)))
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


def place_personal(plan, encounter_phases):
    # Splice each personal row into the party timeline: resolve its `after`
    # anchor and fold the phase "Notes" row where PERSONAL_NOTE says.
    canonical = {p['id']: {m['id']: m for m in p['mechanics']} for p in encounter_phases}
    kept = []
    for phase in plan['phases']:
        pid = phase['id']
        anchors = PERSONAL_ANCHOR.get(pid, {})
        by_name = {m['name']: m for m in phase['mechanics']}
        for mechanic in phase['mechanics']:
            if mechanic['name'] not in anchors:
                raise SystemExit(f"unmapped personal mechanic {pid}/{mechanic['name']!r} "
                                 f"in {plan['job']}+{plan['with']} - add it to PERSONAL_ANCHOR")
            target = anchors[mechanic['name']]
            if target:
                mechanic['after'] = target
        note = phase.pop('note', None)
        directive = PERSONAL_NOTE.get(pid)
        if note and directive:
            kind, where = directive
            if kind == 'row':
                phase['note'], phase['noteAfter'] = note, where
            elif kind == 'mechanic':
                host = by_name.get(where)
                if host is None:  # combo has no such row - keep the note as its own
                    host = {'id': f"{plan['job']}{plan['with']}-{pid}-note".lower(),
                            'name': where, 'actions': []}
                    if anchors.get(where):
                        host['after'] = anchors[where]
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
            # P4 has no personal rows, but keeps its per-tank Notes at phase top.
            phase['note'] = note
        for mechanic in phase['mechanics']:
            if mechanic.get('after'):
                target = canonical[pid][mechanic['after']]
                mechanic['name'], mechanic['time'] = target['name'], target['time']
        if phase['mechanics'] or phase.get('note'):
            kept.append(phase)
    plan['phases'] = kept
    return plan


def convert_tank_tabs(archive, strings, encounter_phases):
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
                    for column, phase in (('C', phase_a), ('G', phase_b)):
                        lines = [clean(cells.get(f'{column}{row}', ''))]
                        following = row + 1
                        while following < end and not cells.get(f'B{following}'):
                            value = clean(cells.get(f'{column}{following}', ''))
                            if not value:
                                break
                            lines.append(value)
                            following += 1
                        if any(lines):
                            phase['note'] = join_notes(lines)
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
            if phase_id == 'p6':
                for ref, value in cells.items():
                    if not ref.startswith('D') or not header_row < int(ref[1:]) < end:
                        continue
                    match = re.match(r'\s*([A-Z]{3}(?:/[A-Z]{3})*):\s*(.+)', value)
                    if match:
                        for job, phase in ((job_a, phase_a), (job_b, phase_b)):
                            if job in match[1].split('/'):
                                instruction = clean(match[2])
                                target = 'Wave Cannon 2' if instruction.startswith('Save MP') else 'Cosmo Dive 1'
                                host = next((m for m in phase['mechanics'] if m['name'] == target), None)
                                if host is None:
                                    raise SystemExit(f'Missing TOP footer host {worksheet}/{job}/{target}')
                                host['note'] = join_notes([host.get('note', ''), instruction])
            phases_a.append(phase_a)
            phases_b.append(phase_b)
        plans.append(place_personal({'job': job_a, 'with': job_b, 'phases': phases_a}, encounter_phases))
        plans.append(place_personal({'job': job_b, 'with': job_a, 'phases': phases_b}, encounter_phases))
    return {'plans': plans}


def add_source_notes(sheet, worksheets):
    # Explicit source cells, including instructions below the main Notes row.
    # Keep these at phase level so unassigned roles can also read them.
    refs = {
        'p2': ('MF', ['C17']),
        'p5': ('Dynamis', ['C24', 'C25']),
    }
    for phase in sheet['phases']:
        if phase['id'] not in refs:
            continue
        tab, cells = refs[phase['id']]
        values = [clean(worksheets[tab].get(cell, '')) for cell in cells]
        if not all(values):
            raise SystemExit(f'Missing reviewed TOP source note in {tab}: {cells}')
        phase['note'] = '\n'.join(values)
    exception = [clean(worksheets['Alpha Omega'].get(cell, '')) for cell in ('C33', 'C34', 'C37')]
    if not all(exception):
        raise SystemExit('Missing reviewed TOP GNB/DRK Party Mit note')
    for plan in sheet['tankMits']['plans']:
        phase = next(p for p in plan['phases'] if p['id'] == 'p6')
        # Keep optional invuln-swap instructions on the relevant stack.
        if phase.get('note'):
            host = next(m for m in phase['mechanics'] if m['after'] == 'p6-wave-cannon-3')
            host['note'] = join_notes([host.get('note', ''), phase.pop('note')])
        if {plan['job'], plan['with']} == {'GNB', 'DRK'}:
            phase['note'] = '\n'.join(exception)
            phase['noteAfter'] = 'p6-cosmo-memory-1'
    p6 = next(p for p in sheet['phases'] if p['id'] == 'p6')
    memory = next(m for m in p6['mechanics'] if m['mechanicId'] == 'p6-cosmo-memory-1')
    lb = next(a for a in memory['assignments']['T1'] if a['name'] == 'Tank LB')
    lb['note'] = 'First tank LB priority: ' + clean(worksheets['Alpha Omega']['E49'])
    wave_note = join_notes([worksheets['Alpha Omega'][cell] for cell in ('E43', 'E46')])
    for mechanic in p6['mechanics']:
        if mechanic['mechanicId'] in ('p6-wave-cannon-3', 'p6-wave-cannon-6'):
            mechanic['note'] = wave_note
    # The pairing tabs address healers, but personal tank plans are invisible
    # to them. Surface the warning with its exact pairing scope at phase top.
    warning = 'Healers must put personal mit on tanks or they die to busters'
    pairs = []
    for plan in sheet['tankMits']['plans']:
        phase = next((p for p in plan['phases'] if p['id'] == 'p5'), None)
        if phase and any(warning in m.get('note', '') for m in phase['mechanics']):
            pair = frozenset((plan['job'], plan['with']))
            if not any(pair == existing for existing, _ in pairs):
                pairs.append((pair, f"{plan['job']}/{plan['with']}"))
    if pairs:
        phase = next(p for p in sheet['phases'] if p['id'] == 'p5')
        phase['note'] += '\n' + 'For ' + ', '.join(label for _, label in pairs) + ': ' + warning + '.'
    scope_party_notes(sheet)


def scope_party_notes(sheet):
    for phase in sheet['phases']:
        if phase['id'] == 'p2':
            phase['noteRoles'] = ['melee', 'caster']
        if phase['id'] == 'p5':
            lines = phase['note'].splitlines()
            healer_notes = [line for line in lines if 'Healers must' in line]
            phase['note'] = '\n'.join(line for line in lines if line not in healer_notes)
            for job in HEALERS:
                first = next(a for m in phase['mechanics'] for a in m['assignments'].get(job, [])
                             if not a.get('carryOver'))
                first['note'] = join_notes([first.get('note', ''), *healer_notes])
        for mechanic in phase['mechanics']:
            if mechanic.get('note') and mechanic['mechanicId'] in (
                    'p2-optimized-meteor-1', 'p6-wave-cannon-3', 'p6-wave-cannon-6'):
                note = mechanic.pop('note')
                for actions in mechanic['assignments'].values():
                    for action in actions:
                        if not action.get('carryOver'):
                            action['note'] = join_notes([action.get('note', ''), note])


def convert():
    archive = workbook.fetch(SHEET_ID)
    strings = [''.join(si.itertext()) for si in ET.fromstring(archive.read('xl/sharedStrings.xml'))]
    sheet = {
        'id': 'topmitty', 'fightId': 'top', 'name': 'TOP Mitty',
        'author': 'Malachite Laurent', 'updated': '2026-09-17',

        'source': {'name': 'TOP Mitty spreadsheet',
                   'url': 'https://docs.google.com/spreadsheets/d/1ROErvG1BhTuNvXqPGcR6ZyyhJ7uNTZdf2WzKyVj9hh4/edit'},
        'description': "Party mitigation for TOP from Malachite Laurent's plan. "
                       'Pick a tank position, a healer job, or a DPS position.',
        'slots': [{'id': slot, **({'job': slot} if slot in HEALERS else {}), 'role': ROLES[slot]}
                  for slot in COLUMNS.values()],
        'phases': [],
    }
    worksheets = {}
    for phase_id, worksheet, occurrence in PHASES:
        if worksheet not in worksheets:
            root = ET.fromstring(archive.read(workbook.worksheet(archive, worksheet)))
            cells = {}
            for cell in root.findall('.//s:sheetData/s:row/s:c', NS):
                value = cell.find('s:v', NS)
                if value is None or not value.text:
                    continue
                cells[cell.get('r')] = strings[int(value.text)] if cell.get('t') == 's' else value.text
            worksheets[worksheet] = cells
        cells = worksheets[worksheet]
        headers = sorted(int(ref[1:]) for ref, value in cells.items()
                         if ref.startswith('C') and value == 'Tank 1')
        header = headers[occurrence - 1]
        # A grid stops at the next "Tank 1" block on the same sheet, or 200 rows on.
        end = min(header + 200, headers[occurrence] if occurrence < len(headers) else header + 200)
        mechanics = []
        for row in range(header + 2, end, 2):
            title = cells.get(f'B{row}', '')
            if not title or title == 'Notes' or re.match(r'^P\d+:', title):
                if title == 'Notes' or re.match(r'^P\d+:', title):
                    break
                continue
            name = clean(title)
            # The source's numeric P2 label groups these two late raidwides.
            if phase_id == 'p2' and re.fullmatch(r'611(?:\.0+)?', name):
                name = 'Optimized Meteor / Cosmo Memory'
            mechanic = {'id': f'{phase_id}-r{row}', 'name': name, 'assignments': {}}
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
    # The encounter is the fight's source of truth and is never written here;
    # the workbook's rows bind onto the mechanics already on file.
    encounter = load_encounter('top')
    sheet = bind_party(sheet, encounter)
    sheet['tankMits'] = convert_tank_tabs(archive, strings, encounter['phases'])
    add_source_notes(sheet, worksheets)
    out = Path(__file__).resolve().parents[1] / 'packages/encounter-data/fights/top/sheets/topmitty.json'
    out.write_text(json.dumps(sheet, indent=2, ensure_ascii=False) + '\n')
    print([(p['id'], len(p['mechanics']),
            sum(len(a) for m in p['mechanics'] for a in m['assignments'].values())) for p in sheet['phases']])
    print([(f"{p['job']}+{p['with']}", sum(len(m['actions']) for ph in p['phases'] for m in ph['mechanics']))
           for p in sheet['tankMits']['plans']])


if __name__ == '__main__':
    convert()
