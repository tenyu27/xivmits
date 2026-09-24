"""Regression checks against the Ikuya v6.1 assignments and note scopes."""
import json
from pathlib import Path
import unittest

from import_dmu_ikuya import add_press_note, align_tank_rows, omni_blocks, parse_omni_cell
from normalize_sheet import load_encounter


class IkuyaTankTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.encounter = load_encounter('dmu')
        path = Path(__file__).resolve().parents[1] / 'packages/encounter-data/fights/dmu/sheets/ikuya.json'
        cls.sheet = json.loads(path.read_text())

    def test_press_notes_exclude_blank_seats_and_carryovers(self):
        row = {'assignments': {'C': [{'name': 'Addle', 'carryOver': True}],
                               'M2': [{'name': 'Feint'}]}}
        add_press_note(row, 'Use late into the castbar.')
        self.assertNotIn('note', row)
        self.assertNotIn('note', row['assignments']['C'][0])
        self.assertEqual(row['assignments']['M2'][0]['note'], 'Use late into the castbar.')
        for phase in self.sheet['phases']:
            for mechanic in phase['mechanics']:
                self.assertNotIn('castbar', mechanic.get('note', ''))
                for actions in mechanic['assignments'].values():
                    for action in actions:
                        if action.get('carryOver'):
                            self.assertNotIn('Use late into', action.get('note', ''))

    def test_omnitank_blocks_follow_headings_after_inserted_rows(self):
        cells = {}
        for phase, start in enumerate([2, 24, 51, 80, 105], 1):
            cells.update({f'E{start}': f'Phase {phase}: Boss', f'D{start+4}': 'Time',
                          f'B{start+6}': 'Buster', f'B{start+8}': 'Notes'})
        self.assertEqual(omni_blocks(cells), [
            (phase, [start+6], 'split' if phase in (3, 5) else 'seat', start+8, start+4)
            for phase, start in enumerate([2, 24, 51, 80, 105], 1)])
        del cells['E80']
        with self.assertRaisesRegex(ValueError, 'five Omnitank'):
            omni_blocks(cells)

    def test_p1_addle_is_one_press_then_one_carryover(self):
        addles = [(row['mechanicId'], action.get('carryOver', False))
                  for row in self.sheet['phases'][0]['mechanics']
                  for action in row['assignments'].get('C', []) if action['name'] == 'Addle']
        self.assertEqual(addles, [('p1-double-trouble-trap-1', False),
                                 ('p1-light-of-judgment-1', True)])

    def test_v61_tank_timing_notes(self):
        for plan in self.sheet['tankMits']['plans']:
            for row in plan['phases'][2]['mechanics'][:2]:
                self.assertIn('Stray Flames', row['actions'][0]['note'])
            for row in plan['phases'][4]['mechanics']:
                for action in row['actions']:
                    if 'If playing WAR/DRK' in action.get('note', ''):
                        self.assertIn(plan['job'], ['WAR', 'DRK'])
                        self.assertIn(action['name'], ['Holmgang', 'Living Dead'])
                        self.assertFalse(action.get('carryOver', False))

    def test_thunder_rows_do_not_reuse_preceding_party_buster(self):
        # Only sets 1 and 5 exist in the party workbook. Sets 2–4 must
        # retain their own occurrence even with a misleading earlier anchor.
        rows = []
        for source_row in (45, 47, 49, 51, 53):
            for boss in ('chaos', 'exdeath'):
                rows.append({'id': f'drk-p3-r{source_row}-{boss}',
                             'name': 'Thunder III', 'time': '0:51',
                             'after': 'p3-thunder-iii-1',
                             'boss': boss.title(), 'actions': []})
        draft = {'tankMits': {'plans': [{'phases': [{'id': 'p3', 'mechanics': rows}]}]}}
        align_tank_rows(draft, self.encounter)
        self.assertEqual([r['after'] for r in rows],
                         [f'p3-thunder-iii-{n}' for n in range(1, 6) for _ in range(2)])

    def test_every_committed_tank_row_has_the_reviewed_anchor(self):
        # Source order, including both sub-hits of the final Fell Forces.
        expected = {
            'p1': ['p1-revolting-ruin-iii-1', 'p1-hyperdrive-1',
                   'p1-revolting-ruin-iii-2', 'p1-hyperdrive-2'],
            'p2': ['p2-ultimate-embrace-1', 'p2-wings-of-destruction-1', 'p2-ultimate-embrace-2'],
            'p3': [f'p3-thunder-iii-{n}' for n in range(1, 6)] + ['p3-black-hole-10'],
            'p4': [None],
            'p5': ['p5-fell-forces-1', 'p5-maddening-orchestra-1', 'p5-flare-1',
                   'p5-fell-forces-2', 'p5-fell-forces-3', 'p5-maddening-orchestra-2',
                   'p5-flare-2', 'p5-fell-forces-4', 'p5-fell-forces-4'],
        }
        for plan in self.sheet['tankMits']['plans']:
            for phase in plan['phases']:
                with self.subTest(job=plan['job'], phase=phase['id']):
                    self.assertEqual([r.get('after') for r in phase['mechanics']],
                                     [a for a in expected[phase['id']] for _ in range(2)])
                    canonical = {m['id']: m for p in self.encounter['phases']
                                 if p['id'] == phase['id'] for m in p['mechanics']}
                    for row in phase['mechanics']:
                        if row.get('after'):
                            self.assertEqual(row['name'], canonical[row['after']]['name'])
                            self.assertEqual(row['time'], canonical[row['after']]['time'])

    def test_drk_ot_p1_and_both_p3_branches(self):
        plan = next(p for p in self.sheet['tankMits']['plans'] if p['job'] == 'DRK')
        p1 = [r for r in plan['phases'][0]['mechanics'] if r['seat'] == 'OT']
        self.assertEqual(p1[0]['actions'][:2], [
            {'name': 'The Blackest Night', 'buddy': True}, {'name': 'Oblation', 'buddy': True}])
        self.assertEqual(p1[0]['actions'][2]['name'], 'Provoke')
        self.assertEqual([a['name'] for a in p1[1]['actions']],
                         ['Rampart', 'Shadowed Vigil', 'Dark Mind', 'The Blackest Night', 'Oblation'])
        self.assertEqual(p1[2]['actions'], [{'name': 'Living Dead'}])
        self.assertEqual(p1[3]['actions'], [])
        p3 = plan['phases'][2]['mechanics']
        for boss, occurrence in [('Chaos', 2), ('Exdeath', 4)]:
            invulns = [r['after'] for r in p3 if r['boss'] == boss
                       and any(a['name'] == 'Living Dead' for a in r['actions'])]
            self.assertEqual(invulns, [f'p3-thunder-iii-{occurrence}'])

    def test_fell_forces_keeps_solo_and_third_hit_separate(self):
        for plan in self.sheet['tankMits']['plans']:
            rows = [r for r in plan['phases'][4]['mechanics'] if r.get('after') == 'p5-fell-forces-4']
            self.assertEqual([r['tag'] for r in rows], ['Avoid', 'Solo 2 hits', 'Share 3rd hit', 'Share 3rd hit'])
            for row in rows[2:]:
                rampart = next(a for a in row['actions'] if a['name'] == 'Rampart')
                self.assertTrue(rampart['carryOver'])
                self.assertTrue(any(not a.get('carryOver') for a in row['actions']))

    def test_job_scoped_short_mit_and_carryover(self):
        text = 'Rampart + 40% + Short Mit (PLD/DRK) + Provoke ²'
        for job, shorts in [('DRK', ['The Blackest Night', 'Oblation']), ('PLD', ['Holy Sheltron']),
                            ('WAR', []), ('GNB', [])]:
            actions, _ = parse_omni_cell(text, job, {'²': 'Provoke after debuffs apply.'})
            self.assertEqual([a['name'] for a in actions[2:-1]], shorts)
            self.assertIn('debuffs', actions[-1]['note'])
        actions, _ = parse_omni_cell('Short Mit\n➔ Rampart + 40% + 90s', 'DRK', {})
        self.assertEqual([a.get('carryOver', False) for a in actions], [False, False, True, True, True])
        with self.assertRaisesRegex(ValueError, 'Unresolved Omnitank footnote'):
            parse_omni_cell('Invulnerability ⁴', 'DRK', {})


if __name__ == '__main__':
    unittest.main()
