"""Rebuild the reviewed DSR timeline from six slow, public FFLogs clears.

Maintainer-only: python3 scripts/reconcile_dsr.py [--cache /tmp/dsr-logs]
The sheet importer never calls this script or changes encounter timings.
See docs/DSR.md for selection, phase boundaries, and per-mechanic evidence.
"""
import argparse
import json
import re
from pathlib import Path
from statistics import median

import fflogs
from normalize_sheet import number_repeated

ROOT = Path(__file__).resolve().parents[1]
REPORTS = [('YrAbahP16g4vC3JM', 16), ('xVGLdpmW8nPJCQDq', 22),
           ('1rdVP7JzgmwLkyDp', 26), ('JTYXp1dVZB3xGaKA', 17),
           ('2VaqKp76fHZG4A3C', 47), ('TnGb23dmQPWJZv9Y', 25)]
PHASES = [('p2', 'P2', 'Thordan'), ('p3', 'P3', 'Nidhogg'),
          ('p4', 'P4', 'Eyes'), ('rewind', 'Rewind', 'Save Haurchefant'),
          ('p5', 'P5', 'Dark Thordan'), ('p6', 'P6', 'Double Dragons'),
          ('p7', 'P7', 'Dragon King Thordan')]

# Each entry names a logged primary ability, its event type, the number of
# sequences, optional secondary IDs, and visibility. A sequence collapses
# simultaneous targets and hits less than six seconds apart, not new presses.
# Explicit entries keep autos, player-pet casts, and implementation events out.
SPECS = {
    'p2': [
        (25544, 'begincast', 2, [25545], 'minor'),
        (25541, 'damage', 2, [], 'tank'),
        (25555, 'begincast', 1, [], ''),
        (25548, 'begincast', 1, [25549], 'minor'),
        (25550, 'begincast', 1, [25551], 'minor'),
        (25297, 'damage', 1, [25579, 25298, 25299], 'tank'),
        (25542, 'begincast', 1, [], ''),
        (25543, 'begincast', 1, [], 'tank'),
        (25569, 'begincast', 1, [], ''),
        (25571, 'damage', 1, [], 'minor'),
        (25574, 'begincast', 1, [25575], 'minor'),
        (25576, 'begincast', 1, [25577], 'minor'),
        (25534, 'damage', 1, [25533], ''),
        (25536, 'begincast', 2, [25537, 25538], 'minor'),
        (25539, 'begincast', 1, [], 'minor'),
        (26377, 'damage', 1, [26376], ''),
    ],
    'p3': [
        (26381, 'begincast', 1, [], 'minor'),
        (26388, 'damage', 2, [], ''),
        (26385, 'begincast', 3, [], 'minor'),
        (26379, 'begincast', 2, [26380], 'minor'),
        (26392, 'begincast', 1, [], 'minor'),
        (26396, 'damage', 1, [], 'tank'),
        (29750, 'begincast', 1, [], 'minor'),
    ],
    'p4': [
        (26810, 'damage', 1, [], ''), (26814, 'begincast', 1, [], 'minor'),
        (26817, 'damage', 1, [], ''), (26815, 'damage', 1, [], 'minor'),
        (26819, 'begincast', 1, [26820], ''),
        (26813, 'begincast', 1, [], ''),
    ],
    'rewind': [
        (25314, 'begincast', 1, [], 'minor'),
        # Four separate bait pairs, five seconds apart. See clusters().
        (25369, 'damage', 4, [], ''),
        (25316, 'cast', 1, [], ''),
    ],
    'p5': [
        (27526, 'cast', 1, [], 'minor'),
        (27529, 'begincast', 1, [], ''),
        (27530, 'damage', 1, [29346], 'minor'),
        (25546, 'begincast', 1, [25547], 'minor'),
        (27534, 'begincast', 1, [27533], 'minor'),
        (25542, 'begincast', 2, [], ''),
        (25543, 'begincast', 2, [], 'tank'),
        (25541, 'damage', 2, [], 'tank'),
        (27538, 'begincast', 1, [], ''),
        (25548, 'begincast', 1, [25549], 'minor'),
        (25310, 'begincast', 1, [25311], 'minor'),
        (27543, 'begincast', 1, [], 'minor'),
        (27528, 'begincast', 1, [], 'minor'),
    ],
    'p6': [
        (27956, 'begincast', 2, [27957, 27954, 27955, 27958, 27959, 27963, 27964, 27965], ''),
        (27969, 'begincast', 2, [27970, 27971, 27972], ''),
        # Four random wing variants share one mechanic and occurrence counter.
        (27939, 'begincast', 2, [27940, 27942, 27943, 27941, 27944], 'tank'),
        (27945, 'damage', 2, [], 'minor'),
        (27973, 'begincast', 1, [], ''),
        (27974, 'begincast', 1, [27975], 'minor'),
        (29739, 'cast', 1, [29740], 'minor'),
        (27966, 'begincast', 2, [27967], 'minor'),
        (27968, 'cast', 1, [28903], 'minor'),
        (27937, 'begincast', 1, [], 'minor'),
        (26810, 'damage', 1, [], ''),
    ],
    'p7': [
        (29752, 'damage', 1, [], ''),
        (28059, 'begincast', 3, [28060, 28061], 'minor'),
        (28051, 'begincast', 3, [28052, 28053, 28054, 28055, 29452, 29453, 29454], ''),
        (28057, 'begincast', 2, [28058, 28114, 28115], ''),
        (28206, 'begincast', 1, [29455, 29456, 29457], 'minor'),
    ],
}


