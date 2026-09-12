# FRU encounter reconciliation

P1 names, timings, and visibility are reviewed. P2 is implemented for review;
P3 has its start anchor only, and P3–P5 mechanics remain sheet-derived. Read this alongside
[REMODEL.md](REMODEL.md).

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

## P2 progress, awaiting review

P2 uses the same six reports, with every timestamp measured from that report's
FFLogs P2 transition. Its durations in A–F are 277.783, 278.009, 277.827,
277.606, 277.603 and 277.630 seconds. The longest observed P1 plus P2 is
166.506 + 278.009 = 444.515 seconds, giving P3 a stored start of **7:25**.
P2 retains its **2:47** canonical start.

The Shiva tab's eleven rows and all 86 action entries are preserved. P2 has
58 encounter rows; the remaining 47 are hidden with `minor: true`.
Only Quadruple Slap 1 and 2 are marked tank-only. Their actual damage packets
place the hits at 0:12 and 0:16. Immune events without packet IDs are excluded
from damage timing, including the early zero-damage Hallowed Ray event in A.

Mirror, Mirror keeps its own assignment at cast start, **1:26**, following the
reviewed Utopian Sky convention. Other visible rows use damage timing.
The sheet's Sinbound Holy anchors to the first of four hits. Its House of Light
anchors to **The House of Light 4**, after Light Rampant; the three earlier
occurrences remain hidden. Junction loses the sheet's “Transition” suffix and
uses the logged damage at **4:24**, before the P3 transition at about 4:38.
These P2 names and mappings still need user review.

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
| 0:12 | Quadruple Slap 1 | damage | 11.984 | absent | absent | 11.983 | 11.988 | absent | hidden, tank-only |
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
| 2:47 | The House of Light 4 | damage | 167.348 | 167.321 | 167.552 | 167.418 | 167.336 | 167.357 | all |
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
