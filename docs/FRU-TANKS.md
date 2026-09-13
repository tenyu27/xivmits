# FRU tank-only mechanic review

All five phases are reviewed and approved. All six tank-pairing tabs have
been reconciled against the FFLogs encounter and imported by `scripts/fru_tanks.py`.
The viewer selects MT/OT opening duties and the strategy controls described below.

## P1: reviewed

Audited all six tank tabs from the live [FRU Mit but Good workbook](https://docs.google.com/spreadsheets/d/1M1LHe4mpb1lyxkLWJxrDwe_JH897nickG3XLTtwnI90/edit) on 2026-09-12. The tables preserve the source assignments used by the importer.

| Phase time | Mechanic | Ability ID | Proposed visibility |
|---|---|---|---|
| 0:26 | Powder Mark Trail 1 | 40168 | Tanks |
| 0:42 | Burn Mark 1 | 40169 | Tanks |
| 2:12 | Powder Mark Trail 2 | 40168 | Tanks |
| 2:28 | Burn Mark 2 | 40169 | Tanks |

All four exist with tank roles in the encounter and are now visible for tanks following review. No additional P1 tank-only mechanic appears in any pairing tab. Damage-hit anchors and phase start 0:00 are unchanged.

Requeried FFLogs ability events for all six reference clears in [FRU.md](FRU.md). First real damage per pull remains the anchor; synthetic immune damage without a packet is excluded. Powder Mark Trail 2 has real hits at 131.958, 131.914 and 131.727 seconds. Burn Mark 2 has first hits at 147.662, 147.913, 147.796 and 147.837 seconds. Faster phase transitions can omit the last Burn Mark.

## Pairing coverage and source caveats

- WARGNB, WARPLD, WARDRK and GNBPLD explicitly provide both MT/OT arrangements. GNBDRK and PLDDRK provide one arrangement and say to swap as needed for P1/P2. Do not present an inferred reverse arrangement as a separately written source plan.
- Each arrangement includes the default first-Powder invuln and an alternative second-Powder invuln. Both branches use the same four encounter mechanics.
- The late-40% footnote attached to Powder Mark Trail 2 says it covers Burnished Glory 2. FFLogs puts Burnished Glory 2 at 2:03 and Powder Mark Trail 2 damage at 2:12. Preserve this as a source discrepancy; do not turn it into a new timing instruction.
- Kitchen Sink is the source's unspecified instruction for both tanks at alternative Burn Mark 2. Do not invent an exact ability list.
- GNBPLD omits Sheltron from the default off-tank Paladin Burn Mark 1 cell, while WARPLD includes it. Preserve the actual cell rather than copying one pairing over another.
- Carry-over formatting is inconsistent between some equivalent cells, including GNB Burn Mark 2. The tables below preserve the source formatting; any correction needs an explicit review.

## Complete P1 source assignments

Shorthand is copied from the workbook. `[lingering]` and `[conditional]` preserve font semantics per token; unmarked text is ordinary source text. A blank cell is shown as an em dash. Buddy-mit lines belong to the tank whose column contains them.

### WARGNB

Alternative MT/OT swapped positions.

| Branch / mechanic | WARRIOR (Main Tank) | GUNBREAKER (Off Tank) | GUNBREAKER (Main Tank) | WARRIOR (Off Tank) |
|---|---|---|---|---|
| Default / Powder Mark Trail 1 | Holmgang | — | Bolide | — |
| Default / Burn Mark 1 | Rampart, Thrill, Bloodwhetting | Rampart, Camo, HoC | Rampart, Camo, HoC | Rampart, Thrill, Bloodwhetting |
| Default / Powder Mark Trail 2 | *Damnation, (Late) Rampart, Thrill, Bloodwhetting | Provoke [conditional] | *Great Nebula, (Late) Rampart/Camo, HoC | Provoke [conditional] |
| Default / Burn Mark 2 | Rampart [lingering] | Great Nebula, Rampart, Camo<br>Buddy Mit: HoC | Rampart/Camo [lingering] | Damnation, Rampart, Thrill<br>Buddy Mit: Nascent |
| Alternative / Powder Mark Trail 1 | Damnation, (Late) Rampart, Thrill, Bloodwhetting | Provoke [conditional] | Great Nebula, (Late) Rampart/Camo, HoC | Provoke [conditional] |
| Alternative / Burn Mark 1 | Rampart [lingering] | Rampart, Camo<br>Buddy Mit: HoC | Rampart [lingering], Camo [lingering] | Rampart, Thrill<br>Buddy Mit: Nascent |
| Alternative / Powder Mark Trail 2 | Holmgang | — | Bolide | — |
| Alternative / Burn Mark 2 | Kitchen Sink | Kitchen Sink | Kitchen Sink | Kitchen Sink |

Source notes (C20): Healers should mit main tank for burn mark 2 *Late 40% should cover burnished glory 2 (shake first)

Source notes (J20): *Late 40% should cover burnished glory 2

### WARPLD

Alternative MT/OT swapped positions. Allows additional invuln in p3, see bottom notes.

| Branch / mechanic | WARRIOR (Main Tank) | PALADIN (Off Tank) | PALADIN (Main Tank) | WARRIOR (Off Tank) |
|---|---|---|---|---|
| Default / Powder Mark Trail 1 | Holmgang | — | Hallowed | — |
| Default / Burn Mark 1 | Rampart, Thrill, Bloodwhetting | Rampart, Bulwark, Sheltron | Rampart, Bulwark, Sheltron | Rampart, Thrill, Bloodwhetting |
| Default / Powder Mark Trail 2 | *Damnation, (Late) Rampart, Thrill, Bloodwhetting | Provoke [conditional]<br>Buddy Mit: Intervention | *Guardian, (Late) Rampart, Bulwark, Sheltron | Provoke [conditional] |
| Default / Burn Mark 2 | Rampart [lingering] | Guardian, Rampart, Bulwark<br>Buddy Mit: Intervention | Rampart [lingering], Sheltron | Damnation, Rampart, Thrill<br>Buddy Mit: Nascent |
| Alternative / Powder Mark Trail 1 | Damnation, (Late) Rampart, Thrill, Bloodwhetting | Provoke [conditional] | Guardian, (Late) Rampart, Bulwark, Sheltron | Provoke [conditional] |
| Alternative / Burn Mark 1 | Rampart [lingering] | Rampart, Bulwark, Sheltron<br>Buddy Mit: Intervention | Rampart [lingering], Sheltron | Rampart, Thrill, Bloodwhetting |
| Alternative / Powder Mark Trail 2 | Holmgang | — | Hallowed | — |
| Alternative / Burn Mark 2 | Kitchen Sink | Kitchen Sink | Kitchen Sink | Kitchen Sink |

Source notes (C20): Healers should mit main tank for burn mark 2 *Late 40% should cover burnished glory 2 (shake first)

Source notes (J20): *Late 40% should cover burnished glory 2

### WARDRK

Alternative MT/OT swapped positions.

| Branch / mechanic | WARRIOR (Main Tank) | DARK KNIGHT (Off Tank) | DARK KNIGHT (Main Tank) | WARRIOR (Off Tank) |
|---|---|---|---|---|
| Default / Powder Mark Trail 1 | Holmgang | — | Living Dead | — |
| Default / Burn Mark 1 | Rampart, Thrill, Bloodwhetting | Rampart, Dark Mind, TBN | Rampart, Dark Mind, TBN | Rampart, Thrill, Bloodwhetting |
| Default / Powder Mark Trail 2 | *Damnation, (Late) Rampart, Thrill, Bloodwhetting | Provoke [conditional]<br>Buddy Mit: Oblation, TBN [conditional] | *Shadowed Vigil, (Late) Rampart, Dark Mind, TBN | Provoke [conditional] |
| Default / Burn Mark 2 | Rampart [lingering] | Shadowed Vigil, Rampart, Dark Mind<br>Buddy Mit: TBN, Oblation | Rampart [lingering], TBN | Damnation, Rampart, Thrill<br>Buddy Mit: Nascent |
| Alternative / Powder Mark Trail 1 | Damnation, (Late) Rampart, Thrill, Bloodwhetting | Provoke [conditional] | Shadowed Vigil, (Late) Rampart, Dark Mind, TBN | Provoke [conditional] |
| Alternative / Burn Mark 1 | Rampart [lingering] | Rampart, Dark Mind, Oblation<br>Buddy Mit: TBN | Rampart [lingering], TBN | Rampart, Thrill, Bloodwhetting |
| Alternative / Powder Mark Trail 2 | Holmgang | — | Living Dead | — |
| Alternative / Burn Mark 2 | Kitchen Sink | Kitchen Sink | Kitchen Sink | Kitchen Sink |

Source notes (C20): Healers should mit main tank for burn mark 2 *Late 40% should cover burnished glory 2 (shake first)

Source notes (J20): *Late 40% should cover burnished glory 2

### GNBDRK

Tank invulns/mits for phase 1 and 2 assume LEFT COLUMN IS MT. Swap if needed. P3 and onwards have very specific invuln timings!

| Branch / mechanic | GUNBREAKER | DARK KNIGHT |
|---|---|---|
| Default / Powder Mark Trail 1 | Bolide | — |
| Default / Burn Mark 1 | Rampart, Camo, HoC | Rampart, Dark Mind, TBN |
| Default / Powder Mark Trail 2 | *Great Nebula, (Late) Rampart/Camo, HoC | Provoke [conditional]<br>Buddy Mit: Oblation, TBN [conditional] |
| Default / Burn Mark 2 | Rampart, Camo | Shadowed Vigil, Rampart, Dark Mind<br>Buddy Mit: TBN, Oblation |
| Alternative / Powder Mark Trail 1 | Great Nebula, (Late) Rampart/Camo, HoC | Provoke |
| Alternative / Burn Mark 1 | Rampart, Camo | Rampart, Dark Mind, Oblation<br>Buddy Mit: TBN |
| Alternative / Powder Mark Trail 2 | Bolide | — |
| Alternative / Burn Mark 2 | Kitchen Sink | Kitchen Sink |

Source notes (C20): Healers should mit main tank for burn mark 2 *Late 40% should cover burnished glory 2

### GNBPLD

Alternative MT/OT swapped positions.

| Branch / mechanic | GUNBREAKER (Main Tank) | PALADIN (Off Tank) | PALADIN (Main Tank) | GUNBREAKER (Off Tank) |
|---|---|---|---|---|
| Default / Powder Mark Trail 1 | Bolide | — | Hallowed | — |
| Default / Burn Mark 1 | Rampart, Camo, HoC | Rampart, Bulwark | Rampart, Bulwark, Sheltron | Rampart, Camo, HoC |
| Default / Powder Mark Trail 2 | *Great Nebula, (Late) Rampart/Camo, HoC | Provoke [conditional]<br>Buddy Mit: Intervention | *Guardian, (Late) Rampart, Bulwark, Sheltron | Provoke [conditional] |
| Default / Burn Mark 2 | Rampart, Camo | Guardian, Rampart, Bulwark<br>Buddy Mit: Intervention | Rampart, Sheltron | Great Nebula, Rampart, Camo<br>Buddy Mit: HoC |
| Alternative / Powder Mark Trail 1 | Great Nebula, (Late) Rampart/Camo, HoC | Provoke [conditional] | Guardian, (Late) Rampart, Bulwark, Sheltron | Provoke [conditional] |
| Alternative / Burn Mark 1 | Rampart [lingering], Camo [lingering] | Rampart, Bulwark, Sheltron<br>Buddy Mit: Intervention | Rampart [lingering], Sheltron | Rampart, Camo, HoC |
| Alternative / Powder Mark Trail 2 | Bolide | — | Hallowed | — |
| Alternative / Burn Mark 2 | Kitchen Sink | Kitchen Sink | Kitchen Sink | Kitchen Sink |

Source notes (C20): Healers should mit main tank for burn mark 2 *Late 40% should cover burnished glory 2

Source notes (J20): *Late 40% should cover burnished glory 2

### PLDDRK

Tank invulns/mits for phase 1 and 2 assume LEFT COLUMN IS MT. Swap if needed. P3 and onwards have very specific invuln timings!

| Branch / mechanic | PALADIN | DARK KNIGHT |
|---|---|---|
| Default / Powder Mark Trail 1 | Hallowed | — |
| Default / Burn Mark 1 | Rampart, Bulwark, Sheltron | Rampart, Dark Mind, TBN |
| Default / Powder Mark Trail 2 | *Guardian, Bulwark, (Late) Rampart, Sheltron | Provoke [conditional]<br>Buddy Mit: Oblation, TBN [conditional] |
| Default / Burn Mark 2 | Rampart [lingering], Sheltron | Shadowed Vigil, Rampart, Dark Mind<br>Buddy Mit: TBN, Oblation |
| Alternative / Powder Mark Trail 1 | Guardian, (Late) Rampart, Bulwark, Sheltron | Provoke |
| Alternative / Burn Mark 1 | Rampart [lingering], Sheltron | Rampart, Dark Mind, Oblation<br>Buddy Mit: TBN |
| Alternative / Powder Mark Trail 2 | Hallowed | — |
| Alternative / Burn Mark 2 | Kitchen Sink | Kitchen Sink |

Source notes (C20): Healers should mit main tank for burn mark 2 *Late 40% can cover burnished glory 2


## P2: reviewed

All six live tank tabs have exactly one P2 mechanic row, B40, Quadruple Slap.
Each gives the off tank an invulnerability and leaves the main tank cell empty.
There is no alternative P2 block or additional tank-only mechanic in these tabs.
Both P1 invuln-order branches lead to this same P2 row.

| P2 time | Pull time | Mechanic | Ability IDs | Display |
|---|---|---|---|---|
| 0:12 | 2:59 | Quadruple Slap | 40191, 40192 | Tanks; one assignment covering both hits |
| 0:16 | 3:03 | Quadruple Slap follow-up | 40192 | Hidden, retained in encounter |

The existing encounter already matches this treatment. Keep the visible name
unnumbered and anchor its assignment to the first damage timestamp, as reviewed
in the party pass. These are mechanic hit times, not literal invulnerability
button-press instructions.

Fresh FFLogs checks across the six reference clears confirm actual first damage
at 11.984, 11.983 and 11.988 seconds, with follow-up damage at 16.171, 16.168
and 16.174 seconds. The three Paladin-invuln samples only report synthetic
immune damage without packets at cast completion; those do not move the anchors
to 0:11/0:15. P2 starts at canonical pull time 2:47.

| Tab | Written default MT / OT | Quadruple Slap assignment | Written swapped MT / OT | Swapped assignment |
|---|---|---|---|---|
| WARGNB | WAR / GNB | GNB: Superbolide | GNB / WAR | WAR: Holmgang |
| WARPLD | WAR / PLD | PLD: Hallowed Ground | PLD / WAR | WAR: Holmgang |
| WARDRK | WAR / DRK | DRK: Living Dead | DRK / WAR | WAR: Holmgang |
| GNBPLD | GNB / PLD | PLD: Hallowed Ground | PLD / GNB | GNB: Superbolide |
| GNBDRK | GNB / DRK | DRK: Living Dead | Not separately written | Header says swap as needed for P1/P2 |
| PLDDRK | PLD / DRK | DRK: Living Dead | Not separately written | Header says swap as needed for P1/P2 |

Source cells are F40/M40 for the four double-layout tabs, and G40 for the two
single-layout tabs. Source shorthand Bolide and Hallowed is expanded above to
Superbolide and Hallowed Ground. The phase note at C42, and J42 where present,
is identical throughout: "Personal mit is free for autos this phase."
Autos remain a phase note rather than an invented timed tank mechanic.

## P3: reviewed

All six tank tabs contain Black Halo and Darkest Dance, with no additional P3
tank-only mechanic rows. The existing encounter already marks these visible
for tanks. Retain these FFLogs damage anchors:

| P3 time | Pull time | Mechanic | Ability IDs | Display |
|---|---|---|---|---|
| 1:24 | 8:49 | Black Halo | 40290 | Tanks |
| 2:13 | 9:38 | Darkest Dance | 40181 cast, 40182 damage | Tanks; first hit |
| 2:16 | 9:41 | Darkest Dance knockback | 40183 | Hidden; party damage, not tank-only |

Rechecked the saved FFLogs event responses for all six reference clears.
Black Halo damage occurs at 83.675, 83.997, 83.491, 83.971, 83.742 and
83.889 seconds. Darkest Dance's first real damage occurs at 133.098,
133.641, 132.696, 133.208 and 133.422 seconds; reference D only has a
synthetic immune event without a packet for that first hit. The knockback
hits non-tanks too, so it must not inherit the tank-only role restriction.
P3's canonical phase start remains 7:25. These times describe mechanic
resolution, not the instant to press an invulnerability.

### Branches and caveats

- WAR/GNB and WAR/DRK assign the MT Kitchen Sink on Black Halo with OT buddy
  mitigation, then the OT's invulnerability on Darkest Dance. Both written
  MT/OT layouts follow that pattern.
- WAR/PLD assigns Kitchen Sink and buddy mitigation for both mechanics in
  both layouts. Its separate D90 note says: "If you swap MT/OT prior to phase
  3, Hallowed is available for Darkest Dance." Keep this as a distinct route
  with the earlier invuln usage taken into account, not an unconditional
  addition to either default row.
- GNB/PLD assigns Kitchen Sink on Black Halo without any written buddy mit.
  Darkest Dance has OT Kitchen Sink plus MT buddy mit. Do not copy the missing
  Black Halo buddy assignment from another pairing.
- GNB/DRK lists Superbolide on Black Halo, conditional on GNB having invulned
  Powder Mark 1 or 2 and DRK not invulning Darkest Dance. Kitchen Sink and
  DRK's TBN/Oblation buddy mitigation are italic conditional alternatives in
  the source. The normal Darkest Dance row is DRK Kitchen Sink plus GNB HoC.
  The alternative lets DRK use Living Dead on Darkest Dance, explicitly
  requiring all P4/P5 invulns to be swapped. Preserve that dependency.
- PLD/DRK assigns Kitchen Sink with buddy mitigation to each buster and
  explicitly warns: "Don't get baited by Hallowed being up".
- Kitchen Sink remains an unspecified source instruction. Do not invent
  individual cooldowns. GNBDRK and PLDDRK's header permission to swap roles
  applies to P1/P2; it does not establish arbitrary reverse P3 plans.

### Complete P3 source assignments

The following preserves the workbook shorthand and all explicitly written
layouts. For GNBDRK Black Halo, the Kitchen Sink line and DRK buddy line are
conditional alternatives, as described above.

#### WARGNB

| Mechanic | WARRIOR (Main Tank) | GUNBREAKER (Off Tank) | GUNBREAKER (Main Tank) | WARRIOR (Off Tank) |
|---|---|---|---|---|
| Black Halo | Kitchen Sink | Buddy Mit: HoC | Kitchen Sink | Buddy Mit: Nascent |
| Darkest Dance | — | Bolide | — | Holmgang |

#### WARPLD

| Mechanic | WARRIOR (Main Tank) | PALADIN (Off Tank) | PALADIN (Main Tank) | WARRIOR (Off Tank) |
|---|---|---|---|---|
| Black Halo | Kitchen Sink | Buddy Mit: Intervention | Kitchen Sink | Buddy Mit: Nascent |
| Darkest Dance | Buddy Mit: Nascent | Kitchen Sink | Buddy Mit: Intervention | Kitchen Sink |

Source note (D90): If you swap MT/OT prior to phase 3, Hallowed is available for Darkest Dance.

#### WARDRK

| Mechanic | WARRIOR (Main Tank) | DARK KNIGHT (Off Tank) | DARK KNIGHT (Main Tank) | WARRIOR (Off Tank) |
|---|---|---|---|---|
| Black Halo | Kitchen Sink | Buddy Mit: TBN, Oblation | Kitchen Sink | Buddy Mit: Nascent |
| Darkest Dance | — | Living Dead | — | Holmgang |

#### GNBDRK

| Mechanic | GUNBREAKER | DARK KNIGHT |
|---|---|---|
| Black Halo | *Bolide<br>Kitchen Sink | Buddy Mit: TBN, Oblation |
| Darkest Dance | Buddy Mit: HoC | Kitchen Sink |

Source note (C56): *Only available if invulning PM1 or PM2 and DRK not invulning Darkest Dance.

Source note (G56): DRK can invuln Darkest Dance instead. This requires swapping all invulns in p4 and p5

#### GNBPLD

| Mechanic | GUNBREAKER (Main Tank) | PALADIN (Off Tank) | PALADIN (Main Tank) | GUNBREAKER (Off Tank) |
|---|---|---|---|---|
| Black Halo | Kitchen Sink | — | Kitchen Sink | — |
| Darkest Dance | Buddy Mit: HoC | Kitchen Sink | Buddy Mit: Intervention | Kitchen Sink |

#### PLDDRK

| Mechanic | PALADIN | DARK KNIGHT |
|---|---|---|
| Black Halo | Kitchen Sink | Buddy Mit: TBN, Oblation |
| Darkest Dance | Buddy Mit: Intervention | Kitchen Sink |

Source note (C56): Don't get baited by Hallowed being up


## P4: reviewed

Reconciled all six live tank tabs. Each has Somber Dance, Hallowed Wings,
and optional 7/1 Akh Morn 1/2 assignments. Somber Dance is the only strictly
tank-only encounter mechanic among these. The latter three rows must remain
party mechanics, with tank personal assignments attached to their existing IDs.
No extra Edge of Oblivion rows are needed for tank plans.

| P4 time | Pull time | Mechanic | Treatment |
|---|---|---|---|
| 0:58 | 11:10 | Somber Dance | Visible for tanks; first-hit assignment covers both hits |
| 1:01 | 11:13 | Somber Dance second hit | Hidden, tank-only; retained |
| 1:11 | 11:23 | Akh Morn 1 | Existing party row; optional 7/1 personal assignments |
| 2:20 | 12:32 | Hallowed Wings | Existing party row; both tanks have personal mitigation |
| 2:25 | 12:37 | Hallowed Wings second hit | Hidden; retained, no separate source assignment |
| 2:34 | 12:46 | Akh Morn 2 | Existing party row; optional 7/1 personal assignments |

The six saved FFLogs P4 responses confirm Somber Dance real first-hit packets
at 57.963, 57.498, 57.641, 57.704 and 57.955 seconds, with second hits at
61.220, 60.745, 60.932, 60.957 and 61.210 seconds. Reference A does not have
real damage packets for these invulned hits. Ability IDs are 40283 for the
cast, 40284 for the first hit, and 40285 for the second. Keep the current
first-hit anchor and both IDs under the visible Somber Dance row.

Akh Morn first damage occurs at 70.980–71.420 and 153.513–154.011 seconds.
Player targets include both solo-tank and multi-player groups across reports;
7/1 is a strategy, not a reason to mark the encounter mechanic tank-only.
Hallowed Wings player damage uses 40332 at 139.672–140.154 seconds and hits
the party. Keep the existing 2:20 row rather than binding the tank sheet to
the earlier 0:53 Darklit cast, which has no player damage in these samples.
P4's canonical phase start remains 10:12. All clocks remain FFLogs-derived.

### Pairing defaults

| Tab | Somber Dance invuln | Suggested first / second 7/1 solo tank |
|---|---|---|
| WARGNB | MT: Holmgang or Superbolide | OT first, MT second |
| WARPLD | WAR: Holmgang in both layouts | PLD first, WAR second |
| WARDRK | MT: Holmgang or Living Dead | OT first, MT second |
| GNBPLD | GNB: Superbolide in both layouts | PLD first, GNB second |
| GNBDRK | DRK: Living Dead | GNB first, DRK second |
| PLDDRK | DRK: Living Dead | PLD first, DRK second |

GNBDRK's P3 alternative, DRK invulning Darkest Dance, explicitly requires
swapping P4/P5 invulns; its P4 Somber assignment must therefore change to GNB
Superbolide on that route. Do not apply that swap independently of the P3 route.

Hallowed Wings personal assignments are consistent by job across all six tabs:
WAR Damnation + Thrill of Battle; GNB Great Nebula; PLD Guardian;
DRK Shadowed Vigil + Dark Mind. These supplement the party overlay.

All six tabs say either tank may solo Akh Morn and offer the other order in
light-grey text. The non-solo tank uses the source's buddy mitigation instead
of pressing the solo tank's personal list. Preserve each cell: the DRK lists,
for example, do not universally include Dark Mind. The first Akh Morn solo
list explicitly says "Right After 1st Somber"; preserve this early-use note
while keeping the mechanic anchor at 1:11. These are not simultaneous presses
at the Akh Morn damage timestamp. Keep 7/1 rows conditional on choosing that
strategy rather than displaying both branches as required actions.

### Complete P4 source assignments

Shorthand and literal `or` alternatives below are copied from the workbook.
The source note under each grid explains the alternative solo order.

#### WARGNB

| Mechanic | WARRIOR (Main Tank) | GUNBREAKER (Off Tank) | GUNBREAKER (Main Tank) | WARRIOR (Off Tank) |
|---|---|---|---|---|
| Somber Dance | Holmgang | — | Bolide | — |
| Hallowed Wing | Damnation, Thrill | Great Nebula | Great Nebula | Damnation, Thrill |
| 7/1 Akh Morn 1 | Buddy Mit: Nascent<br>or (Right After 1st Somber) Rampart, Bloodwhetting | (Right After 1st Somber) Rampart/Camo, HoC<br>or Buddy Mit: HoC | Buddy Mit: HoC<br>or (Right After 1st Somber) Rampart/Camo, HoC | (Right After 1st Somber) Rampart, Bloodwhetting<br>or Buddy Mit: Nascent |
| 7/1 Akh Morn 2 | Rampart, Bloodwhetting<br>or Buddy Mit: Nascent | Buddy Mit: HoC<br>or Rampart, Camo, HoC | Rampart, Camo, HoC<br>or Buddy Mit: HoC | Buddy Mit: Nascent<br>or Rampart, Bloodwhetting |

Source note (C68): If 7/1 AM, use mits below (GNB should take first 7/1 if not discussed)

Source note (J68): If 7/1 AM, use mits below (WAR should take first 7/1 if not discussed)

Source note (D76): Either tank can solo Akh Morn, discuss with your cotank and use the LIGHT GRAY mits.

#### WARPLD

| Mechanic | WARRIOR (Main Tank) | PALADIN (Off Tank) | PALADIN (Main Tank) | WARRIOR (Off Tank) |
|---|---|---|---|---|
| Somber Dance | Holmgang | — | — | Holmgang |
| Hallowed Wing | Damnation, Thrill | Guardian | Guardian | Damnation, Thrill |
| 7/1 Akh Morn 1 | Buddy Mit: Nascent<br>or (Right After 1st Somber) Rampart, Bloodwhetting | (Right After 1st Somber) Rampart, Bulwark, Sheltron<br>or Buddy Mit: Intervention | (Right After 1st Somber) Rampart, Bulwark, Sheltron<br>or Buddy Mit: Intervention | Buddy Mit: Nascent<br>or (Right After 1st Somber) Rampart, Bloodwhetting |
| 7/1 Akh Morn 2 | Rampart, Bloodwhetting<br>or Buddy Mit: Nascent | Buddy Mit: Intervention<br>or Rampart, Bulwark, Sheltron | Buddy Mit: Intervention<br>or Rampart, Bulwark, Sheltron | Rampart, Bloodwhetting<br>or Buddy Mit: Nascent |

Source note (C66): If 7/1 AM, use mits below (PLD should take first 7/1 if not discussed)

Source note (J66): If 7/1 AM, use mits below (PLD should take first 7/1 if not discussed)

Source note (D74): Either tank can solo Akh Morn, discuss with your cotank and use the LIGHT GRAY mits.

Source note (K74): Same as left.

#### WARDRK

| Mechanic | WARRIOR (Main Tank) | DARK KNIGHT (Off Tank) | DARK KNIGHT (Main Tank) | WARRIOR (Off Tank) |
|---|---|---|---|---|
| Somber Dance | Holmgang | — | Living Dead | — |
| Hallowed Wing | Damnation, Thrill | Shadowed Vigil, Dark Mind | Shadowed Vigil, Dark Mind | Damnation, Thrill |
| 7/1 Akh Morn 1 | Buddy Mit: Nascent<br>or (Right After 1st Somber) Rampart, Bloodwhetting | (Right After 1st Somber) Rampart, Dark Mind, TBN, Oblation<br>or Buddy Mit: TBN, Oblation | Buddy Mit: Oblation, TBN<br>or (Right After 1st Somber) Rampart, Oblation, TBN | (Right After 1st Somber) Rampart, Bloodwhetting<br>or Buddy Mit: Nascent |
| 7/1 Akh Morn 2 | Rampart, Bloodwhetting<br>or Buddy Mit: Nascent | Buddy Mit: TBN, Oblation<br>or Rampart, TBN, Oblation | Rampart, Oblation, TBN<br>or Buddy Mit: Oblation, TBN | Buddy Mit: Nascent<br>or Rampart, Bloodwhetting |

Source note (C68): If 7/1 AM, use mits below (DRK should take first 7/1 if not discussed)

Source note (J68): If 7/1 AM, use mits below (WAR should take first 7/1 if not discussed)

Source note (D76): Either tank can solo Akh Morn, discuss with your cotank and use the LIGHT GRAY mits.

#### GNBDRK

| Mechanic | GUNBREAKER | DARK KNIGHT |
|---|---|---|
| Somber Dance | — | Living Dead |
| Hallowed Wings | Great Nebula | Shadowed Vigil, Dark Mind |
| 7/1 Akh Morn 1 |  (Right After 1st Somber) Rampart/Camo, HoC<br>or Buddy Mit: HoC | Buddy Mit: TBN, Oblation<br>or (Right After 1st Somber) Rampart, TBN, Oblation |
| 7/1 Akh Morn 2 | Buddy Mit: HoC<br>or Rampart, Camo, HoC | Rampart, TBN, Oblation<br>or Buddy Mit: TBN, Oblation |

Source note (C70): If 7/1 AM, use mits below (GNB should take first 7/1 if not discussed)

Source note (D78): Either tank can solo Akh Morn, discuss with your cotank and use the LIGHT GRAY mits.

#### GNBPLD

| Mechanic | GUNBREAKER (Main Tank) | PALADIN (Off Tank) | PALADIN (Main Tank) | GUNBREAKER (Off Tank) |
|---|---|---|---|---|
| Somber Dance | Bolide | — | — | Bolide |
| Hallowed Wing | Great Nebula | Guardian | Guardian | Great Nebula |
| 7/1 Akh Morn 1 | Buddy Mit: HoC<br>or (Right After 1st Somber) Rampart/Camo, HoC | (Right After 1st Somber) Rampart, Bulwark, Sheltron<br>or Buddy Mit: Intervention | (Right After 1st Somber) Rampart, Bulwark, Sheltron<br>or Buddy Mit: Intervention | Buddy Mit: HoC<br>or (Right After 1st Somber) Rampart/Camo, HoC |
| 7/1 Akh Morn 2 | Rampart, Camo, HoC<br>or Buddy Mit: HoC | Buddy Mit: Intervention<br>or Rampart, Bulwark, Sheltron | Buddy Mit: Intervention<br>or Rampart, Bulwark, Sheltron | Rampart, Camo, HoC<br>or Buddy Mit: HoC |

Source note (C66): If 7/1 AM, use mits below (PLD should take first 7/1 if not discussed)

Source note (J66): If 7/1 AM, use mits below (PLD should take first 7/1 if not discussed)

Source note (D74): Either tank can solo Akh Morn, discuss with your cotank and use the LIGHT GRAY mits.

Source note (K74): Same as left.

#### PLDDRK

| Mechanic | PALADIN | DARK KNIGHT |
|---|---|---|
| Somber Dance | — | Living Dead |
| Hallowed Wing | Guardian | Shadowed Vigil, Dark Mind |
| 7/1 Akh Morn 1 |  (Right After 1st Somber) Rampart, Sheltron, Bulwark<br>or Buddy Mit: Intervention | Buddy Mit: TBN, Oblation<br>or (Right After 1st Somber) Rampart, Dark Mind, TBN, Oblation |
| 7/1 Akh Morn 2 | Buddy Mit: Intervention<br>or Rampart, Bulwark, Sheltron | Rampart, TBN, Oblation<br>or Buddy Mit: TBN, Oblation |

Source note (C70): If 7/1 AM, use mits below (PLD should take first 7/1 if not discussed)

Source note (D78): Either tank can solo Akh Morn, discuss with your cotank and use the LIGHT GRAY mits.


## P5: reviewed

All six live tank tabs contain exactly Wings Dark and Light 1 and 2. Both
are already visible for tanks and anchored to the first hit in the encounter.
The second hits remain hidden encounter records; preserve explicit second-hit
personal/buddy instructions under each visible sequence rather than suggesting
those abilities should be pressed at the first hit.

| P5 time | Pull time | Mechanic | Display |
|---|---|---|---|
| 0:58 | 15:21 | Wings Dark and Light 1 | Tanks |
| 1:01 | 15:24 | Sequence 1 second hit | Hidden, retained |
| 2:55 | 17:18 | Wings Dark and Light 2 | Tanks |
| 2:59 | 17:22 | Sequence 2 second hit | Hidden, retained |

Rechecked the saved event responses for all six FFLogs reference clears.
First real player-damage timestamps span 57.559–58.251, 61.258–62.020,
174.901–175.292 and 178.445–179.659 seconds for these four hits.
Each report contributes once to each median, regardless of target count.
Damage IDs 40314/40315/39879/39880 hit tanks in these samples; cast variants
40313/40233 remain attached to the visible rows. Synthetic immune events
without packets do not determine damage timing. P5 begins at canonical 14:23.
No new tank-only Akh Morn, Polarizing Strikes, or Pandora's Box row is needed;
those remain party mechanics.

### Invuln routes and second-hit coverage

| Pairing | Sequence 1 invuln | Sequence 2 invuln |
|---|---|---|
| WARGNB | WAR: Holmgang | GNB: Superbolide |
| WARPLD | WAR: Holmgang | PLD: Hallowed Ground |
| WARDRK | WAR: Holmgang | DRK: Living Dead |
| GNBPLD | PLD: Hallowed Ground | GNB: Superbolide |
| GNBDRK | GNB: Superbolide | DRK: Living Dead |
| PLDDRK | PLD: Hallowed Ground | DRK: Living Dead |

These orders are by job, not MT/OT: the four tabs with both layouts retain
the same P5 job order in their swapped layout. GNBDRK's alternative route,
DRK invulning P3 Darkest Dance, explicitly swaps all P4/P5 invulns. On that
route P5 is DRK first, GNB second, linked to GNB invulning P4 Somber Dance.
Do not expose those as independent arbitrary swaps.

The other tank uses Kitchen Sink. The invulning tank supplies buddy mitigation
for the second hit: WAR Nascent Flash; GNB Heart of Corundum; PLD Intervention;
DRK The Blackest Night and Oblation. Every DRK Kitchen Sink cell explicitly
says TBN second hit. Preserve that timing on DRK's personal TBN as well as the
buddy-target distinction. Kitchen Sink remains unspecified beyond what the
cell explicitly names.

### Complete P5 source assignments

#### WARGNB

| Mechanic | WARRIOR (Main Tank) | GUNBREAKER (Off Tank) | GUNBREAKER (Main Tank) | WARRIOR (Off Tank) |
|---|---|---|---|---|
| Wings Dark and Light 1 | Holmgang<br>Buddy Mit 2nd Hit: Nascent | Kitchen Sink | Kitchen Sink | Holmgang<br>Buddy Mit 2nd Hit: Nascent |
| Wings Dark and Light 2 | Kitchen Sink | Bolide<br>Buddy Mit 2nd Hit: HoC | Bolide<br>Buddy Mit 2nd Hit: HoC | Kitchen Sink |

#### WARPLD

| Mechanic | WARRIOR (Main Tank) | PALADIN (Off Tank) | PALADIN (Main Tank) | WARRIOR (Off Tank) |
|---|---|---|---|---|
| Wings Dark and Light 1 | Holmgang<br>Buddy Mit 2nd Hit: Nascent | Kitchen Sink | Kitchen Sink | Holmgang<br>Buddy Mit 2nd Hit: Nascent |
| Wings Dark and Light 2 | Kitchen Sink | Hallowed<br>Buddy Mit 2nd Hit: Intervention | Hallowed<br>Buddy Mit 2nd Hit: Intervention | Kitchen Sink |

#### WARDRK

| Mechanic | WARRIOR (Main Tank) | DARK KNIGHT (Off Tank) | DARK KNIGHT (Main Tank) | WARRIOR (Off Tank) |
|---|---|---|---|---|
| Wings Dark and Light 1 | Holmgang<br>Buddy Mit 2nd Hit: Nascent | Kitchen Sink (TBN 2nd hit) | Kitchen Sink (TBN 2nd hit) | Holmgang<br>Buddy Mit 2nd Hit: Nascent |
| Wings Dark and Light 2 | Kitchen Sink | Living Dead<br>Buddy Mit 2nd Hit: TBN, Oblation | Living Dead<br>Buddy Mit 2nd Hit: TBN, Oblation | Kitchen Sink |

#### GNBDRK

| Mechanic | GUNBREAKER | DARK KNIGHT |
|---|---|---|
| Wings Dark and Light 1 | Bolide<br>Buddy Mit 2nd Hit: HoC | Kitchen Sink (TBN 2nd hit) |
| Wings Dark and Light 2 | Kitchen Sink | Living Dead<br>Buddy Mit 2nd Hit: TBN, Oblation |

#### GNBPLD

| Mechanic | GUNBREAKER (Main Tank) | PALADIN (Off Tank) | PALADIN (Main Tank) | GUNBREAKER (Off Tank) |
|---|---|---|---|---|
| Wings Dark and Light 1 | Kitchen Sink | Hallowed Ground<br>Buddy Mit 2nd Hit: Intervention | Hallowed Ground<br>Buddy Mit 2nd Hit: Intervention | Kitchen Sink |
| Wings Dark and Light 2 | Bolide<br>Buddy Mit 2nd Hit: HoC | Kitchen Sink | Kitchen Sink | Bolide<br>Buddy Mit 2nd Hit: HoC |

#### PLDDRK

| Mechanic | PALADIN | DARK KNIGHT |
|---|---|---|
| Wings Dark and Light 1 | Hallowed<br>Buddy Mit 2nd Hit: Intervention | Kitchen Sink (TBN 2nd hit) |
| Wings Dark and Light 2 | Kitchen Sink | Living Dead<br>Buddy Mit 2nd Hit: TBN, Oblation |


## Approved import requirements

- Select the player's job, tank position, and co-tank job. Pairing changes
  actual assignments; own job and position alone are insufficient.
- Preserve both written MT/OT layouts where supplied. The P1/P2 swap note in
  GNBDRK and PLDDRK does not authorize inventing reverse P3–P5 source plans.
- Preserve P1's first/second Powder Mark invuln alternatives and the linked
  P3–P5 invuln routes. Do not allow independent choices that contradict the
  source's cross-phase requirements.
- Keep P4 7/1 Akh Morn optional, with solo order selecting personal versus
  buddy assignments. Retain the early-use note for the first Akh Morn.
- Anchor visible mechanics to their reviewed first hit; preserve explicit
  P5 second-hit personal and buddy instructions within those sequences.
- Preserve unspecified Kitchen Sink instructions and document source
  discrepancies instead of inventing cooldown lists or timing corrections.
- Tank plans supplement the party overlay. Hallowed Wings, Akh Morn and
  other party mechanics retain their party visibility and assignments.

These are the data and behavior requirements established by the review.
The controls and validation are implemented as described below.

## Implementation and verification

`import_fru_mitbutgood.py` imports the party grid and calls `fru_tanks.py` with
the same freshly fetched workbook. It emits twelve directed job/co-tank plans.
Each row copies its name/time from the reviewed encounter anchor; only the P5
second-hit continuation uses the retained second-hit time. The importer never
writes the encounter. Grid title checks and the catalog's ability registry
make moved rows or unknown actions fail rather than disappearing silently.

MT determines the opening main tank; OT determines the off tank. The co-tank
selector uses the existing paired-plan UI. There is no separate MT/OT route
selector. The remaining segmented controls select:

- **P1 invuln:** 1st or 2nd Powder Mark.
- **P3 strategy:** GNB/DRK chooses the standard invuln plan or Darkest Dance,
  with linked P4/P5 changes. WAR/PLD exposes the Hallowed-on-Dance tank swap
  only when PLD opens as MT.
- **P4 7/1 solo:** 1st or 2nd, relative to the selected player.

Preferences persist per sheet and unordered job pairing. Seat changes always
change opening duties; unavailable strategies resolve to their default.
Cheatsheet links carry the seat and choices, and PiP receives the same resolved
plan. Seat and conditional rows are filtered before rendering or Mit-only
filtering. The schema rejects unknown seats, choices, defaults, and conditions.

For GNBDRK/PLDDRK's source instruction to swap P1/P2, the reverse-duty ability
lists use the already reviewed job lists: WARDRK's DRK main column, WARGNB's
GNB off column, and WARPLD's PLD off column. This implements the source's swap
instruction; it does not claim those tabs contain separately written reverse
layouts. P3 onward retains the pairing's specific job duties. In particular,
GNB opening as the off tank and invulning P2 does not also receive Superbolide
at Black Halo: that route uses Kitchen Sink and DRK buddy mitigation.

GNB/DRK's Darkest Dance alternative changes P3, P4 and both P5 sequences
atomically. WAR/PLD's Hallowed-on-Dance route fixes PLD opening and the switch
to WAR holding Black Halo; the opening and later assignments cannot be chosen
in contradictory combinations. Kitchen Sink stays an explicit note-kind ability,
without an invented kit. P1 rich-text carry-overs and the Shake-first footnote
are retained.

P5 buddy mits and personal TBN render on labelled second-hit lines, including
with notes hidden. P4 solo/early timing tags survive the icon-only cheatsheet.
Regression tests enumerate all routes and both P1/7/1 branches, verify linked
invulns and second-hit targeting, and reject malformed conditions. The Python
importer tests cover rich-text semantics and action parsing. React server-render
checks cover the main selector page, share-link parameters, and the three
MitView layouts. Live Chrome verification followed on 2026-09-13, as recorded below.

### Live Chrome verification, 2026-09-13

Verified route changes through native Chrome controls: the GNB/DRK alternative
updates Black Halo/Darkest Dance and both P5 sequences; selecting DRK-first
7/1 shows solo/early mitigation on Akh Morn 1 and buddy mitigation on Akh Morn 2.
Second-hit buddy and personal TBN lines remain visible with notes hidden.
The cheatsheet carries the current route, P1 invuln, 7/1 order, and Mit-only
preference; Full view restores them. All-phases and live PiP preserve the same
assignments. At 300% browser zoom the controls wrap without visible horizontal
page overflow; zoom was restored afterward.

The browser check caught a shared-link persistence bug: changing phase removed
the URL before the linked role/job had been stored, so reload returned to setup.
Full view now persists the resolved role/job/co-tank and strategy choices;
cheatsheet stays read-only. Changing job/co-tank also clears stale shared URL
parameters. Repeated the shared-link → phase change → reload flow successfully
with DRK/GNB, the alternate route, Powder Mark 2, and DRK-first 7/1.

### Order-control refinement

The focused controls now read Role, Job, Other tank, Mits. Tank-route and
order choices use segmented controls. P1 invuln is 1st/2nd; P4 7/1 solo is
Off/1st/2nd, relative to the selected player's job. The stored first-solo job
is unchanged so both players and shared links still describe the same plan.
Route segments use MT/OT with concise alternative labels and source details
in tooltips. In live Chrome, switching DRK from 1st to 2nd moved buddy duties
to Akh Morn 1 and solo duties to Akh Morn 2 as expected.

### Seat-driven opening duties

Removed the duplicate MT/OT route segments. MT is the opening main tank and OT
is the off tank. Pair-specific P3 alternatives remain independent strategy
controls, with their later-phase invulns linked. P1 and P4 order controls retain
1st/2nd labels. Regression coverage checks seat changes and strategy visibility.

Strategy controls follow phase order: P1 invuln, applicable P3 strategy, P4 7/1.
P4 always selects a solo order; the first source-listed tank defaults to first.

### P3 alternatives removed

The current viewer and importer use only the standard P3 plan. GNB/DRK's
Darkest Dance invuln branch and WAR/PLD's Hallowed-on-Dance swap are excluded,
including their linked P4/P5 changes. Earlier alternative tables remain source
research, not implemented choices. Controls are P1 invuln and P4 7/1 only.
