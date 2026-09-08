# XIVMits — PRD

**Domain:** xivmits.com · **Platform:** static web on GitHub Pages · **Version:** V1
**Audience:** FFXIV Savage / Ultimate raiders · **Free, no accounts, no backend**

Companion to [DESIGN.md](./DESIGN.md). This defines *what* ships; that defines *how it looks*.

---

## 1. Vision

Mit plans live in spreadsheets. Spreadsheets are good for *building* a plan, bad for *reading* one mid-prog: they hold all 8 players' assignments at once.

A player needs three things: current phase, mechanics needing mit, what *they* press.

XIVMits takes an existing community-maintained mit sheet — the one a group or the wider community has agreed on — and renders it role-focused.

Flow: pick fight → pick sheet → pick your role/job → see your assignments by phase → optionally open Picture-in-Picture.

XIVMits is a **viewer, not a planner**. Planners optimize for constructing an 8-player plan. XIVMits optimizes for consuming one.

**Core question:** *What do I need to mit during this phase?* Anything not answering that is secondary or cut.

Guiding rule: **choose your fight, choose your sheet, choose yourself, then get out of the way.**

---

## 2. Problem

A typical mit spreadsheet holds mechanics, timestamps, both tanks, both healers, melee, ranged, casters, notes, phases, healing assignments, group-specific info. During prog that causes:

- **Too much info** — a SGE does not need WAR/PLD/SCH/DNC/PCT/VPR/DRG columns.
- **Horizontal scrolling** — bad on one monitor, small second monitor, phone, tablet, between pulls.
- **Slow phase navigation** — players re-reference the phase they're practicing constantly; it should be one click.
- **Poor overlay** — a full spreadsheet window next to FFXIV wastes screen. A small always-on-top window with only your assignments is better.

---

## 3. Goals / Non-Goals

**V1 goals:** open xivmits.com → your assignments in seconds. Remove irrelevant party info. Near-instant phase switching. Compact PiP over FFXIV. No login, no setup. Fully static. Sheets added via structured repo data.

**Non-goals (V1):** mit planner, spreadsheet editor, collaborative planning, static-management platform, healing calculator, damage sim, FFLogs analyzer, ACT/Dalamud plugin, encounter tracker, timeline sync, discussion platform, UGC platform, accounts.

Do not add these merely because other mit tools have them.

---

## 4. Navigation Model

```text
Fight → Mit Sheet → Role / Job → Phase → Assignments
```

Shallow. No extra layers unless necessary.

### Homepage

The app *is* the homepage — a reference utility, not a dashboard.

```text
XIVMits                                    Theme [System ▾]

What do I mit?
Pick a community mit sheet and get just your presses, phase by phase.

Fight      [Dancing Mad (Ultimate) ▾]
Mit sheet  [Ikuya Mitty            ▾]
Role [H ▾]   Job [SGE ▾]

[View Mits →]

Made by tenyu · Support on Ko-fi          Have a question or feedback?
FINAL FANTASY is a registered trademark of Square Enix Holdings Co., Ltd.
```

The headline is the user's own question, not a description of the product. The
subheadline is the one-line answer to what the tool does, so a first-time
visitor knows what they are about to get before picking a role.

Each selector unlocks the next; `View Mits` unlocks when complete. Selections apply immediately where practical — the button may become unnecessary, but V1 keeps it for clarity.

### Fight

Top-level encounter: id, name, optional shortName, type (Savage / Ultimate / Criterion / Other). Category filtering not needed while the encounter count is small.

### Mit Sheet

One encounter may have several sheets — each is one complete party plan agreed on by a group or the community.

Examples: Community Standard, Week 1 Sheet, Melee LB Strat, NAUR Static.

Metadata: id, fightId, name, optional author/source link/description, updated date, phases, slots, assignments. The dropdown shows the short name. Updated dates remain maintainer metadata and do not appear in the viewer.

### Role / Job

Two selectors, because they answer different questions: **role** is the seat you
occupy in the plan (`MT`, `P`), **job** is what you actually play (`GNB`).

