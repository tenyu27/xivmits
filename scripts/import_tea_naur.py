"""Convert the NAUR TEA mitigation workbook into reviewed repo JSON.

Usage:
  python3 scripts/import_tea_naur.py              # fetch the live workbook, write the sheet
  python3 scripts/import_tea_naur.py --xlsx PATH  # read a local export instead
  python3 scripts/import_tea_naur.py --write-encounter

The encounter timeline is not derived from the workbook. `build_encounter`
records the fight (wiki names, cactbot clock and ability ids) and a normal run
never writes it — pass `--write-encounter` to regenerate the committed file.
The sheet is an overlay of `{mechanicId, note?, assignments}` on that timeline.

Clocks after P1 are phase-relative. The cactbot timeline jumps (Liquid Hand
removed at 196s, Temporal Stasis sync at 492s, Final Word sync at 900s), so
only Living Liquid begins at pull time 0:00. Limit Cut is its own phase even
though the workbook files that row at the end of P1: its clock starts at the
Hawk Blaster anchor, not on the P1 pull.

J Waves have one 50s bar in the timeline, not a hit time each. Wave i is placed
at an even split, `705.7 + (i + 1) * (50 / 16)`, so wave 0 is the first hit
after J Storm.
"""
import argparse
import json
import math
import re
from pathlib import Path

import workbook
from import_fru_mitbutgood import read_cells

ROOT = Path(__file__).resolve().parents[1]
ENCOUNTER_PATH = ROOT / 'packages/encounter-data/fights/tea/encounter.json'
SHEET_PATH = ROOT / 'packages/encounter-data/fights/tea/sheets/naur.json'

SHEET_ID = '1A58RflNeNq9mesuvSEcQzIvQ3MwOGyvPRi5khNACrc8'
SOURCE_URL = ('https://docs.google.com/spreadsheets/d/'
              '1A58RflNeNq9mesuvSEcQzIvQ3MwOGyvPRi5khNACrc8/edit'
              '?gid=1511755464#gid=1511755464')

COLUMNS = {'C': 'MT', 'D': 'OT', 'E': 'SCH', 'F': 'SGE', 'G': 'WHM', 'H': 'AST',
           'I': 'M1', 'J': 'M2', 'K': 'P', 'L': 'C'}
HEALERS = ['SCH', 'SGE', 'WHM', 'AST']
ROLES = {'MT': 'tank', 'OT': 'tank', **{job: 'healer' for job in HEALERS},
         'M1': 'melee', 'M2': 'melee', 'P': 'ranged', 'C': 'caster'}

# Output names a level-80 duty must not assign. Checked on every produced
# action so a shorthand expansion cannot smuggle in a later button.
FORBIDDEN = {
    'Holy Sheltron', 'Bloodwhetting', 'Heart of Corundum', 'Oblation',
    'Aquaveil', 'Liturgy of the Bell', 'Exaltation', 'Expedient',
    'Magick Barrier', 'Macrocosmos', 'Concitation', 'Medica III',
    'Helios Conjunction', 'Eukrasian Prognosis II', 'Physis',
    'Krasis', 'Pneuma', 'Protraction', 'Divine Caress',
}

# "Everything" is the healer's raid-mit kit at 80. Later additions (Expedient,
# Liturgy of the Bell, Aquaveil, Exaltation, Macrocosmos, Physis) are not here.
EVERYTHING = {
    'SCH': ['Sacred Soil', 'Fey Illumination', 'Whispering Dawn', 'Fey Blessing',
            'Summon Seraph', 'Indomitability', 'Deployment Tactics'],
    'SGE': ['Kerachole', 'Ixochole', 'Holos', 'Panhaima', 'Eukrasian Prognosis', 'Physis II'],
    'WHM': ['Temperance', 'Plenary Indulgence', 'Asylum', 'Assize', 'Medica II'],
    'AST': ['Collective Unconscious', 'Neutral Sect', 'Earthly Star',
            'Celestial Opposition', 'Horoscope'],
}

