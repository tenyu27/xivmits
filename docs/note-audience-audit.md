# Note audience audit, 24 September 2026

Follow-up to the Ikuya note-placement fix. Reviewed phase notes, mechanic notes, assignments, and importer placement across all five committed sheets.

Corrected:

- TOP P2 Feint/Addle advice is limited to melee and casters. Optimized Meteor coverage and P6 Wave Cannon timing notes follow fresh assignments, so job-filtered extras do not leave notes behind. The P5 healer warning appears with each healer's first assignment; its tank-pairing condition is retained.
- DSR P5 tank-buster advice follows the healer's Assist Tanks assignment. Rewind's shield timing follows only the first Brightwing shields; the bait order remains visible to everyone.
- FRU's P1 buff-cap warning is limited to tanks and healers. P4 tank strategy is limited to tanks; the ranged relocation instruction remains on ranged Party Mit.
- LPDU wall priority, tank LB priority, boss swaps, and the Paladin tank-seat rule are limited to tanks.

Phase and mechanic notes support `noteRoles` for strategy guidance that applies without an assigned action. Assignment instructions continue to use action notes. The shared renderer applies audiences in normal and compact views; Notes Hide, icon-only, and cheatsheet views still suppress notes.

Chrome checks confirmed the affected notes appear for relevant jobs and disappear for unrelated jobs. Automated rendering checks cover every supported job, both full and compact views, phase and list layouts, Notes Hide, and the cheatsheet. Lint, build, 63 JavaScript tests, and 32 Python tests passed.

Resolved with the user's identification: [LPDU P3 I32–I38](https://docs.google.com/spreadsheets/d/1aA_qF_UsoS51MCDZ4PwQHhprpK7eGO8TXOdZ7pQlkV0/edit#gid=247845947&range=I32:I38) shows Passage of Arms. Added PLD-only OT assignments on the two Stack/Roles rows, with an instruction to choose one use when it is the stack. Removed the unrelated generic beam instruction from Thunder III. Registered XIVAPI Action 7385 and bundled icon 002515.

Final source reproduction caught two stale LPDU fake-melee Addle placements. Chrome confirmed P4 Z26 is empty, P5 Z8 assigns Addle to Ultima Repeater 1, and P5 Z32 assigns it to Forsaken 1. Moved the conditional Addles from P4 Ultima Upsurge 2 and P5 Celestriad to those source rows. The entire LPDU party overlay and the entire Ikuya sheet now reproduce exactly from the audited workbooks.