The plan is written once for whoever stands in a slot, so it says `Party Mit` —
which is Heart of Light for a Gunbreaker and Shake It Off for a Warrior. Without
the job that name cannot become a concrete button, and 61 of the DMU sheet's 510
assignments are exactly that kind of generic instruction. Asking one more
question turns all of them into a named ability with an icon.

The Ikuya sheet's checked `Extras` column works the same way. It adds
`Extra (RDM/MCH)` to each DPS seat for that mechanic. The job resolver turns it
into Magick Barrier for RDM or Dismantle for MCH and drops it for other jobs.

**Job options are filtered by the seat**: `MT`/`OT` offer the four tanks,
`H` the four healers (one seat — the job is the whole choice), and DPS is split
three ways — `M1`/`M2` the six melee, `P` the three physical ranged, `C` the
four casters. A seat can never show a job that cannot sit in it.

**A job is usually required.** `View Mits` stays disabled until one is chosen,
and a seat reached by URL without a job shows a prompt rather than a plan.
Without the job, `Party Mit` cannot resolve to a real ability and a job-qualified
line cannot be filtered — so a jobless view is a worse plan, not a faster one.
Changing seat to one the current job cannot fill clears the job rather than
silently keeping an impossible pairing. **The exception is a melee seat**: every
melee job mitigates identically (Feint, and nothing generic), so the job
selector is disabled and shows `--`, and the view renders with no job.

Seats come from the sheet. Where it names positions (`MT`, `P`), those are the
seats directly. Where it names *jobs* instead — the DMU sheet's healer columns
are `WHM`/`AST`/`SCH`/`SGE`, because every healer kit mitigates differently —
the seat is a label and the **job picks which column to read**: `H` + Sage reads
the Sage column. There is one healer seat, not two, because a job-keyed
sheet does not distinguish them. Until a job is chosen for such a seat there is
genuinely nothing to show, and the view says so.

A sheet declares its own **slots**. A slot is an opaque ID plus an optional `job` label, so one data model covers every way a sheet divides the party — no separate interfaces, no fixed enum.

| Sheet style | Slot IDs | Rendered |
|---|---|---|
| Position-based | `MT`, `OT`, `H1`, `H2`, `M1`, `M2`, `R1`, `R2` | `H2` |
| Job-based | `SGE` (with `job: "SGE"`) | `SGE` |
| Mixed (the DMU/Ikuya case) | `MT`, `OT`, `WHM`, `AST`, `SCH`, `SGE`, `M1`, `M2`, `P`, `C` | `MT`, `SGE`, `P` |

Label rule: show `ID · job` when the two differ (**H · SGE**), the ID alone when they match or no job is set (**SGE**, **P**). Mixed sheets are the common real-world case — tanks and DPS are assigned by position because the plan is the same whatever job stands there, while healers are assigned by job because their kits are not interchangeable.

Slot IDs are validated against the sheet's own `slots` array at build time. An assignment referencing an undeclared slot fails the build.

---

## 5. Focused Mit View

Primary screen.

```text
XIVMits                                    Theme [System ▾]

Ultimate · Ikuya Mitty                       Change fight/sheet
Dancing Mad (Ultimate)

Role [H ▾]  Job [SGE ▾]   Show [Icon + text]  Notes ( )

P1   P2   [P3]   P4   P5                         [Pop out]

Exdeath & Chaos                               3 assigned
──────────────────────────────────────────────────────
ULTIMATE RELATIVITY                                0:23
Kerachole

SHELL CRUSHER                                      1:14
Holos
Panhaima
  Still active · Party Mit (GNB/DRK)

APOCALYPSE                                         1:58
Kerachole
  Hold until the second set of towers resolves.
──────────────────────────────────────────────────────
                                        View original sheet
```

Readability over density. The phase heading names the phase and nothing else.

The role selector stays on this screen. Swapping between two jobs you play is a dropdown change, not a trip back to selection.

### Phase navigation

The most important interaction. Must stay visible, obvious, compact, usable in PiP and on mobile.

Requirements: one click changes phase; no route transition, spinner, server request, or slowing animation; current phase strongly indicated; selection persists where practical.

Optional (not required for launch): number keys → phase N, ←/→ → prev/next.

### Flexible phase naming

