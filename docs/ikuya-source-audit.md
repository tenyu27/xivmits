# Ikuya source audit, 23 September 2026

Compared the P1–P5 and Omnitank tabs of [Ikuya Mitty](https://docs.google.com/spreadsheets/d/10C3ytfH3irHqkb45rchIq5oqdAs-v_OKTj57M-Twi3k/edit), version 6.1 dated 20 September, in Chrome and through its XLSX export.

P1 has one Addle press, on the first Double-Trouble Trap, carried into the first Light of Judgment. There is no second P1 Addle assignment. The source changelog records removing that second use in version 2.3.

The reported SMN problem was a note shown on an unassigned row. Press-timing notes for P1 Light of Judgment and P5 Forsaken now belong to fresh actions. They disappear for jobs without those actions and do not instruct players to re-press carry-overs. Accretions advice is split between non-healers, healers, AST, and WHM. Phase-wide targeted-mit caveats remain conditional on the viewer having a relevant ability.

Updated source assignments:

- P2 WHM: Temperance and Divine Caress at Tower V, Temperance carried at VI, Bell at VII and carried at VIII.
- P2 AST: Neutral Sect at Tower V instead of VI.
- P3 OT: Reprisal starts at the first Thunder III instead of the preceding Stray Flames/Tsunami.
- Tank plans: added the first Thunder III Rampart timing note and the WAR/DRK P5 invulnerability-swap advice.

Omnitank phase blocks, notes, and priority headers now follow headings rather than fixed worksheet row numbers. The source inserted two rows before P4; the old importer could no longer read the current workbook. Encounter mechanics and times were not changed.

Chrome verification covered all five phases for all 21 supported jobs, including both tank and melee seats, 31 job/seat combinations. Melee seats intentionally share the job-free Feint plan. Checked caster Addle/carry-over output, job-specific extras, healer advice, and tank plans against the source columns.

Validation: lint, production build, 58 JavaScript tests, and 31 Python importer tests passed. New regressions cover blank-row and carry-over note scoping, all-job rendered note visibility, healer-specific Accretions advice, P1 Addle, tank notes, and inserted Omnitank rows.
