# FRU encounter reconciliation

All five phases are reconciled, with names, timings, and visibility reviewed.
Read this alongside
[REMODEL.md](REMODEL.md).

P1 tank-only visibility was subsequently approved in [FRU-TANKS.md](FRU-TANKS.md).
The phase tables below record the earlier party-grid review; the four P1
Powder/Burn Mark entries now display for tanks.

## Party-sheet reconciliation

Rechecked the live workbook's five party tabs on 2026-09-12. The importer
retains 45 source rows and 371 expanded assignments: P1 7/59, P2 11/86,
P3 9/68, P4 9/68, P5 9/90 (rows/actions). P4 includes the two empty
Edge of Oblivion overlays; the encounter still hides them. The one deliberately
excluded source row is P3 Dark Water III 3 and its RDM Barrier assignment,
as approved during review. Grouped sheet rows bind to the reviewed first
mechanic; they do not duplicate presses onto subsequent hits.

The workbook's font formatting is part of its instructions. Grey text is
lingering mitigation (`carryOver`, 13 actions); italic muted/coloured text is
conditional (15 expanded actions, labelled in their notes). Mixed-format
cells are read per action, so P1's final Burnished Glory retains Fey/Soil
while Concitation remains a new press. Italic black target names and footnote
markers are only emphasis. Conditions that the workbook leaves unspecified
remain labelled conditional rather than acquiring invented requirements.

The P4 note below the grid preserves the 7/1 Akh Morn strategy and the option
to move physical-ranged party mit to Hallowed Wings. Pandora's Box retains
the source's Tank LB priority: WAR > DRK > PLD > GNB. Footnotes, early/late
instructions, boss targets, and job-scoped extras remain attached to actions.
Tank-pairing tabs are now imported as reviewed in [FRU-TANKS.md](FRU-TANKS.md);
the counts above describe the party overlay only.

`python3 -m unittest discover -s scripts -p 'test_import_fru_mitbutgood.py'`
checks rich-text carry-overs, conditional notes, shorthand parsing, and strict
extra-action handling. Regenerating the sheet never writes encounter timings.

## Sources and clocks

Read through `scripts/fflogs.py`, using FFLogs v2 `reportData.report.fights`,
`phaseTransitions`, `masterData.abilities`, and paginated `events` filtered by
`source.type = 'NPC'`. Ability IDs below are `abilityGameID`, not report-local
actor IDs. Events were restricted to each fight's phase interval.