Don't assume P1–P4. Each phase has a short label plus optional long name: `P1, P2A, P2B, Intermission, P3, Enrage` or `P3 — Ultimate Relativity`. Short label drives tabs and PiP; long name is the page heading.

### Mechanics

Fields: `id`, `name`, and an optional `time`. Order is the array order inside the phase — deterministic, no sort key to keep in sync.

Raiders identify actions by mechanic name, not timestamp. Hierarchy: **mechanic name → mitigation → optional timestamp** — never timestamp-first.

### Assignments

A mechanic's `assignments` map slot ID → an ordered list of **actions**. An action is a plain-text ability name plus optional annotation:

| Field | Required | Purpose |
|---|---|---|
| `name` | yes | The ability, as the raider would say it — `Kerachole`, `Party Mit (GNB/DRK)` |
| `note` | no | Timing or condition — *"Use as Kefka re-centres for the first Graven Image."* |
| `noteLink` | no | HTTP(S) link to a timing example (clip, timestamped VOD) |
| `carryOver` | no | This action was pressed earlier and is still ticking here |

Ability IDs are not required in V1; the name is the identity.

**Carry-over** exists because mitigation is a duration, not an event. A 90s party mit pressed before Mystery Magic is still covering Wave Cannon, and a plan that only lists the press moment reads as if the later mechanic is unmitigated. A carry-over action renders de-emphasised behind a *Still active* label — present so the player knows the mechanic is covered, quiet so it is never confused with something to press now.

A `note` is annotation, never load-bearing. The action name alone must be actionable; the note only refines *when*.

### Every mechanic, only your mits

Show **every mechanic in the phase**, and under each one only what *this* player
presses. A mechanic with nothing assigned keeps its name and timestamp and
leaves the area beneath it blank.

Showing only assigned mechanics reads as tighter, and it is wrong. Phases repeat
mechanic names — DMU P1 has `Light of Judgment` at 1:03 and 2:12 and three
separate `Double-Trouble Trap`s. A list that shows two of them and hides the
rest cannot tell you *which* one you are covering. The blanks are what make the
list a timeline you can find your place in, and finding your place is the point
(§1). Blank rows are cheap; ambiguity mid-pull is not.

**Job-qualified lines are still dropped.** `Party Mit (GNB/DRK)` is an
instruction to whoever is the GNB or DRK; for a Warrior it is not an assignment,
so the line goes — but the mechanic stays, blank. With no job chosen nothing is
dropped, because there is nothing to judge against. If a phase has six damage events and SGE covers three, show those three. Maximizes glanceability. An optional "show all mechanics" toggle is a future addition.

### Ability icons

Icons aid recognition in combat: mid-pull you match a shape on a hotbar faster
than you read a word. They sit inline before the action name at 20px.

**The text is the interface; the icon is an accelerator.** Every action name
must read perfectly with icons stripped, because for many of them there is no
icon to show. Of 34 distinct action names in the DMU sheet, 26 resolve to a game
action. The other eight — `Party Mit (GNB/DRK)`, `Assist Tanks`, `Avoid
HP-restoring abilities`, `LB3` — describe a *decision*, not a single button, and
deliberately render text-only. A layout that looks broken without an icon is a
bug, not a missing asset.

Icons are therefore `alt=""` and `aria-hidden`, never the sole content of
anything, and occupy a fixed 20px box so a missing one cannot reflow the row.

**Sourcing** is maintainer-side and offline, like sheet conversion. See §9.

---

## 6. Picture-in-Picture

Signature feature. Uses the **Document Picture-in-Picture API** — arbitrary HTML in an always-on-top window, no video wrapper. Requires HTTPS and user activation; GitHub Pages supports HTTPS on correctly configured custom domains.

PiP is a combat view, not a shrunk website.

```text
┌──────────────────────────────┐
│ SGE    P1 P2 [P3] P4 P5      │
├──────────────────────────────┤
│ ULTIMATE RELATIVITY          │
│ Kerachole                    │
│                              │
│ SHELL CRUSHER                │
│ Holos                        │
│ Panhaima                     │
│                              │
│ APOCALYPSE                   │
│ Kerachole                    │
└──────────────────────────────┘
```

