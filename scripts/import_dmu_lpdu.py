"""Convert the "LPDU General DMU Mit Compile" P1-P5 tabs into reviewed repo JSON.

Usage: python3 scripts/import_dmu_lpdu.py '/path/to/LPDU.xlsx' ['/path/to/tank.xlsx']

Uses Python's standard library. The site never reads Excel at runtime.

Two workbooks. The first is the compile itself, whose five phase tabs are the
party-wide grids. The second is optional and is the separate tank workbook
("Dancing Mad (Ultimate) EU Mitigation - Tanks", tinyurl.com/LPDUtankmit) that
the compile links to; when given, its one tab becomes `tankMits`. The compile's
own hidden "Tank FAQ" / "Tank Mitigation (All Comps)" tabs are leftovers from
other sheets and are deliberately ignored.

Layout, per phase tab:
  * row 6 is the header: D "Time", then E MT / G OT / J White Mage /
    L Astrologian / N Scholar / P Sage / R M1 / T M2 / V R1 / X R2 /
    Z "Fake Melee Extras"
  * mechanic rows have the cast name in column B and a stored time fraction in
    column D; column A occasionally carries a priority call for that row
  * a handful of rows carry only prose (a boss-swap marker, a pastebin warning);
    those are folded into the neighbouring mechanic or the phase note

The encounter is shared with the Ikuya sheet, so rows map onto the canonical
mechanic IDs in data/fights/dmu/encounter.json by position -- MECHANICS below is
that mapping, written out rather than inferred because two phases disagree with
the source's own row order. LPDU's untimed "1st..4th beams" rows are the tether
sets the encounter calls Black Holes II/III; its P3 beam rows are interleaved
differently from the encounter's timed order, and the timed order wins.

Cells are shorthand ("Rep", "Soil", "EukProg/Kera"). ABILITY expands each token
to the in-game action name so the text reads on its own and
scripts/fetch_icons.py can resolve an icon. GENERIC names ("Party Mit",
"Short Mit") stay generic: jobs.json resolves them to the viewer's own button.
OVERRIDES holds the cells that are prose rather than a token list.
"""
import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

COLUMNS = {'E': 'MT', 'G': 'OT', 'J': 'WHM', 'L': 'AST', 'N': 'SCH', 'P': 'SGE',
           'R': 'M1', 'T': 'M2', 'V': 'P', 'X': 'C'}
# "Fake Melee Extras" is not a slot: it is the mit an *extra* caster or physical
# ranged brings when the party runs a fake melee, so it lands on those seats.
EXTRAS_COLUMN = 'Z'
HEALERS = ['WHM', 'AST', 'SCH', 'SGE']

SHEETS = {'p1': 3, 'p2': 4, 'p3': 5, 'p4': 6, 'p5': 9}

# Source row -> canonical mechanic ID. `None` means the row is prose handled by
# ROW_NOTES / PHASE_NOTES rather than an assignment row.
MECHANICS = {
    'p1': [
        (8, 'p1-revolting-ruin-1'), (9, 'p1-mystery-magic-1'), (11, 'p1-wave-cannon-1'),
        (13, 'p1-double-trouble-trap-1'), (15, 'p1-light-of-judgment-1'), (17, 'p1-hyperdrive-1'),
        (18, 'p1-gravitas-ii-part-i-1'), (20, 'p1-revolting-ruin-2'), (21, 'p1-gravitas-ii-part-ii-1'),
        (23, 'p1-double-trouble-trap-2'), (25, 'p1-light-of-judgment-2'), (27, 'p1-hyperdrive-2'),
        (28, 'p1-double-trouble-trap-3'), (30, 'p1-indulgent-will-1'), (32, 'p1-mystery-magic-2'),
    ],
    'p2': [
        (8, 'p2-ultimate-embrace-1'), (10, 'p2-forsaken-1'), (12, 'p2-towers-i-1'),
        (14, 'p2-towers-ii-past-future-s-end-1'), (16, 'p2-towers-iii-all-things-ending-1'),
        (18, 'p2-towers-iv-past-future-s-end-1'), (20, 'p2-towers-v-all-things-ending-1'),
        (22, 'p2-towers-vi-past-future-s-end-1'), (24, 'p2-towers-vii-all-things-ending-1'),
        (26, 'p2-towers-viii-past-future-s-end-1'), (28, 'p2-light-of-judgement-1'),
        (30, 'p2-wings-of-destruction-1'), (32, 'p2-ultimate-embrace-2'),
    ],
    'p3': [
        (8, 'p3-bowels-of-agony-chaos-1'), (10, 'p3-stray-flames-tsunami-1'),
        (12, 'p3-thunder-iii-1st-set-1'), (14, 'p3-stray-flames-tsunami-2'), (16, 'p3-ultima-blaster-1'),
        (18, 'p3-vacuum-wave-1'), (20, 'p3-cyclone-1'), (22, 'p3-thunder-iii-2nd-set-1'),
        (24, 'p3-the-decisive-battle-1'), (26, 'p3-thunder-iii-3rd-set-1'), (30, 'p3-earthquake-1'),
        (32, 'p3-shocking-impact-shockwave-1'), (34, 'p3-black-holes-ii-3rd-tether-set-1'),
        (36, 'p3-thunder-iii-4th-set-1'), (38, 'p3-shocking-impact-shockwave-2'),
        (40, 'p3-black-holes-ii-4th-tether-set-1'), (42, 'p3-thunder-iii-5th-set-1'),
        (44, 'p3-black-holes-ii-5th-tether-set-1'), (46, 'p3-shocking-impact-shockwave-3'),
        (48, 'p3-black-holes-iii-6th-tether-set-1'), (50, 'p3-stomp-a-mole-knock-down-1'),
    ],
    'p4': [
        (8, 'p4-grand-cross-1'), (10, 'p4-inferno-tsunami-1'), (12, 'p4-grand-cross-2'),
        (14, 'p4-inferno-tsunami-2'), (16, 'p4-grand-cross-3'), (18, 'p4-flood-of-naught-1'),
        (20, 'p4-death-bolt-wave-1'), (22, 'p4-ultima-upsurge-1'), (24, 'p4-death-bolt-wave-2'),
        (26, 'p4-ultima-upsurge-2'),
    ],
    'p5': [
        (8, 'p5-ultima-repeater-1'), (10, 'p5-fell-forces-3x-1'), (12, 'p5-chaotic-flood-1'),
        (14, 'p5-maddening-orchestra-1'), (16, 'p5-fell-forces-2x-1'), (18, 'p5-celestriad-1'),
        (20, 'p5-ultima-repeater-2'), (22, 'p5-fell-forces-2x-2'), (24, 'p5-stray-entropy-1'),
        (26, 'p5-maddening-orchestra-2'), (28, 'p5-fell-forces-3x-2'), (32, 'p5-forsaken-1st-hit-1'),
        (34, 'p5-forsaken-bonds-2nd-hit-1'), (36, 'p5-forsaken-3rd-hit-1'),
        (38, 'p5-forsaken-bonds-4th-hit-1'), (40, 'p5-forsaken-5th-hit-1'),
        (42, 'p5-forsaken-bonds-6th-hit-1'), (44, 'p5-forsaken-7th-hit-1'),
        (46, 'p5-forsaken-bonds-8th-hit-1'), (48, 'p5-forsaken-null-1'),
    ],
}

