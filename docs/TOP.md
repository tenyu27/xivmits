# TOP encounter reconciliation

All six phases now use FFLogs mechanic IDs, ability IDs and damage timings.
The party workbook and all six tank-pairing tabs remain overlays on that
encounter. This follows the FRU and DMU model in [REMODEL.md](REMODEL.md).

## Sources and clocks

Fetched on 2026-09-14 through `scripts/fflogs.py`, using `fights`,
`phaseTransitions`, `masterData.abilities` and paginated `events` filtered to
NPC damage, cast and begincast events. The original six clears, A through F,
came from the three slowest and three fastest entries in one 25-clear ranking
result. That first-page sample was insufficient to establish the longest
phase lengths.

The follow-up search located the final `fightRankings(metric:speed)` page
across all 60 partitions: 1 through 18 of encounter 1068 and 1 through 42 of
encounter 1077. There were 29 nonempty partitions. Pages are ordered by
increasing duration; exponential search followed by binary search found each
last page. The last pages yielded 643 entries before report/fight deduplication.
Candidates were examined by descending ranked duration. G through R are 12
readable slow clears from that search, added to the original six.

The longest ranked clear found is
[fBKVAnCH1FQXWtJP / 12](https://www.fflogs.com/reports/fBKVAnCH1FQXWtJP?fight=12),
**19:10.719**, in encounter 1068, partition 1, page 15. Its events are archived
and inaccessible to the current client-credentials API, and its fight metadata
has no phase transitions. It is not used to invent phase lengths.

The longest readable candidate is G,
[cfAQFpr6HmkyjWK8 / 24](https://www.fflogs.com/reports/cfAQFpr6HmkyjWK8?fight=24),
ranked **19:07.125**. Every candidate above it was archived or private.
No earlier ranking page can contain a longer candidate: the minimum duration
on every final page is at or below G's duration. Rankings are not an index of
every public pull, so this is the longest readable ranked clear found by this
search, not a claim about every report on FFLogs.

Ranking duration differs slightly from `endTime - startTime`, for example G's
fight interval is 19:07.927. All phase measurements below use the report's
timestamps, never the ranking duration. Archived reports contribute no timing
evidence. These 18 clears establish a sampled baseline, not absolute enrage
limits.

| Ref | Report / fight | P1 length | P2 length | P3 length | P4 length | P5 length | P6 length |
|---|---|---|---|---|---|---|---|
| A | [m814Rc26bwrPGTKB / 9](https://www.fflogs.com/reports/m814Rc26bwrPGTKB?fight=9) | 130.981 | 137.394 | 191.400 | 71.651 | 286.112 | 317.274 |
| B | [cmfJdaC4ZwjWABQb / 24](https://www.fflogs.com/reports/cmfJdaC4ZwjWABQb?fight=24) | 129.086 | 142.790 | 189.825 | 71.491 | 286.046 | 320.437 |
| C | [DNPLyBGH3Vcgnhdv / 15](https://www.fflogs.com/reports/DNPLyBGH3Vcgnhdv?fight=15) | 130.016 | 143.809 | 191.951 | 71.488 | 286.119 | 318.809 |
| D | [3NkpnCyjVbvf1Fa4 / 8](https://www.fflogs.com/reports/3NkpnCyjVbvf1Fa4?fight=8) | 118.849 | 125.748 | 181.683 | 71.603 | 286.116 | 317.297 |
| E | [wQ8PWhr4NaRtH6c2 / 15](https://www.fflogs.com/reports/wQ8PWhr4NaRtH6c2?fight=15) | 119.638 | 130.778 | 181.660 | 71.610 | 286.035 | 314.254 |
| F | [LKMGRJTzgY9HFynk / 2](https://www.fflogs.com/reports/LKMGRJTzgY9HFynk?fight=2) | 119.471 | 131.263 | 190.531 | 71.566 | 286.002 | 310.571 |
| G | [cfAQFpr6HmkyjWK8 / 24](https://www.fflogs.com/reports/cfAQFpr6HmkyjWK8?fight=24) | 130.489 | 143.869 | 193.251 | 71.609 | 285.935 | 322.774 |
| H | [mYywQGCaNKZvMT4d / 8](https://www.fflogs.com/reports/mYywQGCaNKZvMT4d?fight=8) | 129.309 | 143.934 | 192.363 | 71.601 | 285.993 | 322.098 |
| I | [pXfHVTZhD6zWwn7G / 12](https://www.fflogs.com/reports/pXfHVTZhD6zWwn7G?fight=12) | 130.290 | 144.796 | 191.733 | 71.483 | 286.068 | 320.939 |
| J | [MRpPtcAKVywvfhrN / 6](https://www.fflogs.com/reports/MRpPtcAKVywvfhrN?fight=6) | 131.055 | 142.898 | 192.966 | 71.587 | 285.989 | 320.439 |
| K | [rAydmxBjp79XtbGz / 10](https://www.fflogs.com/reports/rAydmxBjp79XtbGz?fight=10) | 130.128 | 143.571 | 191.533 | 71.625 | 286.100 | 321.907 |
| L | [7ZvTyLA9ckxp6Vja / 1](https://www.fflogs.com/reports/7ZvTyLA9ckxp6Vja?fight=1) | 128.643 | 143.642 | 191.637 | 71.452 | 285.989 | 323.409 |
| M | [TW4Hm6hXRrZavw3N / 9](https://www.fflogs.com/reports/TW4Hm6hXRrZavw3N?fight=9) | 130.366 | 141.209 | 192.176 | 71.699 | 286.244 | 322.797 |
| N | [yMTqNwFRLacJWvx7 / 8](https://www.fflogs.com/reports/yMTqNwFRLacJWvx7?fight=8) | 130.594 | 138.866 | 193.547 | 71.598 | 286.101 | 323.395 |
| O | [J3P84vzxT6YDhwGq / 1](https://www.fflogs.com/reports/J3P84vzxT6YDhwGq?fight=1) | 128.390 | 145.123 | 192.476 | 71.586 | 286.041 | 320.162 |
| P | [AcWLhJpbytZzYxQP / 2](https://www.fflogs.com/reports/AcWLhJpbytZzYxQP?fight=2) | 130.358 | 140.214 | 192.977 | 71.451 | 285.896 | 322.583 |
| Q | [jnNdVLk31xb2yGpW / 28](https://www.fflogs.com/reports/jnNdVLk31xb2yGpW?fight=28) | 127.985 | 143.663 | 191.532 | 71.496 | 286.188 | 322.615 |
| R | [M4LKvkqQJf3tFGRc / 3](https://www.fflogs.com/reports/M4LKvkqQJf3tFGRc?fight=3) | 128.684 | 144.768 | 191.194 | 71.407 | 286.151 | 321.183 |

Lengths and evidence samples are seconds. Mechanic times use the median of
the first qualifying event per pull within the listed phase-relative window,
rounded to the nearest second. Each pull contributes once, regardless of how
many players it damages. Damage requires a real `packetID`; synthetic immune
events without one are excluded. An absent sample does not prove a mechanic
was skipped, particularly for invulnerable tanks.

Canonical phase starts sum the longest observed preceding phase lengths,
then round once. P1 starts at zero. P1 through P3 depend on the phase push;
P4 and P5 vary by less than 0.4 seconds here. As in FRU, the resulting starts are a
conservative sampled baseline, not the timestamps of any single clear.

The expanded sample increases P2's maximum from 143.809 to 145.123 seconds
and P3's from 191.951 to 193.547 seconds. The phase-start changes are P3
`4:35 -> 4:36`, P4 `7:47 -> 7:50`, P5 `8:58 -> 9:01` and P6
`13:45 -> 13:48`. P1 and P2 remain `0:00` and `2:11` after rounding.
The longest individual phases come from different clears, so choosing only
the longest total kill would still underestimate some later phase starts.

FFLogs puts its P6 transition at the completion of Blind Faith, before the
long transformation. The damage follows at 0.18 seconds. Blind Faith's five
source assignments stay at the visible P5 cast cue (`4:35`), ahead of that
damage. The P6 damage event remains recorded at `0:00`, hidden and unassigned.
Cosmo Memory lands at `1:10` on this phase clock.

## Grouping and visibility

Damaging mechanics use damage timing. Avoidable mechanics without qualifying
damage use cast completion. Pantokrator keeps its workbook setup assignments
at cast start, following FRU's Utopian Sky / Mirror, Mirror rule. Party Synergy
is an unassigned hidden setup row. Program Loop, Limitless Synergy and the enrage cues likewise record cast
start. An interrupted enrage is never given an invented damage timestamp.

The encounter keeps named setup mechanics and avoidable attacks as hidden
`minor` rows. Auto attacks, P6 Flash Gale auto replacements, unknown animation
actions, individual ticks and every repeated avoidable cone are omitted.
Repeated avoidable sequences such as Wave Repeater, Flame Thrower, Hyper Pulse,
Rear Lasers and Cosmo Arrow are grouped, with their follow-up ability IDs
attached. This is a mechanic timeline, not a raw event list.

Repeated mitigation hits remain addressable: four P1 stacks, five Diffuse
Wave Cannon Kyrios hits, four P3 defect sets, three P4 protean/stack pairs,
four P5 world resolutions and both P6 protean hits in each set. The workbook's
grouped assignments bind once to the first hit; no presses or carry-overs are
inferred for subsequent hits.

P3's Patch Set rows bind to the Latent Defect resolution: the simultaneous
Critical Overflow / Synchronization Bug and Latent Performance / Cascading
Latent Defect damage. The later tether breaks are separate hidden Patch rows,
timed to the first break in each set, and can vary with player movement.
P5 Delta/Sigma/Omega Mech use sheet-level interval groups, referenced by the
first World mechanic in each sequence. Each group starts one second after its
raidwide and includes every recorded mechanic before the next Solar Ray:
Delta `0:26–1:31`, Sigma `1:49–3:00`, Omega `3:18–4:24` (end exclusive).
Omega includes both World resolutions. The resolved row retains all covered
mechanic IDs and their ability IDs; the encounter keeps its original events
and timestamps. Separate overlays or tank anchors inside a group fail validation
rather than silently disappearing.
P6 Cosmo Meteor binds to the first meteor damage; Flares binds to the final
simultaneous flare/stack damage. The earlier cast is not its damage timer.

P2 Cosmo Memory remains visible without assignments. Busters show blank rows
for tanks: P1 Diffuse Wave Cannon
Kyrios, P2 Solar Ray / Optimized Bladedance and each P5 Solar Ray first hit.
Their subsequent hits are hidden unless assigned. The P3 review hides Sniper
Cannon and monitors by default. Assigned tank plans still show their monitors
row. Monitors retain no role restriction: report C records damage to all eight
jobs. P5 monitors and Blaster
also hit non-tanks in C and have no tank-only restriction; they remain hidden
without assignments.

## Workbook bindings

Source: [TOP Mitty](https://docs.google.com/spreadsheets/d/1ROErvG1BhTuNvXqPGcR6ZyyhJ7uNTZdf2WzKyVj9hh4/edit),
fetched as XLSX with `scripts/workbook.py`. The regenerated overlay retains
37 party rows and all 252 party actions. By phase the new row/action counts
are 5/32, 1/24, 6/39, 7/21, 7/57 and 11/79. All 12 tank plans retain their actions, notes and alternatives.

The workbook's shorthand expansions are maintained by the importer.
The reviewed SCH label is Seraph Veil, mapped to Seraphic Veil, action 16548. `PARTY_MECHANICS` binds its names explicitly and an
unknown row fails the import. The importer never writes `encounter.json`.

| Phase | Workbook row | Encounter ID | Time |
|---|---|---|---|
| p1 | Pantokrator | `p1-pantokrator-1` | 1:04 |
| p1 | Stack 1 | `p1-condensed-wave-cannon-kyrios-1` | 1:22 |
| p1 | Stack 2 | `p1-condensed-wave-cannon-kyrios-2` | 1:28 |
| p1 | Stack 3 | `p1-condensed-wave-cannon-kyrios-3` | 1:34 |
| p1 | Stack 4 | `p1-condensed-wave-cannon-kyrios-4` | 1:40 |
| p2 | 611: Optimized Meteor / Cosmo Memory | `p2-optimized-meteor-1` | 1:49 |
| p3 | Hello World | `p3-hello-world-1` | 0:42 |
| p3 | Critical Error | `p3-critical-error-1` | 2:31 |
| p3 | 1st Patch Set | `p3-latent-defect-1` | 1:06 |
| p3 | 2nd Patch Set | `p3-latent-defect-2` | 1:27 |
| p3 | 3rd Patch Set | `p3-latent-defect-3` | 1:48 |
| p3 | 4th Patch Set | `p3-latent-defect-4` | 2:09 |
| p4 | Protean 1 | `p4-wave-cannon-1` | 0:15 |
| p4 | Protean 2 | `p4-wave-cannon-3` | 0:26 |
| p4 | Protean 3 | `p4-wave-cannon-5` | 0:36 |
| p4 | Stack 1 | `p4-wave-cannon-2` | 0:20 |
| p4 | Stack 2 | `p4-wave-cannon-4` | 0:30 |
| p4 | Stack 3 | `p4-wave-cannon-6` | 0:41 |
| p4 | Blue Screen | `p4-blue-screen-1` | 0:56 |
| p5 | Delta Cast | `p5-run-mi-delta-version-1` | 0:25 |
| p5 | Delta Mech | `p5-hello-distant-world-1` (group) | 0:26 |
| p5 | Sigma Cast | `p5-run-mi-sigma-version-1` | 1:48 |
| p5 | Sigma Mech | `p5-hello-distant-world-2` (group) | 1:49 |
| p5 | Omega Cast | `p5-run-mi-omega-version-1` | 3:17 |
| p5 | Omega Mech | `p5-hello-distant-world-3` (group) | 3:18 |
| p5 | Blind Faith | `p5-blind-faith-1` | 4:35 |
| p6 | Cosmo Memory | `p6-cosmo-memory-1` | 1:10 |
| p6 | Cosmo Dive 1 | `p6-cosmo-dive-1` | 1:40 |
| p6 | Cosmo Dive 2 | `p6-cosmo-dive-2` | 3:34 |
| p6 | Protean 1 | `p6-wave-cannon-1` | 2:17 |
| p6 | Protean 2 | `p6-wave-cannon-4` | 2:51 |
| p6 | Wave Cannon 1 | `p6-wave-cannon-3` | 2:26 |
| p6 | Wave Cannon 2 | `p6-wave-cannon-6` | 2:59 |
| p6 | Cosmo Meteor | `p6-cosmo-meteor-1` | 3:58 |
| p6 | Flares | `p6-cosmo-meteor-3` | 4:16 |
| p6 | Magic Number 1 | `p6-magic-number-1` | 4:30 |
| p6 | Magic Number 2 | `p6-magic-number-2` | 4:46 |

The P2 review identified the workbook's numeric `611.0` label as Optimized
Meteor plus Cosmo Memory. Its 24 actions bind once to Meteor's damage at
1:49, with a mechanic note naming both attacks. Cosmo Memory remains a visible
row at 1:59. Party Synergy has no assignments and is hidden. This replaces
the incorrect interpretation of `611.0` as Party Synergy.

## Tank anchors

Personal rows now inherit the actual mechanic's name and time, so their
headings fold into the shared party timeline in every layout. Prepull remains
an unanchored instruction. P4's tank notes remain at the phase top. P3's
phase note remains after Hello, World. Pairing choices, buddy mitigation,
alternative plans and job-scoped source footers are preserved.

| Phase | Tank workbook row | Encounter ID | Time |
|---|---|---|---|
| p1 | Prepull | phase top | — |
| p1 | Diffuse Wave Cannon | `p1-diffuse-wave-cannon-kyrios-1` | 1:49 |
| p2 | Solar Ray | `p2-solar-ray-1` | 0:13 |
| p2 | Tank Tethers | `p2-optimized-bladedance-1` | 1:35 |
| p3 | Patch 1 | `p3-latent-defect-1` | 1:06 |
| p3 | Patch 2 | `p3-latent-defect-2` | 1:27 |
| p3 | Patch 3 | `p3-latent-defect-3` | 1:48 |
| p3 | Patch 4 | `p3-latent-defect-4` | 2:09 |
| p3 | Critical Error | `p3-critical-error-1` | 2:31 |
| p3 | Monitors | `p3-oversampled-wave-cannon-1` | 2:52 |
| p5 | Delta Solar Ray | `p5-solar-ray-1` | 0:09 |
| p5 | Sigma Solar Ray | `p5-solar-ray-3` | 1:31 |
| p5 | Omega Solar Ray | `p5-solar-ray-5` | 3:00 |
| p5 | Final Buster | `p5-solar-ray-7` | 4:24 |
| p6 | Cosmo Dive 1 | `p6-cosmo-dive-1` | 1:40 |
| p6 | Wave Cannon 1 | `p6-wave-cannon-3` | 2:26 |
| p6 | Wave Cannon 2 | `p6-wave-cannon-6` | 2:59 |
| p6 | Cosmo Dive 2 | `p6-cosmo-dive-2` | 3:34 |

## Evidence

Each table uses phase-relative seconds. A through F are individual original
samples; the final two columns give the count and range of qualifying samples
from the 12 slow clears G through R. Stored times use the median across all
18 pulls with a qualifying event, not a median of the two groups. Windows are
inclusive at the start and exclusive at the end. `cast` means completion;
`begincast` means cast start. Ability IDs are the game's `abilityGameID`;
the full associations are in `encounter.json`. The ID slug uses the primary
cast's logged name, or the damage name when there is no separate cast.
Only variants observed in the sampled phases are included. The slow clears
add no new hostile mechanic ability IDs and reveal no additional late mechanic
between the existing enrage cues and the kill or phase transition.

### P1, start 0:00

28 encounter rows.

| ID | Stored | Event | Window | A | B | C | D | E | F | Slow n | Slow range | Blank row |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `p1-program-loop-1` | 0:11 | begincast | 0 to 20 | 10.955 | 10.920 | 11.277 | 11.259 | 11.019 | 11.132 | 12 | 10.358 to 11.219 | hidden |
| `p1-storage-violation-1` | 0:30 | damage | 28 to 33 | 29.705 | 29.682 | 30.040 | 30.047 | 29.766 | 29.892 | 12 | 29.129 to 29.990 | hidden |
| `p1-blaster-1` | 0:30 | damage | 28 to 33 | 29.837 | 29.815 | 30.129 | 30.137 | 29.899 | 30.025 | 12 | 29.174 to 30.078 | hidden |
| `p1-storage-violation-2` | 0:39 | damage | 37 to 42 | 38.753 | 38.702 | 39.045 | 39.075 | 38.805 | 38.883 | 12 | 38.174 to 39.035 | hidden |
| `p1-blaster-2` | 0:39 | damage | 37 to 42 | 38.753 | 38.791 | 39.088 | 39.120 | 38.851 | 38.973 | 12 | 38.129 to 39.035 | hidden |
| `p1-storage-violation-3` | 0:48 | damage | 46 to 51 | 47.753 | 47.709 | 48.058 | 48.089 | 47.804 | 47.930 | 12 | 47.191 to 48.034 | hidden |
| `p1-blaster-3` | 0:48 | damage | 46 to 51 | 47.708 | 47.709 | 48.058 | 48.089 | 47.804 | 47.930 | 12 | 47.101 to 48.034 | hidden |
| `p1-blaster-4` | 0:57 | damage | 55 to 60 | 56.710 | 56.679 | 57.013 | 57.075 | 56.721 | 56.884 | 12 | 56.079 to 56.943 | hidden |
| `p1-storage-violation-4` | 0:57 | damage | 55 to 60 | 56.710 | 56.724 | 57.058 | 57.075 | 56.810 | 56.928 | 12 | 56.169 to 57.032 | hidden |
| `p1-pantokrator-1` | 1:04 | begincast | 60 to 70 | 64.234 | 64.265 | 64.597 | 64.630 | 64.262 | 64.409 | 12 | 63.646 to 64.524 | all |
| `p1-flame-thrower-1` | 1:15 | cast | 70 to 80 | 75.322 | 75.387 | 75.689 | 75.719 | 75.393 | 75.505 | 12 | 74.738 to 75.616 | hidden |
| `p1-condensed-wave-cannon-kyrios-1` | 1:22 | damage | 80 to 85 | 81.646 | 81.682 | 82.020 | 82.024 | 81.675 | 81.832 | 12 | 81.065 to 81.935 | all |
| `p1-ballistic-impact-1` | 1:22 | cast | 80 to 85 | 81.868 | 81.903 | 82.243 | 82.245 | 81.898 | 82.056 | 12 | 81.288 to 82.157 | hidden |
| `p1-guided-missile-kyrios-1` | 1:22 | damage | 80 to 85 | 82.002 | 81.992 | 82.332 | 82.335 | 81.987 | 82.145 | 12 | 81.377 to 82.291 | hidden |
| `p1-condensed-wave-cannon-kyrios-2` | 1:28 | damage | 86 to 91 | 87.661 | 87.697 | 87.986 | 88.014 | 87.682 | 87.801 | 12 | 87.083 to 87.947 | all |
| `p1-guided-missile-kyrios-2` | 1:28 | damage | 86 to 91 | 87.971 | 88.008 | 88.298 | 88.326 | 87.994 | 88.115 | 12 | 87.394 to 88.258 | hidden |
| `p1-condensed-wave-cannon-kyrios-3` | 1:34 | damage | 92 to 97 | 93.630 | 93.670 | 93.998 | 94.003 | 93.680 | 93.812 | 12 | 93.056 to 93.954 | all |
| `p1-guided-missile-kyrios-3` | 1:34 | damage | 92 to 97 | 93.944 | 93.983 | 94.309 | 94.315 | 93.991 | 94.169 | 12 | 93.410 to 94.265 | hidden |
| `p1-condensed-wave-cannon-kyrios-4` | 1:40 | damage | 98 to 103 | 99.649 | 99.694 | 100.009 | 100.030 | 99.678 | 99.824 | 12 | 99.074 to 99.921 | all |
| `p1-guided-missile-kyrios-4` | 1:40 | damage | 98 to 103 | 99.960 | 100.005 | 100.320 | 100.341 | 100.034 | 100.137 | 12 | 99.429 to 100.275 | hidden |
| `p1-wave-cannon-kyrios-1` | 1:49 | damage | 107 to 111 | 108.516 | 108.532 | 108.873 | 108.924 | 108.551 | 108.687 | 12 | 107.933 to 108.786 | hidden |
| `p1-diffuse-wave-cannon-kyrios-1` | 1:49 | damage | 107 to 109.5 | 108.516 | 108.532 | 108.873 | 108.924 | 108.551 | 108.687 | 12 | 107.933 to 108.786 | tank-only |
| `p1-diffuse-wave-cannon-kyrios-2` | 1:51 | damage | 109.5 to 111.5 | 110.566 | 110.582 | 110.921 | 110.982 | 110.635 | 110.739 | 12 | 110.020 to 110.836 | hidden |
| `p1-diffuse-wave-cannon-kyrios-3` | 1:53 | damage | 111.5 to 113.5 | 112.658 | 112.681 | 113.015 | 113.085 | 112.764 | 112.831 | 12 | 112.117 to 112.936 | hidden |
| `p1-diffuse-wave-cannon-kyrios-4` | 1:55 | damage | 113.5 to 115.5 | 114.709 | 114.736 | 115.062 | 115.141 | 114.846 | 114.882 | 12 | 114.164 to 114.985 | hidden |
| `p1-diffuse-wave-cannon-kyrios-5` | 1:57 | damage | 115.5 to 117.5 | 116.804 | 116.840 | 117.156 | absent | absent | absent | 12 | 116.253 to 117.117 | hidden |
| `p1-wave-cannon-kyrios-2` | 1:58 | damage | 116 to 120 | 117.564 | 117.556 | 117.914 | absent | absent | absent | 12 | 116.965 to 117.832 | hidden |
| `p1-atomic-ray-1` | 2:03 | begincast | 120 to 140 | 122.961 | 122.915 | 123.254 | absent | absent | absent | 12 | 122.361 to 123.238 | hidden |

### P2, start 2:11

21 encounter rows.

| ID | Stored | Event | Window | A | B | C | D | E | F | Slow n | Slow range | Blank row |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `p2-firewall-1` | 0:04 | cast | 0 to 8 | 4.192 | 4.194 | 4.184 | 4.200 | 4.176 | 4.188 | 12 | 4.186 to 4.203 | hidden |
| `p2-solar-ray-1` | 0:13 | damage | 10 to 16 | 13.147 | absent | 13.134 | 13.140 | 13.149 | 13.144 | 12 | 13.141 to 13.165 | tank-only |
| `p2-party-synergy-1` | 0:26 | begincast | 20 to 30 | 25.799 | 25.683 | 25.697 | 25.698 | 25.684 | 25.709 | 12 | 25.702 to 25.812 | hidden |
| `p2-superliminal-steel-1` | 0:39 | cast | 35 to 42 | 39.176 | 39.136 | 39.105 | 39.146 | 39.066 | 39.122 | 12 | 39.110 to 39.210 | hidden |
| `p2-beyond-strength-1` | 0:39 | cast | 35 to 42 | 39.176 | 39.136 | 39.105 | 39.146 | 39.066 | 39.122 | 12 | 39.110 to 39.210 | hidden |
| `p2-optical-laser-1` | 0:46 | cast | 43 to 48 | 45.994 | 45.888 | 45.885 | 45.895 | 45.820 | 45.891 | 12 | 45.874 to 46.008 | hidden |
| `p2-optimized-fire-iii-1` | 0:46 | damage | 44 to 48 | 46.261 | 46.156 | 46.152 | 46.209 | 46.133 | 46.158 | 12 | 46.144 to 46.323 | hidden |
| `p2-discharger-1` | 0:53 | cast | 50 to 55 | 52.810 | 52.728 | 52.704 | 52.780 | 52.749 | 52.702 | 12 | 52.687 to 52.899 | hidden |
| `p2-efficient-bladework-1` | 0:57 | cast | 54 to 60 | 57.133 | 57.111 | 57.115 | 57.160 | 57.103 | 57.077 | 12 | 57.093 to 57.238 | hidden |
| `p2-spotlight-1` | 0:58 | damage | 55 to 61 | 57.713 | 57.648 | 57.650 | 57.696 | 57.636 | 57.656 | 12 | 57.628 to 57.814 | hidden |
| `p2-synthetic-shield-1` | 1:11 | cast | 68 to 73 | 70.491 | 70.497 | 70.515 | 70.524 | 70.558 | 70.454 | 12 | 70.342 to 70.610 | hidden |
| `p2-limitless-synergy-1` | 1:16 | begincast | 73 to 83 | 75.788 | 75.773 | 75.813 | 75.795 | 75.837 | 75.759 | 12 | 75.641 to 75.884 | hidden |
| `p2-optimized-passage-of-arms-1` | 1:26 | cast | 83 to 90 | 85.810 | 85.777 | 85.831 | 85.807 | 85.838 | 85.655 | 12 | 85.669 to 85.893 | hidden |
| `p2-laser-shower-1` | 1:26 | begincast | 83 to 90 | 85.810 | 85.777 | 85.831 | 85.807 | 85.838 | 85.655 | 12 | 85.669 to 85.893 | hidden |
| `p2-synthetic-shield-2` | 1:27 | cast | 84 to 90 | 87.103 | 87.074 | 87.077 | 87.058 | 87.083 | 87.082 | 12 | 86.954 to 87.191 | hidden |
| `p2-optimized-sagittarius-arrow-1` | 1:34 | cast | 92 to 99 | 94.181 | 94.130 | 94.164 | 94.161 | 94.192 | 94.123 | 12 | 94.047 to 94.287 | hidden |
| `p2-optimized-bladedance-1` | 1:35 | damage | 92 to 99 | 94.848 | 94.800 | 94.922 | 94.832 | 94.815 | 94.835 | 12 | 94.689 to 94.955 | tank-only |
| `p2-beyond-defense-1` | 1:46 | damage | 103 to 110 | 106.119 | 106.094 | 106.108 | 106.095 | 106.103 | 106.110 | 12 | 105.967 to 106.214 | hidden |
| `p2-optimized-meteor-1` | 1:49 | damage | 106 to 112 | 108.792 | 108.772 | 108.868 | 108.779 | 108.857 | 108.786 | 12 | 108.652 to 108.951 | all |
| `p2-pile-pitch-1` | 1:49 | damage | 107 to 113 | 109.327 | 109.265 | 109.269 | 109.314 | 109.257 | 109.320 | 12 | 109.183 to 109.420 | hidden |
| `p2-cosmo-memory-1` | 1:59 | damage | 116 to 124 | 118.866 | 118.877 | 118.936 | 118.865 | 118.896 | 118.867 | 12 | 118.740 to 118.982 | all |

### P3, start 4:36

20 encounter rows.

| ID | Stored | Event | Window | A | B | C | D | E | F | Slow n | Slow range | Blank row |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `p3-wave-repeater-1` | 0:14 | cast | 13 to 17 | 14.299 | 14.318 | 14.322 | 14.325 | 14.316 | 14.310 | 12 | 14.284 to 14.340 | hidden |
| `p3-wave-repeater-2` | 0:22 | cast | 21 to 25 | 22.453 | 22.452 | 22.482 | 22.475 | 22.491 | 22.470 | 12 | 22.432 to 22.482 | hidden |
| `p3-colossal-blow-1` | 0:26 | cast | 25 to 30 | 26.333 | 26.386 | 26.361 | 26.349 | 26.404 | 26.349 | 12 | 26.317 to 26.388 | hidden |
| `p3-sniper-cannon-1` | 0:29 | damage | 27 to 32 | 28.963 | 28.980 | 28.990 | 28.977 | 28.985 | 28.982 | 12 | 28.945 to 29.007 | hidden |
| `p3-hello-world-1` | 0:42 | damage | 40 to 46 | 42.327 | 42.376 | 42.373 | 42.340 | 42.347 | 42.357 | 12 | 42.301 to 42.399 | all |
| `p3-latent-defect-1` | 1:06 | damage | 64 to 70 | 66.303 | 66.338 | 66.331 | 66.316 | 66.326 | 66.301 | 12 | 66.258 to 66.364 | all |
| `p3-patch-1` | 1:08 | damage | 62 to 78 | 68.488 | 68.348 | 68.116 | 67.922 | 67.619 | 67.904 | 12 | 67.373 to 68.472 | hidden |
| `p3-critical-performance-bug-1` | 1:12 | cast | 70 to 80 | 71.649 | 71.700 | 71.729 | 71.663 | 71.674 | 71.693 | 12 | 71.637 to 71.750 | hidden |
| `p3-latent-defect-2` | 1:27 | damage | 85 to 91 | 87.327 | 87.383 | 87.375 | 87.395 | 87.354 | 87.386 | 12 | 87.313 to 87.430 | all |
| `p3-patch-2` | 1:29 | damage | 83 to 99 | 89.200 | 88.946 | 88.939 | 89.667 | 88.692 | 89.347 | 12 | 88.422 to 89.630 | hidden |
| `p3-critical-performance-bug-2` | 1:34 | cast | 91 to 101 | 93.791 | 94.438 | 94.486 | 94.077 | 94.004 | 93.582 | 12 | 93.757 to 94.846 | hidden |
| `p3-latent-defect-3` | 1:48 | damage | 106 to 112 | 108.405 | 108.461 | 108.440 | 108.380 | 108.410 | 108.422 | 12 | 108.366 to 108.508 | all |
| `p3-patch-3` | 1:50 | damage | 104 to 120 | 109.565 | 110.204 | 110.449 | 110.695 | 110.324 | 110.028 | 12 | 109.865 to 111.302 | hidden |
| `p3-critical-performance-bug-3` | 1:55 | cast | 112 to 122 | 114.687 | 115.161 | 115.005 | 115.870 | 115.099 | 114.841 | 12 | 114.797 to 115.612 | hidden |
| `p3-patch-4` | 2:08 | damage | 125 to 141 | 128.401 | 128.465 | 128.460 | 128.391 | 128.474 | 128.441 | 12 | 128.374 to 128.478 | hidden |
| `p3-latent-defect-4` | 2:09 | damage | 127 to 133 | 129.468 | 129.536 | 129.490 | 129.460 | 129.453 | 129.465 | 12 | 129.432 to 129.568 | all |
| `p3-critical-performance-bug-4` | 2:16 | cast | 133 to 143 | 135.829 | 136.360 | 136.642 | 136.772 | 136.143 | 136.243 | 12 | 136.006 to 136.844 | hidden |
| `p3-critical-error-1` | 2:31 | damage | 148 to 154 | 150.744 | 150.803 | 150.819 | 150.713 | 150.759 | 150.776 | 12 | 150.735 to 150.934 | all |
| `p3-oversampled-wave-cannon-1` | 2:52 | damage | 169 to 176 | 172.079 | 172.069 | 172.093 | 172.101 | 172.114 | 172.160 | 12 | 171.996 to 172.335 | hidden |
| `p3-ion-efflux-1` | 2:58 | begincast | 175 to 195 | 177.554 | 177.619 | 177.587 | absent | absent | 177.555 | 12 | 177.518 to 177.648 | hidden |

### P4, start 7:50

9 encounter rows.

| ID | Stored | Event | Window | A | B | C | D | E | F | Slow n | Slow range | Blank row |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `p4-wave-cannon-1` | 0:15 | damage | 14 to 18 | 15.447 | 15.413 | 15.414 | 15.424 | 15.431 | 15.415 | 12 | 15.380 to 15.513 | all |
| `p4-wave-cannon-2` | 0:20 | damage | 19 to 23 | 20.213 | 20.192 | 20.194 | 20.193 | 20.196 | 20.198 | 12 | 20.120 to 20.270 | all |
| `p4-wave-repeater-1` | 0:22 | cast | 21 to 25 | 22.352 | 22.337 | 22.339 | 22.331 | 22.339 | 22.333 | 12 | 22.264 to 22.406 | hidden |
| `p4-wave-cannon-3` | 0:26 | damage | 24 to 28 | 25.648 | 25.555 | 25.555 | 25.628 | 25.639 | 25.594 | 12 | 25.524 to 25.702 | all |
| `p4-wave-cannon-4` | 0:30 | damage | 29 to 33 | 30.366 | 30.289 | 30.284 | 30.353 | 30.364 | 30.326 | 12 | 30.225 to 30.422 | all |
| `p4-wave-cannon-5` | 0:36 | damage | 34 to 38 | 35.890 | 35.779 | 35.787 | 35.873 | 35.900 | 35.820 | 12 | 35.706 to 35.942 | all |
| `p4-wave-repeater-2` | 0:40 | cast | 38 to 42 | 39.854 | 39.748 | 39.716 | 39.834 | 39.863 | 39.754 | 12 | 39.650 to 39.905 | hidden |
| `p4-wave-cannon-6` | 0:41 | damage | 39 to 43 | 40.613 | 40.460 | 40.522 | 40.594 | 40.622 | 40.555 | 12 | 40.441 to 40.663 | all |
| `p4-blue-screen-1` | 0:56 | damage | 54 to 60 | 56.335 | 56.199 | 56.178 | 56.322 | 56.359 | 56.279 | 12 | 56.107 to 56.430 | all |

### P5, start 9:01

44 encounter rows.

| ID | Stored | Event | Window | A | B | C | D | E | F | Slow n | Slow range | Blank row |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `p5-solar-ray-1` | 0:09 | damage | 6 to 11 | absent | 8.890 | 8.894 | absent | 8.921 | absent | 6 | 8.898 to 8.920 | tank-only |
| `p5-solar-ray-2` | 0:12 | damage | 10 to 14 | absent | 12.105 | 12.070 | absent | 12.091 | absent | 6 | 12.077 to 12.196 | hidden |
| `p5-run-mi-delta-version-1` | 0:25 | damage | 23 to 28 | 25.655 | 25.470 | 25.442 | 25.666 | 25.691 | 25.601 | 12 | 25.421 to 25.687 | all |
| `p5-peripheral-synthesis-1` | 0:35 | cast | 33 to 38 | 35.177 | 34.999 | 34.966 | 35.212 | 35.227 | 35.124 | 12 | 34.934 to 35.235 | hidden |
| `p5-archive-peripheral-1` | 0:38 | cast | 36 to 41 | 38.161 | 37.991 | 37.962 | 38.198 | 38.204 | 38.121 | 12 | 37.929 to 38.218 | hidden |
| `p5-patch-1` | 0:47 | damage | 44 to 48 | 46.753 | 46.572 | 46.543 | 46.750 | 46.784 | 46.704 | 12 | 46.508 to 46.783 | hidden |
| `p5-optical-laser-1` | 0:48 | cast | 46 to 50 | 48.042 | 47.868 | 47.837 | 48.042 | 48.071 | 48.000 | 12 | 47.814 to 48.072 | hidden |
| `p5-patch-2` | 0:50 | damage | 48 to 52 | 50.448 | 50.280 | 50.560 | 49.959 | 49.936 | 50.012 | 12 | 49.599 to 50.579 | hidden |
| `p5-explosion-1` | 0:51 | cast | 49 to 53 | 51.028 | 50.860 | 50.825 | 51.074 | 51.091 | 50.994 | 12 | 50.771 to 51.108 | hidden |
| `p5-beyond-defense-1` | 0:54 | damage | 52 to 57 | 54.452 | 54.204 | 54.252 | 54.326 | 54.247 | 54.257 | 12 | 53.982 to 54.248 | hidden |
| `p5-hyper-pulse-1` | 0:56 | cast | 54 to 59 | 55.882 | 55.771 | 55.771 | 55.974 | 56.022 | 55.868 | 12 | 55.643 to 56.016 | hidden |
| `p5-oversampled-wave-cannon-1` | 0:59 | damage | 57 to 62 | 59.044 | 58.810 | 58.809 | 59.051 | 59.050 | 58.949 | 12 | 58.746 to 59.096 | hidden |
| `p5-pile-pitch-1` | 0:59 | damage | 58 to 62 | 59.849 | 59.436 | 59.657 | 59.496 | 59.628 | 59.665 | 12 | 59.196 to 59.630 | hidden |
| `p5-patch-3` | 1:08 | damage | 65 to 69 | 68.442 | 67.572 | 67.041 | 68.232 | 68.158 | 67.800 | 12 | 66.901 to 68.332 | hidden |
| `p5-swivel-cannon-1` | 1:11 | cast | 69 to 74 | 71.293 | 71.104 | 71.108 | 71.349 | 71.354 | 71.246 | 12 | 71.025 to 71.359 | hidden |
| `p5-hello-distant-world-1` | 1:12 | damage | 70 to 74 | 72.630 | 72.444 | 72.406 | 72.643 | 72.644 | 72.585 | 12 | 72.385 to 72.652 | all |
| `p5-patch-4` | 1:21 | damage | 79 to 83 | 81.555 | 80.666 | 80.947 | 80.846 | 80.595 | 80.879 | 12 | 79.961 to 81.538 | hidden |
| `p5-solar-ray-3` | 1:31 | damage | 89 to 94 | 91.316 | 91.082 | 91.362 | 91.046 | 91.152 | 91.143 | 11 | 90.664 to 91.171 | tank-only |
| `p5-solar-ray-4` | 1:34 | damage | 93 to 97 | 94.481 | 94.300 | 94.534 | 94.251 | 94.304 | 94.401 | 11 | 93.828 to 94.391 | hidden |
| `p5-run-mi-sigma-version-1` | 1:48 | damage | 106 to 111 | 108.070 | 107.738 | 108.117 | 107.718 | 107.877 | 107.760 | 12 | 107.196 to 107.847 | all |
| `p5-program-loop-1` | 2:06 | cast | 124 to 129 | 126.101 | 125.836 | 126.145 | 125.755 | 125.905 | 125.790 | 12 | 125.253 to 125.903 | hidden |
| `p5-hyper-pulse-2` | 2:10 | damage | 128 to 132 | 129.941 | 129.638 | 129.990 | 129.585 | 129.742 | 129.625 | 12 | 129.090 to 129.746 | hidden |
| `p5-wave-cannon-1` | 2:10 | damage | 128 to 134 | 130.252 | 129.952 | 130.348 | 129.897 | 130.055 | 129.985 | 12 | 129.403 to 130.060 | hidden |
| `p5-discharger-1` | 2:18 | cast | 136 to 141 | 138.177 | 137.913 | 138.269 | 137.827 | 137.984 | 137.896 | 12 | 137.293 to 138.013 | hidden |
| `p5-storage-violation-1` | 2:22 | damage | 141 to 146 | 142.765 | 142.515 | 142.830 | 142.417 | 142.569 | 142.452 | 12 | 141.927 to 142.574 | hidden |
| `p5-rear-lasers-1` | 2:36 | cast | 155 to 160 | 156.477 | 156.233 | 156.605 | 156.138 | 156.263 | 156.223 | 12 | 155.608 to 156.344 | hidden |
| `p5-optimized-blizzard-iii-1` | 2:39 | cast | 157 to 162 | absent | absent | 159.688 | absent | absent | absent | 4 | 158.893 to 159.136 | hidden |
| `p5-hyper-pulse-3` | 2:47 | damage | 165 to 169 | 166.992 | 166.744 | 167.065 | 166.609 | 166.793 | 166.694 | 12 | 166.092 to 166.849 | hidden |
| `p5-hello-distant-world-2` | 2:47 | damage | 165 to 169 | 167.036 | 166.699 | 167.111 | 166.696 | 166.881 | 166.739 | 12 | 166.182 to 166.805 | all |
| `p5-solar-ray-5` | 3:00 | damage | 179 to 184 | 180.803 | 180.599 | 180.969 | 180.458 | 180.624 | 180.591 | 12 | 179.997 to 180.708 | tank-only |
| `p5-solar-ray-6` | 3:04 | damage | 183 to 187 | 184.013 | 183.816 | 184.145 | 183.621 | 183.783 | 183.764 | 12 | 183.159 to 183.886 | hidden |
| `p5-run-mi-omega-version-1` | 3:17 | damage | 196 to 201 | 197.472 | 197.277 | 197.606 | 197.260 | 197.226 | 197.214 | 12 | 196.621 to 197.351 | all |
| `p5-diffuse-wave-cannon-1` | 3:34 | cast | 212 to 218 | 213.945 | 213.762 | 214.121 | 213.749 | 213.711 | 213.730 | 12 | 213.108 to 213.884 | hidden |
| `p5-superliminal-steel-1` | 3:35 | cast | 214 to 216 | 214.971 | 214.792 | 215.147 | 214.772 | 214.733 | 214.710 | 12 | 214.135 to 214.870 | hidden |
| `p5-beyond-strength-1` | 3:35 | cast | 214 to 216 | 214.971 | 214.792 | 215.147 | 214.772 | 214.733 | 214.710 | 12 | 214.135 to 214.870 | hidden |
| `p5-superliminal-steel-2` | 3:39 | cast | 218 to 220 | 218.987 | 218.811 | 219.160 | 218.782 | 218.745 | 218.769 | 12 | 218.143 to 218.897 | hidden |
| `p5-beyond-strength-2` | 3:39 | cast | 218 to 220 | 218.987 | 218.811 | 219.160 | 218.782 | 218.745 | 218.769 | 12 | 218.143 to 218.897 | hidden |
| `p5-hello-distant-world-3` | 3:52 | damage | 231 to 235 | 232.415 | 232.256 | 232.575 | 232.241 | 232.171 | 232.166 | 12 | 231.562 to 232.317 | all |
| `p5-oversampled-wave-cannon-2` | 3:53 | damage | 231 to 236 | 232.907 | 232.703 | 233.066 | 232.687 | 232.616 | 232.657 | 12 | 232.050 to 232.808 | hidden |
| `p5-blaster-1` | 4:08 | damage | 247 to 252 | 248.697 | 248.574 | 248.908 | 248.592 | 248.449 | 248.509 | 12 | 247.959 to 248.598 | hidden |
| `p5-hello-distant-world-4` | 4:10 | damage | 249 to 253 | 250.434 | 250.227 | 250.561 | 250.239 | 250.226 | 250.165 | 12 | 249.602 to 250.342 | all |
| `p5-solar-ray-7` | 4:24 | damage | 262 to 267 | 264.082 | 263.895 | 264.201 | 263.832 | 263.812 | 263.796 | 12 | 263.182 to 263.933 | tank-only |
| `p5-solar-ray-8` | 4:27 | damage | 266 to 270 | 267.289 | 267.115 | 267.375 | 266.996 | 266.977 | 267.013 | 12 | 266.338 to 267.110 | hidden |
| `p5-blind-faith-1` | 4:35 | begincast | 273 to 280 | 274.866 | 274.797 | 274.890 | 274.887 | 274.808 | 274.784 | 12 | 274.670 to 275.006 | all |

### P6, start 13:48

20 encounter rows.

| ID | Stored | Event | Window | A | B | C | D | E | F | Slow n | Slow range | Blank row |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `p6-blind-faith-1` | 0:00 | damage | 0 to 2 | 0.178 | 0.178 | 0.178 | 0.179 | 0.179 | 0.178 | 12 | 0.177 to 0.179 | hidden |
| `p6-cosmo-memory-1` | 1:10 | damage | 67 to 73 | 69.762 | 69.782 | 69.780 | 69.781 | 69.807 | 69.747 | 12 | 69.694 to 69.854 | all |
| `p6-cosmo-arrow-1` | 1:22 | cast | 80 to 85 | 82.158 | 82.207 | 82.165 | 82.145 | 82.195 | 82.164 | 12 | 82.087 to 82.217 | hidden |
| `p6-cosmo-dive-1` | 1:40 | damage | 98 to 103 | 100.006 | 100.059 | 100.022 | 99.956 | 100.038 | 99.999 | 12 | 99.908 to 100.037 | all |
| `p6-unlimited-wave-cannon-1` | 1:55 | cast | 113 to 118 | 115.258 | 115.343 | 115.309 | 115.302 | 115.288 | 115.286 | 12 | 115.156 to 115.348 | hidden |
| `p6-wave-cannon-1` | 2:17 | damage | 136 to 138 | 137.119 | 137.187 | 137.154 | 137.187 | 137.115 | 137.133 | 12 | 137.001 to 137.199 | all |
| `p6-wave-cannon-2` | 2:19 | damage | 138 to 141 | 139.125 | 139.193 | 139.162 | 139.193 | 139.114 | 139.141 | 12 | 139.010 to 139.204 | hidden |
| `p6-wave-cannon-3` | 2:26 | damage | 143 to 148 | 145.629 | 145.610 | 145.525 | 145.596 | 145.418 | 145.530 | 12 | 145.435 to 145.699 | all |
| `p6-cosmo-arrow-2` | 2:39 | cast | 157 to 162 | 159.168 | 159.136 | 159.019 | 159.126 | 159.016 | 159.069 | 12 | 158.934 to 159.211 | hidden |
| `p6-wave-cannon-4` | 2:51 | damage | 170 to 172 | 171.028 | 171.008 | 170.819 | 170.954 | 170.812 | 170.945 | 12 | 170.741 to 171.021 | all |
| `p6-wave-cannon-5` | 2:53 | damage | 172 to 175 | 172.990 | 172.964 | 172.820 | 172.954 | 172.819 | 172.910 | 12 | 172.744 to 172.990 | hidden |
| `p6-wave-cannon-6` | 2:59 | damage | 177 to 182 | 179.495 | 179.516 | 179.223 | 179.500 | 179.331 | 179.478 | 12 | 179.242 to 179.525 | all |
| `p6-unlimited-wave-cannon-2` | 3:12 | cast | 190 to 195 | 192.021 | 191.996 | 191.734 | 191.967 | 191.851 | 191.928 | 12 | 191.778 to 192.046 | hidden |
| `p6-cosmo-dive-2` | 3:34 | damage | 212 to 217 | 213.859 | 213.839 | 213.565 | 213.849 | 213.677 | 213.764 | 12 | 213.587 to 213.840 | all |
| `p6-cosmo-meteor-1` | 3:58 | damage | 236 to 241 | 238.374 | 238.341 | 238.038 | 238.118 | 238.056 | 238.133 | 12 | 237.981 to 238.357 | all |
| `p6-cosmo-meteor-2` | 4:04 | damage | 243 to 246 | 244.388 | 244.369 | 244.056 | 244.132 | 244.073 | 244.152 | 12 | 243.999 to 244.381 | hidden |
| `p6-cosmo-meteor-3` | 4:16 | damage | 254 to 259 | 256.425 | 256.382 | 256.088 | 256.169 | 256.103 | 256.215 | 12 | 256.036 to 256.414 | all |
| `p6-magic-number-1` | 4:30 | damage | 268 to 273 | 269.891 | 269.870 | 269.542 | 269.640 | 269.554 | 269.620 | 12 | 269.478 to 269.889 | all |
| `p6-magic-number-2` | 4:46 | damage | 284 to 289 | 286.065 | 286.010 | 285.715 | 285.823 | 285.731 | 285.756 | 12 | 285.641 to 286.077 | all |
| `p6-run-mi-1` | 4:53 | begincast | 290 to 300 | 293.284 | 293.206 | 292.924 | 293.050 | 292.949 | 292.953 | 12 | 292.851 to 293.302 | hidden |

## Verification

### P4 review

P4 visibility was retained. Wave Cannon's IDs now follow each observed
occurrence: proteans use 31617/31614, 31614/32534 and 31614/31619;
stacks use 31616/31615 with 32534, 31618 and 31620 respectively.
Damage timings and all seven sheet bindings are unchanged.

### P1 review

The phase-by-phase review retained P1's visibility. Blaster's ability lists
were narrowed to the IDs observed in each occurrence: first 31495/31496/31498,
second and third 31496/31498, fourth 31497/31498. The Diffuse timing windows
were widened without overlap to include source H's valid early hits, starting
at 107.933 seconds. All five rounded Diffuse times remain unchanged.

`packages/encounter-data/tests/catalog.test.ts` requires phase starts, mechanic
times and nonempty ability IDs for all six TOP phases. `tests/top.test.ts`
checks source action counts, all tank-row names/times, repeated-hit separation,
P3 monitor visibility and the Blind Faith phase boundary.

The Python importer tests cover tank note continuations, job-scoped footer
notes and strict party binding. Re-running the live importer reproduces the
committed sheet without changing the encounter. The schema supports bounded
sheet groups, resolved at build time for every layout and PiP. The shared viewer
retains personal-mit anchors before filtering hidden mechanics, and cheatsheets
preserve alternative mitigation while intentionally hiding notes. There are no runtime network requests.


### Source instruction corrections, 2026-09-17

P2 now includes the post-Playstation Feint/Addle note. P5 includes the
15-second and 10-second mitigation timing rules, plus the healer buster warning
for WAR/PLD, GNB/DRK, GNB/PLD and PLD/DRK. The warning is at party phase level
so healers can read it, as well as in the original tank plans.

P6 places the timing warning on each Wave Cannon stack, the first tank-LB
priority on Tank 1's Cosmo Memory LB, and the GNB/DRK exception after Cosmo
Memory in the two matching tank plans. General meteor-positioning coordination
is omitted. Tank Rampart timing sits at Cosmo Dive 1, MP conservation at Wave
Cannon 2, and optional invuln swaps at Wave Cannon 1.
The reviewed behavior is note-only: Tank 1 is instructed to move Party Mit
to Cosmo Memory for this pairing; assignments are not automatically moved.
Party assignments remain unchanged apart from the reviewed SCH label.


### Final tank and documentation audit

All 142 evidence rows match the encounter's timestamps and visibility flags.
The visibility column describes the encounter before sheet grouping and personal
assignments. P5 group members render in their reviewed Delta/Sigma/Omega rows.
A live workbook import reproduces the committed sheet without changing the encounter.

The 12 tank plans contain 171 personal rows. Render tests cover both tank seats,
all phases, tabs/list/cheatsheet layouts, and normal/compact rendering. They check
mechanic headings, actions, buddy mitigation, alternatives and notes. P3 monitors
remain hidden without a personal assignment and appear with their assigned Rampart,
including with Mechanics set to Mit only. Tank-only busters retain blank rows for
tanks and stay hidden from unassigned healers. The GNB/DRK exception remains a
pairing-specific note with no automatic assignment changes.

The final audit fixed two viewer omissions: hidden encounter rows previously
removed their personal-mit anchors, and cheatsheets discarded alternative plans. Notes follow the Notes preference in the full view and PiP, except in
icon-only display. Cheatsheets intentionally hide all notes, matching FRU
and DMU; alternative mitigation remains available. Render coverage also includes all 21 supported jobs, both
melee seats, every phase, all layouts and all display modes.