# Workbook token -> in-game name. Physis is Physis II at 80 (trait 510, level
# 60). Benefic 2 is still Benefic II. Seraph is the summon, not the veil.
TOKENS = {
    '90s': ['90s Mit'], 'Short': ['Short Mit'], '120s': ['120s Mit'],
    'Party Mit': ['Party Mit'], 'Invuln': ['Invuln'], 'Reprisal': ['Reprisal'],
    'Rampart': ['Rampart'], 'Feint': ['Feint'], 'Addle': ['Addle'],
    'LB3': ['Tank LB'], 'Succor': ['Succor'], 'Soil': ['Sacred Soil'],
    'Dissipation': ['Dissipation'], 'Dissipate': ['Dissipation'],
    'Kera': ['Kerachole'], 'Physis': ['Physis II'], 'Ixo': ['Ixochole'],
    'Indom': ['Indomitability'], 'Assize': ['Assize'], 'Benison': ['Divine Benison'],
    'CU': ['Collective Unconscious'], 'Benediction': ['Benediction'],
    'Synastry': ['Synastry'], 'Benefic 2': ['Benefic II'], 'Benefic2': ['Benefic II'],
    'ED': ['Essential Dignity'], 'Reci': ['Recitation'], 'Adlo': ['Adloquium'],
    'Deploy': ['Deployment Tactics'], 'Spreadlo': ['Deployment Tactics'],
    'Whisper': ['Whispering Dawn'], 'EProg': ['Eukrasian Prognosis'],
    'Holos': ['Holos'], 'Temperance': ['Temperance'], 'Plenary': ['Plenary Indulgence'],
    'Neutral': ['Neutral Sect'], 'Horoscope': ['Horoscope'], 'Bless': ['Fey Blessing'],
    'Tauro': ['Taurochole'], 'Haima': ['Haima'], 'Tetra': ['Tetragrammaton'],
    'Intersection': ['Celestial Intersection'], 'Opposition': ['Celestial Opposition'],
    'TBN': ['The Blackest Night'], 'Kardia': ['Kardia'], 'Soteria': ['Soteria'],
    'Illum': ['Fey Illumination'], 'Seraph': ['Summon Seraph'],
    'Seraph1': ['Summon Seraph'], 'Seraph2': ['Summon Seraph'],
    'Asylum': ['Asylum'], 'Excog': ['Excogitation'], 'Panhaima': ['Panhaima'],
    'Med2': ['Medica II'], 'AspHelios': ['Aspected Helios'], 'Helios': ['Helios'],
    'Cure3': ['Cure III'], 'Regen': ['Regen'], 'Druo': ['Druochole'],
    'EDiag': ['Eukrasian Diagnosis'], 'Zoe': ['Zoe'],
    'ZoeEProg': ['Zoe', 'Eukrasian Prognosis'], 'Fairy Tether': ['Fey Union'],
    'Star Place': ['Earthly Star'], 'defensive Cards': ['Defensive cards'],
    'Kitchen Sink': ['Kitchen Sink'],
}

SERAPH_NOTES = {
    'Seraph1': 'First Summon Seraph.',
    'Seraph2': 'Second Summon Seraph.',
}

TARGET_NOTES = {
    'MT': 'On the main tank.',
    'OT': 'On the off tank.',
    'to MT': 'On the main tank.',
    'to OT': 'On the off tank.',
    'Tank': 'On a tank.',
    'Tanks': 'On the tanks.',
    'Ranged': 'On a ranged player.',
    'DPS': 'On a DPS.',
    'On BJ': 'On Brute Justice.',
    'Late': 'Late.',
    'if 7 people': 'If 7 people.',
    '#6': 'On player 6.',
}

# (tab, row, phase id, mechanic id, workbook title). Titles are checked, not trusted.
ROWS = [
    ('LLBJCC', 12, 'p1', 'p1-prepull', 'Prepull'),
    ('LLBJCC', 14, 'p1', 'p1-fluid-swing-1', 'Fluid Swing'),
    ('LLBJCC', 16, 'p1', 'p1-cascade-1', 'Cascade'),
    ('LLBJCC', 18, 'p1', 'p1-fluid-swing-2', 'Fluid Swing'),
    ('LLBJCC', 20, 'p1', 'p1-jagd-dolls-1', 'Doll Feeds'),
    ('LLBJCC', 22, 'p1', 'p1-fluid-swing-3', 'Fluid Swing'),
    ('LLBJCC', 24, 'p1', 'p1-protean-wave-1', 'Protean 1'),
    ('LLBJCC', 26, 'p1', 'p1-splash-1', 'Splashes + Drainage'),
    ('LLBJCC', 28, 'p1', 'p1-cascade-2', 'Cascade'),
    ('LLBJCC', 30, 'p1', 'p1-protean-wave-2', 'Protean 2'),
    ('LLBJCC', 32, 'lc', 'lc-limit-cut-1', 'Limit Cut'),
    ('LLBJCC', 48, 'p2', 'p2-j-kick-1', 'JKick'),
    ('LLBJCC', 50, 'p2', 'p2-whirlwind-1', 'Whirlwind'),
    ('LLBJCC', 52, 'p2', 'p2-photon-1', 'Photon'),
    ('LLBJCC', 54, 'p2', 'p2-compressed-water-1', 'Water 1'),
    ('LLBJCC', 56, 'p2', 'p2-hidden-minefield-1', 'Mines'),
    ('LLBJCC', 58, 'p2', 'p2-compressed-water-2', 'Water 2'),
    ('LLBJCC', 60, 'p2', 'p2-limit-cut-2', 'Limit Cut + Flarethrower'),
    ('LLBJCC', 62, 'p2', 'p2-whirlwind-2', 'Whirlwind'),
    ('LLBJCC', 64, 'p2', 'p2-compressed-water-3', 'Water 3'),
    ('LLBJCC', 66, 'p2', 'p2-gavel-1', 'Gavel Lineup'),
    ('LLBJCC', 68, 'p2', 'p2-photon-2', 'Photon'),
    ('LLBJCC', 70, 'p2', 'p2-double-rocket-punch-1', 'Double Rocket Punch'),
    ('LLBJCC', 72, 'p2', 'p2-whirlwind-3', 'Whirlwind'),
    ('Alex PrimePA', 11, 'p3', 'p3-temporal-stasis-1', 'Timestop'),
    ('Alex PrimePA', 13, 'p3', 'p3-chastening-heat-1', 'Chastening Heat + Cleaves'),
    ('Alex PrimePA', 15, 'p3', 'p3-judgment-crystal-1', 'Inception (Crystals Boom)'),
    ('Alex PrimePA', 17, 'p3', 'p3-super-jump-2', 'Super Jump'),
    ('Alex PrimePA', 19, 'p3', 'p3-chastening-heat-2', 'Chastening Heat'),
    ('Alex PrimePA', 21, 'p3', 'p3-divine-spear-2', 'Cleaves'),
    ('Alex PrimePA', 23, 'p3', 'p3-wormhole-formation-1', 'Wormhole'),
    ('Alex PrimePA', 25, 'p3', 'p3-incinerating-heat-1', 'Post-Wormhole Stack'),
    ('Alex PrimePA', 27, 'p3', 'p3-mega-holy-1', 'Mega Holy'),
    ('Alex PrimePA', 29, 'p3', 'p3-j-storm-1', 'JKick'),
    ('Alex PrimePA', 31, 'p3', 'p3-j-wave-0', 'Jwaves (0-3)'),
    ('Alex PrimePA', 33, 'p3', 'p3-j-wave-4', 'Jwaves (4)'),
    ('Alex PrimePA', 35, 'p3', 'p3-j-wave-6', 'Jwaves (6)'),
    ('Alex PrimePA', 37, 'p3', 'p3-j-wave-8', 'Jwaves (8)'),
    ('Alex PrimePA', 39, 'p3', 'p3-divine-judgment-1', 'Transition Raidwide'),
    ('Alex PrimePA', 52, 'p4', 'p4-optical-sight-1', 'Optical Sight (Stack/Spread)'),
    ('Alex PrimePA', 54, 'p4', 'p4-ordained-capital-punishment-1', 'Ordained Capital Punishment'),
    ('Alex PrimePA', 56, 'p4', 'p4-fate-calibration-beta-1', 'Fate Calibration Beta'),
    ('Alex PrimePA', 58, 'p4', 'p4-ordained-capital-punishment-2', 'Ordained Capital Punishment'),
    ('Alex PrimePA', 60, 'p4', 'p4-irresistible-grace-1', 'Irresistable Grace 1'),
    ('Alex PrimePA', 62, 'p4', 'p4-ordained-capital-punishment-3', 'Ordained Capital Punishment'),
    ('Alex PrimePA', 64, 'p4', 'p4-irresistible-grace-2', 'Irresistable Grace 2'),
]