def clusters(events, ability, kind, start, end):
    ids = ({25536, 25537} if ability == 25536 else
           {27939, 27940, 27942, 27943} if ability == 27939 else
           {27956, 27957} if ability == 27956 else {ability})
    times = sorted({e['timestamp'] for e in events if e.get('abilityGameID') in ids
                    and e['type'] == kind and start <= e['timestamp'] < end})
    gap = 2000 if ability == 25369 else 6000
    return [t for i, t in enumerate(times) if i == 0 or t - times[i - 1] > gap]


def clock(seconds):
    seconds = int(seconds + 0.5)
    return f'{seconds // 60}:{seconds % 60:02d}'


def phase_windows(fight, events):
    transitions = {p['id']: p['startTime'] for p in fight['phaseTransitions']}
    # The workbook ends P2 with Final Chorus. FFLogs starts phase 3 at
    # its animation, before the impact. End P2 after the logged damage,
    # using the next millisecond because event windows are half-open.
    chorus = clusters(events, 26377, 'damage', transitions[3], transitions[4])
    final = clusters(events, 29752, 'cast', transitions[7], fight['endTime'])
    if len(chorus) != 1 or len(final) != 1:
        raise ValueError('Expected one Final Chorus and one Alternative End transition')
    starts = [transitions[2], chorus[0] + 1,
              *[transitions[i] for i in range(4, 8)], final[0]]
    ends = starts[1:] + [fight['endTime']]
    if any(start >= end for start, end in zip(starts, ends)):
        raise ValueError('DSR phase boundaries must be strictly increasing')
    return starts, ends


def fetch_report(code, fight_id, cache):
    path = cache / f'{code}.json' if cache else None
    if path and path.exists():
        return json.loads(path.read_text())
    result = fflogs.query('''query($code:String!,$ids:[Int]) {
      reportData { report(code:$code) {
        fights(fightIDs:$ids) {id encounterID kill startTime endTime phaseTransitions {id startTime}}
        masterData {abilities {gameID name}}
        events(fightIDs:$ids, filterExpression:"source.type = 'NPC'", limit:10000) {data nextPageTimestamp}
      }} }''', code=code, ids=[fight_id])['reportData']['report']
    if result['events']['nextPageTimestamp'] is not None:
        raise ValueError(f'{code}: event response truncated; paginate before reconciling')
    if path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result))
    return result