# Prose the source parks in a spare row, folded onto the mechanic it belongs to.
ROW_NOTES = {
    ('p3', 'p3-earthquake-1'): 'Both tanks swap bosses here: the Exdeath starter takes Chaos and the Chaos starter takes Exdeath.',
    ('p3', 'p3-thunder-iii-4th-set-1'): 'Use the first beam set on either tank if it is the stack.',
    # The source writes "Enrage!" in the MT column because that is where it fit
    # on the row. It is not an MT assignment and not a button, so it belongs to
    # the mechanic, shown once for every role.
    ('p5', 'p5-forsaken-null-1'): 'Enrage.',
}

# A phase-wide aside, shown once under the phase heading.
PHASE_NOTES = {
    'p3': 'Paladin is the forced Chaos-start tank and is the offtank (right column) from this point of the fight onward, because of Hallowed Ground timing.',
    'p5': 'This grid shows shields, mitigation and major cooldowns only. Check the job pastebins for the exact healing.',
}

# Column A holds a priority call that belongs to the row it sits on.
COLUMN_A_NOTES = {('p2', 30): 'Wall priority: PLD > WAR > DRK > GNB.',
                  ('p3', 18): 'Tank LB priority: WAR > DRK > PLD > GNB.'}

# Shorthand -> action name. A name data/jobs.json knows how to resolve per job
# ("Party Mit", "Short Mit", "90s Mit", "120s Mit", "Invuln") is left generic on
# purpose; everything else has to be a real in-game action name. A value may
# name several buttons, joined by " + ".
ABILITY = {
    # Tanks
    'Rep': 'Reprisal', 'Ramp': 'Rampart', 'Provoke': 'Provoke',
    'Short': 'Short Mit', 'Shorts': 'Short Mit',
    '90s': '90s Mit', '120s': '120s Mit', 'Invuln': 'Invuln',
    'Party Mit': 'Party Mit', 'Party mit': 'Party Mit', 'party mit': 'Party Mit',
    'Shake': 'Party Mit (WAR)', 'shake': 'Party Mit (WAR)',
    'Veil': 'Party Mit (PLD)', 'veil': 'Party Mit (PLD)',
    'Equilibrium': 'Equilibrium',
    # White Mage
    'Temperence': 'Temperance', 'Caress': 'Divine Caress', 'Plenary': 'Plenary Indulgence',
    'Lilybell': 'Liturgy of the Bell', 'Asylum': 'Asylum', 'Benison': 'Divine Benison',
    'Aquaveil': 'Aquaveil', 'Aqua veil': 'Aquaveil', 'Regen': 'Regen',
    'Bene': 'Benediction', 'Benediction': 'Benediction',
    # Astrologian
    'Neutral': 'Neutral Sect', 'Sun Sign': 'Sun Sign', 'Macrocosmos': 'Macrocosmos',
    'Collective Unconsious': 'Collective Unconscious', 'Exalt': 'Exaltation',
    'Celestial Intersection': 'Celestial Intersection', 'Ewer': 'The Ewer',
    # "All single target mit" is AST's pair of single-target tank mits; "Card
    # mits" is the damage-reduction card.
    'All single target mit': 'Exaltation + Celestial Intersection', 'Card mits': 'The Bole',
    # Scholar
    'Soil': 'Sacred Soil', 'Exped': 'Expedient', 'Expedient': 'Expedient',
    'Expedience': 'Expedient', 'Illum': 'Fey Illumination', 'Fey Illum': 'Fey Illumination',
    'Seraph': 'Summon Seraph', 'Seraphism': 'Seraphism', 'Spreadlo': 'Spreadlo',
    'Succor': 'Succor', 'Succor(s)': 'Succor', 'Adlo': 'Adloquium',
    'Excog': 'Excogitation', 'Protraction': 'Protraction', 'Tether': 'Aetherpact',
    # Sage
    'Eprog': 'Eukrasian Prognosis II', 'Eprog(s)': 'Eukrasian Prognosis II',
    'Zoe Eprog': 'Zoe Shields', 'Ediag': 'Eukrasian Diagnosis',
    'Kera': 'Kerachole', 'Holos': 'Holos', 'Panhaima': 'Panhaima', 'Haima': 'Haima',
    'Physis': 'Physis II', 'Philo': 'Philosophia', 'Pneuma': 'Pneuma', 'Zoe': 'Zoe',
    'Taurochole': 'Taurochole', 'Krasis': 'Krasis', 'Pepsis': 'Pepsis',
    'Prognosis': 'Prognosis', 'Ixo': 'Ixochole', 'Druo': 'Druochole',
    'kera': 'Kerachole', 'Prep Zoe': 'Zoe', 'prep Zoe': 'Zoe',
    # DPS
    'Feint': 'Feint', 'Addle': 'Addle', 'Pranged 90s': 'Party Mit',
}

