"""Import the six reviewed FRU tank tabs; encounter anchors are read-only.

Opening duties follow MT/OT; P3 uses the standard source plan.
See docs/FRU-TANKS.md for the source cells and reviewed exceptions.
"""
import re
from copy import deepcopy
import workbook

PAIRS = ['WARGNB', 'WARPLD', 'WARDRK', 'GNBDRK', 'GNBPLD', 'PLDDRK']
HEADERS = {
    'WARGNB': [11, 39, 51, 63, 83], 'WARPLD': [11, 39, 50, 61, 81],
    'WARDRK': [11, 39, 51, 63, 83], 'GNBDRK': [11, 39, 51, 65, 85],
    'GNBPLD': [11, 39, 50, 61, 81], 'PLDDRK': [11, 39, 51, 65, 85],
}
NAMES = {
    'Bolide': 'Superbolide', 'Hallowed': 'Hallowed Ground', 'Thrill': 'Thrill of Battle',
    'Camo': 'Camouflage', 'HoC': 'Heart of Corundum', 'Sheltron': 'Holy Sheltron',
    'TBN': 'The Blackest Night', 'Nascent': 'Nascent Flash',
}
INVULN = {'WAR': 'Holmgang', 'GNB': 'Superbolide', 'PLD': 'Hallowed Ground', 'DRK': 'Living Dead'}
ANCHORS = [
    ['p1-powder-mark-trail-1', 'p1-burn-mark-1', 'p1-powder-mark-trail-2', 'p1-burn-mark-2'],
    ['p2-quadruple-slap-1'], ['p3-black-halo-1', 'p3-darkest-dance-1'],
    ['p4-somber-dance-1', 'p4-hallowed-wings-2', 'p4-akh-morn-1', 'p4-akh-morn-2'],
    ['p5-wings-dark-and-light-1', 'p5-wings-dark-and-light-3'],
]


def parse_actions(raw, formats=()):
    """Read commas/slashes as presses, preserving buddy scope and rich text."""
    actions = []
    offset = 0
    for line in raw.splitlines(keepends=True):
        buddy = 'Buddy Mit' in line
        second = '2nd Hit' in line or '2nd hit' in line
        start = line.index(':') + 1 if buddy else 0
        for match in re.finditer(r'[^,/\n]+', line[start:]):
            token = match.group().strip()
            if not token:
                continue
            pos = offset + start + match.start() + len(match.group()) - len(match.group().lstrip())
            muted, italic = formats[pos] if formats else (False, False)
            late = '(Late)' in token or token.startswith('*')
            shake_first = token.startswith('*Damnation')
            early = '(Right After 1st Somber)' in token
            token = token.replace('(Late)', '').replace('(Right After 1st Somber)', '').lstrip('*').strip()
            personal_tbn = token == 'Kitchen Sink (TBN 2nd hit)'
            if personal_tbn:
                token = 'Kitchen Sink'
            action = {'name': NAMES.get(token, token)}
            notes = []
            if buddy:
                action['buddy'] = True
                notes.append('On your co-tank.')
            if second and not personal_tbn:
                notes.append('For the second hit.')
            if late:
                notes.append('Use late.')
            if shake_first:
                notes.append('Use Shake It Off first.')
            if early:
                notes.append('Use right after the first Somber Dance hit.')
            if muted and not italic:
                action['carryOver'] = True
            if muted and italic and token == 'Provoke':
                notes.append('Conditional tank swap.')
            if notes:
                action['note'] = ' '.join(notes)
            actions.append(action)
            if personal_tbn:
                actions.append({'name': 'The Blackest Night', 'note': 'For the second hit.'})
        offset += len(line)
    return actions