# Caret and prose cells. A caret amends the earlier press in that column; it is
# not an action on the row it sits on. `slots` is where the note lands.
CARETS = {
    ('LLBJCC', 'K22'): ('p1-jagd-dolls-1', 'K', 'If playing MCH.', '(^ if MCH)'),
    ('LLBJCC', 'L28'): ('p1-splash-1', 'L', 'On Living Liquid.', '(^on LL)'),
    ('LLBJCC', 'M28'): ('p1-splash-1', 'M', 'On Living Liquid.', '(^on LL)'),
    ('LLBJCC', 'K57'): ('p2-hidden-minefield-1', 'K', 'Press it when Enumeration goes off.', '(press it when'),
    ('LLBJCC', 'L60'): ('p2-compressed-water-2', 'L', 'On Brute Justice.', '(^on BJ)'),
    ('LLBJCC', 'M64'): ('p2-whirlwind-2', 'M', 'On Cruise Chaser.', '(^on CC)'),
    ('LLBJCC', 'M72'): ('p2-double-rocket-punch-1', 'M', 'On your co-tank.', '(^to other Tank)'),
    ('Alex PrimePA', 'C38'): ('p3-j-wave-8', 'C', 'Whenever it is up.', '(whenever its up)'),
}
# The rest of the Mines party-mit sentence, split across the next row's cell.
CONTINUATION_TAILS = {('LLBJCC', 'K58'): 'Enum goes off)'}

PROSE = {
    ('LLBJCC', 'F21'): 'press Holos',
    ('LLBJCC', 'C34'): 'Note: Doll feeds',
    ('LLBJCC', 'C44'): 'A tip for Soil',
    ('Alex PrimePA', 'C41'): 'Note: If a Warrior',
}

MECHANIC_NOTES = {
    'p1-jagd-dolls-1': (
        'Press Holos, Kerachole, Sacred Soil, or Temperance once the first doll AoEs go off.',
        ['healer'],
    ),
    'p1-splash-1': ('Also covers Drainage.', None),
    'p2-hidden-minefield-1': ('Enumeration follows.', None),
    'p2-limit-cut-2': ('Flarethrower follows.', None),
    'p2-whirlwind-3': ('Second Whirlwind follows.', None),
    'p3-chastening-heat-1': ('Divine Spear cleaves follow.', None),
    'p3-mega-holy-1': ('Second Mega Holy follows.', None),
    'p3-j-wave-0': ('Covers J Waves 0 through 3.', None),
    'p4-optical-sight-1': ('Second Optical Sight follows.', None),
    'p4-ordained-capital-punishment-1': ('Ordained Punishment follows.', None),
    'p4-ordained-capital-punishment-2': ('Ordained Punishment follows.', None),
    'p4-ordained-capital-punishment-3': ('Ordained Punishment follows.', None),
}