# Cells that are prose, not a token list. Keyed by (phase, column, row). An
# empty list means the cell says nothing this slot presses -- its text belongs
# to the mechanic instead, via ROW_NOTES.
OVERRIDES = {
    # -- P1
    ('p1', 'E', 8): [{'name': 'Kitchen Sink'}],
    ('p1', 'N', 8): [{'name': 'Protraction'},
                     {'name': 'Spreadlo', 'note': 'Off the MT, after the second hit.'},
                     {'name': 'Excogitation', 'note': 'On the OT.'}],
    ('p1', 'P', 8): [{'name': 'Haima', 'note': 'On the MT.'},
                     {'name': 'Taurochole', 'note': 'On the MT.'},
                     {'name': 'Eukrasian Prognosis II', 'note': 'Between the hits, then prep Zoe.'},
                     {'name': 'Zoe'}],
    ('p1', 'G', 8): [{'name': 'Buddy Mit', 'buddy': True}, {'name': 'Oblation (DRK)', 'buddy': True},
                     {'name': 'Provoke'}],
    ('p1', 'E', 9): [{'name': 'Party Mit', 'note': 'After the buster.'},
                     {'name': 'Reprisal', 'note': 'After the knockback.'}],
    ('p1', 'G', 9): [{'name': 'Party Mit (GNB/DRK)', 'note': 'After the knockback.'},
                     {'name': 'Party Mit (WAR/PLD)', 'note': 'After the stack/spread.'}],
    ('p1', 'E', 17): [{'name': 'Buddy Mit', 'buddy': True}, {'name': 'Oblation (DRK)', 'buddy': True}],
    ('p1', 'J', 20): [{'name': 'Benediction', 'note': 'If the tank is DRK.'}],
    ('p1', 'E', 21): [{'name': 'Reprisal', 'note': 'On the 14-second debuff.'}],
    ('p1', 'E', 23): [{'name': 'Party Mit (GNB/DRK)', 'note': 'On the 1-second debuff.'},
                      {'name': 'Party Mit (WAR/PLD)', 'note': 'After the knockback.'}],
    ('p1', 'G', 23): [{'name': 'Reprisal', 'note': 'On the knockback.'}],
    ('p1', 'J', 23): [{'name': 'Plenary Indulgence', 'note': 'Before the knockback.'}],
    ('p1', 'N', 23): [{'name': 'Succor'}, {'name': 'Sacred Soil'},
                      {'name': 'Summon Seraph', 'note': 'After the knockback.'}],
    ('p1', 'E', 27): [{'name': 'Invuln', 'note': 'Kitchen sink instead if WAR.', 'noteJobs': ['WAR']}],
    ('p1', 'E', 30): [{'name': 'Reprisal', 'note': 'On the confusion.'}],
    # -- P2
    ('p2', 'E', 8): [{'name': 'Kitchen Sink', 'note': 'Invuln and solo it if WAR.', 'noteJobs': ['WAR']}],
    ('p2', 'N', 8): [{'name': 'Spreadlo', 'note': 'Off the MT.'},
                     {'name': 'Sacred Soil', 'note': 'At 80% of the cast.'}],
    ('p2', 'E', 30): [{'name': 'Kitchen Sink', 'note': 'No short mit.'}, {'name': 'Reprisal'}],
    ('p2', 'G', 30): [{'name': 'Kitchen Sink', 'note': 'No short mit.'}],
    # -- P3
    ('p3', 'E', 8): [{'name': 'Reprisal', 'note': 'On the autos, as soon as Chaos is targetable.'}],
    ('p3', 'P', 10): [{'name': 'Philosophia'}, {'name': 'Physis II'},
                      {'name': 'Eukrasian Prognosis II'}, {'name': 'Holos'},
                      {'name': 'Zoe', 'note': 'Prep it for the next set.'}],
    ('p3', 'E', 12): [{'name': 'Short Mit'}, {'name': 'Rampart'},
                      {'name': '90s Mit', 'note': 'First hit.'}],
    ('p3', 'G', 12): [{'name': 'Reprisal'}, {'name': 'Short Mit'}, {'name': 'Rampart'},
                      {'name': '90s Mit', 'note': 'Second hit.'}],
    ('p3', 'N', 12): [{'name': 'Sacred Soil', 'note': 'The buster is free here.'},
                      {'name': 'Expedient'}],
    ('p3', 'P', 12): [{'name': 'Pepsis'}, {'name': 'Zoe Shields'},
                      {'name': 'Kerachole', 'note': 'After the second buster.'}],
    ('p3', 'E', 14): [{'name': 'Reprisal', 'note': 'During the Latitude/Longitude cast. Make sure it hits Chaos.'}],
    ('p3', 'E', 24): [{'name': 'Provoke', 'note': 'On Chaos. Stand under, and make sure neither boss can move before you move under.'}],
    ('p3', 'G', 24): [{'name': 'Provoke', 'note': 'On Exdeath. Stand under, and make sure neither boss can move before you move under.'}],
    ('p3', 'E', 26): [{'name': '120s Mit', 'note': 'Use late, on the second hit.'},
                      {'name': 'Short Mit (WAR/PLD/DRK)'}],
    ('p3', 'G', 26): [{'name': '120s Mit', 'note': 'Use late.'},
                      {'name': 'Reprisal', 'note': 'First hit.'},
                      {'name': 'Short Mit (WAR/PLD/DRK)'}],
    ('p3', 'P', 26): [{'name': 'Zoe Shields'}, {'name': 'Haima', 'note': 'On the MT.'},
                      {'name': 'Taurochole', 'note': 'On the OT.'},
                      {'name': 'Eukrasian Diagnosis', 'note': 'Both tanks, after the hits.'}],
    ('p3', 'E', 30): [{'name': 'Short Mit', 'note': 'At 1 HP. WAR: use Equilibrium once your HP drops to 1.', 'noteJobs': ['WAR']}],
    ('p3', 'G', 30): [{'name': 'Short Mit', 'note': 'At 1 HP. WAR: use Equilibrium once your HP drops to 1.', 'noteJobs': ['WAR']}],
    ('p3', 'J', 30): [{'name': 'Plenary Indulgence'},
                      {'name': 'Benediction', 'note': 'On the healer taking Accretion — see pastebin line 107.'}],
    ('p3', 'L', 30): [{'name': 'Macrocosmos', 'note': 'Check the pastebin.'}],
    ('p3', 'P', 30): [{'name': 'Physis II'}, {'name': 'Krasis'},
                      {'name': 'Druochole', 'note': 'On the healer.'},
                      {'name': 'Eukrasian Prognosis II', 'note': 'After the first pop.'},
                      {'name': 'Pepsis'}, {'name': 'Prognosis'},
                      {'name': 'Ixochole', 'note': 'After the vuln, for safety.'}],
    ('p3', 'E', 32): [{'name': 'Reprisal', 'note': 'Use early.'}],
    ('p3', 'E', 42): [{'name': 'Short Mit'}, {'name': 'Rampart'},
                      {'name': '90s Mit', 'note': 'Second hit.'}],
    ('p3', 'G', 42): [{'name': 'Short Mit'}, {'name': 'Rampart'},
                      {'name': '90s Mit', 'note': 'First hit.'}, {'name': 'Reprisal'}],
    ('p3', 'N', 40): [{'name': 'Succor'}, {'name': 'Expedient'}],
    ('p3', 'P', 40): [{'name': 'Eukrasian Prognosis II', 'note': 'Each set.'},
                      {'name': 'Physis II', 'note': 'As the last beam hits.'},
                      {'name': 'Panhaima', 'note': 'As the last beam hits.'}],
    ('p3', 'E', 44): [{'name': 'Short Mit', 'note': 'On cooldown from this point.'}],
    ('p3', 'G', 44): [{'name': 'Short Mit', 'note': 'On cooldown from this point.'}],
    ('p3', 'E', 46): [{'name': 'Provoke', 'note': 'Face the boss NW, Kefka-relative, right after the third beam.'}],
    ('p3', 'P', 46): [{'name': 'Pneuma', 'note': 'On the white hole.'},
                      {'name': 'Eukrasian Prognosis II'}, {'name': 'Kerachole'}],
    ('p3', 'E', 48): [{'name': '120s Mit', 'note': 'After the last beam.'}],
    ('p3', 'G', 48): [{'name': '120s Mit', 'note': 'After the last beam.'}],
    ('p3', 'J', 48): [{'name': 'Babysit the beam tank'}],
    ('p3', 'P', 48): [{'name': 'Haima', 'note': 'On the beam tank; on the Chaos tank if you cannot.'}],
    ('p3', 'P', 50): [{'name': 'Eukrasian Prognosis II'}, {'name': 'Kerachole'},
                      {'name': 'Physis II', 'note': 'Reshield as necessary between hits.'}],
    # -- P4
    ('p4', 'E', 8): [{'name': '90s Mit'}, {'name': 'Short Mit', 'note': 'For the autos.'}],
    ('p4', 'G', 8): [{'name': '90s Mit', 'note': 'In case you forgot your stance.'}],
    ('p4', 'J', 8): [{'name': 'Divine Benison', 'note': 'On the MT.'},
                     {'name': 'Aquaveil', 'note': 'On the MT.'},
                     {'name': 'Asylum', 'note': 'Off cooldown.'},
                     {'name': 'Temperance', 'note': 'At 80% of the Grand Cross castbar.'}],
    ('p4', 'P', 8): [{'name': 'Kerachole', 'note': 'At the end of the Kefka Says castbar.'},
                     {'name': 'Eukrasian Prognosis II'},
                     {'name': 'Holos', 'note': 'At 80% of the Grand Cross castbar.'}],
    ('p4', 'R', 8): [{'name': 'Feint', 'note': 'On the autos.'}],
    ('p4', 'G', 14): [{'name': 'Party Mit (GNB/DRK)'}],
    ('p4', 'E', 16): [{'name': 'Buddy Mit', 'note': 'On R1.', 'buddy': True},
                      {'name': 'Oblation (DRK)', 'note': 'On R1.', 'buddy': True}],
    ('p4', 'G', 16): [{'name': 'Party Mit (WAR/PLD)'},
                      {'name': 'Buddy Mit', 'note': 'On R2.', 'buddy': True},
                      {'name': 'Oblation (DRK)', 'note': 'On R2.', 'buddy': True}],
    ('p4', 'J', 18): [{'name': 'Liturgy of the Bell'},
                      {'name': 'Divine Benison', 'note': 'All stacks after the hit.'}],
    ('p4', 'P', 20): [{'name': 'Pneuma'},
                      {'name': 'Zoe Shields', 'note': 'After the yellow debuff.'}],
    ('p4', 'E', 22): [{'name': 'Reprisal'}, {'name': 'Party Mit (GNB/DRK)'}],
    ('p4', 'E', 24): [{'name': 'Party Mit (WAR)'}],
    # -- P5
    ('p5', 'G', 8): [{'name': 'Provoke', 'note': 'Start with aggro.'},
                     {'name': 'Party Mit', 'note': 'At the Smile quote; WAR/PLD can use theirs earlier.'}],
    ('p5', 'P', 8): [{'name': 'Eukrasian Prognosis II'}, {'name': 'Kerachole'}, {'name': 'Physis II'},
                     {'name': 'Haima', 'note': 'On the MT.'}],
    ('p5', 'V', 8): [{'name': 'Party Mit', 'note': 'At the Smile quote.'}],
    ('p5', 'N', 10): [{'name': 'Succor'}, {'name': 'Expedient', 'note': 'After the first hit.'}],
    ('p5', 'P', 10): [{'name': 'Eukrasian Prognosis II'},
                      {'name': 'Holos', 'note': 'After the first hit.'}],
    ('p5', 'E', 14): [{'name': 'Rampart'}, {'name': '90s Mit'}, {'name': 'Short Mit'},
                      {'name': 'Invuln', 'note': 'On the flare.'}],
    ('p5', 'G', 14): [{'name': '120s Mit', 'note': 'First two hits.'},
                      {'name': 'Short Mit', 'note': 'On the flare.'}],
    ('p5', 'N', 16): [{'name': 'Succor'},
                      {'name': 'Summon Seraph', 'note': 'On the second auto hit.'}],
    ('p5', 'P', 18): [{'name': 'Eukrasian Prognosis II'},
                      {'name': 'Physis II', 'note': 'On the first tower spawn.'}],
    ('p5', 'E', 26): [{'name': 'Rampart'}, {'name': 'Short Mit'},
                      {'name': '120s Mit', 'note': 'On the flare.'}],
    ('p5', 'G', 26): [{'name': 'Rampart'}, {'name': 'Short Mit'},
                      {'name': 'Invuln', 'note': 'On the flare.'}],
    ('p5', 'N', 26): [{'name': 'Succor'}, {'name': 'Sacred Soil', 'note': 'Use early.'}],
    ('p5', 'P', 26): [{'name': 'Eukrasian Prognosis II'},
                      {'name': 'Kerachole', 'note': 'Use early.'},
                      {'name': 'Haima', 'note': 'On the tank that is not invulning.'}],
    ('p5', 'E', 28): [{'name': '90s Mit', 'note': 'On the third auto; share it with the OT.'}],
    ('p5', 'G', 28): [{'name': 'Invuln'}, {'name': '90s Mit', 'note': 'On the third auto.'}],
    ('p5', 'J', 28): [{'name': 'Benediction', 'note': 'On the WAR/DRK that invulned, after the second auto. Not negotiable.'}],
    ('p5', 'P', 28): [{'name': 'Eukrasian Prognosis II'},
                      {'name': 'Krasis', 'note': 'On the invulning tank, after the second auto.'},
                      {'name': 'Taurochole', 'note': 'On the invulning tank, after the second auto.'}],
    ('p5', 'N', 32): [{'name': 'Fey Illumination'}, {'name': 'Spreadlo'},
                      {'name': 'Expedient', 'note': 'At 80% of the castbar.'},
                      {'name': 'Sacred Soil', 'note': 'At 80% of the castbar.'}],
    ('p5', 'P', 32): [{'name': 'Zoe Shields'}, {'name': 'Holos'},
                      {'name': 'Kerachole', 'note': 'At 80% of the castbar.'}],
    ('p5', 'E', 44): [{'name': 'Buddy Mit', 'note': 'On R1.', 'buddy': True},
                      {'name': 'Oblation (DRK)', 'note': 'On R1.', 'buddy': True}],
    ('p5', 'G', 44): [{'name': 'Buddy Mit', 'note': 'On R2.', 'buddy': True},
                      {'name': 'Oblation (DRK)', 'note': 'On R2.', 'buddy': True}],
    # "Enrage!" is not a button, and not an MT assignment - see ROW_NOTES.
    ('p5', 'E', 48): [],
    ('p5', 'N', 42): [{'name': 'Succor'}, {'name': 'Seraphism'},
                      {'name': 'Summon Seraph', 'note': 'Off cooldown.'}],
    ('p5', 'P', 44): [{'name': 'Eukrasian Prognosis II'}, {'name': 'Panhaima'},
                      {'name': 'Physis II'}, {'name': 'Pneuma', 'note': 'After.'}],
}

