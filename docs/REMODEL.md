# Remodel progress

Working notes for the `remodel` branch. Read [AGENTS.md](../AGENTS.md) first for
the project's shape and rules; this file only covers what changed here, what is
deliberately unfinished, and the traps worth knowing before touching it.

## Why

Two problems, one branch.

The repo was a single Vite app, and two more sites are planned —
`analyze.xivmits.com` and `parse.xivmits.com` as Cloudflare Workers — with
nowhere to put shared domain logic.

More importantly, **the fight data was derived from mit sheets.** Each importer
built `encounter.json` from whichever spreadsheet it was reading, so a fight's
timeline was only as complete as one author's mit plan, and its timings were
that author's estimates. That inverts the real relationship: a fight exists
independently of anyone's plan for it.

## The model now

**Logs are the source of truth for what happens and when. A mit sheet is an
overlay that references it.**

```
FFLogs report ──> encounter.json        mechanics, ids, times, ability ids
                        ▲
                        │ mechanicId
                  sheets/*.json         only: who presses what
```

- `encounter.json` owns the timeline. An importer **never** writes it.
- A sheet row is `{mechanicId, note?, assignments}` — no names, no times.
- Mechanic ids derive from the log: `p<phase>-<slug of primary FFLogs ability
  name>-<occurrence>`. Primary = the cast bar where one exists, else the damage
  ability.
- `abilities.json` maps every wording a sheet uses onto one ability carrying the
  game's Action row id — the number FFLogs reports as `abilityGameID`.

This is directional, not frozen. Logs write the encounter; sheets only read it.
Re-reconciling against better logs is expected.

## State

| Area | Status |
|---|---|
| Monorepo + Yarn 4 | done |
| DMU encounter reconciled | done — all 5 phases |
| FRU encounter | P1 reviewed; P2 reconciled from six clears for review; P3 start anchored at 7:25; P3–P5 mechanics still sheet-derived. See [FRU.md](FRU.md) |
| TOP encounter | **not started** — still sheet-derived, no ability ids or mechanic times |
| Importers bind to encounter | done — all 4 |
| Google Sheets as source | done — all 4 fetch by id |
| Ability registry | done — 97 abilities, 86 with game action ids |
| Status → ability mapping | **abandoned, see below** |
| `apps/analyze`, `apps/parse` | not started, deliberately |
| `packages/fflogs`, `packages/analysis` | not started; `scripts/fflogs.py` is the current client |

### DMU reconciliation detail

| Phase | Start | Rows | Clears used |
|---|---|---|---|
| p1 | 0:00 | 15 + 4 minor | 2 |
| p2 | 3:29 | 13 + 1 minor | 2 |
| p3 | 7:08 | 28 + 3 minor | 2 |
| p4 | 12:21 | 10 | 12 |
| p5 | 15:04 | 22 | 12 |

**Phase lengths are not all fixed.** Measured across 100 ranked clears:

| Phase | Length | Note |
|---|---|---|
| p1, p2, p4 | fixed | p4 is 163s in all 12 sampled |
| p3 | 296–313s | ends on a phase push, so it varies with DPS |
| p5 | 206–225s | ends on the kill |

The two logs used for P1–P3 sit at the maximum: `q2Xx` has the longest P3 in the
ranked set (313.3s) and `DK6c` ties the longest P5 (224.5s), so the reconciled
timeline covers the slowest case a clearing team sees.

**P5 is complete.** `Forsaken Null` is its enrage, recorded at **3:14, the
cast** — 3:14.25 median across 15 logs, range 3:14.05–3:14.33, the tightest
timing in the fight. Not for P3's reason: nothing goes untargetable here, it is
simply the end of the phase, so cast or damage makes no practical difference.
Faster teams kill before it, which is why it is absent from all 12 fast clears;
its presence is correct, not an artifact.

**P3's enrage is recorded, from two wipe logs.** `Meteor` (49752) and a second
`Bowels of Agony` (49753 — not the 47858 used earlier in the phase) cast
together at 5:01 and land lethal at ~5:06. The row is timed at **5:01, the cast
start**, because that is when the boss goes untargetable and nothing further can
be mitigated; the damage is unavoidable either way. Both wipe logs confirm
nothing happens between 4:44 and 5:01. Marked `minor`, since no sheet mits it.

