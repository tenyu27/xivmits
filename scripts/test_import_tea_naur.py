"""Parser and timeline checks for the NAUR TEA import. No workbook required."""
import json
import re
import unittest
from pathlib import Path

from import_tea_naur import (
    ENCOUNTER_PATH, FORBIDDEN, build_encounter, clock, extra_actions, parse_actions,
)

ROOT = Path(__file__).resolve().parents[1]


class ParserTest(unittest.TestCase):
    def test_generics_and_level_80_names(self):
        self.assertEqual(parse_actions('MT', '90s/Short/Reprisal'), [
            {'name': '90s Mit'}, {'name': 'Short Mit'}, {'name': 'Reprisal'},
        ])
        self.assertEqual(parse_actions('MT', '120s/Short'), [
            {'name': '120s Mit'}, {'name': 'Short Mit'},
        ])
        self.assertEqual(parse_actions('SGE', 'Physis/Ixo'), [
            {'name': 'Physis II'}, {'name': 'Ixochole'},
        ])
        self.assertEqual(parse_actions('SGE', 'ZoeEProg -8s'), [
            {'name': 'Zoe', 'note': '8 seconds before.'},
            {'name': 'Eukrasian Prognosis', 'note': '8 seconds before.'},
        ])
        self.assertEqual(parse_actions('AST', 'Synastry+Benefic 2(MT)/ED(MT)'), [
            {'name': 'Synastry', 'note': 'On the main tank.'},
            {'name': 'Benefic II', 'note': 'On the main tank.'},
            {'name': 'Essential Dignity', 'note': 'On the main tank.'},
        ])
        self.assertEqual(parse_actions('AST', 'Synastry+Benefic2(MT)'), [
            {'name': 'Synastry', 'note': 'On the main tank.'},
            {'name': 'Benefic II', 'note': 'On the main tank.'},
        ])

    def test_offset_stays_on_its_segment_and_star_placement_is_kept(self):
        self.assertEqual(parse_actions('WHM', 'Regen/Benison(MT) -5s'), [
            {'name': 'Regen'},
            {'name': 'Divine Benison', 'note': 'On the main tank. 5 seconds before.'},
        ])
        self.assertEqual(
            parse_actions('AST', 'Horoscope/Intersection(MT) -15s /Star Place on Pull'),
            [
                {'name': 'Horoscope'},
                {'name': 'Celestial Intersection', 'note': 'On the main tank. 15 seconds before.'},
                {'name': 'Earthly Star', 'note': 'Place it on the pull.'},
            ],
        )
        self.assertEqual(parse_actions('AST', 'Star Place(#6)'), [
            {'name': 'Earthly Star', 'note': 'Place it on player 6.'},
        ])
        self.assertEqual(parse_actions('AST', 'Star Place'), [
            {'name': 'Earthly Star', 'note': 'Place it.'},
        ])

    def test_whole_cell_calls_and_extras(self):
        self.assertEqual(parse_actions('OT', '(TBN on CD)'), [
            {'name': 'The Blackest Night (DRK)', 'note': 'On cooldown.'},
        ])
        self.assertEqual(parse_actions('P', '(Party Mit)'), [
            {'name': 'Party Mit', 'note': 'Optional.'},
        ])
        self.assertEqual(parse_actions('MT', 'Reprisal (On BJ)/Short'), [
            {'name': 'Reprisal', 'note': 'On Brute Justice.'},
            {'name': 'Short Mit'},
        ])
        self.assertEqual([slot for slot, _action in extra_actions('PLD Wings')], ['MT', 'OT'])
        self.assertEqual(extra_actions('Dismantle')[0][1]['name'], 'Extra (MCH)')
        names = {action['name'] for _slot, action in extra_actions('(Minne/Mantra)')}
        self.assertEqual(names, {"Nature's Minne (BRD)", 'Mantra (MNK)'})

    def test_everything_is_the_level_80_kit(self):
        names = {action['name'] for action in parse_actions('SGE', 'Everything')}
        self.assertIn('Physis II', names)
        self.assertIn('Eukrasian Prognosis', names)
        self.assertNotIn('Eukrasian Prognosis II', names)
        for slot in ('SCH', 'SGE', 'WHM', 'AST'):
            for action in parse_actions(slot, 'Everything'):
                self.assertNotIn(action['name'], FORBIDDEN)

    def test_unknown_token_target_or_extra_fails(self):
        with self.assertRaises(ValueError):
            parse_actions('SCH', 'Expedient')
        with self.assertRaises(ValueError):
            parse_actions('WHM', 'Aquaveil')
        with self.assertRaises(ValueError):
            parse_actions('MT', 'Short (somewhere)')
        with self.assertRaises(ValueError):
            extra_actions('Barrier')

    def test_clock_rounds_halves_up_past_binary_error(self):
        self.assertEqual(clock(19.5), '0:20')
        self.assertEqual(clock(1247.6 - 909.1), '5:39')
        self.assertEqual(clock(521.5 - 500), '0:22')