PHASE_NOTES = {
    'p1': (
        'Doll feeds and Protean 2 can be tough on healers. Ranged DPS, please use '
        'personals on doll feeds, and melee DPS, please use personals on Protean 2 '
        '(Second Wind, Manaward, Radiant Aegis, Riddle of Earth, Shade Shift).',
        None,
    ),
    'p2': (
        'Once the first water debuff hits 14 seconds, press Sacred Soil or Kerachole, '
        'then on cooldown to cover the rest. This is immediately after Photon.',
        ['healer'],
    ),
    'p3': (
        'If a Warrior is in the party, both tanks can swap mits and roles for this phase.',
        ['tank'],
    ),
}

HEADER_ROWS = {'LLBJCC': (10, 46), 'Alex PrimePA': (9, 50)}
HEADER_PREFIX = {
    'C': 'Tank 1', 'D': 'Tank 2', 'E': 'Scholar', 'F': 'Sage', 'G': 'White Mage',
    'H': 'Astrologian', 'I': 'Melee 1', 'J': 'Melee 2', 'K': 'Phys Range',
    'L': 'Caster', 'M': 'Extras',
}
LABELS = {
    ('LLBJCC', 'D5'): 'P1: Living Liquid / Hand',
    ('LLBJCC', 'D39'): 'P2: Brute Justice / Cruise Chaser',
    ('Alex PrimePA', 'D4'): 'P3: Alexander Prime',
    ('Alex PrimePA', 'D45'): 'P4: Perfect Alexander',
}
CREDITS = {
    ('LLBJCC', 'E2'): 'for questions',
    ('LLBJCC', 'I2'): 'edited for NAUR',
    ('LLBJCC', 'I3'): 'reworked on',
}


def clock(seconds):
    """m:ss, halves rounded away from zero. The schema allows no fractional time.

    The epsilon keeps a binary fraction that landed just under n.5 (1247.6 - 909.1)
    from rounding down.
    """
    total = math.floor(seconds + 0.5 + 1e-6) if seconds >= 0 else math.ceil(seconds - 0.5 - 1e-6)
    return f'{int(total) // 60}:{int(total) % 60:02d}'


def ability_id(hex_id):
    return int(hex_id, 16)


def mechanic(mechanic_id, name, at, ability_ids=(), roles=None, minor=False):
    row = {'id': mechanic_id, 'name': name, 'time': clock(at)}
    if roles:
        row['roles'] = list(roles)
    if minor:
        row['minor'] = True
    row['fflogs'] = {'abilityIds': [ability_id(item) if isinstance(item, str) else item
                                     for item in ability_ids]}
    return row