Note `fightRankings` lists only kills, so the enrage cannot be reached from the
API — those two logs were supplied by hand.

**P1–P3 rest on only two clears.** P4 and P5 used twelve, which is what revealed
that `Flood of Naught` is a multi-part cast rather than a per-pull branch, and
that `Stray Apocalypse` deals no damage at all. The same sample would likely
sharpen P1–P3 — P3 especially, where the two logs disagreed on Earthquake count
and on whether `Shocking Impact` or `Shockwave` fired.

Enforced by `packages/encounter-data/tests/catalog.test.ts`: the `anchored` list
asserts every mechanic in the named phases has a `time` and at least one ability
id. **Extend that list as you reconcile a phase** — it is what stops a future
edit from quietly dropping the anchors.

## Traps

**Re-running an importer reflects the spreadsheet, not your edits.** A hand edit
to a sheet JSON is lost on the next import. When Ikuya's "7-8th Set" actions
needed splitting onto their own beam rows, the rule had to go *into* the
importer (`spread_parked_actions`) to survive. If you fix sheet data by hand,
ask where the rule belongs.

**`abilities.json` is generated.** `scripts/fetch_icons.py` rebuilds it from
XIVAPI. Anything hand-added to it is lost. That is why the status mapping was
kept in a separate file — and then dropped.

**LPDU keeps a hand-written row→mechanic table.** `MECHANICS` in
`scripts/import_dmu_lpdu.py` maps spreadsheet rows to mechanic ids by position.
Renaming a mechanic id breaks it, and nothing in CI catches it because CI never
runs the importers. It went stale exactly this way during the id migration (45
of 79 ids).

**LPDU's tank plans come from a second spreadsheet.** `TANK_SHEET_ID`. Without
it the importer refuses rather than dropping `tankMits` silently.

**Google Sheets export needs link sharing.** `…/export?format=xlsx` only works
on "anyone with the link". Tabs resolve by name; never by worksheet index —
part file numbering does not follow tab order (LPDU's P5 is not next to P1–P4).

**Tank plans keep their own clock.** The Ikuya Omnitank tab times and names its
rows on the workbook's clock, in the workbook's wording, so after the encounter
was reconciled they disagreed with the party rows they render beside — "Thunder
III" next to "Thunder III (2nd Set)", tens of seconds off. `align_tank_rows` in
the ikuya importer maps a row onto the mechanic family it describes and makes it
adopt that mechanic's id, name and time. Only `Autos` stays bespoke — a
phase-top cue rather than a mechanic. LPDU needs only the timings straightened,
via `snap_tank_times`, because its importer already reads the encounter.

Four knobs in the ikuya importer drive that:

| | |
|---|---|
| `TANK_FAMILIES` | workbook wording → the encounter mechanic family it names |
| `TANK_KEEP_NAME` | rows that are not a mechanic and keep their wording |
| `TANK_ROW_TAGS` | a call the workbook implies by naming a row (`Fell Forces III` → `Share 3rd hit`) |
| `TANK_CARRIED` | a long cooldown re-listed on a later row, which is the same press still running (`Rampart` on the shared third auto) |

**A personal row's time decides whether it folds.** MitView drops a personal
row's heading when it names the mechanic it sits under — otherwise the name
prints twice, once for the party row and once beneath it. That fold needs the
row's time to agree with its anchor, which is why both importers now snap tank
rows onto the encounter's clock (`align_tank_rows` for ikuya, `snap_tank_times`
for LPDU). Rows that genuinely name something else keep their heading: LPDU's
`HP Reduction`, `3rd in Line Tank`, `Autos N`, and ikuya's `Autos`.

**A tank row's tag belongs to that row.** It is drawn beside the Personal label,
never lifted onto the mechanic heading: the call describes one press, and a
mechanic can carry several rows that each need their own - the Solo line and the
Share-3rd-hit line of the same Fell Forces. A row is dropped only when it holds
nothing at all; one holding only carried-over actions still says that cooldown
covers this mechanic.

