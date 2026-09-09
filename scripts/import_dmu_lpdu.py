"""Convert the "LPDU General DMU Mit Compile" P1-P5 tabs into reviewed repo JSON.

Usage: python3 scripts/import_dmu_lpdu.py '/path/to/LPDU.xlsx'
Uses Python's standard library. The site never reads Excel at runtime.

Scope (this pass): the five party-wide mitigation grids only. The hidden
"Tank FAQ" / "Tank Mitigation (All Comps)" tabs are NOT imported -- they would
become `tankMits`, and that is a separate pass.

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
ROLES = {'MT': 'tank', 'OT': 'tank', 'M1': 'melee', 'M2': 'melee', 'P': 'ranged', 'C': 'caster',
         **{job: 'healer' for job in HEALERS}}

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
}

# A phase-wide aside, shown once under the phase heading.
PHASE_NOTES = {
    'p3': 'Paladin is the forced Chaos-start tank and is the offtank (right column) from this point of the fight onward, because of Hallowed Ground timing.',
    'p5': 'This grid shows shields, mitigation and major cooldowns only. Check the job pastebins for the exact healing.',
}

# Column A holds a priority call that belongs to the row it sits on.
COLUMN_A_NOTES = {('p2', 30): 'Wall priority: PLD > WAR > DRK > GNB.',
                  ('p3', 18): 'Tank LB priority: WAR > DRK > PLD > GNB.'}

# Generic names, resolved to the viewer's own button by data/jobs.json. Anything
# not listed here has to be a real in-game action name.
GENERIC = {'Party Mit', 'Buddy Mit', 'Short Mit', '90s Mit', '120s Mit', 'Invuln', 'Extra'}

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

# Cells that are prose, not a token list. Keyed by (phase, column, row).
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
                      {'name': 'Short Mit', 'note': 'Not Heart of Corundum.', 'noteJobs': ['GNB']}],
    ('p3', 'G', 26): [{'name': '120s Mit', 'note': 'Use late.'},
                      {'name': 'Reprisal', 'note': 'First hit.'},
                      {'name': 'Short Mit', 'note': 'Not Heart of Corundum.', 'noteJobs': ['GNB']}],
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
    ('p5', 'N', 42): [{'name': 'Succor'}, {'name': 'Seraphism'},
                      {'name': 'Summon Seraph', 'note': 'Off cooldown.'}],
    ('p5', 'P', 44): [{'name': 'Eukrasian Prognosis II'}, {'name': 'Panhaima'},
                      {'name': 'Physis II'}, {'name': 'Pneuma', 'note': 'After.'}],
    ('p5', 'E', 48): [{'name': 'Enrage'}],
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


def convert(path):
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
                actions = OVERRIDES.get((phase_id, column, row)) or cell_actions(raw)
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
        'name': 'LPDU Mit Compile',
        'author': 'LPDU',
        'updated': '2026-09-09',
        'sourceFile': 'LPDU GENERAL DMU MIT COMPILE',
        'source': {
            'name': 'LPDU General DMU Mit Compile',
            'url': 'https://docs.google.com/spreadsheets/d/1aA_qF_UsoS51MCDZ4PwQHhprpK7eGO8TXOdZ7pQlkV0/edit',
        },
        'description': 'P1–P5 party mitigation from the LPDU compile sheet, which follows LPDU strats. Choose a tank position, healer job, or DPS position.',
        'slots': [{'id': 'MT', 'role': 'tank'}, {'id': 'OT', 'role': 'tank'},
                  *({'id': job, 'job': job, 'role': 'healer'} for job in HEALERS),
                  {'id': 'M1', 'role': 'melee'}, {'id': 'M2', 'role': 'melee'},
                  {'id': 'P', 'role': 'ranged'}, {'id': 'C', 'role': 'caster'}],
        'phases': phases,
    }


if __name__ == '__main__':
    sheet = convert(sys.argv[1])
    out = Path(__file__).resolve().parent.parent / 'data' / 'fights' / 'dmu' / 'sheets' / 'lpdu.json'
    out.write_text(json.dumps(sheet, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'wrote {out}')