**Keep:** large mechanic names, large mit names/icons, phase buttons, high contrast, minimal chrome, the carry-over marker.
**Drop:** fight/sheet selection, timestamps, note links, metadata, source links, footer, theme control, extra controls. The browser's native window chrome handles unrestricted resizing. Action notes stay — the timing they carry is exactly what you need mid-pull — but everything that only matters while *choosing* a sheet goes.

Phase switching stays available in PiP, and main window + PiP stay synchronized in both directions: one React tree renders both views through a portal into the PiP document, so there is no second copy of the state to drift.

The PiP window inherits the **resolved** theme of the opener, not its own OS preference — a light-mode PiP over a dark-mode page reads as a bug. Closing the tab, or leaving the focused view, closes the PiP window with it.

**Support:** feature-detect `"documentPictureInPicture" in window`. Supported → show **Pop out**. Unsupported → hide it or say *"Picture-in-Picture isn't supported by this browser."* The normal view must remain fully functional without PiP.

---

## 7. Persistence & Sharing

`localStorage` remembers local selections, keyed so a player with two statics on two sheets keeps a separate role in each:

| Key | Shape | Holds |
|---|---|---|
| `lastFight` | string | last fight ID |
| `lastSheetByFight` | `{ [fightId]: sheetId }` | last sheet per fight |
| `lastRoleBySheet` | `{ "fight/sheet": slotId }` | last role per sheet |
| `lastPhaseBySheet` | `{ "fight/sheet": phaseId }` | last phase per sheet |
| `layout` | `tabs` \| `list` | by-phase tabs or one scrolling list of all phases |
| `theme` | `system` \| `light` \| `dark` | theme choice |

Every read and write is wrapped — a browser with storage blocked loses persistence and nothing else. A stored value that no longer exists in the data (a renamed slot, a deleted sheet) is discarded on read rather than trusted. Nothing is uploaded; no account.

Sheets get stable URLs:

```text
xivmits.com/dmu/community/
xivmits.com/dmu/community/?role=H&phase=P3   # optional
```

The URL identifies encounter + sheet. Role stays local so the whole group shares one link; query params exist for direct links — a raid lead pointing eight people at P3, or someone linking a specific role while explaining it.

Query params are a **handoff, not a mode**: they seed the initial selection, then the app rewrites the URL back to the clean sheet path on the first role or phase change. The link that got you here does not keep overriding what you pick. Stored preferences lose to an explicit query param on arrival, and win otherwise.

Keep URL state human-readable.

**Workflow:** raid lead posts one sheet link in Discord → everyone opens it → first visit asks *"Who are you?"* → they pick **H · SGE** → remembered locally → future visits to that sheet link open their assignments. Visits to the root path always show the selection screen with the saved fight, sheet, role and job prepopulated. Zero signup.

---

## 8. Design

Mobile-first and responsive: desktop (primary + PiP launch), small second monitor, mobile, tablet. Reading your own assignments must never require horizontal scrolling.

Aesthetic: simple, dark-first, clean, high contrast, utilitarian, slightly game-adjacent without being themed. WTFDIG is the reference point — content selection ahead of decoration.

Avoid: hero illustrations, decorative gradients, complex nav, dashboard cards, marketing sections, heavy animation, ornamental borders.

Themes: system / dark / light, chosen from an icon control in the header and stored in `localStorage`. The stored choice is applied by an inline script in `index.html` before first paint, so there is no flash of the wrong theme. Dark mode needs excellent contrast, and the PiP window follows the resolved theme of the page that opened it.

**Accessibility:** semantic buttons, keyboard-accessible selectors, visible focus states, adequate contrast, no color-only information, scalable text, ability names readable without icons.

**Empty states:** no assignments for this role/phase → *"No assigned mits for this phase."* No sheet data → *"No mitigation data available for this phase."* Never an unexplained empty list.

**Errors:** unknown fight, sheet, or over-deep URL → the selection screen with *"Mit sheet not found."* and a **Change fight/sheet** action that clears the bad URL. Stored role no longer in the sheet → discard it and re-prompt. PiP unsupported → the button is not rendered and the page works unchanged; PiP refused after being offered → an inline message, never a dead button. Malformed data → build-time validation fails deployment.

