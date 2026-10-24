"""TOP's workbook remains an overlay on the reconciled encounter."""
import unittest

import import_top_topmitty as top
from normalize_sheet import load_encounter


def draft():
    return {'phases': [
        {'id': 'p5', 'mechanics': [
            {'id': 'blind', 'name': 'Blind Faith', 'assignments': {'SCH': [{'name': 'Sacred Soil'}]}},
        ]},
        {'id': 'p6', 'mechanics': [
            {'id': 'magic-1', 'name': 'Magic Number', 'assignments': {'T1': [{'name': 'Tank LB'}]}},
            {'id': 'magic-2', 'name': 'Magic Number', 'assignments': {'T2': [{'name': 'Tank LB'}]}},
        ]},
    ]}


class TopBindingTest(unittest.TestCase):
    def test_blind_faith_stays_at_p5_cast_and_magic_numbers_keep_their_seats(self):
        encounter = load_encounter('top')
        source = draft()
        blind_actions = source['phases'][0]['mechanics'][0]['assignments']
        result = top.bind_party(source, encounter)
        self.assertEqual(result['phases'][0]['mechanics'][0]['mechanicId'], 'p5-blind-faith-1')
        self.assertEqual(result['phases'][0]['mechanics'][0]['assignments'], blind_actions)
        rows = result['phases'][1]['mechanics']
        self.assertEqual([r['mechanicId'] for r in rows],
                         ['p6-magic-number-1', 'p6-magic-number-2'])
        self.assertEqual(list(rows[0]['assignments']), ['T1'])
        self.assertEqual(list(rows[1]['assignments']), ['T2'])
        self.assertEqual(encounter, load_encounter('top'))

    def test_sequence_groups_keep_assignments_and_reference_both_boundaries(self):
        source = draft()
        for version in ('Delta', 'Sigma', 'Omega'):
            source['phases'][0]['mechanics'].append({
                'id': version.lower(), 'name': f'{version} Mech',
                'assignments': {'SCH': [{'name': 'Seraph'}]},
            })
        result = top.bind_party(source, load_encounter('top'))
        for n, row in enumerate(result['phases'][0]['mechanics'][1:], 1):
            version = ('Delta', 'Sigma', 'Omega')[n - 1]
            self.assertEqual(row['mechanicId'], f'p5-hello-distant-world-{n}')
            self.assertEqual(row['group'], {
                'name': f'{version} Mech',
                'after': f'p5-run-mi-{version.lower()}-version-1',
                'before': f'p5-solar-ray-{n * 2 + 1}',
            })
            self.assertEqual(row['assignments'], {'SCH': [{'name': 'Seraph'}]})

    def test_unknown_source_row_fails_instead_of_dropping_assignments(self):
        source = draft()
        source['phases'][1]['mechanics'][0]['name'] = 'Unreviewed row'
        with self.assertRaisesRegex(SystemExit, 'Unmapped TOP party mechanic'):
            top.bind_party(source, load_encounter('top'))

    def test_missing_transition_row_fails_instead_of_silently_losing_it(self):
        source = draft()
        source['phases'][0]['mechanics'] = []
        with self.assertRaisesRegex(SystemExit, 'exactly one P5 Blind Faith'):
            top.bind_party(source, load_encounter('top'))


class TopSyncLevelTest(unittest.TestCase):
    def test_sheet_nebula_is_not_expanded_to_level_92_great_nebula(self):
        # The upstream pairing tabs write "Nebula". TOP syncs to 90; Great
        # Nebula replaces Nebula at 92.
        self.assertNotIn('Nebula', top.TANK_ABILITY)
        self.assertNotIn('Great Nebula', top.TANK_EVERYTHING['GNB'])
        self.assertEqual(
            [action['name'] for action in top.tank_actions('Rampart, Camo, Nebula, HOC', 'GNB')],
            ['Rampart', 'Camouflage', 'Nebula', 'Heart of Corundum'],
        )
        self.assertEqual(
            [action['name'] for action in top.tank_actions('Kitchen Sink', 'GNB')],
            ['Rampart', 'Nebula', 'Camouflage', 'Heart of Corundum'],
        )
        self.assertEqual(
            [action['name'] for action in top.tank_actions('Nebula, HOC', 'GNB')],
            ['Nebula', 'Heart of Corundum'],
        )


if __name__ == '__main__':
    unittest.main()
