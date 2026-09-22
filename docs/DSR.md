# DSR encounter and sheet import

Imported [Malachite Laurent's DSR workbook](https://docs.google.com/spreadsheets/d/1sUEuFDGa_Qg4SYHo4y7b4oEvUGvmhkUMn2rPdXdWEo0/edit?gid=1960553822#gid=1960553822)
on 2026-09-17. The party grid covers Thordan, Nidhogg, Eyes, Rewind,
Dark Thordan, Double Dragons, and Dragon King Thordan. All six tank-pairing
tabs contribute both jobs, giving 12 personal plans. The workbook has no
P1 door-boss plan. The viewer therefore begins at the Thordan checkpoint.

## Logs and phase clocks

Queried FFLogs v2 `worldData.encounter.fightRankings(metric: speed)` for
1065 and 1076. Original DSR's default partition had 423 ranking entries
across nine pages. Legacy DSR's default partition had 38 entries on one page.
The six slowest legacy entries were selected, with accessible event data and
checkpoint clear durations from 18:28.215 to 18:54.174. These are the slowest
entries in that ranking snapshot, not a claim to have searched every public
clear across every historical partition.

The original ranking's longest entry was
[VW6wtRMdz2vm9ZQ4 / 2](https://www.fflogs.com/reports/VW6wtRMdz2vm9ZQ4?fight=2).
Its 20:54.016 report duration includes 158.570 seconds before the Thordan
checkpoint. Its events, and those of the other three slow original entries
examined, are archived and unavailable through the client API. They are not
used for the mechanic audit or phase maxima.

[DSR-TIMINGS.md](DSR-TIMINGS.md) lists the six accessible reports, exact phase
durations, and each selected mechanic's phase-relative observations.
The report fight duration includes a short terminal delay, so it differs
slightly from the ranking's `duration`. Phase lengths use the report's
actual transitions, not the leaderboard duration.

For each phase, add the longest observed preceding phase length to the
unrounded cumulative clock, then round once to seconds for `phase.start`.
Mechanic times use the median observation relative to their own phase.
This follows the FRU/TOP convention and does not shift mechanics earlier
because one group pushed a preceding phase faster.

| Phase | Start from checkpoint |
| --- | --- |
| P2 Thordan | 0:00 |
| P3 Nidhogg | 3:26 |
| P4 Eyes | 5:40 |
| Rewind | 6:57 |
| P5 Dark Thordan | 8:21 |
| P6 Double Dragons | 11:29 |
| P7 Dragon King Thordan | 15:15 |

Phase ownership follows the workbook sections. Final Chorus closes P2; P3
starts immediately after its logged damage, rather than at FFLogs' earlier
animation transition. The half-open event window ends one millisecond after
the impact. P2 Final Chorus is at 3:23, the median checkpoint-relative impact;
P3 starts at 3:26, using the longest observed P2 including that transition.
FFLogs phase IDs 2 and 4 through 7 supply the other pre-P7 boundaries. P7
begins at Alternative End's cast event, roughly nine seconds before FFLogs
phase 8 becomes targetable, matching the source's P7 Transition row.

Cast-bar mechanics use `begincast`. Instant attacks use the first damage
event, including Ultimate End and Final Chorus, whose earlier animation casts
deal no damage. Rewind's Pure of Heart uses cast completion because its long
cast begins before the four Brightwing bait pairs. Minor non-damage cues use
their cast event. Ability IDs come from report master data and logged events.
Random Broad Swing, Hallowed Wings, and Great Wyrmsbreath variants share
occurrence counters. Simultaneous targets and multihit sequences do not
duplicate the sheet's presses. Brightwing's four bait pairs remain separate.

## Workbook decisions

The party overlay contains 34 rows, including the blank fourth Brightwing
pair and Feint/healer assignments from the P5 footnotes. It has 268 actions:
48 / 20 / 25 / 26 / 34 / 50 / 65 by phase. The 12 tank plans contain 310
personal and buddy actions.

- Eyes uses rows 999 through 1005. Rows 1973 through 1979 repeat the same
  block, except the first explicitly says early Temperance. The importer
  checks that equivalence and keeps the first block once.
- Double Dragons and Dragon King Thordan retain copied TOP placeholders
  below their grids. They are checked as known template rows and excluded.
  The tank tabs likewise stop after their real P7 notes, before stale Cosmo
  Dive instructions.
- Second grid lines are meaningful. Reprisal, optional Spreadlo/Holos,
  second-GCD Soil/Kerachole, early Soil/Kerachole after the second melee auto,
  and single-target shields on the Mortal Vow melee are preserved.
- Level-90 shield names remain Succor and Eukrasian Prognosis. The source's
  ZoeProg/ZoeEukrpog shorthand expands to Zoe plus Eukrasian Prognosis.
  The existing per-job generic Party Mit and Buddy Mit resolution is reused.
- Rewind's source order is healers, melee, ranged, tanks. It maps to the
  four Brightwing occurrences. Tank buddy assignments target M1/M2 explicitly.
- The P5 footnote assigns M1 Feint to the second Heavenly Heel. Its healer
  instruction becomes an Assist Tanks assignment for each healer, with the
  source instruction as the mechanic note. This keeps it visible in Mit only
  even though the canonical buster is tank-scoped.
- The optional M2 Feint beside Wroth Flames retains the source's Hallowed
  Plume instruction. The source does not identify a specific Plume occurrence,
  so no new occurrence-specific assignment is invented.
- The tank rows called Ascalon's Might include the preceding Heavenly Heel
  for the second P2 buster and both P5 busters. They anchor at that earlier
  cast. Strength's personal mitigation anchors at Holy Shield Bash. Personal
  rows reuse canonical names and times, so the viewer folds them correctly.
- Tank tabs fix duties by job pairing; MT/OT does not exchange their invuln
  routes. Buddy lines remain separate from personal cooldowns. Kitchen Sink
  retains the established generic instruction instead of inventing buttons.
- Tank row notes retain the WB2 and AM1 timing instructions. Two PLD
  footnotes copied "Nebula" from the GNB column; the corresponding PLD row
  explicitly assigns Sentinel, so the importer applies that timing to Sentinel.
  Source typos such as Camoflauce, Sentinal, and Rerprisal are normalized.

## Rebuilding and verification

`scripts/reconcile_dsr.py` is an explicit maintainer operation. It alone writes
the encounter and timing evidence. It rejects incomplete FFLogs responses,
non-clears, unseen mechanics, and unexpected extra occurrences.

`scripts/import_dsr_malachite.py` downloads the workbook by default, or accepts
`--xlsx` for a reviewed snapshot. It validates the source layout and action
tokens, binds rows to the existing encounter, and writes only the sheet.
Unknown rows, changed duplicate blocks, and unknown action/continuation
text fail rather than silently disappearing. Workbook formats in this snapshot
contain no muted carry-over assignments.

Run from the repository root:

```sh
rtk proxy python3 scripts/reconcile_dsr.py --cache /tmp/dsr-logs
rtk proxy python3 scripts/import_dsr_malachite.py
rtk proxy python3 -m unittest discover -s scripts -p 'test_*.py'
rtk yarn run lint
rtk yarn run build
rtk yarn run test
```

Python tests cover shorthand, buddy scope, continuation notes, strict failures,
and random mechanic variants. Catalog tests cover phase starts, all pairings,
source counts, transitions, and canonical personal anchors. Rendering tests
exercise all supported jobs, layouts, Mit only, compact rendering, and both
tank seats.

## Chrome source audit — 2026-09-18

Compared the live workbook's five party tabs and six tank tabs with the local
viewer in Google Chrome. Read the rendered assignments and notes through
Chrome's accessibility tree, with visual inspection of the source grids.
The viewer used All phases, Notes shown, Mit only, and personal mits enabled.

| Coverage | Chrome checks |
| --- | --- |
| SCH, SGE, WHM, AST | Each healer column, optional buttons, early/late timing, Mortal Vow shields, and P5 buster instruction |
| BRD, MCH, DNC | Party mitigation; Dismantle appears only for MCH |
| BLM, SMN, RDM, PCT | Addle; Magick Barrier appears only for RDM |
| MNK, DRG, NIN, SAM, RPR, VPR | Both M1 and M2 columns; identical Feint duties within each seat |
| WAR/DRK, WAR/GNB, WAR/PLD, GNB/DRK, GNB/PLD, PLD/DRK | Both jobs in both MT and OT: 24 configurations |

For every tank configuration, checked party mitigation and Reprisal placement,
M1/M2 buddy targets, personal cooldowns, invulnerability routes, co-tank buddy
buttons, Heel/Slashes targets, and timing notes. Switching seats changed party
duties and preserved the selected pairing's personal plan. Source instructions
that leave coordination to the tanks remain notes, including the first-Might
Reprisal instruction in non-WAR pairings.

The audit found the P5 healer footnote was hidden from healers by tank-role
filtering. Added explicit Assist Tanks assignments, then revisited all four
healers in Chrome: Heavenly Heel 3 (the second P5 buster) now shows the
instruction in Mit only. A regression test covers all layouts and compact
rendering. This pass checked buttons and targets but missed Final Chorus phase ownership;
the phase audit below corrects that omission.

## Fight selection order

Encounters require an ISO `released` date. Catalog validation sorts newest
first, so the existing fight dropdown displays DMU, FRU, TOP, DSR without
fight-specific UI logic. Original release dates are 2026-06-02, 2024-11-26,
2023-01-24, and 2022-04-26 respectively. Dates follow the Lodestone's
[7.51 maintenance notice](https://na.finalfantasyxiv.com/lodestone/news/detail/5c2bb994bb4ea2c665ab87552a0853d9e941b2e8)
and [archived update log](https://na.finalfantasyxiv.com/lodestone/special/update_log/2/).

## Phase and row audit — 2026-09-18

Revisited all five party tabs in Chrome, checking section headings and row
order rather than only action presence. Compared all 34 overlay rows with
their source sections. Also checked the five phase headers and row bindings
in all six tank tabs.

| Source section | Viewer mapping |
| --- | --- |
| Thordan P2 | Strength, Quaga, Sanctity, Ultimate End, Final Chorus |
| Nidhogg P3 | First Stack → Eye of the Tyrant 1; Second Stack → Eye of the Tyrant 2; Soul Tether |
| Eyes P4 | Resentment; Orb Pops → Flare Nova; Dives → Mirage Dive; Steep in Rage |
| Rewind | Healers/Melee/Range/Tank → Brightwing 1–4; Pure of Heart |
| Dark Thordan P5 | Wrath, first Quaga, Death, second Quaga, second Heel footnotes |
| Double Dragons P6 | First Wyrmsbreath, first Akh Afah, Wroth, second Akh Afah, second Wyrmsbreath, final Cauterize |
| Dragon King P7 | Transition → Alternative End; three Akh Morns interleaved with two Gigaflares |

Final Chorus was the only misplaced source row found. The encounter, importer,
phase clocks, and generated timing evidence now agree on P2 ownership.
The importer checks each party row against the preceding workbook phase
heading and rejects a mismatch. Tests cover the complete source phase/order
mapping, transition windows, and Final Chorus rendering in every layout.

Canonical labels still use logged ability names and fight-wide occurrence
counts, as other encounters do. Thus the second P5 Heel is displayed as
Heavenly Heel 3, and the final P6 Cauterize as Cauterize 3; these are the
correct occurrences, not assignments moved from another source row.

## Note placement audit — 2026-09-18

Compared source continuation cells and tank footnotes with their action,
mechanic, phase, and job scope. Fixed mechanic-specific tank footnotes that
were previously imported as phase-wide notes:

- First-Might Reprisal coordination now sits under Ascalon's Might 1.
- Second-buster Feint coordination now sits under the second P5 Heavenly Heel.
  The shared healer instruction already appears there and is not repeated.
- WB2 cooldown timing now sits under Great Wyrmsbreath 2.
- AM1 cooldown timing now sits under the first Akh Morn's Edge.
- The instruction to use cooldowns on autos throughout P3 remains a phase note.

Optional Deployment Tactics/Holos and early or second-GCD Soil/Kerachole
notes explicitly name their abilities, since the viewer places action notes
below the entire action group. Mortal Vow shields, Rewind melee buddy targets,
Heel/Slashes duties, late Rewind shields, early Temperance/ranged mitigation,
and end-of-cast Holmgang retain their source mechanic and action scope.

Rechecked the relocated notes in Chrome for all 12 job/co-tank perspectives,
and healer timing/optional notes for SCH and SGE. Rendering tests verify that
each tank row note follows its own heading and precedes the next mechanic,
in both seats and list/tab layouts. The Notes toggle hides them; cheatsheets
continue to omit notes by design.