| Reference | Report / fight | Clear duration | P2 start from pull |
|---|---|---|---|
| A | [Qz4m6k9Z2AgCwWYh / 1](https://www.fflogs.com/reports/Qz4m6k9Z2AgCwWYh?fight=1) | 18:52.881 | 2:45.078 |
| B | [WG4cxnvZRkTHKr3d / 29](https://www.fflogs.com/reports/WG4cxnvZRkTHKr3d?fight=29) | 18:53.823 | 2:46.506 |
| C | [1bxym3nNVFf7rCk9 / 6](https://www.fflogs.com/reports/1bxym3nNVFf7rCk9?fight=6) | 18:09.620 | 2:27.482 |
| D | [JR4QdYPpLKfT6tyj / 28](https://www.fflogs.com/reports/JR4QdYPpLKfT6tyj?fight=28) | 18:18.339 | 2:31.358 |
| E | [q7ZQNHBDh8VvR2jC / 30](https://www.fflogs.com/reports/q7ZQNHBDh8VvR2jC?fight=30) | 18:18.476 | 2:31.577 |
| F | [KFthYXTAnQVN8Ba6 / 26](https://www.fflogs.com/reports/KFthYXTAnQVN8Ba6?fight=26) | 18:19.990 | 2:28.742 |

A and B are the supplied slow clears. C–F are the first four entries returned
by `worldData.encounter(id:1079).fightRankings(page:1,metric:speed)` in this
review. They supplement variant coverage, not the slow-clear anchor.

Use the longest observed duration for phase starts. P1 starts at `0:00`.
The longest P1 in this sample ends at B's FFLogs P2 transition, 166.506 seconds,
so P2's stored `start` is **2:47**. This is a measured slow-clear baseline,
not proof of the encounter's absolute maximum. For later phases, measure
mechanics relative to each log's own FFLogs phase start, and build the canonical
phase starts using the longest observed preceding phases. Do not average fast
and slow phase lengths or copy the workbook's clocks.

Mechanic `time` is the median of the first matching event per sampled pull,
rounded to the nearest second. Each pull contributes once, regardless of the
number of damage targets. Use actual damage packets for damaging mechanics.
For avoidable mechanics with no damage, use cast completion. Utopian Sky's
setup marker and the interrupted enrage use cast start, explicitly labelled
`begincast` in the table.

Powder Mark Trail 2 has synthetic immune events, `hitType: 10`, at cast
completion in A, D and E. Those carry zero damage and no packet ID. They are
excluded from the damage timer; the three actual hit packets place it at
2:11.727–2:11.958, stored as **2:12**. “Absent” in the table means no qualifying
event, including that exclusion, rather than proof the mechanic did not occur.

## Names, variants, and sheet bindings

Cross-reference is the [FRU Mit but Good Fatebreaker tab](https://docs.google.com/spreadsheets/d/1M1LHe4mpb1lyxkLWJxrDwe_JH897nickG3XLTtwnI90/edit),
fetched as XLSX through `scripts/workbook.py`. Its seven party rows and all
59 action entries are preserved by the importer.

| Sheet row | Encounter assignment anchor | Time |
|---|---|---|
| Cyclonic Break 1 | Cyclonic Break 1 | 0:16 |
| Utopian Sky | Utopian Sky | 0:32 |
| Cyclonic Break 2 | Cyclonic Break 2 | 0:58 |
| Burnished Glory 1 | Burnished Glory 1 | 1:28 |
| Fall of Faith (1/2) | Fall of Faith 1 | 1:47 |
| Fall of Faith (3/4) | Fall of Faith 3 | 1:53 |
| Burnished Glory 2 | Burnished Glory 2 | 2:03 |

Utopian Sky keeps its own assignments at its castbar start, **0:32**.
Sinbound Fire III / Sinbound Thunder III remains a separate hidden encounter
row at 0:51, with no assignments moved onto it.

Fall of Faith has four resolutions. The source groups 1/2 and 3/4, so their
presses anchor to hits 1 and 3. Hits 2 and 4 remain independently addressable,
hidden, unassigned encounter rows. No extra presses or carry-over durations are inferred.

- Cyclonic Break 1 uses cast IDs 40144 / 40148; the second uses 40329 / 40330.
  Both resolve with 40145 and repeated avoidable cones 40146. The Sinsmoke /
  Sinsmite follow-ups, 40147 / 40149, get their own rows at 0:18 and 1:00.
- Utopian Sky has setup IDs 40154 / 40155, Blasting Zone 40157 / 40158,
  and Sinbound Fire III / Sinbound Thunder III 40159 / 40160.
- Bound of Faith 40165 resolves through Solemn Charge 40166 and Sinsmoke
  40167. Its row uses the damage at 1:20.
- Each Fall of Faith can use cast 40137 or 40140. The fire branch resolves
  through Solemn Charge 40138 and Sinblaze 40156; lightning through Solemn
  Charge 40141, Sinsmite 40142 and Bow Shock 40143. Bow Shock follows Sinsmite
  by about 0.4 seconds. These are parts of each resolution, not separate tethers.
- The final Burnt Strike branches between 40129 / Blastburn 40130 and
  40133 / Burnout 40134. Explosion's sampled tower IDs are 40122–40126,
  40131 and 40135. No unobserved variants have been added.
- Burnished Glory's two raidwides use 40170, with subsequent Bleeding ticks.
  Bleeding is FFLogs status 1002951, not an action ID, and its server ticks are
  not separate mechanic rows. The final cast is a different action, 40128.
  A and B show its cast start at 2:31.585 / 2:31.842. B shows completion at
  2:41.814; neither sample has its damage in P1. The minor enrage row records
  the observed cast start, **2:32**, without inventing a lethal-hit time.

P1 has 28 rows. Only the seven rows used by the mit sheet are visible by
default; the other 21 carry `minor: true` and stay in the encounter with their
names, timings, and ability IDs. The viewer can still show them if a sheet
assigns them.

Both occurrences of Powder Mark Trail and Burn Mark carry `roles: ['tank']`
and `minor: true`. Their damage targets in both supplied logs are tanks.
Bound of Faith's Sinsmoke hits all eight players, so it is not tank-only.
Auto attacks, individual DoT ticks, and each repeated cone are not separate
rows; the cone ability is attached to its Cyclonic Break occurrence.

## P1 evidence

All numeric source columns are seconds from that pull's start. `cast` means
completion; `begincast` means cast start. Full ability associations live in
`packages/encounter-data/fights/fru/encounter.json`.

| Stored | Mechanic | Event | A | B | C | D | E | F | Blank-row visibility |
|---|---|---|---|---|---|---|---|---|---|
| 0:16 | Cyclonic Break 1 | damage | 15.631 | 15.976 | 15.675 | 15.851 | 15.693 | 15.863 | all |
| 0:18 | Sinsmoke / Sinsmite 1 | damage | 17.724 | 18.023 | 17.813 | 17.854 | 17.745 | 18.001 | hidden |
| 0:26 | Powder Mark Trail 1 | damage | 25.665 | 26.019 | 25.740 | 25.828 | 25.723 | 25.885 | hidden, tank-only |
| 0:32 | Utopian Sky | begincast | 31.730 | 31.872 | 31.800 | 31.754 | 31.779 | 31.717 | all |
| 0:42 | Burn Mark 1 | damage | 41.574 | 41.940 | 41.715 | 41.782 | 41.719 | 41.871 | hidden, tank-only |
| 0:50 | Blasting Zone | cast | 49.986 | 50.212 | 50.026 | 50.026 | 50.050 | 49.980 | hidden |
| 0:51 | Sinbound Fire III / Sinbound Thunder III | damage | 51.454 | 51.644 | 51.490 | 51.452 | 51.476 | 51.406 | hidden |
| 0:58 | Cyclonic Break 2 | damage | 57.732 | 57.946 | 57.756 | 57.774 | 57.801 | 57.694 | all |
| 1:00 | Sinsmoke / Sinsmite 2 | damage | 59.825 | 59.998 | 59.848 | 59.868 | 59.850 | 59.783 | hidden |
| 1:05 | Turn of the Heavens | cast | 64.498 | 64.649 | 64.559 | 64.547 | 64.574 | 64.505 | hidden |
| 1:06 | Burnt Strike 1 | cast | 65.481 | 65.635 | 65.536 | 65.526 | 65.552 | 65.483 | hidden |
| 1:07 | Burnout 1 | cast | 67.167 | 67.336 | 67.267 | 67.220 | 67.244 | 67.179 | hidden |
| 1:12 | Burnt Strike 2 | cast | 71.485 | 71.678 | 71.577 | 71.546 | 71.561 | 71.498 | hidden |
| 1:14 | Blastburn 1 | cast | 73.490 | 73.688 | 73.577 | 73.549 | 73.565 | 73.501 | hidden |
| 1:16 | Brightfire | cast | 75.580 | 75.746 | 75.623 | 75.647 | 75.653 | 75.592 | hidden |
| 1:20 | Bound of Faith | damage | 80.033 | 80.262 | 80.160 | 80.102 | 80.106 | 80.040 | hidden |
| 1:28 | Burnished Glory 1 | damage | 87.875 | 88.037 | 87.990 | 87.946 | 87.943 | 87.874 | all |
| 1:47 | Fall of Faith 1 | damage | 107.130 | 107.470 | 107.459 | 107.236 | 107.332 | 107.123 | all |
| 1:50 | Fall of Faith 2 | damage | 110.338 | 110.463 | 110.481 | 110.358 | 110.450 | 110.333 | hidden |
| 1:53 | Fall of Faith 3 | damage | 112.829 | 112.921 | 112.926 | 112.942 | 112.945 | 112.787 | all |
| 1:55 | Fall of Faith 4 | damage | 115.415 | 115.512 | 115.414 | 115.352 | 115.530 | 115.414 | hidden |
| 2:03 | Burnished Glory 2 | damage | 123.211 | 123.470 | 123.415 | 123.325 | 123.331 | 123.215 | all |
| 2:12 | Powder Mark Trail 2 | damage | absent | 131.958 | 131.914 | absent | absent | 131.727 | hidden, tank-only |
| 2:23 | Burnt Strike 3 | cast | 142.402 | 142.683 | 142.629 | 142.539 | 142.757 | 142.640 | hidden |
| 2:24 | Blastburn / Burnout 2 | cast | 144.408 | 144.382 | absent | 144.545 | 144.764 | absent | hidden |
| 2:27 | Explosion | damage | 147.038 | 147.287 | absent | 147.174 | 147.440 | absent | hidden |
| 2:28 | Burn Mark 2 | damage | 147.662 | 147.913 | absent | 147.796 | 147.837 | absent | hidden, tank-only |
| 2:32 | Burnished Glory 3 (Enrage) | begincast | 151.585 | 151.842 | absent | absent | absent | absent | hidden |

## P2 reconciliation, reviewed

P2 uses the same six reports, with every timestamp measured from that report's
FFLogs P2 transition. Its durations in A–F are 277.783, 278.009, 277.827,
277.606, 277.603 and 277.630 seconds. The longest observed P1 plus P2 is
166.506 + 278.009 = 444.515 seconds, giving P3 a stored start of **7:25**.
P2 retains its **2:47** canonical start.

The Shiva tab's eleven rows and all 86 action entries are preserved. P2 has
58 encounter rows: eleven sheet rows, a tank-only Quadruple Slap row, and
46 hidden rows with `minor: true`. Quadruple Slap shows for tanks at the first
hit, **0:12**, and carries both hit IDs, 40191 and 40192. Its second hit at
0:16 stays recorded as a hidden, tank-only row. Immune events without packet IDs are excluded
from damage timing, including the early zero-damage Hallowed Ray event in A.

Mirror, Mirror keeps its own assignment at cast start, **1:26**, following the
reviewed Utopian Sky convention. Other visible rows use damage timing.
The sheet's Sinbound Holy anchors to the first of four hits. Its House of Light
anchors to **The House of Light**, after Light Rampant; the three earlier
occurrences remain hidden. The visible name omits the occurrence number; its
log-derived ID remains `p2-the-house-of-light-4`. Junction loses the sheet's “Transition” suffix and
uses the logged damage at **4:24**, before the P3 transition at about 4:38.
P2 names, mappings, and the tank-only Quadruple Slap row are reviewed.

Both Banish III variants are recorded, cast IDs 40220 / 40221 and damage IDs
40222 / 40223. The first kick includes the sampled Axe Kick variant 40202
alongside Scythe Kick 40203. Twin Stillness / Twin Silence are avoidable attacks,
not tankbusters. Shining Armor's zero-damage events have no packet IDs, so the
Frost Armor / Shining Armor marker uses cast completion.

The hidden intermission rows include Swelling Frost, Endless Ice Age's cast
start, the six Sinbound Blizzard III sets, Hiemal Storm and Hiemal Ray hits,
and Icecrusher. Icecrusher hits an NPC and is recorded at cast time, not as
party damage. Endless Ice Age has no observed completion here. Missing late
Hiemal events are left absent in the evidence rather than invented.

### P2 evidence

Seconds are relative to each log's P2 anchor. Each stored timestamp rounds the
median of the first qualifying event per pull. Damage requires a packet ID;
`cast` is completion and `begincast` is cast start. Columns A–F refer to the
reports above. Absent means no qualifying event in that pull.

| Stored | Mechanic | Event | A | B | C | D | E | F | Blank-row visibility |
|---|---|---|---|---|---|---|---|---|---|
| 0:12 | Quadruple Slap | damage | 11.984 | absent | absent | 11.983 | 11.988 | absent | tank-only |
| 0:16 | Quadruple Slap 2 | damage | 16.171 | absent | absent | 16.168 | 16.174 | absent | hidden, tank-only |
| 0:22 | Mirror Image | begincast | 21.871 | 21.861 | 21.878 | 21.876 | 21.876 | 21.857 | hidden |
| 0:33 | Diamond Dust | damage | 32.872 | 32.864 | 32.872 | 32.876 | 32.871 | 32.863 | all |
| 0:41 | Scythe Kick / Axe Kick 1 | cast | 40.627 | 40.599 | 40.611 | 40.633 | 40.616 | 40.880 | hidden |
| 0:42 | The House of Light 1 | damage | 42.050 | 42.031 | 42.037 | 42.062 | 42.088 | 42.306 | hidden |
| 0:44 | Frigid Stone | damage | 43.515 | 43.465 | 43.508 | 43.533 | 43.511 | 43.511 | hidden |
| 0:44 | Icicle Impact 1 | cast | 43.650 | 43.598 | 43.641 | 43.622 | 43.644 | 43.601 | hidden |
| 0:48 | Icicle Impact 2 | cast | 47.652 | 47.621 | 47.644 | 47.633 | 47.655 | 47.653 | hidden |
| 0:48 | Heavenly Strike | damage | 48.410 | 48.381 | 48.399 | 48.391 | 48.413 | 48.412 | hidden |
| 0:50 | Frigid Needle | cast | 50.325 | 50.215 | 50.311 | 50.308 | 50.283 | 50.283 | hidden |
| 0:52 | Icicle Impact 3 | cast | 51.660 | 51.596 | 51.641 | 51.644 | 51.661 | 51.618 | hidden |
| 0:52 | Sinbound Holy 1 | damage | 52.195 | 52.133 | 52.220 | 52.179 | 52.196 | 52.198 | all |
| 0:54 | Sinbound Holy 2 | damage | 53.800 | 53.696 | 53.735 | 53.737 | 53.755 | 53.759 | hidden |
| 0:55 | Sinbound Holy 3 | damage | 55.316 | 55.256 | 55.292 | 55.294 | 55.314 | 55.364 | hidden |
| 0:57 | Sinbound Holy 4 | damage | 56.920 | 56.820 | 56.892 | 56.852 | 56.874 | 56.882 | hidden |
| 1:00 | Frost Armor / Shining Armor | cast | 59.949 | 59.903 | 59.961 | 59.924 | 59.948 | 59.962 | hidden |
| 1:06 | Twin Stillness / Twin Silence 1 | cast | 66.446 | 66.436 | 66.458 | 66.425 | 66.463 | 66.470 | hidden |
| 1:09 | Twin Stillness / Twin Silence 2 | cast | 68.542 | 68.541 | 68.547 | 68.519 | 68.560 | 68.563 | hidden |
| 1:21 | Hallowed Ray | damage | 80.654 | 80.602 | 80.699 | 80.771 | 80.689 | 80.819 | all |
| 1:26 | Mirror, Mirror | begincast | 85.912 | 85.872 | 85.942 | 86.030 | 85.949 | 86.079 | all |
| 1:43 | Scythe Kick 2 | cast | 103.031 | 103.019 | 103.061 | 103.150 | 103.058 | 103.182 | hidden |
| 1:43 | Reflected Scythe Kick 1 | cast | 103.120 | 103.108 | 103.150 | 103.239 | 103.148 | 103.274 | hidden |
| 1:44 | The House of Light 2 | damage | 104.368 | 104.359 | 104.440 | 104.528 | 104.398 | 104.521 | hidden |
| 1:53 | Reflected Scythe Kick 2 | cast | 113.106 | 113.072 | 113.114 | 113.223 | 113.131 | 113.255 | hidden |
| 1:54 | The House of Light 3 | damage | 114.357 | 114.326 | 114.404 | 114.474 | 114.382 | 114.503 | hidden |
| 2:00 | Banish III 1 | damage | 119.885 | 119.868 | 119.918 | 119.995 | 119.949 | 120.032 | all |
| 2:10 | Light Rampant | damage | 129.604 | 129.531 | 129.706 | 129.703 | 129.568 | 129.617 | all |
| 2:17 | Luminous Hammer 1 | damage | 137.233 | 137.176 | 137.357 | 137.405 | 137.238 | 137.279 | hidden |
| 2:19 | Luminous Hammer 2 | damage | 138.840 | 138.741 | 138.956 | 138.919 | 138.797 | 138.843 | hidden |
| 2:20 | Luminous Hammer 3 | damage | 140.357 | 140.304 | 140.469 | 140.478 | 140.357 | 140.403 | hidden |
| 2:21 | Bright Hunger 1 | damage | 140.536 | 140.438 | 140.603 | 140.611 | 140.492 | 140.579 | hidden |
| 2:22 | Luminous Hammer 4 | damage | 141.920 | 141.869 | 142.068 | 142.038 | 141.920 | 142.006 | hidden |
| 2:24 | Luminous Hammer 5 | damage | 143.479 | 143.434 | 143.582 | 143.639 | 143.479 | 143.522 | hidden |
| 2:26 | Powerful Light | damage | 146.242 | 146.164 | 146.342 | 146.355 | 146.198 | 146.240 | all |
| 2:28 | Burst 1 | cast | 148.071 | 147.998 | 148.165 | 148.136 | 148.028 | 148.067 | hidden |
| 2:31 | Burst 2 | cast | 151.107 | 151.042 | 151.189 | 151.164 | 151.058 | 151.095 | hidden |
| 2:35 | Bright Hunger 2 | damage | 155.216 | 155.160 | 155.336 | 155.306 | 155.162 | 155.193 | hidden |
| 2:38 | Banish III 2 | damage | 158.388 | 158.383 | 158.552 | 158.470 | 158.372 | 158.444 | all |
| 2:47 | The House of Light | damage | 167.348 | 167.321 | 167.552 | 167.418 | 167.336 | 167.357 | all |
| 3:06 | Absolute Zero | damage | 186.229 | 186.194 | 186.343 | 186.118 | 186.181 | 186.189 | all |
| 3:08 | Swelling Frost | cast | 188.369 | 188.338 | 188.479 | 188.262 | 188.317 | 188.329 | hidden |
| 3:32 | Endless Ice Age | begincast | 211.955 | 211.919 | 212.058 | 211.852 | 211.893 | 211.885 | hidden |
| 3:40 | Sinbound Blizzard III 1 | cast | 220.334 | 220.323 | 220.444 | 220.196 | 220.273 | 220.259 | hidden |
| 3:41 | Hiemal Storm 1 | cast | 221.451 | 221.439 | 221.558 | 221.311 | 221.388 | 221.373 | hidden |
| 3:45 | Hiemal Storm 2 | cast | 224.791 | 224.741 | 224.900 | 224.657 | 224.727 | 224.715 | hidden |
| 3:46 | Sinbound Blizzard III 2 | cast | 225.730 | 225.678 | 225.834 | 225.550 | 225.663 | 225.654 | hidden |
| 3:48 | Hiemal Storm 3 | cast | 228.051 | 228.050 | 228.197 | 227.914 | 228.022 | 228.011 | hidden |
| 3:48 | Hiemal Ray 1 | damage | 228.542 | 228.495 | 228.641 | 228.448 | 228.467 | 228.455 | hidden |
| 3:51 | Hiemal Ray 2 | damage | 230.596 | 230.554 | 230.691 | 230.494 | absent | 230.505 | hidden |
| 3:51 | Sinbound Blizzard III 3 | cast | 231.088 | 231.046 | 231.226 | 230.938 | 231.052 | 231.040 | hidden |
| 3:51 | Hiemal Storm 4 | cast | 231.356 | 231.359 | 231.492 | 231.250 | absent | absent | hidden |
| 3:53 | Hiemal Ray 3 | damage | 232.653 | absent | 232.738 | 232.546 | absent | absent | hidden |
| 3:56 | Sinbound Blizzard III 4 | cast | 236.447 | 236.412 | 236.613 | 236.335 | 236.404 | 236.431 | hidden |
| 4:02 | Sinbound Blizzard III 5 | cast | 241.801 | 241.777 | 242.036 | 241.724 | 241.795 | 241.817 | hidden |
| 4:07 | Sinbound Blizzard III 6 | cast | 247.152 | 247.140 | 247.413 | 247.108 | 247.187 | 247.205 | hidden |
| 4:08 | Icecrusher | cast | 248.134 | 248.122 | 248.211 | 248.041 | 248.034 | 248.051 | hidden |
| 4:24 | Junction | damage | 264.035 | 264.291 | 264.080 | 263.896 | 263.889 | 263.905 | all |

## P3 reconciliation, reviewed

The same six reports cover P3 from its FFLogs phase transition to P4's.
The measured durations in A–F are 166.631, 167.266, 166.294, 167.050,
166.803 and 167.003 seconds. Keep P3's canonical start at **7:25**.
Adding the longest observed P3 to the preceding unrounded baseline gives
444.515 + 167.266 = 611.781 seconds, so P4 starts at **10:12**.
P4 is now reconciled below.

The Gaia tab has ten party rows and 69 action entries. Nine rows and 68 actions
are imported; the reviewed exclusion is Dark Water III 3 and its RDM extra.
The encounter has 35 rows: thirteen visible party rows, two visible tank-only
rows, and twenty hidden rows. Hidden rows retain their times and ability IDs.

| Sheet row | Encounter assignment anchor | P3 time |
|---|---|---|
| Ultimate Relativity | Ultimate Relativity | 0:19 |
| Fire/Dark Set 1/2 | Dark Fire III 1 | 0:31 |
| Set 3 and Rewind | Dark Fire III 3 | 0:51 |
| Shell Crusher | Shell Crusher | 1:07 |
| Shockwave Pulsar 1 | Shockwave Pulsar 1 | 1:15 |
| Dark Water 1 | Dark Water III 1 | 1:51 |
| Dark Eruption | Dark Eruption | 2:05 |
| Dark Water 3 | Excluded for now; encounter row hidden | 2:19 |
| Shockwave Pulsar 2 | Shockwave Pulsar 2 | 2:25 |
| Memory's End | Memory's End | 2:38 |

All three Dark Fire III and Unholy Darkness occurrences are separate visible
rows, at 0:31, 0:41 and 0:51. Fire uses 40276 and darkness uses 40277. Each
family's damage timestamps round to those same seconds; darkness follows fire
by about 0.1 seconds. The source groups sets 1/2 and set 3 with rewind. Those
assignments stay on Dark Fire III 1 and 3, the first hit of each assigned group;
no duplicate presses are added to Unholy Darkness. The rewind stays hidden.
Dark Blizzard III 40279 and Shadoweye 40278 remain hidden cast markers.
The rewind row groups Dark Eruption 40274 with Dark Water III 40271.

Dark Water III 1–3 refer to the three Apocalypse resolutions, as the sheet
does. The earlier rewind is explicitly named as such. The first Apocalypse
water row carries its castbar/setup IDs 40270 and 40272 as well as damage
40271. The visible Dark Eruption uses castbar 40273 and damage 40274; its name
has no suffix because the earlier hidden rewind has a distinct composite name.

Black Halo, 40290, shows only for tanks at **1:24**. Darkest Dance's first hit,
castbar 40181 and damage 40182, shows only for tanks at **2:13**. These hits
only target tanks in the six samples. The follow-up 40183 hits the party and
stays hidden at 2:16. D has no qualifying first-hit damage packet, so its
synthetic immune event does not contribute to the first-hit timer.

Shell Crusher 40286 / 40287 hits the party. Shockwave Pulsar uses 40282.
Memory's End uses castbar 40300 and damage 40335 and resolves in all six
clears. Its timestamp is damage, not an inferred enrage deadline.
Hell's Judgment has a logged cast but no damage event in this query, so its
hidden row uses cast completion at 0:04. The sheet's existing early-mit notes
still refer to that cast.

Sinbound Meltdown's three sets use castbar 40291, initial damage 40235 and
rotating follow-ups 40292. Each set is one hidden row, anchored to its initial
damage. Apocalypse's setup cast is separate from its six hidden wave rows.
Wave timing uses casts of 40297 rather than the few avoidable damage events.
Spirit Taker 40288 / 40289 is hidden and is not marked tank-only; its sampled
damage targets include several non-tank jobs.

### P3 evidence

Seconds are relative to each report's P3 anchor. The stored time rounds the
median of the first qualifying event per pull. Damage requires a packet ID;
`cast` is completion and `begincast` is cast start. Reports A–F are above.

| Stored | Mechanic | Event | A | B | C | D | E | F | Blank-row visibility |
|---|---|---|---|---|---|---|---|---|---|
| 0:04 | Hell's Judgment | cast | 4.046 | 4.068 | 4.077 | 4.055 | 4.057 | 4.054 | hidden |
| 0:19 | Ultimate Relativity | damage | 19.166 | 19.232 | 19.195 | 19.198 | 19.210 | 19.204 | all |
| 0:28 | Speed | cast | 27.902 | 27.993 | 27.916 | 27.929 | 27.938 | 27.941 | hidden |
| 0:31 | Dark Fire III 1 | damage | 30.842 | 30.899 | 30.849 | 30.829 | 30.836 | 30.835 | all |
| 0:31 | Unholy Darkness 1 | damage | 30.930 | 31.034 | 30.983 | 30.961 | 30.969 | 30.967 | all |
| 0:36 | Sinbound Meltdown 1 | damage | 35.925 | 36.045 | 35.972 | 35.952 | 35.960 | 35.956 | hidden |
| 0:40 | Dark Blizzard III | cast | 40.202 | 40.249 | 40.208 | 40.227 | 40.238 | 40.232 | hidden |
| 0:41 | Dark Fire III 2 | damage | 40.826 | 40.875 | 40.832 | 40.851 | 40.861 | 40.899 | all |
| 0:41 | Unholy Darkness 2 | damage | 40.960 | 41.008 | 40.967 | 40.984 | 40.995 | 40.986 | all |
| 0:46 | Sinbound Meltdown 2 | damage | 45.989 | 46.061 | 45.957 | 45.976 | 46.030 | 46.018 | hidden |
| 0:51 | Dark Fire III 3 | damage | 50.801 | 50.931 | 50.857 | 50.877 | 50.889 | 50.826 | all |
| 0:51 | Unholy Darkness 3 | damage | 50.934 | 51.020 | 50.989 | 50.966 | 50.978 | 50.960 | all |
| 0:57 | Sinbound Meltdown 3 | damage | 56.990 | 57.055 | 57.003 | 56.981 | 57.003 | 56.977 | hidden |
| 1:02 | Shadoweye | cast | 62.196 | 62.240 | 62.207 | 62.236 | 62.221 | 62.237 | hidden |
| 1:03 | Dark Eruption / Dark Water III (Rewind) | damage | 62.683 | 62.730 | 62.694 | 62.725 | 62.711 | 62.726 | hidden |
| 1:07 | Shell Crusher | damage | 67.442 | 67.551 | 67.245 | 67.484 | 67.394 | 67.449 | all |
| 1:15 | Shockwave Pulsar 1 | damage | 75.452 | 75.550 | 75.264 | 75.506 | 75.411 | 75.468 | all |
| 1:24 | Black Halo | damage | 83.675 | 83.997 | 83.491 | 83.971 | 83.742 | 83.889 | tank-only |
| 1:30 | Spell-in-Waiting Refrain | begincast | 90.094 | 90.433 | 89.901 | 90.377 | 90.154 | 90.303 | hidden |
| 1:44 | Apocalypse | begincast | 103.374 | 103.711 | 103.191 | 103.622 | 103.437 | 103.572 | hidden |
| 1:51 | Dark Water III 1 | damage | 111.347 | 111.667 | 111.155 | 111.584 | 111.420 | 111.546 | all |
| 1:54 | Spirit Taker | damage | 113.758 | 114.079 | 113.425 | 113.849 | 113.911 | 113.862 | hidden |
| 2:01 | Apocalypse (Wave 1) | cast | 121.243 | 121.629 | 121.035 | 121.540 | 121.309 | 121.435 | hidden |
| 2:03 | Apocalypse (Wave 2) | cast | 123.245 | 123.641 | 123.039 | 123.583 | 123.315 | 123.441 | hidden |
| 2:05 | Dark Eruption | damage | 124.625 | 124.982 | 124.242 | 124.872 | 124.698 | 124.780 | all |
| 2:05 | Apocalypse (Wave 3) | cast | 125.247 | 125.652 | 125.043 | 125.583 | 125.320 | 125.449 | hidden |
| 2:07 | Apocalypse (Wave 4) | cast | 127.255 | 127.658 | 127.046 | 127.588 | 127.326 | 127.455 | hidden |
| 2:09 | Apocalypse (Wave 5) | cast | 129.261 | 129.667 | 129.049 | 129.590 | 129.328 | 129.455 | hidden |
| 2:10 | Dark Water III 2 | damage | 130.333 | 130.694 | 130.159 | 130.610 | 130.398 | 130.569 | hidden |
| 2:11 | Apocalypse (Wave 6) | cast | 131.270 | 131.675 | 131.049 | 131.630 | 131.331 | 131.461 | hidden |
| 2:13 | Darkest Dance | damage | 133.098 | 133.641 | 132.696 | absent | 133.208 | 133.422 | tank-only |
| 2:16 | Darkest Dance (Knockback) | damage | 135.547 | 136.099 | 135.142 | 135.902 | 135.658 | 135.869 | hidden |
| 2:19 | Dark Water III 3 | damage | 139.331 | 139.673 | 139.187 | 139.591 | 139.401 | 139.565 | hidden |
| 2:25 | Shockwave Pulsar 2 | damage | 144.852 | 145.394 | 144.476 | 145.195 | 144.973 | 145.177 | all |
| 2:38 | Memory's End | damage | 157.966 | 158.541 | 157.630 | 158.340 | 158.117 | 158.315 | all |

## P4 reconciliation, reviewed

P4 uses the same six reports and each report's FFLogs P4 transition as its
relative-time origin. Durations in A–F are 251.513, 250.525, 242.328,
242.698, 242.667 and 242.599 seconds. The phase includes the transition
cinematic before P5 becomes targetable. The longest observed duration is
251.513 seconds. Added to the unrounded preceding baseline of 611.781,
this puts P5 at 863.294 seconds, stored as **14:23**. P4 remains **10:12**.

All nine Light and Dark sheet rows and 68 actions are preserved. P4 has
38 encounter rows: seven visible sheet rows, one visible tank-only row,
and 30 hidden rows. All four Edge of Oblivion occurrences are hidden by review
decision. The sheet includes its first two rows with empty assignments; those
empty references remain, but do not override the encounter's `minor` flag.

| Sheet row | Encounter assignment anchor | P4 time |
|---|---|---|
| Edge of Oblivion 1 | Hidden by review decision | 0:25 |
| Darklit Dragonsong | Darklit Dragonsong | 0:35 |
| The Path of Light | The Path of Light | 0:46 |
| Edge of Oblivion 2 | Hidden by review decision | 1:04 |
| Akh Morn Afah 1 | Akh Morn 1 | 1:11 |
| Crystallize Time | Crystallize Time | 1:36 |
| Crystallize Mech | Crystallized Mech | 1:36 |
| Hallowed Wing | Hallowed Wings | 2:20 |
| Akh Morn Afah 2 | Akh Morn 2 | 2:34 |

Somber Dance is visible for tanks at its first hit, **0:58**, with castbar
40283 and both damage IDs 40284 / 40285. The second hit stays hidden at 1:01.
A has synthetic immune events without packet IDs for both hits; the five
other reports supply the actual tank damage timestamps.

The two “Akh Morn Afah” rows name sequences. Each anchors to the first Akh Morn
hit, with both bosses' cast IDs 40302 / 40247 and damage IDs 40303 / 40248.
Each set has four pulses. Morn Afah follows at 1:21 / 2:44 and has separate
hidden rows, cast IDs 40304 / 40249 and damage 40250. No extra mitigation
presses are inferred from the grouped sheet cells.

The sheet's “Crystallize Mech” maps to **Crystallized Mech**, a reviewed group
anchored one second after Crystallize Time finishes casting. Per-report anchors
in A–F are 96.253, 96.645, 96.174, 96.346, 96.264 and 96.552 seconds; the median
96.305 rounds to **1:36**. It shares the displayed second with the preceding
Crystallize Time damage row, but follows it in encounter order.

The group carries all 22 action IDs observed in NPC cast-start, cast-completion,
and damage events after that cast finishes and before the first player hit of
Hallowed Wings. This includes internal action IDs 40175 / 40244 and the
Hallowed Wings preparatory casts 40229 / 40332 within the interval. It excludes
the actual Hallowed Wings hit and status IDs. The individual resolutions remain
hidden encounter rows, including Dark Water III at 1:49. The sheet's original
early-use notes and all grouped assignments are preserved.

Hallowed Wings during Darklit uses 40227 / 40228. In these samples its damage
target is the fragment of fate NPC, so that hidden row uses cast completion.
The sheet's later Hallowed Wing maps to **Hallowed Wings**, without a number:
its first party hit is 40332, associated with castbar 40229, at 2:20. The
second party hit uses the same damage ID with castbar 40230 at 2:25 and stays
hidden. These are party hits, not tank-only mechanics.

All damage timing in this P4 pass requires a packet ID and a player target.
This matters for Maelstrom, early Hallowed Wings, Tidal Light, and abilities
that hit the fragment of fate alongside players. Maelstrom and the two Tidal
Light sets use cast completion. Tidal Light associates setup 40251 / 40252
and its travelling follow-ups 40253. Akh Rhai and Longing of the Lost are
recorded at the first event in each sequence, without creating one row per
pulse or per player's delayed resolution. Unknown internal action names
40117, 40175, 40231, 40232 and 40244 are not promoted to named mechanics;
40175 and 40244 are retained in the Crystallized Mech interval group.

The two slow clears show simultaneous Memory's End 40305 and Absolute Zero
40245 cast starts at 2:45.612 / 2:45.879. The hidden enrage row uses **2:46**,
the observed cast start. Neither has a completed cast or damage in the fetched
P4 events. The faster clears push before that cast. No lethal timestamp is
inferred from the transition cinematic.

### P4 evidence

Seconds are relative to each report's P4 anchor. Times round the median first
qualifying event per pull. Damage requires a packet ID and a player target;
`cast` is completion and `begincast` is cast start. Reports A–F are above.

| Stored | Mechanic | Event | A | B | C | D | E | F | Blank-row visibility |
|---|---|---|---|---|---|---|---|---|---|
| 0:08 | Materialization | cast | 8.216 | 8.229 | 8.187 | 8.205 | 8.200 | 8.196 | hidden |
| 0:19 | Drachen Armor | cast | 19.415 | 19.451 | 19.402 | 19.438 | 19.438 | 19.420 | hidden |
| 0:22 | Akh Rhai | cast | 21.991 | 22.002 | 21.978 | 22.021 | 22.025 | 22.002 | hidden |
| 0:25 | Edge of Oblivion 1 | damage | 25.060 | 25.038 | 25.003 | 25.048 | 25.056 | 25.035 | hidden |
| 0:35 | Darklit Dragonsong | damage | 34.750 | 34.983 | 34.657 | 34.695 | 34.715 | 34.929 | all |
| 0:46 | Bright Hunger | damage | 45.689 | 45.911 | 45.604 | 45.591 | 45.623 | 45.842 | hidden |
| 0:46 | The Path of Light | damage | 46.489 | 46.758 | 46.409 | 46.438 | 46.473 | 46.731 | all |
| 0:49 | Spirit Taker 1 | damage | 49.250 | 49.521 | 49.083 | 49.237 | 49.236 | 49.402 | hidden |
| 0:53 | Hallowed Wings (Darklit) | cast | 53.076 | 53.321 | 53.000 | 53.018 | 53.069 | 53.277 | hidden |
| 0:53 | Dark Water III (Darklit) | damage | 53.476 | 53.679 | 53.357 | 53.417 | 53.425 | 53.633 | hidden |
| 0:58 | Somber Dance | damage | absent | 57.963 | 57.498 | 57.641 | 57.704 | 57.955 | tank-only |
| 1:01 | Somber Dance (Second hit) | damage | absent | 61.220 | 60.745 | 60.932 | 60.957 | 61.210 | hidden, tank-only |
| 1:04 | Edge of Oblivion 2 | damage | 63.819 | 64.035 | 63.725 | 63.781 | 63.810 | 64.013 | hidden |
| 1:11 | Akh Morn 1 | damage | 71.129 | 71.420 | 70.980 | 71.126 | 71.112 | 71.353 | all |
| 1:21 | Morn Afah 1 | damage | 81.233 | 81.616 | 81.138 | 81.302 | 81.228 | 81.518 | hidden |
| 1:36 | Crystallize Time | damage | 96.144 | 96.540 | 96.067 | 96.239 | 96.152 | 96.443 | all |
| 1:36 | Crystallized Mech | cast end + 1s | 96.253 | 96.645 | 96.174 | 96.346 | 96.264 | 96.552 | all |
| 1:42 | Edge of Oblivion 3 | damage | 101.927 | 102.312 | 101.851 | 102.019 | 101.942 | 102.234 | hidden |
| 1:45 | Speed (Crystallize Time) | cast | 104.959 | 105.311 | 104.878 | 105.041 | 104.974 | 105.264 | hidden |
| 1:47 | Maelstrom 1 | cast | 107.229 | 107.638 | 107.151 | 107.308 | 107.245 | 107.536 | hidden |
| 1:49 | Dark Water III (Crystallize Time) | damage | 108.654 | 109.069 | 108.579 | 108.733 | 108.675 | 108.961 | hidden |
| 1:50 | Dark Blizzard III (Crystallize Time) | cast | 110.170 | 110.548 | 110.095 | 110.245 | 110.190 | 110.477 | hidden |
| 1:50 | Longing of the Lost | damage | 110.527 | 110.770 | 110.273 | 110.467 | 110.368 | 110.654 | hidden |
| 1:51 | Dark Aero III | damage | 110.793 | 111.172 | 110.720 | 110.867 | 110.811 | 111.102 | hidden |
| 1:51 | Dark Eruption (Crystallize Time) | damage | 110.793 | 111.172 | 110.720 | 110.867 | 110.811 | 111.102 | hidden |
| 1:53 | Maelstrom 2 | cast | 112.754 | 113.093 | 112.685 | 112.823 | 112.774 | 113.063 | hidden |
| 1:54 | Unholy Darkness | damage | 113.911 | 114.298 | 113.847 | 114.025 | 113.932 | 114.222 | hidden |
| 1:57 | Tidal Light 1 | cast | 116.580 | 116.981 | 116.525 | 116.696 | 116.604 | 116.894 | hidden |
| 1:58 | Maelstrom 3 | cast | 117.740 | 118.100 | 117.682 | 117.810 | 117.763 | 118.056 | hidden |
| 2:03 | Tidal Light 2 | cast | 122.950 | 123.382 | 122.900 | 123.067 | 122.979 | 123.269 | hidden |
| 2:08 | Quietus | damage | 127.803 | 128.171 | 127.718 | 127.879 | 127.836 | 128.086 | hidden |
| 2:14 | Spirit Taker 2 | damage | 133.499 | 134.071 | 133.647 | 133.631 | 133.676 | 134.014 | hidden |
| 2:20 | Hallowed Wings | damage | 139.900 | 140.154 | 139.672 | 140.049 | 139.960 | 140.034 | all |
| 2:25 | Hallowed Wings (Second hit) | damage | 144.392 | 144.720 | 144.226 | 144.553 | 144.460 | 144.575 | hidden |
| 2:34 | Akh Morn 2 | damage | 153.828 | 154.011 | 153.513 | 153.912 | 153.863 | 153.808 | all |
| 2:41 | Edge of Oblivion 4 | damage | 160.942 | 161.104 | 160.646 | 161.047 | 161.034 | 160.943 | hidden |
| 2:44 | Morn Afah 2 | damage | 163.922 | 164.183 | 163.678 | 164.073 | 163.979 | 163.975 | hidden |
| 2:46 | Memory's End / Absolute Zero (Enrage) | begincast | 165.612 | 165.879 | absent | absent | absent | absent | hidden |

## P5 reconciliation, reviewed

P5 keeps its canonical **14:23** start, derived from the longest observed
preceding phase durations. All timings below are relative to each report's
own FFLogs P5 start. The six phase durations in A–F are 271.876, 271.517,
256.489, 260.519, 260.633 and 264.998 seconds. These are kill times, not
measurements of the hard enrage deadline.

All nine Pandora sheet rows and 90 action entries are preserved. P5 has 21
encounter rows: nine sheet rows, two additional visible tank-only rows, and
ten hidden rows. The existing sheet names bind directly; only the obsolete
sheet-derived IDs change to log-derived occurrence IDs.

| P5 time | Visible mechanic | Visibility |
|---|---|---|
| 0:12 | Fulgent Blade 1 | All |
| 0:39 | Akh Morn 1 | All |
| 0:58 | Wings Dark and Light 1 | Tanks only |
| 1:19 | Polarizing Strikes 1 | All |
| 1:55 | Pandora's Box | All |
| 2:05 | Fulgent Blade 2 | All |
| 2:32 | Akh Morn 2 | All |
| 2:55 | Wings Dark and Light 2 | Tanks only |
| 3:11 | Polarizing Strikes 2 | All |
| 3:36 | Fulgent Blade 3 | All |
| 4:03 | Akh Morn 3 | All |

Fulgent Blade uses 40306. Each following exaline sequence is retained as one
hidden row, with setup IDs 40118 / 40307 and follow-up IDs 40309 / 40308.
Those rows use the first setup cast completion, not a player's avoidable hit.
Akh Morn uses castbar 40310 and damage 40311 / 40312. Its targets include
non-tanks in every sampled set, so it is not tank-only.

Paradise Regained 40319 precedes each Wings Dark and Light sequence.
Wings uses castbar variants 40313 / 40233 and tank-hit IDs 40314 / 40315 /
39879 / 39880. Each visible row anchors to the first actual tank damage in
its set; both-hit associations stay on that row, with a separate hidden
second-hit row. Immune events without packet IDs do not set damage timers.
Explosion 40320 hits non-tanks in all six samples. Each set of three
explosions has a separate hidden row anchored to the first hit; it is not
folded into the tank-only Wings row.

Polarizing Strikes uses castbar 40316, subsequent Polarizing Paths 40234,
Cruel Path of Light / Darkness 40317 / 40318, and follow-ups 40119 / 40120.
Each sheet row represents the full four-hit sequence and anchors to its first
player damage. All six action IDs are retained on that occurrence. The
following three hits and follow-up casts do not imply additional mit presses.

Pandora's Box 40326 deals party damage at 1:55. The source's Tank LB and
late-use notes remain unchanged. The hidden Paradise Lost enrage row uses
observed cast start, **4:11**, with IDs 40327 / 40328. All six clears begin
these casts; the supplied slow clears show 40327 completing around 4:22,
but no Paradise Lost damage. No lethal timestamp is inferred from a clear.
The repeated tank attack reported as `unknown_9cb3`, 40115, is not promoted
to a named mechanic.

### P5 evidence

Seconds are relative to each report's P5 anchor. Stored times round the
median first qualifying event per pull. Damage requires a packet ID and a
player target; `cast` is completion and `begincast` is cast start. A–F are
the same six reports listed above.

| Stored | Mechanic | Event | A | B | C | D | E | F | Blank-row visibility |
|---|---|---|---|---|---|---|---|---|---|
| 0:12 | Fulgent Blade 1 | damage | 12.094 | 12.110 | 12.077 | 12.089 | 12.070 | 12.101 | all |
| 0:22 | The Path of Darkness / The Path of Light 1 | cast | 22.404 | 22.331 | 22.318 | 22.299 | 22.311 | 22.371 | hidden |
| 0:39 | Akh Morn 1 | damage | 38.595 | 38.509 | 38.627 | 38.568 | 38.621 | 38.635 | all |
| 0:46 | Paradise Regained 1 | cast | 46.434 | 46.375 | 46.482 | 46.413 | 46.470 | 46.461 | hidden |
| 0:58 | Explosion 1 | damage | 57.517 | 57.424 | 57.530 | 57.469 | 57.523 | 57.493 | hidden |
| 0:58 | Wings Dark and Light 1 | damage | 57.697 | 57.738 | 57.799 | 57.559 | 57.611 | 58.251 | tank-only |
| 1:01 | Wings Dark and Light 1 (Second hit) | damage | 61.395 | 61.448 | 61.496 | 61.258 | 62.020 | 61.369 | hidden, tank-only |
| 1:19 | Polarizing Strikes 1 | damage | 79.194 | 79.236 | 79.281 | 79.062 | 79.200 | 79.138 | all |
| 1:55 | Pandora's Box | damage | 114.624 | 114.539 | 114.762 | 114.521 | 114.625 | 114.571 | all |
| 2:05 | Fulgent Blade 2 | damage | 125.313 | 125.254 | 125.449 | 125.209 | 125.316 | 125.326 | all |
| 2:16 | The Path of Darkness / The Path of Light 2 | cast | 135.541 | 135.482 | 135.694 | 135.448 | 135.562 | 135.576 | hidden |
| 2:32 | Akh Morn 2 | damage | 151.821 | 151.625 | 152.002 | 151.765 | 151.866 | 151.889 | all |
| 2:44 | Paradise Regained 2 | cast | 163.813 | 163.601 | 163.977 | 163.726 | 163.851 | 163.860 | hidden |
| 2:55 | Explosion 2 | damage | 174.890 | 174.647 | 175.023 | 174.768 | 174.901 | 174.941 | hidden |
| 2:55 | Wings Dark and Light 2 | damage | 174.980 | 175.228 | 175.292 | 174.901 | 174.991 | 174.986 | tank-only |
| 2:59 | Wings Dark and Light 2 (Second hit) | damage | 179.161 | 178.445 | 179.659 | 179.182 | 178.688 | 178.679 | hidden, tank-only |
| 3:11 | Polarizing Strikes 2 | damage | 191.172 | 190.956 | 191.512 | 191.046 | 191.170 | 191.142 | all |
| 3:36 | Fulgent Blade 3 | damage | 216.026 | 215.668 | 216.335 | 215.768 | 215.991 | 215.938 | all |
| 3:46 | The Path of Darkness / The Path of Light 3 | cast | 226.263 | 225.907 | 226.574 | 226.006 | 226.236 | 226.170 | hidden |
| 4:03 | Akh Morn 3 | damage | 242.557 | 242.046 | 242.883 | 242.285 | 242.546 | 242.460 | all |
| 4:11 | Paradise Lost (Enrage) | begincast | 250.610 | 250.091 | 250.955 | 250.333 | 250.606 | 250.521 | hidden |