Every failure resolves to a working screen with a way forward. There is no error state in this app that a player can get stuck in, because there is nothing to get stuck on — the worst case is picking a sheet again.

---

## 9. Data Architecture

Data lives in the repo, split per encounter/sheet to reduce merge conflicts and ease contributions:

```text
data/fights/
  dmu/
    fight.json      # the encounter and its phases
    ikuya.json      # one complete party plan
    naur.json
  fru/
    fight.json
    sheet-a.json
```

Path *is* identity: `data/fights/<fightId>/fight.json` and `data/fights/<fightId>/<sheetId>.json`. A file whose `id` disagrees with its directory fails the build, so a sheet can never be reachable at a URL that does not match its own data.

### Fight

```json
{
  "id": "dmu",
  "name": "Dancing Mad (Ultimate)",
  "shortName": "DMU",
  "type": "Ultimate",
  "phases": [
    { "id": "p1", "label": "P1", "name": "Kefka" },
    { "id": "p2", "label": "P2", "name": "Forsaken Kefka" },
    { "id": "p3", "label": "P3", "name": "Exdeath & Chaos" },
    { "id": "p4", "label": "P4", "name": "Kefka Says" },
    { "id": "p5", "label": "P5", "name": "Kefka Reimagined" }
  ]
}
```

`label` is the tab text and must stay short — it has to fit a 280px PiP window. `name` is the phase heading in the full view and may be the boss name rather than a number; players say "Exdeath and Chaos", not "phase three".

The fight owns the phase list. Sheets reference phase IDs but never invent them, so every sheet for one encounter has the same tab row in the same order.

### Mit sheet

```json
{
  "id": "ikuya",
  "fightId": "dmu",
  "name": "Ikuya Mitty",
  "author": "Ikuya Kirishima",
  "updated": "2026-09-07",
  "description": "P1–P5 from Ikuya Kirishima's mitigation plan.",
  "sourceFile": "Ikuya Mitty (DMU).xlsx",
  "sourceVersion": "6.0 (1 Sep)",
  "source": { "name": "Ikuya Mitty spreadsheet", "url": "https://..." },

  "slots": [
    { "id": "MT" },
    { "id": "OT" },
    { "id": "WHM", "job": "WHM", "role": "healer" },
    { "id": "SGE", "job": "SGE", "role": "healer" },
    { "id": "M1", "role": "melee" }, { "id": "M2", "role": "melee" },
    { "id": "P", "role": "ranged" }, { "id": "C", "role": "caster" }
  ],

  "phases": [
    {
      "id": "p3",
      "mechanics": [
        {
          "id": "p3-ultimate-relativity",
          "name": "Ultimate Relativity",
          "time": "0:23",
          "assignments": {
            "SGE": [{ "name": "Kerachole" }]
          }
        },
        {
          "id": "p3-shell-crusher",
          "name": "Shell Crusher",
          "time": "1:14",
          "assignments": {
            "SGE": [
              { "name": "Holos" },
              { "name": "Panhaima", "note": "Cast before the second hit lands." }
            ],
            "MT": [
              { "name": "Party Mit (GNB/DRK)", "carryOver": true }
            ]
          }
        }
      ]
    }
  ]
}
```

Every field beyond `id` / `fightId` / `name` / `updated` / `slots` / `phases` is optional. A sheet with nothing but mechanic names and assignments is a valid, complete sheet.

`sourceFile`, `sourceVersion`, and `updated` record which spreadsheet export this was converted from. They are provenance for the maintainer re-running a conversion, not user-facing copy.

### Validation

A Zod schema runs inside the Vite plugin that builds the catalog, so validation happens on `buildStart`, on every dev-server data change, and in CI — there is no path that ships unvalidated data. Schemas are `.strict()`: an unrecognised key is an error, not silently dropped, which catches a typo'd field before it silently renders nothing.

Checked:

- IDs are slugs; sheet and fight IDs match their file path;
- phase IDs, slot IDs, and mechanic IDs are unique within their file;
- every sheet phase ID exists in its fight;
- every assignment slot ID exists in the sheet's `slots`;
- `updated` is an ISO date; `time` is `M:SS`; `noteLink` and `source.url` are HTTP(S);
- at least one fight exists, and no two sheets share `fightId`/`id`.