def import_tanks(archive, encounter):
    from import_fru_mitbutgood import read_cells, cell_formats
    strings = workbook.shared_strings(archive)
    tabs = workbook.tabs(archive)
    source = {}
    for tab in PAIRS:
        path = tabs[tab]
        cells, _ = read_cells(archive, strings, path)
        source[tab] = (cells, cell_formats(archive, path))
        expected_rows = [
            [(1, 'Powder Mark Trail 1'), (3, 'Burn Mark 1'), (5, 'Powder Mark Trail 2'), (7, 'Burn Mark 2'),
             (14, 'Powder Mark Trail 1'), (16, 'Burn Mark 1'), (18, 'Powder Mark Trail 2'), (20, 'Burn Mark 2')],
            [(1, 'Quadruple Slap')], [(1, 'Black Halo'), (3, 'Darkest Dance')],
            [(1, 'Somber Dance'), (3, 'Hallowed Wing'), (7, '7/1 Akh Morn 1'), (9, '7/1 Akh Morn 2')],
            [(1, 'Wings Dark and Light 1'), (3, 'Wings Dark and Light 2')],
        ]
        for h, rows in zip(HEADERS[tab], expected_rows):
            for offset, title in rows:
                actual = cells.get(f'B{h + offset}', '').strip().replace('Hallowed Wings', 'Hallowed Wing')
                if actual != title:
                    raise ValueError(f'{tab}/B{h + offset}: expected {title}, got {actual}')

    def cell(tab, ref, branch=None):
        cells, styles = source[tab]
        raw = cells.get(ref, '')
        fmt = styles.get(ref, [])
        if branch is not None:
            parts = list(re.finditer(r'(?:^|\nor )([^\n]*(?:\n(?!or )[^\n]*)*)', raw))
            if len(parts) != 2:
                raise ValueError(f'{tab}/{ref}: expected two solo/buddy alternatives: {raw!r}')
            part = parts[branch]
            raw = part.group(1)
            fmt = fmt[part.start(1):part.end(1)]
        return parse_actions(raw, fmt)

    mechanics = {m['id']: m for p in encounter['phases'] for m in p['mechanics']}
    plans = []
    for tab in PAIRS:
        left, right = tab[:3], tab[3:]
        double = 'J11' in source[tab][0]
        for job, other in [(left, right), (right, left)]:
            plan = {'job': job, 'with': other, 'choices': [
                {'id': 'powder', 'label': 'P1 invuln', 'default': 'first',
                 'options': [{'id': 'first', 'label': 'Powder Mark 1'}, {'id': 'second', 'label': 'Powder Mark 2'}]},
                {'id': 'akh', 'label': 'P4 Akh Morn', 'default': left, 'options': [
                    {'id': left, 'label': f'7/1: {left} solos first'},
                    {'id': right, 'label': f'7/1: {right} solos first'},
                ]},
            ], 'phases': [{'id': f'p{i + 1}', 'mechanics': []} for i in range(5)]}
            plan['phases'][0]['note'] = ('MT is the opening main tank; OT is the off tank. '
                'For the mitigated Powder Mark, use the marked cooldowns late. The source footnote claiming '
                'Powder Mark 2 mitigation covers Burnished Glory 2 conflicts with the log order. '
                'Healers should mitigate the opening tank for Burn Mark 2 on the first-Powder invuln plan.')
            plan['phases'][1]['note'] = 'Personal mit is free for autos this phase.'
            if not double:
                plan['phases'][2]['note'] = f'{left} takes Black Halo; DRK takes Darkest Dance. The opening-tank swap applies to P1/P2 only.'
            if tab == 'PLDDRK':
                plan['phases'][2]['note'] += " Do not use Hallowed Ground here just because it is available."

            def add(phase, anchor, actions, when, tag=None, second=False):
                if not actions:
                    return
                m = mechanics[anchor]
                row = {'id': f'{anchor}-personal-{len(plan["phases"][phase]["mechanics"]) + 1}',
                       'name': m['name'], 'time': m['time'], 'after': anchor,
                       'seat': 'MT' if opening == job else 'OT',
                       'when': dict(when), 'actions': deepcopy(actions)}
                if tag:
                    row['tag'] = tag
                if second:
                    follow = mechanics['p5-wings-dark-and-light-' + ('2' if anchor.endswith('-1') else '4')]
                    row.update(name=follow['name'], time=follow['time'], tag='Second hit')
                plan['phases'][phase]['mechanics'].append(row)

            for opening in [left, right]:
                when = {}
                # Four tabs have explicit reverse layouts. For the two DRK tabs,
                # the source's P1/P2 swap instruction exchanges tank duties;
                # use that job's reviewed matching duties in WARDRK/GNBPLD.
                def location(phase):
                    if double:
                        return tab, ('C' if job == left else 'F') if opening == left else ('J' if job == right else 'M')
                    if phase >= 2 or opening == left:
                        return tab, 'C' if job == left else 'G'
                    if job == 'DRK':
                        return 'WARDRK', 'J'
                    return ('WARGNB', 'F') if job == 'GNB' else ('WARPLD', 'F')

                for phase in range(5):
                    src, col = location(phase)
                    h = HEADERS[src][phase]
                    if phase == 0:
                        for variant, shift in [('first', 0), ('second', 13)]:
                            for i, anchor in enumerate(ANCHORS[0]):
                                add(0, anchor, cell(src, f'{col}{h + 1 + 2 * i + shift}'), {**when, 'powder': variant})
                    elif phase == 1:
                        # Only the non-opening tank invulns, for both opening orders.
                        if job != opening:
                            add(1, ANCHORS[1][0], [{'name': INVULN[job]}], when, 'Invuln')
                    elif phase == 2:
                        for i, anchor in enumerate(ANCHORS[2]):
                            actions = cell(src, f'{col}{h + 1 + 2 * i}')
                            if tab == 'GNBDRK':
                                halo_invuln = opening == 'GNB'
                                if i == 0:
                                    actions = ([{'name': 'Superbolide'}] if halo_invuln else [{'name': 'Kitchen Sink'}]) if job == 'GNB' else ([] if halo_invuln else parse_actions('Buddy Mit: TBN, Oblation'))
                            add(2, anchor, actions, when)
                    elif phase == 3:
                        for i, anchor in enumerate(ANCHORS[3][:2]):
                            actions = cell(src, f'{col}{h + 1 + 2 * i}')
                            add(3, anchor, actions, when)
                        for first in [left, right]:
                            for i, anchor in enumerate(ANCHORS[3][2:]):
                                solo = (job == first) == (i == 0)
                                ref = f'{col}{h + 7 + 2 * i}'
                                raw = source[src][0][ref]
                                primary_solo = not raw.lstrip().startswith('Buddy Mit')
                                branch = 0 if solo == primary_solo else 1
                                add(3, anchor, cell(src, ref, branch), {**when, 'akh': first},
                                    'Solo · after first Somber' if solo and i == 0 else 'Solo' if solo else 'Buddy')
                    else:
                        for i, anchor in enumerate(ANCHORS[4]):
                            actions = cell(src, f'{col}{h + 1 + 2 * i}')
                            later = [a for a in actions if 'For the second hit.' in a.get('note', '')]
                            add(4, anchor, [a for a in actions if a not in later], when)
                            add(4, anchor, later, when, second=True)
            plans.append(plan)
    return {'note': 'MT is the opening main tank; OT is the off tank. P3 uses the standard plan for each pairing.', 'plans': plans}