SEPARATORS = [' + ', '+ ', ' // ', ' -> ', ', ', '/']

# Kitchen sink is Rampart + every tank cooldown, pressed together.
KITCHEN_SINK = ['Rampart', '120s Mit', '90s Mit', 'Short Mit']

# A trailing "(...)" or " on/off/after ..." tail on an otherwise clean token.
TAIL_NOTES = {
    'off cd': 'Off cooldown.', 'off CD': 'Off cooldown.',
    'both': 'Both tanks.', 'Both': 'Both tanks.', 'both tanks': 'Both tanks.',
    'both tanks': 'Both tanks.',
    'MT': 'On the MT.', 'mt': 'On the MT.', 'OT': 'On the OT.',
    '(on spawn)': 'On spawn.', 'late': 'Use late.',
    'chaos autos': 'On the Chaos autos.', 'autos': 'On the autos.',
}


def clean(value):
    return ' '.join(str(value).split())


def split_top(text, seps):
    """Split on separators that are not inside parentheses."""
    parts, depth, current = [], 0, ''
    i = 0
    while i < len(text):
        char = text[i]
        if char == '(':
            depth += 1
        elif char == ')':
            depth = max(0, depth - 1)
        if depth == 0:
            hit = next((s for s in seps if text.startswith(s, i)), None)
            if hit:
                parts.append(current)
                current = ''
                i += len(hit)
                continue
        current += char
        i += 1
    parts.append(current)
    return [p.strip() for p in parts if p.strip()]


