"""Bind importer output onto the canonical encounter timeline.

The encounter file is the fight's source of truth. Its mechanic list, ids, times
and FFLogs ability ids are reconciled against real logs (see scripts/fflogs.py)
and are never written by a sheet importer - importing a mit sheet must not
change the fight.

A mit sheet is an overlay: each row references an encounter mechanic by id, the
way an action references an ability, and adds only who presses what.

    {"mechanicId": "p1-gravitas-2", "assignments": {"SCH": [{"name": "Seraph"}]}}

An importer therefore hands `bind_sheet` rows carrying the spreadsheet's own
names, and gets back rows carrying encounter ids. A row that matches no
mechanic is an error, not a new mechanic: either the sheet names it differently
(add an alias) or the encounter is genuinely missing it (reconcile the log
first).
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIGHTS = ROOT / 'packages/encounter-data/fights'

_ALREADY_NUMBERED = re.compile(r'\(\d+\)$|\b\d+(?:st|nd|rd|th)?\b', re.IGNORECASE)


def load_encounter(fight_id):
    """The committed encounter for a fight. Read-only as far as importers care."""
    return json.loads((FIGHTS / fight_id / 'encounter.json').read_text(encoding='utf-8'))


def number_repeated(names):
    """Suffix 1..n onto names that repeat across the fight and carry no number.

    The encounter's own names were built this way, so a sheet's raw row names
    have to go through the same rule before they can be matched against them.
    """
    totals = {}
    for name in names:
        if not _ALREADY_NUMBERED.search(name):
            totals[name] = totals.get(name, 0) + 1
    seen, out = {}, []
    for name in names:
        if totals.get(name, 0) > 1:
            seen[name] = seen.get(name, 0) + 1
            out.append(f'{name} {seen[name]}')
        else:
            out.append(name)
    return out


def bind_sheet(sheet, encounter, aliases=None):
    """Rewrite a sheet's rows to reference `encounter` mechanic ids.

    `sheet` is the importer's draft: phases whose mechanics carry `name`, an
    importer-local `id`, optional `note`, and `assignments`. Returns the same
    sheet with each row reduced to {mechanicId, note?, assignments}, and the
    tankMits `after` / `noteAfter` anchors remapped to encounter ids.

    `aliases` maps a sheet's row name to the encounter's name, for mechanics the
    two call different things.
    """
    aliases = aliases or {}
    by_phase = {p['id']: p for p in encounter['phases']}

    # Fight-wide, matching how the encounter numbered its own repeated names.
    raw = [m['name'] for p in sheet['phases'] for m in p['mechanics']]
    numbered = iter(number_repeated(raw))

    anchors, missing = {}, []
    for phase in sheet['phases']:
        encounter_phase = by_phase.get(phase['id'])
        if encounter_phase is None:
            raise SystemExit(f"encounter has no phase {phase['id']}")
        # Consume each encounter mechanic at most once, in file order, so
        # repeated names bind to successive occurrences.
        available = list(encounter_phase['mechanics'])
        rows = []
        for mechanic in phase['mechanics']:
            name = next(numbered)
            wanted = aliases.get(name, name)
            match = next((m for m in available if m['name'] == wanted), None)
            if match is None:
                missing.append(f"  {phase['id']}: {name!r}"
                               + (f" (aliased to {wanted!r})" if wanted != name else ''))
                continue
            available.remove(match)
            anchors[(phase['id'], mechanic['id'])] = match['id']
            rows.append({
                'mechanicId': match['id'],
                **({'note': mechanic['note']} if mechanic.get('note') else {}),
                'assignments': mechanic['assignments'],
            })
        phase['mechanics'] = rows

    if missing:
        raise SystemExit(
            f"{len(missing)} sheet row(s) match no mechanic in {encounter['id']}/encounter.json:\n"
            + '\n'.join(missing)
            + "\n\nAdd an alias if the sheet just names it differently, or reconcile the\n"
              "encounter against a log first if the mechanic is genuinely missing.\n"
              "Importers never add mechanics to an encounter.")

    for plan in sheet.get('tankMits', {}).get('plans', []):
        for phase in plan['phases']:
            if phase.get('noteAfter'):
                phase['noteAfter'] = anchors[(phase['id'], phase['noteAfter'])]
            for mechanic in phase['mechanics']:
                if mechanic.get('after'):
                    mechanic['after'] = anchors[(phase['id'], mechanic['after'])]
    return sheet


def snap_tank_times(sheet, encounter):
    """Put every anchored tank row on its mechanic's clock.

    A tank workbook keeps its own timings, a second or two off the encounter's
    log-derived ones. That gap is invisible in the spreadsheet and glaring on the
    site: a personal row whose time disagrees with the mechanic it sits under
    cannot fold into it, so the mechanic's name is printed twice.
    """
    times = {m['id']: m.get('time') for phase in encounter['phases'] for m in phase['mechanics']}
    for plan in sheet.get('tankMits', {}).get('plans', []):
        for phase in plan['phases']:
            for mechanic in phase['mechanics']:
                anchored = times.get(mechanic.get('after'))
                if anchored:
                    mechanic['time'] = anchored
    return sheet
