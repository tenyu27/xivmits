"""Regression checks for source formatting that changes what players press."""
import io
import unittest
import zipfile

from import_fru_mitbutgood import cell_formats, formatted_actions, extras
from fru_tanks import parse_actions


class PartyGridFormattingTest(unittest.TestCase):
    def test_mixed_rich_text_preserves_only_lingering_actions(self):
        ns = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
        with zipfile.ZipFile(io.BytesIO(), 'w') as archive:
            archive.writestr('xl/styles.xml', f'''<styleSheet xmlns="{ns}">
              <fonts><font><color rgb="FF000000"/></font></fonts>
              <cellXfs><xf fontId="0"/></cellXfs></styleSheet>''')
            archive.writestr('xl/sharedStrings.xml', f'''<sst xmlns="{ns}"><si>
              <r><rPr><color rgb="FF666666"/></rPr><t>Fey</t></r>
              <r><t>/Concit/</t></r>
              <r><rPr><color rgb="FF666666"/></rPr><t>Soil</t></r>
              </si></sst>''')
            archive.writestr('xl/worksheets/sheet1.xml', f'''<worksheet xmlns="{ns}">
              <sheetData><row r="27"><c r="E27" t="s"><v>0</v></c></row></sheetData>
              </worksheet>''')
            formats = cell_formats(archive, 'xl/worksheets/sheet1.xml')['E27']
        self.assertEqual(formatted_actions('Fey/Concit/Soil', {}, formats), [
            {'name': 'Fey Illumination', 'carryOver': True},
            {'name': 'Concitation'},
            {'name': 'Sacred Soil', 'carryOver': True},
        ])

    def test_conditional_is_not_a_carryover_and_keeps_footnote(self):
        actions = formatted_actions('Rep**', {'**': 'Catch Fulgent Blade.'}, [(True, True)] * 5)
        self.assertNotIn('carryOver', actions[0])
        self.assertIn('Catch Fulgent Blade.', actions[0]['note'])
        self.assertIn('Conditional', actions[0]['note'])

    def test_typo_and_italic_target_do_not_change_action_meaning(self):
        self.assertEqual(formatted_actions('Seraph/ism', {}, [(False, False)] * 10),
                         [{'name': 'Seraphism'}])
        self.assertEqual(formatted_actions('Feint (Shiva)', {}, [(False, True)] * 13),
                         [{'name': 'Feint', 'note': 'On Shiva.'}])

    def test_unknown_extra_fails_instead_of_disappearing(self):
        with self.assertRaises(ValueError):
            extras('Barrier/New Mit')

    def test_tank_second_hit_keeps_personal_and_buddy_targets_separate(self):
        personal = parse_actions('Kitchen Sink (TBN 2nd hit)')
        self.assertEqual(personal, [
            {'name': 'Kitchen Sink'},
            {'name': 'The Blackest Night', 'note': 'For the second hit.'},
        ])
        buddy = parse_actions('Living Dead\nBuddy Mit 2nd Hit: TBN, Oblation')
        self.assertNotIn('buddy', buddy[0])
        self.assertTrue(all(a['buddy'] for a in buddy[1:]))
        self.assertTrue(all('second hit' in a['note'] for a in buddy[1:]))

    def test_tank_lingering_rampart_does_not_hide_fresh_sheltron(self):
        actions = parse_actions('Rampart, Sheltron', [(True, False)] * 7 + [(False, False)] * 10)
        self.assertEqual(actions, [
            {'name': 'Rampart', 'carryOver': True}, {'name': 'Holy Sheltron'},
        ])


if __name__ == '__main__':
    unittest.main()