def expand(token):
    """One shorthand token -> action dicts."""
    note = None
    if token.lower().startswith('kitchen'):
        names = KITCHEN_SINK[:-1] if 'no short' in token.lower() else KITCHEN_SINK
        return [{'name': name} for name in names]
    for tail, text in TAIL_NOTES.items():
        if token.endswith(' ' + tail):
            token, note = token[: -len(tail) - 1].strip(), text
            break
    name = ABILITY.get(token)
    if name is None:
        raise ValueError(f'Unknown token {token!r}')
    # One shorthand may stand for several buttons pressed together.
    actions = [{'name': part} for part in name.split(' + ')]
    if note:
        for action in actions:
            action['note'] = note
    return actions


def cell_actions(raw):
    """One grid cell -> list of action dicts."""
    out = []
    for token in split_top(clean(raw), SEPARATORS):
        out.extend(expand(token))
    # A duplicate name from two segments is one press, not two.
    seen, deduped = set(), []
    for action in out:
        key = (action['name'], action.get('note'))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(action)
    return deduped


def extras(raw):
    """The "Fake Melee Extras" column: mit an extra caster (Addle) or physical
    ranged (their 90s party mit) brings when the party runs a fake melee."""
    note = 'Only when the party runs a fake melee.'
    out = []
    for token in split_top(clean(raw), SEPARATORS):
        if token == 'Addle':
            out.append(('C', {'name': 'Addle', 'note': note}))
        elif token == 'Pranged 90s':
            out.append(('P', {'name': 'Party Mit', 'note': note}))
        else:
            raise ValueError(f'Unknown extras token {token!r}')
    return out


def read_cells(archive, strings, worksheet):
    root = ET.fromstring(archive.read(f'xl/worksheets/sheet{worksheet}.xml'))
    cells = {}
    for cell in root.findall('.//s:sheetData/s:row/s:c', NS):
        value = cell.find('s:v', NS)
        if value is None or not value.text:
            continue
        cells[cell.get('r')] = strings[int(value.text)] if cell.get('t') == 's' else value.text
    return cells


def convert(path, moved=None):
    """The party grid. `moved` collects the personal mit lifted out of the tank
    columns, keyed by (phase, mechanic, seat), for the tank plan to absorb."""
    moved = {} if moved is None else moved
    archive = zipfile.ZipFile(path)
    strings = [''.join(node.itertext()) for node in
               ET.fromstring(archive.read('xl/sharedStrings.xml'))]

    phases = []
    for phase_id, worksheet in SHEETS.items():
        cells = read_cells(archive, strings, worksheet)
        mechanics = []
        for row, mechanic_id in MECHANICS[phase_id]:
            assignments = {}
            for column, slot in COLUMNS.items():
                raw = cells.get(f'{column}{row}')
                if not raw:
                    continue
                key = (phase_id, column, row)
                actions = OVERRIDES[key] if key in OVERRIDES else cell_actions(raw)
                if actions:
                    assignments.setdefault(slot, []).extend(actions)
            for slot, action in extras(cells.get(f'{EXTRAS_COLUMN}{row}', '') or ''):
                assignments.setdefault(slot, []).append(action)
            entry = {'mechanicId': mechanic_id}
            note_parts = [ROW_NOTES.get((phase_id, mechanic_id)),
                          COLUMN_A_NOTES.get((phase_id, row))]
            note = ' '.join(part for part in note_parts if part)
            if note:
                entry['note'] = note
            if not assignments and not note:
                continue
            # The tank columns keep only what a tank presses for the group;
            # its own cooldowns move to `tankMits`, so the two are stated once
            # each. `moved` carries them (and their notes) to convert_tanks.
            lifted = False
            for seat in ('MT', 'OT'):
                actions = assignments.get(seat)
                if not actions:
                    continue
                personal = [a for a in actions if not is_group_mit(a['name'])]
                if personal:
                    moved[(phase_id, mechanic_id, seat)] = personal
                    lifted = True
                group = [a for a in actions if is_group_mit(a['name'])]
                if group:
                    assignments[seat] = group
                else:
                    del assignments[seat]
            # A mechanic whose only tank content just moved to `tankMits` still
            # keeps its row: the personal line anchors to it, and folds into it.
            if not assignments and not note and not lifted:
                continue
            entry['assignments'] = assignments
            mechanics.append(entry)
        phase = {'id': phase_id}
        if phase_id in PHASE_NOTES:
            phase['note'] = PHASE_NOTES[phase_id]
        phase['mechanics'] = mechanics
        phases.append(phase)

    return {
        'id': 'lpdu',
        'fightId': 'dmu',
        'name': 'LPDU',
        'author': 'LPDU',
        'updated': '2026-09-09',
        'sourceFile': 'LPDU GENERAL DMU MIT COMPILE + LPDU tank mit sheet',
        'source': {
            'name': 'LPDU General DMU Mit Compile',
            'url': 'https://docs.google.com/spreadsheets/d/1aA_qF_UsoS51MCDZ4PwQHhprpK7eGO8TXOdZ7pQlkV0/edit',
        },
        'description': 'P1–P5 mitigation from the LPDU compile sheet, which follows LPDU strats, '
                       'with tank personal mit from the LPDU tank sheet. Choose a tank position, '
                       'healer job, or DPS position.',
        # Paladin is forced offtank from P3 onward - the sheet calls it
        # non-negotiable, because the invulns do not line up with a PLD main
        # tank - so the MT seat does not offer it.
        'slots': [{'id': 'MT', 'role': 'tank', 'jobs': ['WAR', 'DRK', 'GNB']},
                  {'id': 'OT', 'role': 'tank'},
                  *({'id': job, 'job': job, 'role': 'healer'} for job in HEALERS),
                  {'id': 'M1', 'role': 'melee'}, {'id': 'M2', 'role': 'melee'},
                  {'id': 'P', 'role': 'ranged'}, {'id': 'C', 'role': 'caster'}],
        'phases': phases,
    }