def build_encounter():
    """The fight, independent of any mit sheet.

    Times are seconds from each phase anchor: P1 at pull, Limit Cut at the
    200.0 Hawk Blaster sync, P2 at J Kick 226.1, P3 at Temporal Stasis 500.0,
    P4 at The Final Word 909.1. Ability ids are the cactbot timeline's.
    """
    p1 = 0.0
    lc = 200.0
    p2 = 226.1
    p3 = 500.0
    p4 = 909.1
    tank = ['tank']
    return {
        'id': 'tea',
        'name': 'The Epic of Alexander (Ultimate)',
        'shortName': 'TEA',
        'type': 'Ultimate',
        'released': '2019-11-12',
        'syncLevel': 80,
        'fflogs': {'encounterIds': [1062, 1075]},
        'phases': [
            {
                'id': 'p1', 'label': 'P1', 'name': 'Living Liquid', 'start': '0:00',
                'mechanics': [
                    mechanic('p1-prepull', 'Prepull', 0),
                    mechanic('p1-fluid-swing-1', 'Fluid Swing 1', 11.4 - p1, ['49B0'], tank),
                    mechanic('p1-cascade-1', 'Cascade 1', 19.5 - p1, ['4826']),
                    mechanic('p1-hand-of-prayer-1', 'Hand of Prayer 1', 35.8 - p1, ['482B', '482C'], minor=True),
                    mechanic('p1-fluid-swing-2', 'Fluid Swing 2', 37.7 - p1, ['49B0', '49B7'], tank),
                    mechanic('p1-jagd-dolls-1', 'Jagd Dolls 1', 39.7 - p1, ['481E']),
                    mechanic('p1-embolus-1', 'Embolus 1', 41.6 - p1, ['4829'], minor=True),
                    mechanic('p1-hand-of-pain-1', 'Hand of Pain 1', 42.8 - p1, ['482D'], minor=True),
                    mechanic('p1-jagd-dolls-2', 'Jagd Dolls 2', 50.3 - p1, ['481E'], minor=True),
                    mechanic('p1-fluid-swing-3', 'Fluid Swing 3', 56.7 - p1, ['49B0', '49B7'], tank),
                    mechanic('p1-protean-wave-1', 'Protean Wave 1', 69.8 - p1, ['4822', '4823']),
                    mechanic('p1-hand-of-pain-2', 'Hand of Pain 2', 70.0 - p1, ['482D'], minor=True),
                    mechanic('p1-sluice-1', 'Sluice 1', 74.9 - p1, ['49B1'], minor=True),
                    mechanic('p1-splash-1', 'Splash 1', 81.1 - p1),
                    mechanic('p1-drainage-1', 'Drainage', 86.6 - p1, ['4827'], tank, minor=True),
                    mechanic('p1-hand-of-pain-3', 'Hand of Pain 3', 89.1 - p1, ['482D'], minor=True),
                    mechanic('p1-cascade-2', 'Cascade 2', 91.7 - p1, ['4826']),
                    mechanic('p1-throttle-1', 'Throttle', 95.9 - p1, ['4828'], minor=True),
                    mechanic('p1-protean-wave-2', 'Protean Wave 2', 107.0 - p1, ['4822', '4823']),
                    mechanic('p1-hand-of-pain-4', 'Hand of Pain 4', 109.0 - p1, ['482D'], minor=True),
                    mechanic('p1-sluice-2', 'Sluice 2', 112.0 - p1, ['49B1'], minor=True),
                    mechanic('p1-embolus-2', 'Embolus 2', 119.1 - p1, ['4829'], minor=True),
                    mechanic('p1-hand-of-prayer-2', 'Hand of Prayer 2', 124.2 - p1, ['482B', '482C'], minor=True),
                    mechanic('p1-splash-2', 'Splash 2', 127.4 - p1, minor=True),
                    mechanic('p1-hand-of-pain-5', 'Hand of Pain 5', 129.3 - p1, ['482D'], minor=True),
                    mechanic('p1-fluid-swing-4', 'Fluid Swing 4', 134.1 - p1, ['49B0'], tank, minor=True),
                    mechanic('p1-cascade-enrage-1', 'Cascade Enrage', 142.1 - p1, ['49B3'], minor=True),
                ],
            },
            {
                'id': 'lc', 'label': 'LC', 'name': 'Limit Cut',
                'mechanics': [
                    mechanic('lc-hawk-blaster-1', 'Hawk Blaster 1', 200.0 - lc, ['4830'], minor=True),
                    mechanic('lc-limit-cut-1', 'Limit Cut 1', 207.4 - lc, ['4834', '4B4F']),
                ],
            },
            {
                'id': 'p2', 'label': 'P2', 'name': 'Brute Justice & Cruise Chaser',
                'mechanics': [
                    mechanic('p2-j-kick-1', 'J Kick', 226.1 - p2, ['4854']),
                    mechanic('p2-whirlwind-1', 'Whirlwind 1', 238.3 - p2, ['49C2']),
                    mechanic('p2-judgment-nisi-1', 'Judgment Nisi', 241.3 - p2, ['483E'], minor=True),
                    mechanic('p2-link-up-1', 'Link-Up', 247.4 - p2, ['483F'], minor=True),
                    mechanic('p2-optical-sight-1', 'Optical Sight', 255.4 - p2, ['482F'], minor=True),
                    mechanic('p2-chakrams-1', 'Chakrams', 256.2 - p2, ['4855'], minor=True),
                    mechanic('p2-hawk-blaster-1', 'Hawk Blaster', 260.6 - p2, ['4831'], minor=True),
                    mechanic('p2-photon-1', 'Photon 1', 262.5 - p2, ['4836']),
                    mechanic('p2-spin-crusher-1', 'Spin Crusher', 272.7 - p2, ['4A72'], minor=True),
                    mechanic('p2-compressed-water-1', 'Compressed Water 1', 277.3 - p2, ['4841']),
                    mechanic('p2-earth-missile-1', 'Earth Missile', 288.6 - p2, ['484E'], minor=True),
                    mechanic('p2-hidden-minefield-1', 'Hidden Minefield', 290.6 - p2, ['4851']),
                    mechanic('p2-enumeration-1', 'Enumeration 1', 292.7 - p2, ['4850'], minor=True),
                    mechanic('p2-compressed-water-2', 'Compressed Water 2', 306.7 - p2, ['4841']),
                    mechanic('p2-limit-cut-2', 'Limit Cut 2', 313.5 - p2, ['4833']),
                    mechanic('p2-flarethrower-1', 'Flarethrower', 315.5 - p2, ['4845'], tank, minor=True),
                    mechanic('p2-whirlwind-2', 'Whirlwind 2', 327.6 - p2, ['49C2']),
                    mechanic('p2-compressed-water-3', 'Compressed Water 3', 336.2 - p2, ['4841']),
                    mechanic('p2-propeller-wind-1', 'Propeller Wind', 354.5 - p2, ['4832'], minor=True),
                    mechanic('p2-gavel-1', 'Gavel', 356.5 - p2, ['483C']),
                    mechanic('p2-photon-2', 'Photon 2', 366.8 - p2, ['4836'], tank),
                    mechanic('p2-double-rocket-punch-1', 'Double Rocket Punch', 374.8 - p2, ['4847'], tank),
                    mechanic('p2-super-jump-1', 'Super Jump 1', 382.1 - p2, ['484A'], minor=True),
                    mechanic('p2-apocalyptic-ray-1', 'Apocalyptic Ray', 384.4 - p2, minor=True),
                    mechanic('p2-whirlwind-3', 'Whirlwind 3', 395.0 - p2, ['49C2']),
                    mechanic('p2-whirlwind-4', 'Whirlwind 4', 403.1 - p2, ['49C2']),
                    mechanic('p2-final-sentence-1', 'Final Sentence', 413.7 - p2, ['4856'], minor=True),
                    mechanic('p2-eternal-darkness-1', 'Eternal Darkness 1', 423.7 - p2, ['483A'], minor=True),
                ],
            },
            {
                'id': 'p3', 'label': 'P3', 'name': 'Alexander Prime',
                'mechanics': [
                    mechanic('p3-temporal-stasis-1', 'Temporal Stasis', 500.0 - p3, ['485A']),
                    mechanic('p3-surety-1', 'Surety and Severity', 503.1 - p3, ['4861'], minor=True),
                    mechanic('p3-chastening-heat-1', 'Chastening Heat 1', 521.5 - p3, ['4A80'], tank),
                    mechanic('p3-divine-spear-1', 'Divine Spear 1', 524.6 - p3, ['4A82'], tank, minor=True),
                    mechanic('p3-inception-formation-1', 'Inception Formation', 537.9 - p3, ['486F'], minor=True),
                    mechanic('p3-judgment-crystal-1', 'Judgment Crystal 1', 552.4 - p3, ['485B']),
                    mechanic('p3-judgment-crystal-2', 'Judgment Crystal 2', 558.2 - p3, ['485C'], minor=True),
                    mechanic('p3-inception-1', 'Inception', 581.0 - p3, ['485E'], minor=True),
                    mechanic('p3-sacrament-1', 'Sacrament', 589.4 - p3, ['485F'], minor=True),
                    mechanic('p3-super-jump-2', 'Super Jump 2', 598.3 - p3, ['484A'], tank),
                    mechanic('p3-chastening-heat-2', 'Chastening Heat 2', 610.9 - p3, ['4A80'], tank),
                    mechanic('p3-divine-spear-2', 'Divine Spear 2', 616.0 - p3, ['4A82'], tank),
                    mechanic('p3-wormhole-formation-1', 'Wormhole Formation', 629.3 - p3, ['486E']),
                    mechanic('p3-incinerating-heat-1', 'Incinerating Heat', 670.0 - p3, ['4A51']),
                    mechanic('p3-enumeration-2', 'Enumeration 2', 674.6 - p3, ['4850'], minor=True),
                    mechanic('p3-mega-holy-1', 'Mega Holy 1', 682.9 - p3, ['4A83']),
                    mechanic('p3-mega-holy-2', 'Mega Holy 2', 690.0 - p3, ['4A83']),
                    mechanic('p3-j-storm-1', 'J Storm', 705.7 - p3, ['4876']),
                    mechanic('p3-j-wave-0', 'J Wave 0', 705.7 + (50 / 16) - p3),
                    mechanic('p3-j-wave-4', 'J Wave 4', 705.7 + 5 * (50 / 16) - p3),
                    mechanic('p3-j-wave-6', 'J Wave 6', 705.7 + 7 * (50 / 16) - p3),
                    mechanic('p3-eternal-darkness-2', 'Eternal Darkness 2', 731.7 - p3, ['4875'], minor=True),
                    mechanic('p3-j-wave-8', 'J Wave 8', 705.7 + 9 * (50 / 16) - p3),
                    mechanic('p3-divine-judgment-enrage-1', 'Divine Judgment Enrage', 771.9 - p3, ['4879'], minor=True),
                    mechanic('p3-divine-judgment-1', 'Divine Judgment', 787.3 - p3, ['487A']),
                ],
            },
            {
                'id': 'p4', 'label': 'P4', 'name': 'Perfect Alexander',
                'mechanics': [
                    mechanic('p4-final-word-1', 'The Final Word', 909.1 - p4, ['487D'], minor=True),
                    mechanic('p4-ordained-motion-1', 'Ordained Motion 1', 916.1 - p4, ['487E', '487F'], minor=True),
                    mechanic('p4-ordained-motion-2', 'Ordained Motion 2', 926.3 - p4, ['487E', '487F'], minor=True),
                    mechanic('p4-optical-sight-1', 'Optical Sight 1', 936.5 - p4, ['488A', '488B']),
                    mechanic('p4-optical-sight-2', 'Optical Sight 2', 942.7 - p4, ['488A', '488B']),
                    mechanic('p4-fate-projection-alpha-1', 'Fate Projection α', 957.6 - p4, ['487B'], minor=True),
                    mechanic('p4-fate-calibration-alpha-1', 'Fate Calibration α', 982.6 - p4, ['487C'], minor=True),
                    mechanic('p4-ordained-capital-punishment-1', 'Ordained Capital Punishment 1', 1008.0 - p4, ['4892']),
                    mechanic('p4-ordained-punishment-1', 'Ordained Punishment 1', 1017.2 - p4, ['4891'], tank),
                    mechanic('p4-fate-projection-beta-1', 'Fate Projection β', 1032.3 - p4, ['4B13'], minor=True),
                    mechanic('p4-fate-calibration-beta-1', 'Fate Calibration β', 1070.3 - p4, ['4B14']),
                    mechanic('p4-ordained-capital-punishment-2', 'Ordained Capital Punishment 2', 1106.8 - p4, ['4892']),
                    mechanic('p4-ordained-punishment-2', 'Ordained Punishment 2', 1116.0 - p4, ['4891'], tank),
                    mechanic('p4-almighty-judgment-1', 'Almighty Judgment 1', 1126.2 - p4, ['488E'], minor=True),
                    mechanic('p4-irresistible-grace-1', 'Irresistible Grace 1', 1142.5 - p4, ['4894']),
                    mechanic('p4-ordained-capital-punishment-3', 'Ordained Capital Punishment 3', 1152.6 - p4, ['4892']),
                    mechanic('p4-ordained-punishment-3', 'Ordained Punishment 3', 1161.8 - p4, ['4891'], tank),
                    mechanic('p4-almighty-judgment-2', 'Almighty Judgment 2', 1171.7 - p4, ['488E'], minor=True),
                    mechanic('p4-irresistible-grace-2', 'Irresistible Grace 2', 1187.9 - p4, ['4894']),
                    mechanic('p4-temporal-prison-1', 'Temporal Prison', 1247.6 - p4, ['4897'], minor=True),
                ],
            },
        ],
    }