**Anchors point at the encounter, not the sheet.** `resolveSheet` renders every
mechanic in a phase, so a personal row may sit under one this sheet assigns
nobody to — ikuya's tanks cover busters their party grid leaves blank.
`validateCatalog` checks `after` against the encounter for that reason.

**Sheets can disagree, legitimately.** Ikuya assigns different mits to each
black-hole beam; LPDU treats the set as one. The encounter carries the finer
granularity and a sheet simply leaves rows blank.

**Never suppress importer output.** `bind_sheet` refuses a row it cannot match
and says which; running an importer with `>/dev/null` turns that into a silent
no-op and the sheet simply keeps its previous content. A cascading string
replacement left two aliases pointing at the same beam, the import failed, and
the stale file looked like earlier work had been reverted.

## The abandoned status mapping

The analyzer will need to match a logged hit's mitigations to a sheet's recorded
mits. Damage events carry a `buffs` field — the status ids on the target at the
moment of the hit — which is the right input.

An attempt derived status→ability links by pairing each `applybuff` with the
caster's most recent cast. **It produced wrong answers and was deleted.**
Co-timing cannot distinguish "granted this status" from "pressed at the same
moment", so it credited `Arms Up` to Bulwark (it is Passage of Arms only) and
`Galvanize` to Concitation (which grants its own barrier).

Do it by **reading each ability's description**, not by correlating timings.

Things that pass worth keeping:

- FFLogs status id = `1000000 + the game's Status row id`. Verified:
  `Accretion` row 1604 → `1001604`, seen in a real DMU log.
- Real name mismatches exist and matter: Adloquium applies **Catalyze**,
  Expedient applies **Desperate Measures** + **Expedience**, Celestial
  Intersection applies **Intersection**, Bloodwhetting applies **Stem the
  Flow**/**Stem the Tide**.
- Some abilities cannot be identified by status at all. `Deployment Tactics`
  spreads an existing shield, and a crit Adloquium also yields Catalyze, so
  `Galvanize`/`Catalyze` need the cast. `Zoe` applies nothing — it enlarges the
  next Eukrasian Prognosis shield, so only its cast reveals it.
- `Neutral Sect` is *not* in that class: it does put a shield on the party.
  `1001892` is the AST's own window, `1001921` the party shield.
- Statuses no cast pairing can reach: enemy debuffs (`Reprisal`, `Feint`,
  `Addle`) land on the boss; pet shields (`Seraphic Veil`) come from the pet;
  LB3 (`Last Bastion`, `Land Waker`) has no ordinary cast.
- `Well Fed` is food. Not a mitigation, and on everyone all pull.

The `status` field on the ability schema is kept for verified ids later.

## Open questions

- Bundle grew 595 → 614 kB: `abilities.json` rides along in the client catalog
  though the UI does not read it yet. Exclude until it does?
- CI has never run this workflow. `main` still carries the pre-monorepo one, so
  Corepack, Yarn 4 and Node 24 have only ever been exercised locally. Open a
  pull request before merging: the workflow runs on `pull_request` with every
  Pages step gated off, which tests the whole path without deploying.
- Reconcile FRU and TOP. TOP has no mechanic times, so it is the bigger job.
- Sheets still reference abilities by `name`. The registry makes migrating to
  `ability` ids safe, but 3089 references, the schema, `MitView` and four
  importers all move together.
- LPDU's AST rows list `Celestial Intersection` twice at Ultimate Embrace, once
  "On the MT" and once "Both tanks" — faithful to the sheet's own shorthand,
  where the second supersedes the first.

## Commands

```
yarn dev            # site, apps/web
yarn build          # what CI builds; invalid data fails here
yarn test           # data contract: anchored phases, ability registry
yarn typecheck
yarn lint

python3 scripts/import_dmu_ikuya.py        # fetches from Google Sheets, no args
python3 scripts/import_dmu_lpdu.py         # needs TANK_SHEET_ID
python3 scripts/fetch_icons.py             # rebuilds icons + abilities.json
```

Importers need no local files. `scripts/fflogs.py` reads `FFLOGS_CLIENTID` and
`FFLOGS_CLIENTSECRET` from a gitignored `.env`; the token is never written to
disk.