Sheet phases are then sorted into the fight's phase order, so tab order comes from the encounter and cannot drift per sheet.

Broken plans fail the build, which fails deployment. Malformed data never reaches a player.

### Content management

No admin UI in V1. Sheets are added by editing data files → commit → PR → merge → GitHub Actions rebuild + deploy. An editor UI would need persistence infrastructure and greatly expand scope; the maintainer count is small enough that repo-managed content is simpler.

### Spreadsheet conversion

No runtime Google Sheets integration. Existing spreadsheets are converted manually into XIVMits data — avoiding Google APIs, auth, CORS, inconsistent sheet structures, runtime deps, and backend.

Conversion lives in `scripts/`, maintainer-side and run by hand: spreadsheet export → JSON → validate → commit → PR → Pages. `scripts/import_ikuya.py` is the worked example. These scripts are deliberately per-sheet rather than general — every spreadsheet lays its party out differently, and a one-off script that a human reads once beats a configurable importer nobody trusts.

### Ability icons

`scripts/fetch_icons.py` resolves action names against **XIVAPI v2**, downloads
each 40×40 PNG into `public/icons/`, and writes the name → filename map to
`data/icons.json`. Both are committed. **The site never calls XIVAPI at
runtime** — that would break the no-third-party-requests rule in §10, and would
make a phase switch depend on someone else's uptime.

Resolution is not a plain name lookup, because sheets do not write action names
the way the game does:

| Sheet writes | Resolves via |
|---|---|
| `Kerachole` | exact match |
| `Feint (Chaos)`, `Sun Sign (7-8th Set)` | strip the trailing parenthetical — it says *when*, not *what* |
| `Seraph`, `Spreadlo`, `Zoe Shields` | a small alias table (`Summon Seraph`, `Deployment Tactics`, `Zoe`) |
| `Party Mit (GNB/DRK)`, `LB3` | nothing — text-only by design |

A name search returns several rows: PvP variants, duty-action re-releases, and
unused rows pointing at placeholder icon `000405`. The script keeps only rows
with `IsPlayerAction` and a non-zero `ClassJobLevel`, discards the placeholder,
and takes the lowest row ID — the original action rather than a re-release.

The build fails if `data/icons.json` names a PNG that is not in `public/icons/`,
so a half-run import cannot ship broken images. Re-run the script after adding a
sheet; it prunes icons nothing references any more.

