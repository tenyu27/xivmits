"""Tank mitigation from overlapping party and personal source rows."""
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import import_dmu_lpdu as lpdu
import import_top_topmitty as top

ROOT = Path(__file__).resolve().parents[1] / 'packages/encounter-data/fights'


class TankImportTest(unittest.TestCase):
    def test_lpdu_passage_icons_are_one_conditional_pld_use(self):
        sheet = json.loads((ROOT / 'dmu/sheets/lpdu.json').read_text())
        rows = sheet['phases'][2]['mechanics']
        passage = [(row['mechanicId'], slot, action) for row in rows
                   for slot, actions in row['assignments'].items() for action in actions
                   if action['name'].startswith('Passage of Arms')]
        self.assertEqual([row for row, _, _ in passage],
                         ['p3-shocking-impact-1', 'p3-shocking-impact-2'])
        for _, slot, action in passage:
            self.assertEqual(slot, 'OT')
            self.assertEqual(action['name'], 'Passage of Arms (PLD)')
            self.assertIn('Choose one use', action['note'])
        self.assertNotIn(('p3', 'p3-thunder-iii-4'), lpdu.ROW_NOTES)

    def test_no_short_kitchen_sink_excludes_short_cooldowns_for_every_job(self):
        for job in lpdu.TANKS:
            actions = lpdu.moved_actions({'name': 'Kitchen Sink', 'note': 'No short mit.'}, job)
            self.assertEqual({a['name'] for a in actions},
                             {'Rampart', lpdu.MIT_120[job], lpdu.MIT_90[job]})
            full = lpdu.moved_actions({'name': 'Kitchen Sink'}, job)
            self.assertTrue(set(lpdu.SHORT_MIT[job]) <= {a['name'] for a in full})

    def test_lpdu_wings_and_flares_have_one_personal_assignment_per_seat(self):
        sheet = json.loads((ROOT / 'dmu/sheets/lpdu.json').read_text())
        for plan in sheet['tankMits']['plans']:
            for seat in ('MT', 'OT'):
                rows = [r for p in plan['phases'] for r in p['mechanics'] if r['seat'] == seat]
                wings = [r for r in rows if r.get('after') == 'p2-wings-of-destruction-1']
                self.assertEqual(len(wings), 1)
                self.assertFalse(set(lpdu.SHORT_MIT[plan['job']]) & {a['name'] for a in wings[0]['actions']})
                for number, time in [(1, '0:46'), (2, '2:17')]:
                    flares = [r for r in rows if r.get('after') == f'p5-flare-{number}']
                    self.assertEqual(len(flares), 1)
                    self.assertEqual(flares[0]['time'], time)
                    self.assertTrue(all(a.get('note') == 'On the flare.' for a in flares[0]['actions']))
                self.assertFalse(any(a.get('note') == 'On the flare.' for r in rows
                                     if r.get('after', '').startswith('p5-maddening-orchestra')
                                     for a in r['actions']))

    def test_top_preserves_note_continuations_and_job_scoped_footer(self):
        cells = {'C63': 'P5: Dynamis', 'C67': 'WARRIOR', 'G67': 'DARK KNIGHT',
                 'B72': 'Omega Solar Ray', 'C72': 'Rampart', 'G72': 'Rampart',
                 'B76': 'Notes', 'C76': 'Prepop after Sigma.', 'G76': 'Prepop after Sigma.',
                 'C77': 'Healers must mitigate tanks.', 'G77': 'Healers must mitigate tanks.',
                 'C82': 'P6: Alpha Omega', 'C86': 'WARRIOR', 'G86': 'DARK KNIGHT',
                 'B87': 'Cosmo Dive 1', 'C87': 'Rampart', 'G87': 'Rampart',
                 'B91': 'Wave Cannon 2', 'G91': 'Shadow Wall',
                 'D98': 'WAR/DRK: Rampart after Cosmo Arrow.', 'D99': 'DRK: Save MP for TBN.'}
        encounter = json.loads((ROOT / 'top/encounter.json').read_text())
        with patch.object(top, 'TANK_TABS', [('WAR', 'DRK', 'WARDRK')]), \
                patch.object(top, 'read_cells', return_value=(cells, 99)):
            plans = top.convert_tank_tabs(None, [], encounter['phases'])['plans']
        for plan in plans:
            omega = plan['phases'][0]['mechanics'][0]
            self.assertEqual(omega['after'], 'p5-solar-ray-5')
            self.assertEqual(omega['time'], '3:00')
            self.assertEqual(omega['note'], 'Prepop after Sigma. Healers must mitigate tanks.')
            self.assertIn('Rampart after Cosmo Arrow.', plan['phases'][1]['mechanics'][0]['note'])
            notes = ' '.join(m.get('note', '') for m in plan['phases'][1]['mechanics'])
            self.assertEqual('Save MP' in notes, plan['job'] == 'DRK')


if __name__ == '__main__':
    unittest.main()
