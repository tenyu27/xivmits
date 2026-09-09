"""Normalize importer output into canonical encounter and sheet-overlay JSON."""

import re


def normalize_encounter(fight, sheet):
    anchors = {}
    counts = {}
    encounter_phases = []

    for phase in fight['phases']:
        sheet_phase = next(item for item in sheet['phases'] if item['id'] == phase['id'])
        encounter_mechanics = []
        overlay_mechanics = []
        for mechanic in sheet_phase['mechanics']:
            name_slug = re.sub(r'(^-|-$)', '', re.sub(r'[^a-z0-9]+', '-', mechanic['name'].lower()))
            base = f"{phase['id']}-{name_slug}"
            counts[base] = counts.get(base, 0) + 1
            mechanic_id = f"{base}-{counts[base]}"
            anchors[(phase['id'], mechanic['id'])] = mechanic_id
            encounter_mechanics.append({
                'id': mechanic_id,
                'name': mechanic['name'],
                **({'time': mechanic['time']} if mechanic.get('time') else {}),
                'fflogs': {'abilityIds': []},
            })
            overlay_mechanics.append({
                'mechanicId': mechanic_id,
                **({'note': mechanic['note']} if mechanic.get('note') else {}),
                'assignments': mechanic['assignments'],
            })
        encounter_phases.append({**phase, 'mechanics': encounter_mechanics})
        sheet_phase['mechanics'] = overlay_mechanics

    for plan in sheet.get('tankMits', {}).get('plans', []):
        for phase in plan['phases']:
            if phase.get('noteAfter'):
                phase['noteAfter'] = anchors[(phase['id'], phase['noteAfter'])]
            for mechanic in phase['mechanics']:
                if mechanic.get('after'):
                    mechanic['after'] = anchors[(phase['id'], mechanic['after'])]

    encounter = {
        key: value for key, value in fight.items() if key != 'phases'
    }
    encounter['fflogs'] = {'encounterIds': []}
    encounter['phases'] = encounter_phases
    _number_repeated_mechanics(encounter_phases)
    return encounter, sheet


def _number_repeated_mechanics(phases):
    mechanics = [mechanic for phase in phases for mechanic in phase['mechanics']]
    already_numbered = re.compile(r'\(\d+\)$|\b\d+(?:st|nd|rd|th)?\b', re.IGNORECASE)
    totals = {}
    for mechanic in mechanics:
        if not already_numbered.search(mechanic['name']):
            totals[mechanic['name']] = totals.get(mechanic['name'], 0) + 1

    seen = {}
    for mechanic in mechanics:
        name = mechanic['name']
        if totals.get(name, 0) > 1:
            seen[name] = seen.get(name, 0) + 1
            mechanic['name'] = f"{name} ({seen[name]})"