def reconcile(cache=None):
    samples, names = [], {}
    for code, fight_id in REPORTS:
        report = fetch_report(code, fight_id, cache)
        fight = report['fights'][0]
        if fight['id'] != fight_id or not fight['kill'] or fight['encounterID'] != 1076:
            raise ValueError(f'{code}: expected a DSR clear')
        events = report['events']['data']
        if report['events']['nextPageTimestamp'] is not None:
            raise ValueError(f'{code}: incomplete events')
        starts, ends = phase_windows(fight, events)
        samples.append((code, fight_id, events, starts, ends))
        names.update({a['gameID']: a['name'] for a in report['masterData']['abilities']})

    encounter = {'id': 'dsr', 'name': "Dragonsong's Reprise (Ultimate)",
                 'shortName': 'DSR', 'type': 'Ultimate', 'released': '2022-04-26',
                 'fflogs': {'encounterIds': [1065, 1076]}, 'phases': []}
    baseline = 0
    evidence = []
    for index, (pid, label, title) in enumerate(PHASES):
        phase = {'id': pid, 'label': label, 'name': title, 'start': clock(baseline), 'mechanics': []}
        occurrences = {}
        for ability, kind, count, secondary, visibility in SPECS[pid]:
            observed = [clusters(events, ability, kind, starts[index], ends[index])
                        for _, _, events, starts, ends in samples]
            if any(len(ts) > count for ts in observed):
                raise ValueError(f'{pid}/{ability}: unexpected extra occurrences')
            for occurrence in range(count):
                observations = [(times[occurrence] - sample[3][index]) / 1000
                                if len(times) > occurrence else None
                                for times, sample in zip(observed, samples)]
                values = [v for v in observations if v is not None]
                if not values:
                    raise ValueError(f'{pid}/{ability}/{occurrence + 1}: never observed')
                name = names[ability]
                slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
                occurrences[slug] = occurrences.get(slug, 0) + 1
                mechanic = {'id': f'{pid}-{slug}-{occurrences[slug]}', 'name': name,
                            'time': clock(median(values)), 'fflogs': {'abilityIds': [ability] + secondary}}
                if visibility == 'minor':
                    mechanic['minor'] = True
                if visibility == 'tank':
                    mechanic['roles'] = ['tank']
                phase['mechanics'].append(mechanic)
                evidence.append((mechanic['id'], kind, observations))
        phase['mechanics'].sort(key=lambda m: tuple(map(int, m['time'].split(':'))))
        encounter['phases'].append(phase)
        baseline += max((s[4][index] - s[3][index]) / 1000 for s in samples)
    mechanics = [m for p in encounter['phases'] for m in p['mechanics']]
    for m, name in zip(mechanics, number_repeated([m['name'] for m in mechanics])):
        m['name'] = name
    output = ROOT / 'packages/encounter-data/fights/dsr/encounter.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(encounter, indent=2) + '\n')
    lines = ['# DSR timing evidence', '', 'Generated by `scripts/reconcile_dsr.py`. Seconds are unrounded.', '',
             '| Report / fight | P2 | P3 | Eyes | Rewind | P5 | P6 | P7 to kill |',
             '| --- | --- | --- | --- | --- | --- | --- | --- |']
    for code, fid, _, starts, ends in samples:
        lines.append(f'| [{code} / {fid}](https://www.fflogs.com/reports/{code}?fight={fid}) | '
                     + ' | '.join(f'{(b-a)/1000:.3f}' for a, b in zip(starts, ends)) + ' |')
    lines += ['', 'Mechanic times use the median phase-relative observation. A dash marks a missing late cast, omitted from that median.', '',
              '| Mechanic | Event | Observations in report order |', '| --- | --- | --- |']
    lines += [f'| {mid} | {kind} | ' + ', '.join(f'{v:.3f}' if v is not None else '-' for v in values) + ' |'
              for mid, kind, values in evidence]
    (ROOT / 'docs/DSR-TIMINGS.md').write_text('\n'.join(lines) + '\n')
    print([(p['id'], p['start'], len(p['mechanics'])) for p in encounter['phases']])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path)
    reconcile(parser.parse_args().cache)