# ---------------------------------------------------------------------------
# Tank personal mit -> `tankMits`.
#
# The tank plan is a separate workbook ("Dancing Mad (Ultimate) EU Mitigation -
# Tanks" by Saybell Valentine, tinyurl.com/LPDUtankmit), one tab: "Universal
# MTOT Sheet". Universal is the point - unlike the Ikuya Omnitank tab there is
# no per-comp page and no choice to make. Both branches the schema knows about
# are fixed by seat, and the sheet says so in its own headers:
#
#   P3 start   MT = Exdeath tank, OT = Chaos tank
#   after the Decisive Battle swap, the two trade
#   invulns    P1: OT on Revolting Ruin 2, MT on Hyperdrive 2
#              P3: MT on Thunder III 2, OT on Thunder III 4
#              P5: MT on Flare 1, OT on Flare 2
#
# So the rows carry `seat` and never `boss` / `invuln`, and the mits page shows
# no branch toggles for this sheet. It is still emitted as one plan per tank
# job, like Ikuya: the shorthand is generic ("KS", "Short", "120S") and the job
# is known at import, so it expands to the real button here rather than at view
# time.
#
# Columns: B time, C mechanic, D MT, E OT, F prio/notes.
TANK_SHEET = 2
TANKS = ['PLD', 'WAR', 'DRK', 'GNB']
INVULN = {'WAR': 'Holmgang', 'PLD': 'Hallowed Ground', 'DRK': 'Living Dead', 'GNB': 'Superbolide'}
MIT_120 = {'WAR': 'Damnation', 'PLD': 'Guardian', 'DRK': 'Shadowed Vigil', 'GNB': 'Great Nebula'}
MIT_90 = {'WAR': 'Thrill of Battle', 'PLD': 'Bulwark', 'DRK': 'Dark Mind', 'GNB': 'Camouflage'}
# The short personal mitigation each tank presses on itself. DRK stacks two.
# WAR's is Bloodwhetting, not the ally-only Nascent Flash - that is the buddy mit.
SHORT_MIT = {'WAR': ['Bloodwhetting'], 'PLD': ['Holy Sheltron'],
             'DRK': ['The Blackest Night', 'Oblation'], 'GNB': ['Heart of Corundum']}
BUDDY_MIT = {'WAR': ['Nascent Flash'], 'PLD': ['Intervention'],
             'DRK': ['The Blackest Night', 'Oblation'], 'GNB': ['Heart of Corundum']}
PARTY_MIT = {'PLD': 'Divine Veil', 'WAR': 'Shake It Off',
             'DRK': 'Dark Missionary', 'GNB': 'Heart of Light'}

# Rampart + both long cooldowns + short mit, pressed together. Named apart from
# the party grid's KITCHEN_SINK, which is the same idea left generic.
TANK_KITCHEN_SINK = {job: ['Rampart', MIT_120[job], MIT_90[job], *SHORT_MIT[job]] for job in TANKS}

def tank_tokens(job):
    """Shorthand -> the buttons this job actually presses."""
    return {
        'KS': TANK_KITCHEN_SINK[job], 'Kitchen Sink': TANK_KITCHEN_SINK[job],
        'Rep': ['Reprisal'], 'Rampart': ['Rampart'], 'Ramp': ['Rampart'],
        'Provoke': ['Provoke'], 'Voke': ['Provoke'],
        'Short': SHORT_MIT[job], 'Party Mit': [PARTY_MIT[job]],
        '90': [MIT_90[job]], '90s': [MIT_90[job]], '90S': [MIT_90[job]],
        '120': [MIT_120[job]], '120s': [MIT_120[job]], '120S': [MIT_120[job]],
        'Invuln': [INVULN[job]],
    }

# Source row -> (phase, canonical mechanic to render below). `None` anchors the
# row to the top of the phase, for a call that lands before the first party
# mechanic. Rows the sheet names for a mechanic the encounter does not carry
# (Graven Image, the autos, Flare Diffusion) hang off the nearest party row.
TANK_ROWS = {
    7: ('p1', 'p1-revolting-ruin-1'), 9: ('p1', 'p1-revolting-ruin-1'),
    11: ('p1', 'p1-mystery-magic-1'), 13: ('p1', 'p1-light-of-judgment-1'),
    15: ('p1', 'p1-hyperdrive-1'), 17: ('p1', 'p1-revolting-ruin-2'),
    19: ('p1', 'p1-gravitas-ii-part-ii-1'), 21: ('p1', 'p1-double-trouble-trap-2'),
    23: ('p1', 'p1-light-of-judgment-2'), 25: ('p1', 'p1-hyperdrive-2'),
    27: ('p1', 'p1-double-trouble-trap-3'),
    31: ('p2', 'p2-ultimate-embrace-1'), 33: ('p2', 'p2-forsaken-1'),
    35: ('p2', 'p2-towers-iv-past-future-s-end-1'), 37: ('p2', 'p2-towers-vi-past-future-s-end-1'),
    39: ('p2', 'p2-light-of-judgement-1'), 41: ('p2', 'p2-wings-of-destruction-1'),
    43: ('p2', 'p2-ultimate-embrace-2'),
    51: ('p3', None), 53: ('p3', 'p3-stray-flames-tsunami-1'),
    55: ('p3', 'p3-thunder-iii-1st-set-1'), 57: ('p3', 'p3-stray-flames-tsunami-2'),
    59: ('p3', 'p3-cyclone-1'), 61: ('p3', 'p3-thunder-iii-2nd-set-1'),
    67: ('p3', 'p3-thunder-iii-3rd-set-1'), 69: ('p3', 'p3-earthquake-1'),
    71: ('p3', 'p3-shocking-impact-shockwave-1'), 73: ('p3', 'p3-thunder-iii-4th-set-1'),
    75: ('p3', 'p3-shocking-impact-shockwave-2'), 77: ('p3', 'p3-thunder-iii-5th-set-1'),
    79: ('p3', 'p3-shocking-impact-shockwave-3'), 81: ('p3', 'p3-shocking-impact-shockwave-3'),
    83: ('p3', 'p3-stomp-a-mole-knock-down-1'),
    89: ('p4', 'p4-grand-cross-3'), 91: ('p4', 'p4-ultima-upsurge-1'),
    93: ('p4', 'p4-death-bolt-wave-2'), 95: ('p4', 'p4-ultima-upsurge-2'),
    101: ('p5', None), 103: ('p5', 'p5-ultima-repeater-1'), 105: ('p5', 'p5-fell-forces-3x-1'),
    107: ('p5', 'p5-chaotic-flood-1'), 109: ('p5', 'p5-maddening-orchestra-1'),
    111: ('p5', 'p5-maddening-orchestra-1'), 113: ('p5', 'p5-fell-forces-2x-1'),
    115: ('p5', 'p5-celestriad-1'), 117: ('p5', 'p5-ultima-repeater-2'),
    119: ('p5', 'p5-fell-forces-2x-2'), 121: ('p5', 'p5-maddening-orchestra-2'),
    123: ('p5', 'p5-maddening-orchestra-2'), 125: ('p5', 'p5-fell-forces-3x-2'),
    127: ('p5', 'p5-forsaken-1st-hit-1'), 129: ('p5', 'p5-forsaken-bonds-4th-hit-1'),
}