class EncounterTest(unittest.TestCase):
    def test_committed_encounter_matches_the_builder(self):
        self.assertEqual(json.loads(ENCOUNTER_PATH.read_text(encoding='utf-8')), build_encounter())

    def test_phase_clocks_and_sync(self):
        fight = build_encounter()
        self.assertEqual(fight['syncLevel'], 80)
        self.assertEqual(fight['released'], '2019-11-12')
        self.assertEqual(fight['fflogs']['encounterIds'], [1062, 1075])
        self.assertEqual([(phase['id'], phase.get('start')) for phase in fight['phases']], [
            ('p1', '0:00'), ('lc', None), ('p2', None), ('p3', None), ('p4', None),
        ])
        by_id = {mechanic['id']: mechanic for phase in fight['phases'] for mechanic in phase['mechanics']}
        self.assertEqual(by_id['p1-cascade-1']['time'], '0:20')
        self.assertEqual(by_id['lc-limit-cut-1']['time'], '0:07')
        self.assertEqual(by_id['p2-j-kick-1']['time'], '0:00')
        self.assertEqual(by_id['p3-j-wave-0']['time'], '3:29')
        self.assertEqual(by_id['p3-j-wave-8']['time'], '3:54')
        self.assertEqual(by_id['p3-divine-judgment-1']['time'], '4:47')
        self.assertEqual(by_id['p1-splash-1']['fflogs']['abilityIds'], [])
        self.assertEqual(by_id['p3-j-wave-0']['fflogs']['abilityIds'], [])
        self.assertTrue(all(mechanic['fflogs']['abilityIds'] or mechanic['id'] in {
            'p1-prepull', 'p1-splash-1', 'p1-splash-2', 'p2-apocalyptic-ray-1',
            'p3-j-wave-0', 'p3-j-wave-4', 'p3-j-wave-6', 'p3-j-wave-8',
        } for mechanic in by_id.values()))

    def test_unnumbered_mechanic_names_are_unique(self):
        names = [mechanic['name'] for phase in build_encounter()['phases'] for mechanic in phase['mechanics']]
        unnumbered = [name for name in names if not re.search(r'\(\d+\)$|\b\d+(?:st|nd|rd|th)?\b', name, re.I)]
        self.assertEqual(len(unnumbered), len(set(unnumbered)))

    def test_sheet_rows_name_mechanics_the_encounter_has(self):
        from import_tea_naur import ROWS
        ids = {mechanic['id'] for phase in build_encounter()['phases'] for mechanic in phase['mechanics']}
        for _tab, _row, phase, mechanic_id, _title in ROWS:
            self.assertIn(mechanic_id, ids)
            self.assertTrue(mechanic_id.startswith(f'{phase}-') or (phase == 'lc' and mechanic_id.startswith('lc-')))


if __name__ == '__main__':
    unittest.main()