**Attribution.** Icons are the property of SQUARE ENIX, redistributed under the
[FFXIV Materials Usage License](https://support.na.square-enix.com/rule.php?id=5382).
They are game assets, not our work, and the repo says so.

### Source attribution

Each sheet may carry a source (`Source: Community Standard Spreadsheet`) and a **View original sheet** link — useful for the full party plan, verification, and discussion. Original stays secondary to the focused view.

Updated date, author, and source version are maintainer provenance and do not
appear in the viewer. Only the link back to the original sheet survives in the
focused view, and none of it appears in PiP.

---

## 10. Technology & Hosting

**Stack:** React 19 + TypeScript + Vite 8. Small footprint, simple static build, easy Pages deploy, good state handling, renders cleanly into the Document PiP DOM, no server assumptions. The React Compiler is on, so memoisation is not hand-written.

**Styling:** Mantine (`@mantine/core`, `@mantine/hooks`) is the design system, with `@tabler/icons-react` for icons. The palette and scale are defined once as a Mantine theme in `src/theme.ts`; `src/index.css` aliases the product tokens onto the CSS variables Mantine generates, so the tokens stay readable and the PiP document still resolves them. UI is built from Mantine components and style props — see DESIGN.md §2–5.

Hand-written CSS is the exception, not the default. It survives only where a prop cannot express the rule: pseudo-elements, sibling selectors, `text-transform`, sticky positioning, and the PiP compact layer. DESIGN.md §2 holds that list and the reason for each.

Explicitly not used, and not to be added: a second UI library, Tailwind, CSS-in-JS.

**State:** React state + `localStorage`. No state-management library — the entire app state is one `selection` object plus a theme string.

**Package manager:** Yarn, and only Yarn. `yarn.lock` is the one lockfile.

**Hosting:** GitHub Pages, custom domain `xivmits.com` with HTTPS.

```text
repo → GitHub Actions → yarn install → yarn build → dist/ → GitHub Pages → https://xivmits.com
```

**Routing:** all fights and sheets are known at build time, so the build **emits a static route per sheet** (`/dmu/ikuya/index.html`) plus a `404.html` fallback, all serving the same SPA shell. Clean URLs, no server, no redirect trickery. Hash routing (`/#/dmu/ikuya`) is simpler but uglier. In-app navigation uses the History API; `popstate` re-reads the URL so Back works.

**Performance:** no required third-party requests after load — system fonts, bundled data, no CDN. No spinner on phase or role change; there is nothing to load, because the whole catalog is compiled into the bundle by a Vite plugin at build time. PiP opens immediately after interaction. Phase and role switching are entirely client-side and synchronous.

**Offline:** not needed for V1. A service worker / PWA could later cache recent sheets — a natural enhancement, not a launch blocker.

**Search:** not needed in V1. Dropdowns suffice until the encounter count grows.

---

## 11. V1 Scope

Three screens:

1. **Selection** — fight, sheet, role/job, then *View Mits*.
2. **Focus view** — fight, sheet, role and job selectors, phase tabs, assignments, *Pop out*, *Change fight/sheet*, sheet provenance.
3. **PiP** — role/job label, phase tabs, assignments.

A header wordmark and theme control sit above all three; nothing else is chrome.

That's the whole application.

| Feature | V1 |
|---|---:|
| Fight selection | Yes |
| Multiple mit sheets per fight | Yes |
| Role selection + job labels | Yes |
| Phase switching (by-phase tabs) | Yes |
| All-phases single scrolling list with phase splitters | Yes |
| Role-focused assignments | Yes |
| Mechanic names, multiple mits per mechanic | Yes |
| Optional timestamps | Yes |
| Ability icons | Yes, where the action resolves |
| Picture-in-Picture (+ phase switching) | Yes, where supported |
| Local role persistence | Yes |
| Shareable sheet URLs | Yes |
| Mobile responsive | Yes |
| Source sheet link | Yes |
| Action notes + carry-over markers | Yes |
| System / light / dark theme | Yes |
| GitHub Pages hosting | Yes |
| Accounts / backend / database | No |
| User-created plans / mit planner | No |
| Google Sheets live sync | No |
| ACT integration / auto fight tracking | No |
| Community comments / FFLogs / damage calc | No |

---

## 12. Future

Only after the core viewer proves useful:

- a "show all mechanics" toggle, for a player who wants the whole phase rather than only their own lines;
- a general spreadsheet → JSON converter, once enough per-sheet scripts exist to show what the common shape actually is;
- PWA / offline mode;
- keyboard shortcuts (number keys → phase N, ←/→ → prev/next);
- display densities (normal / compact);
- curated community sheet repository via PRs.

Needing strong justification — these change what the product is: web-based mit editor, accounts, backend, realtime collaboration, automatic timeline tracking, ACT integration.

---

## 13. Success Criteria

A player can: get a link in Discord → open it → pick their role → immediately see this phase's mit responsibilities → switch phases in one click → optionally keep it over FFXIV in PiP.

Qualitative bar:

> Players prefer opening XIVMits during prog over keeping the spreadsheet open.

The product should feel trivial. No instructions needed. If a user has to understand timelines, planner concepts, dashboards, configuration, accounts, or workspaces, it has grown too complicated.

Intended reaction:

> "Oh, I just pick the fight, our mit sheet, and my job."

---

## 14. V1 Definition

A static site on GitHub Pages presenting community-maintained FFXIV mit sheets in a player-focused format. Pick a fight, pick a sheet, pick your role/job — see exactly what you need to mitigate, organized by phase. Switch phases instantly; open the same view in an always-on-top PiP window.

No login, no backend, no editor, no planner, no encounter tracking. A small, fast reference a raider keeps beside or over the game during prog.