# Cells the sheet writes as prose, or that describe the row rather than the
# column they sit in - "OT Invuln" in the MT column names who invulns, not what
# the MT presses. Keyed by (row, seat); the value is a list of (token, note)
# pairs, expanded per job like any other cell.
TANK_CELLS = {
    (17, 'MT'): [('Provoke', None)], (17, 'OT'): [('Invuln', None)],
    (19, 'MT'): [('Rep', 'Use after the second part lands.')],
    (71, 'MT'): [('Rep', 'On Chaos.')],
    (25, 'MT'): [('Invuln', None)], (25, 'OT'): [],
    (61, 'MT'): [('Invuln', None)], (61, 'OT'): [],
    (73, 'MT'): [], (73, 'OT'): [('Invuln', None)],
    (69, 'MT'): [], (69, 'OT'): [],
    (81, 'MT'): [('120', None), ('Short', None)],
    (81, 'OT'): [('120', None), ('Short', None)],
    (113, 'MT'): [('Invuln', 'CARRY')], (113, 'OT'): [],
    (125, 'MT'): [('90', 'Share the third auto with your co-tank.')],
    (125, 'OT'): [('Invuln', 'CARRY'), ('90', 'On the third auto.')],
}

# Where the tank sheet and the compile disagree, the compile wins - it is the
# sheet LPDU points people at. Row 67 is the third Thunder III, where the tank
# sheet writes a flat "Short" but the compile says "Shorts (not corundum)", so
# the Gunbreaker does not press one at all.
TANK_EXCLUDE = {(67, 'GNB'): {'Heart of Corundum'}}

# A row note that only holds for some tank jobs. The plan is generated per job,
# so an off-list note is simply not written.
TANK_NOTE_JOBS = {
    11: (['GNB', 'DRK'], 'GNB/DRK can mit when the tether knockback appears.'),
    31: (['WAR'], 'Holmgang instead if WAR.'),
    89: (['PLD', 'WAR'], 'Press after the Chaos 2 debuff damage.'),
    93: (['DRK', 'GNB'], 'Press at the start of the Ultima Upsurge castbar.'),
}
# Row notes rewritten from the source's shorthand, or dropped where they only
# point at a picture in the spreadsheet.
TANK_NOTES = {
    9: 'Mit immediately after the second buster hit.',
    21: 'Press when Confetti is on 1s to catch Light of Judgement.',
    23: 'Press on cooldown.',
    55: 'Assumes Exdeath is held middle. Check the wall-Exdeath sheet for Walldeath.',
    69: 'Covered by the Thunder III mitigation above.',
    81: 'Only if you are third in line. Cover your co-tank if they are.',
    101: 'At a third of the "I\'ll raze to the ground" textbox.',
    107: 'Voke again for safety - the OT needs aggro.',
    109: 'Tank swap so the boss does not get dragged out.',
    113: 'The MT is main threat until the next flare.',
    121: 'Tank swap so the boss does not get dragged out. Press Rampart last so it holds until the final auto.',
}
# A note that belongs to some rows only for one seat.
TANK_SEAT_NOTES = {(21, 'MT'): 'WAR/PLD mit after the Confetti hit.'}

# Phase-wide asides on the tank plan, from the sheet's assignment headers.
TANK_PHASE_NOTES = {
    'p5': 'The OT starts with aggro.',
    'p3': ('The MT starts on Exdeath and the OT on Chaos, then the two swap during the '
           'Decisive Battle by standing under their boss after it cast-locks and provoking. '
           'Paladin is forced offtank from P3 onward: the invulns do not work with a Paladin '
           'main tank.'),
}


# Party mitigation the tank workbook also writes down. `tankMits` is what a tank
# does for *itself*; what it does for the group is the party grid's job, and the
# compile is the source for that. So these tokens are dropped here rather than
# said twice, in two sheets that can disagree. A row left with nothing after the
# drop is not emitted at all.
PARTY_TOKENS = {'Party Mit', 'Rep'}


def tank_tokens_for(raw, row, seat):
    """The raw shorthand tokens in one MT/OT cell, before any expansion."""
    pairs = TANK_CELLS.get((row, seat))
    if pairs is not None:
        return [token for token, _ in pairs]
    return split_top(clean(raw), [' + ', '+']) if raw else []


def tank_actions(raw, job, row, seat):
    """One MT/OT cell -> the personal-mit action dicts for this job."""
    pairs = TANK_CELLS.get((row, seat))
    if pairs is None:
        pairs = [(token, None) for token in split_top(clean(raw), [' + ', '+'])] if raw else []
    tokens = tank_tokens(job)
    out = []
    for token, note in pairs:
        if token in PARTY_TOKENS:
            continue
        if token == 'Short to cotank':
            for name in BUDDY_MIT[job]:
                out.append({'name': name, 'buddy': True})
            continue
        if token not in tokens:
            raise ValueError(f'Unknown tank token {token!r} (row {row} {seat})')
        for name in tokens[token]:
            action = {'name': name}
            if note == 'CARRY':
                action['carryOver'] = True
            elif note:
                action['note'] = note
            out.append(action)
    seen, deduped = set(), []
    for action in out:
        key = (action['name'], action.get('note'), action.get('carryOver'))
        if key not in seen:
            seen.add(key)
            deduped.append(action)
    return deduped


# What a tank does *for the group* - the only thing that belongs in the party
# grid's tank columns, as in the Ikuya sheet, whose MT/OT columns hold nothing
# but these. Everything else the LPDU compile writes there is personal mit and
# moves to `tankMits`, where the tank sheet's own rows already live.
def is_group_mit(name):
    return name.startswith('Party Mit') or re.sub(r'\s*\([^)]*\)$', '', name) == 'Reprisal'


def moved_actions(action, job):
    """A personal action lifted off the party grid -> what this job presses."""
    out = []
    for name in party_buttons(action['name'], job):
        moved = {'name': name}
        if action.get('buddy'):
            moved['buddy'] = True
        if action.get('carryOver'):
            moved['carryOver'] = True
        # `noteJobs` scopes the note, not the press.
        if action.get('note') and job in (action.get('noteJobs') or TANKS):
            moved['note'] = action['note']
        out.append(moved)
    return out


