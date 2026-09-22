"""DSR source shorthand, continuation lines, and timing variant regressions."""
import unittest

from import_dsr_malachite import parse_actions, party_actions, continuation, validate_party_rows
from reconcile_dsr import clusters, phase_windows


class DsrImportTest(unittest.TestCase):
    def test_source_section_owns_transition_row(self):
        cells = {'D8': 'P2: Thordan', 'B23': 'Final Chorus (Transition)'}
        validate_party_rows('Thordan', cells, [(23, cells['B23'], 'p2-final-chorus-1')])
        with self.assertRaisesRegex(ValueError, 'source phase p2'):
            validate_party_rows('Thordan', cells, [(23, cells['B23'], 'p3-final-chorus-1')])

    def test_final_chorus_finishes_p2_and_alternative_end_opens_p7(self):
        fight = {'endTime': 90000, 'phaseTransitions': [
            {'id': i, 'startTime': i * 10000} for i in range(2, 9)]}
        events = [{'timestamp': 32500, 'abilityGameID': 26377, 'type': 'damage'},
                  {'timestamp': 32500, 'abilityGameID': 26377, 'type': 'damage'},
                  {'timestamp': 79000, 'abilityGameID': 29752, 'type': 'cast'}]
        starts, ends = phase_windows(fight, events)
        self.assertEqual(starts, [20000, 32501, 40000, 50000, 60000, 70000, 79000])
        self.assertEqual(clusters(events, 26377, 'damage', starts[0], ends[0]), [32500])
        self.assertEqual(clusters(events, 26377, 'damage', starts[1], ends[1]), [])
        with self.assertRaisesRegex(ValueError, 'Expected one Final Chorus'):
            phase_windows(fight, events[2:])

    def test_level_90_shields_and_typo_expand_to_real_buttons(self):
        self.assertEqual(parse_actions('ZoeEukrpog/Panhaima/Kerachole'), [
            {'name': 'Zoe'}, {'name': 'Eukrasian Prognosis'},
            {'name': 'Panhaima'}, {'name': 'Kerachole'},
        ])
        self.assertEqual(parse_actions('Camoflauce, Heart of Corrundum'), [
            {'name': 'Camouflage'}, {'name': 'Heart of Corundum'},
        ])

    def test_buddy_actions_do_not_turn_personals_into_buddy_mits(self):
        actions = parse_actions('Rampart, Sentinel, Sheltron\nBuddy Mit: Intervention')
        self.assertTrue(all('buddy' not in a for a in actions[:3]))
        self.assertEqual(actions[-1], {'name': 'Intervention', 'buddy': True, 'note': 'On your co-tank.'})

    def test_optional_actions_and_early_timing_survive_second_grid_line(self):
        actions = parse_actions('Succor/Soil')
        continuation(actions, 'Early Soil (After 2nd Melee Auto)')
        continuation(actions, '(Spreadlo Optional)')
        self.assertEqual(len([a for a in actions if a['name'] == 'Sacred Soil']), 1)
        self.assertEqual(actions[1]['note'], 'Use Sacred Soil early, after the second melee auto.')
        self.assertEqual(actions[2], {'name': 'Deployment Tactics', 'note': 'Deployment Tactics is optional.'})
        continuation(actions, 'Rep')
        self.assertEqual(actions[-1], {'name': 'Reprisal'})

    def test_source_target_and_optional_feint_remain_explicit(self):
        self.assertEqual(party_actions('*Can Feint\nHallowed Plume'), [
            {'name': 'Feint', 'note': 'Optional; use on Hallowed Plume.'},
        ])
        actions = party_actions('Personals on Melee 2')
        self.assertTrue(all(a['buddy'] and a['note'] == 'On M2.' for a in actions))

    def test_unknown_source_content_fails(self):
        with self.assertRaises(ValueError):
            parse_actions('New Mit')
        with self.assertRaises(ValueError):
            continuation([], 'Use an unreviewed new cooldown')
        with self.assertRaises(ValueError):
            validate_party_rows('Thordan', {'B15': 'Known', 'B17': 'New mechanic'}, [(15, 'Known', 'id')])

    def test_random_wing_and_swing_variants_share_occurrence_order(self):
        events = [{'timestamp': t, 'abilityGameID': a, 'type': 'begincast'}
                  for t, a in [(1000, 27940), (1000, 27940), (20000, 27943)]]
        self.assertEqual(clusters(events, 27939, 'begincast', 0, 30000), [1000, 20000])
        events = [{'timestamp': 1000, 'abilityGameID': 25537, 'type': 'begincast'},
                  {'timestamp': 9000, 'abilityGameID': 25536, 'type': 'begincast'}]
        self.assertEqual(clusters(events, 25536, 'begincast', 0, 10000), [1000, 9000])

    def test_brightwing_pairs_are_not_collapsed_into_one_sequence(self):
        events = [{'timestamp': t, 'abilityGameID': 25369, 'type': 'damage'}
                  for t in [1000, 1040, 6100, 6140, 11200, 11240, 16300, 16340]]
        self.assertEqual(clusters(events, 25369, 'damage', 0, 20000), [1000, 6100, 11200, 16300])


if __name__ == '__main__':
    unittest.main()