def clean(value):
    return re.sub(r'\s+', ' ', str(value)).strip()


def split_outside(text, sep):
    parts, buf, depth = [], '', 0
    for char in text:
        if char == '(':
            depth += 1
        elif char == ')':
            depth = max(0, depth - 1)
        if char == sep and depth == 0:
            parts.append(buf)
            buf = ''
        else:
            buf += char
    parts.append(buf)
    return parts


def action(name, notes):
    text = ' '.join(note for note in notes if note)
    base = re.sub(r'\s*\([^)]*\)\s*$', '', name).strip()
    if base in FORBIDDEN or name in FORBIDDEN:
        raise ValueError(f'{name} is not available at level 80')
    row = {'name': name}
    if text:
        row['note'] = text
    return row


def parse_actions(slot, raw):
    """One role cell -> action dicts. Unknown tokens and targets raise."""
    text = clean(raw)
    if not text:
        return []
    if text == '(TBN on CD)':
        return [action('The Blackest Night (DRK)', ['On cooldown.'])]
    if text == '(Party Mit)':
        return [action('Party Mit', ['Optional.'])]

    actions = []
    for segment in split_outside(text, '/'):
        segment = segment.strip()
        if not segment:
            continue
        offset = None
        timed = re.match(r'^(.*?)\s*-(\d+)s$', segment)
        if timed:
            segment, offset = timed.group(1).strip(), timed.group(2)
        if segment.lower() == 'star place on pull':
            actions.append(action('Earthly Star', ['Place it on the pull.']
                                   + ([f'{int(offset)} seconds before.'] if offset else [])))
            continue
        target = None
        targeted = re.match(r'^(.*?)\s*\(([^)]*)\)\s*$', segment)
        if targeted:
            segment, target = targeted.group(1).strip(), targeted.group(2).strip()
            if target not in TARGET_NOTES:
                raise ValueError(f'Unknown target {target!r} in {raw!r}')
        if segment == 'Everything':
            if slot not in EVERYTHING:
                raise ValueError(f'Everything is a healer call, not a {slot} cell ({raw!r})')
            if target or offset:
                raise ValueError(f'Everything does not take a target or offset ({raw!r})')
            actions.extend(action(name, []) for name in EVERYTHING[slot])
            continue
        atoms = [atom.strip() for atom in split_outside(segment, '+') if atom.strip()]
        if not atoms:
            raise ValueError(f'Empty action in {raw!r}')
        for atom in atoms:
            if atom not in TOKENS:
                raise ValueError(f'Unknown action {atom!r} in {raw!r}')
            notes = []
            if atom in SERAPH_NOTES:
                notes.append(SERAPH_NOTES[atom])
            if atom == 'Star Place':
                notes.append('Place it on player 6.' if target == '#6' else 'Place it.')
            elif target:
                notes.append(TARGET_NOTES[target])
            if offset:
                notes.append(f'{int(offset)} seconds before.')
            for name in TOKENS[atom]:
                actions.append(action(name, notes))
    return actions