def party_buttons(name, job):
    """A party-grid action name -> the buttons this job actually presses, so a
    personal row can be compared against what the party row already shows."""
    match = re.match(r'^(.*?)\s*\(([^)]*)\)$', name)
    base, qualifier = (match.group(1), match.group(2)) if match else (name, None)
    if qualifier and re.fullmatch(r'[A-Z]{3}(/[A-Z]{3})*', qualifier):
        if job not in qualifier.split('/'):
            return []          # someone else's line
    else:
        base = name            # "(3x)" and friends are part of the real name
    return {
        'Party Mit': [PARTY_MIT[job]], 'Short Mit': SHORT_MIT[job],
        '90s Mit': [MIT_90[job]], '120s Mit': [MIT_120[job]],
        'Invuln': [INVULN[job]], 'Buddy Mit': BUDDY_MIT[job],
        'Kitchen Sink': TANK_KITCHEN_SINK[job],
    }.get(base, [base])


def convert_tanks(path, phase_starts, mechanic_names, moved):
    archive = zipfile.ZipFile(path)
    strings = [''.join(node.itertext()) for node in
               ET.fromstring(archive.read('xl/sharedStrings.xml'))]
    cells = read_cells(archive, strings, TANK_SHEET)

    def seconds(value):
        """Seconds from a B-cell: a stored time fraction, or '15:07~'."""
        try:
            return round(float(value) * 1440)
        except (TypeError, ValueError):
            match = re.search(r'(\d+):(\d+)', str(value))
            return int(match.group(1)) * 60 + int(match.group(2)) if match else 0

    plans = []
    for job in TANKS:
        phases = {}
        for row, (phase_id, anchor) in sorted(TANK_ROWS.items()):
            start = phase_starts[phase_id]
            relative = max(0, seconds(cells.get(f'B{row}')) - start)
            name = clean(cells.get(f'C{row}', ''))
            notes = []
            if row in TANK_NOTES:
                notes.append(TANK_NOTES[row])
            elif cells.get(f'F{row}') and row not in TANK_NOTE_JOBS:
                notes.append(clean(cells[f'F{row}']))
            if row in TANK_NOTE_JOBS:
                jobs, text_note = TANK_NOTE_JOBS[row]
                if job in jobs:
                    notes.append(text_note)
            raw = {seat: cells.get(f'{column}{row}') for seat, column in (('MT', 'D'), ('OT', 'E'))}
            written = [token for seat in ('MT', 'OT')
                       for token in tank_tokens_for(raw[seat], row, seat)]
            # A row the tank sheet spends entirely on party mitigation is the
            # party grid's to state, note and all - drop it whole rather than
            # leave an empty row carrying its note.
            if written and all(token in PARTY_TOKENS for token in written):
                continue
            by_seat = {seat: tank_actions(raw[seat], job, row, seat) for seat in ('MT', 'OT')}
            drop = TANK_EXCLUDE.get((row, job))
            if drop:
                by_seat = {seat: [a for a in actions if a['name'] not in drop]
                           for seat, actions in by_seat.items()}
            # A row note belongs to whoever presses something on that row. A row
            # the sheet wrote with no buttons at all is a marker ("Covered by the
            # Thunder III mitigation above") and both seats keep it; otherwise the
            # idle seat would show a note about the other tank's press.
            marker = not written
            for seat in ('MT', 'OT'):
                actions = by_seat[seat]
                seat_notes = list(notes) if actions or marker else []
                if (row, seat) in TANK_SEAT_NOTES and actions:
                    seat_notes.append(TANK_SEAT_NOTES[(row, seat)])
                if not actions and not seat_notes:
                    continue
                # A row that names the very mechanic it hangs off is that
                # mechanic's personal line, not a beat of its own - drop the
                # timestamp so MitView folds it into the party row instead of
                # repeating the heading underneath it. Rows the tank sheet gives
                # its own label ("Autos 1", "Flare Diffusion 1") keep both.
                mechanic = {'id': f'{job}-r{row}-{seat}'.lower(), 'name': name}
                if name != mechanic_names.get(anchor):
                    mechanic['time'] = f'{relative // 60}:{relative % 60:02}'
                if anchor:
                    mechanic['after'] = anchor
                mechanic['seat'] = seat
                if seat_notes:
                    mechanic['note'] = ' '.join(dict.fromkeys(seat_notes))
                mechanic['actions'] = actions
                phases.setdefault(phase_id, []).append(mechanic)
        # Personal mit lifted off the party grid. Whatever the tank sheet's own
        # rows already press is left to them - they carry the sheet's labels
        # ("Autos 1", "Flare Diffusion 1"), which say more than the encounter's
        # name for the same beat - but their notes are the compile's, which are
        # the better ones. Anything left over becomes a row of its own, named
        # for the mechanic so it folds into the party row above.
        for (phase_id, anchor, seat), actions in moved.items():
            rows = [m for m in phases.get(phase_id, [])
                    if m.get('after') == anchor and m['seat'] == seat]
            leftover = []
            for action in (a for source in actions for a in moved_actions(source, job)):
                existing = next((a for row in rows for a in row['actions']
                                 if a['name'] == action['name']), None)
                if existing is None:
                    leftover.append(action)
                elif action.get('note') and 'note' not in existing:
                    existing['note'] = action['note']
            if leftover:
                phases.setdefault(phase_id, []).append({
                    'id': f'{job}-{anchor}-{seat}'.lower(), 'name': mechanic_names[anchor],
                    'after': anchor, 'seat': seat, 'actions': leftover,
                })
        plans.append({'job': job, 'phases': [
            {'id': phase_id,
             **({'note': TANK_PHASE_NOTES[phase_id]} if phase_id in TANK_PHASE_NOTES else {}),
             'mechanics': mechanics}
            for phase_id, mechanics in sorted(phases.items()) if mechanics
        ]})
    return {
        'note': 'Tank personal mit from the LPDU tank sheet (tinyurl.com/LPDUtankmit), which is '
                'universal: both bosses in P3 and both invulns in P5 are fixed by seat, so there '
                'is nothing to choose here.',
        'plans': plans,
    }


if __name__ == '__main__':
    moved = {}
    sheet = convert(sys.argv[1], moved)
    if len(sys.argv) > 2:
        encounter = json.loads((Path(__file__).resolve().parent.parent / 'packages' / 'encounter-data' / 'fights'
                                / 'dmu' / 'encounter.json').read_text(encoding='utf-8'))
        starts = {p['id']: int(p['start'].split(':')[0]) * 60 + int(p['start'].split(':')[1])
                  for p in encounter['phases']}
        names = {m['id']: m['name'] for p in encounter['phases'] for m in p['mechanics']}
        sheet['tankMits'] = convert_tanks(sys.argv[2], starts, names, moved)
    out = Path(__file__).resolve().parent.parent / 'packages' / 'encounter-data' / 'fights' / 'dmu' / 'sheets' / 'lpdu.json'
    out.write_text(json.dumps(sheet, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'wrote {out}')
