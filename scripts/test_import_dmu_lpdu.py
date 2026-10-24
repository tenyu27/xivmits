"""LPDU shorthand: ranged 90s, level-100 Succor, and the P3 row order."""
import json
from pathlib import Path
import unittest

from import_dmu_lpdu import expand


ROOT = Path(__file__).resolve().parents[1]
SHEET = ROOT / 'packages/encounter-data/fights/dmu/sheets/lpdu.json'


class LpduImportTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sheet = json.loads(SHEET.read_text())

    def test_ranged_90s_is_party_mit(self):
        # Column V is the physical-ranged seat. "90s" there is Troubadour,
        # Tactician, or Shield Samba, not a tank cooldown.
        self.assertEqual(expand('90s', 'V'), [{'name': 'Party Mit'}])
        self.assertEqual(expand('90s', 'E'), [{'name': '90s Mit'}])
        self.assertEqual(expand('90s'), [{'name': '90s Mit'}])
        for phase in self.sheet['phases']:
            for mechanic in phase['mechanics']:
                for action in mechanic['assignments'].get('P', []):
                    self.assertNotEqual(action['name'], '90s Mit', mechanic['mechanicId'])

    def test_succor_maps_to_concitation(self):
        # Succor Mastery (trait 628) replaces Succor with Concitation at 96.
        # DMU syncs to 100, so the sheet names the button the player presses.
        self.assertEqual(expand('Succor'), [{'name': 'Concitation'}])
        self.assertEqual(expand('Succor(s)'), [{'name': 'Concitation'}])
        self.assertNotIn('"Succor"', SHEET.read_text())
        named = [action['name']
                 for phase in self.sheet['phases']
                 for mechanic in phase['mechanics']
                 for actions in mechanic['assignments'].values()
                 for action in actions]
        self.assertIn('Concitation', named)
        self.assertNotIn('Succor', named)

    def test_p3_keeps_the_compile_row_order_for_two_boss_tracks(self):
        # The compile lists Exdeath's Thunder III / Stack rows above the beam
        # rows whose encounter times are earlier. That is the spreadsheet, not
        # a mis-sorted mechanic list: row 42 is "Thunder III (5th Set)" and
        # row 44 is "3rd beams"; row 46 is "Stack/Roles 3" and row 48 is
        # "4th beams". The sheet JSON keeps that row order. The viewer follows
        # the encounter clock instead (see the encounter-data test).
        ids = [mechanic['mechanicId']
               for mechanic in next(phase for phase in self.sheet['phases'] if phase['id'] == 'p3')['mechanics']]
        self.assertLess(ids.index('p3-thunder-iii-5'), ids.index('p3-black-hole-5'))
        self.assertLess(ids.index('p3-shocking-impact-3'), ids.index('p3-black-hole-6'))