def extra_actions(raw):
    """Extras column -> (slot, action) pairs. Not a seat of its own."""
    text = clean(raw)
    if text == 'PLD Wings':
        wings = action('Passage of Arms (PLD)', [])
        return [('MT', {**wings, '_from': 'M'}), ('OT', {**wings, '_from': 'M'})]
    if text == 'Dismantle':
        return [('P', {**action('Extra (MCH)', []), '_from': 'M'})]
    if text == '(Minne/Mantra)':
        return [
            ('P', {**action("Nature's Minne (BRD)", ['Optional.']), '_from': 'M'}),
            ('M1', {**action('Mantra (MNK)', ['Optional.']), '_from': 'M'}),
            ('M2', {**action('Mantra (MNK)', ['Optional.']), '_from': 'M'}),
        ]
    raise ValueError(f'Unknown extras: {raw!r}')


def _expect(cells, tab, ref, prefix):
    value = clean(cells.get(ref, ''))
    if not value.startswith(prefix):
        raise ValueError(f'{tab} {ref} was {value!r}, expected to start with {prefix!r}')
    return value


def build_sheet(tabs):
    """Workbook tabs -> the NAUR sheet. Every non-empty cell is consumed or the import fails."""
    consumed = {tab: set() for tab in tabs}
    by_id = {}

    def take(tab, ref):
        if ref not in tabs[tab]:
            raise ValueError(f'{tab} {ref} is empty')
        consumed[tab].add(ref)
        return tabs[tab][ref]

    for (tab, ref), prefix in {**CREDITS, **LABELS}.items():
        _expect(tabs[tab], tab, ref, prefix)
        take(tab, ref)
    for tab, rows in HEADER_ROWS.items():
        for row in rows:
            for column, prefix in HEADER_PREFIX.items():
                ref = f'{column}{row}'
                _expect(tabs[tab], tab, ref, prefix)
                take(tab, ref)
    for (tab, ref), prefix in PROSE.items():
        _expect(tabs[tab], tab, ref, prefix)
        take(tab, ref)
    for (tab, ref), (*_rest, expected) in CARETS.items():
        if clean(tabs[tab].get(ref, '')) != expected:
            raise ValueError(f'{tab} {ref} was {tabs[tab].get(ref)!r}, expected {expected!r}')
        take(tab, ref)
    for (tab, ref), expected in CONTINUATION_TAILS.items():
        if clean(tabs[tab].get(ref, '')) != expected:
            raise ValueError(f'{tab} {ref} was {tabs[tab].get(ref)!r}, expected {expected!r}')
        take(tab, ref)

    for tab, row, phase, mechanic_id, title in ROWS:
        found = clean(take(tab, f'B{row}'))
        if found != title:
            raise ValueError(f'{tab} B{row} was {found!r}, expected {title!r}')
        assignments = {}
        for column, slot in COLUMNS.items():
            ref = f'{column}{row}'
            if ref not in tabs[tab] or (tab, ref) in CARETS or (tab, ref) in CONTINUATION_TAILS:
                continue
            take(tab, ref)
            for made in parse_actions(slot, tabs[tab][ref]):
                made['_from'] = column
                assignments.setdefault(slot, []).append(made)
        extra_ref = f'M{row}'
        if extra_ref in tabs[tab] and (tab, extra_ref) not in CARETS:
            take(tab, extra_ref)
            for slot, made in extra_actions(tabs[tab][extra_ref]):
                assignments.setdefault(slot, []).append(made)
        by_id[mechanic_id] = {'phase': phase, 'assignments': assignments}

    for (tab, ref), (mechanic_id, column, note, _expected) in CARETS.items():
        targets = [item for item in by_id[mechanic_id]['assignments'].values()
                   for item in item if item.get('_from') == column]
        if not targets:
            raise ValueError(f'Caret {tab} {ref} has nothing to attach to')
        for item in targets:
            item['note'] = f"{item['note']} {note}".strip() if item.get('note') else note

    for assignments in by_id.values():
        for slot_actions in assignments['assignments'].values():
            for item in slot_actions:
                item.pop('_from', None)

    leftovers = {tab: sorted(set(cells) - consumed[tab]) for tab, cells in tabs.items()}
    leftovers = {tab: refs for tab, refs in leftovers.items() if refs}
    if leftovers:
        raise ValueError(f'Unmapped cells: {leftovers}')

    phases = []
    for phase_id in ('p1', 'lc', 'p2', 'p3', 'p4'):
        phase = {'id': phase_id, 'mechanics': []}
        note, roles = PHASE_NOTES.get(phase_id, (None, None))
        if note:
            phase['note'] = note
        if roles:
            phase['noteRoles'] = roles
        for _tab, _row, row_phase, mechanic_id, _title in ROWS:
            if row_phase != phase_id:
                continue
            entry = {'mechanicId': mechanic_id, 'assignments': by_id[mechanic_id]['assignments']}
            extra, extra_roles = MECHANIC_NOTES.get(mechanic_id, (None, None))
            if extra:
                entry['note'] = extra
            if extra_roles:
                entry['noteRoles'] = extra_roles
            phase['mechanics'].append(entry)
        phases.append(phase)

    return {
        'id': 'naur',
        'fightId': 'tea',
        'name': 'NAUR',
        'author': '@sounox (LPDU/NAUR) and Jamie Jams @ Faerie',
        'updated': '2025-11-21',
        'sourceVersion': '2025-11-21',
        'source': {'name': 'NAUR TEA mitigation sheet', 'url': SOURCE_URL},
        'description': (
            'Party mitigation for The Epic of Alexander (Ultimate) from the NAUR sheet '
            'by @sounox (LPDU/NAUR) and Jamie Jams @ Faerie, reworked 11/21/2025 for NAUR staff. '
            'Pick a tank position, a healer job, or a DPS position.'
        ),
        'slots': [{'id': slot, **({'job': slot} if slot in HEALERS else {}), 'role': ROLES[slot]}
                  for slot in COLUMNS.values()],
        'phases': phases,
    }


def load_tabs(archive):
    strings = workbook.shared_strings(archive)
    tabs = {}
    for name in ('LLBJCC', 'Alex PrimePA'):
        cells, _maxrow = read_cells(archive, strings, workbook.worksheet(archive, name))
        tabs[name] = cells
    return tabs


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + '\n')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--xlsx', type=Path, help='Local xlsx export. Default: fetch the live workbook.')
    parser.add_argument('--write-encounter', action='store_true',
                        help='Also rewrite encounter.json from build_encounter().')
    args = parser.parse_args(argv)
    if args.xlsx:
        import zipfile
        archive = zipfile.ZipFile(args.xlsx)
    else:
        archive = workbook.fetch(SHEET_ID)
    write_json(SHEET_PATH, build_sheet(load_tabs(archive)))
    print(f'wrote {SHEET_PATH.relative_to(ROOT)}')
    if args.write_encounter:
        write_json(ENCOUNTER_PATH, build_encounter())
        print(f'wrote {ENCOUNTER_PATH.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
