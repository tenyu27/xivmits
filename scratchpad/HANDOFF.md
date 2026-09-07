# XIVMits — handoff

Continue work on **XIVMits**, a static site that renders community FFXIV mit sheets role-focused. Working dir: `/Users/wtyanan/dev/tenyu-projects/xivmits__worktrees/implement` (a git worktree on branch `implement` — run everything from here, do not `cd` to the main checkout).

## Read first
- `AGENTS.md` — conventions and guardrails
- `docs/PRD.md` — scope, data model, non-goals
- `docs/DESIGN.md` — tokens, components, PiP, anti-patterns

All three are **current and specific**. They were rewritten alongside the code, so trust them over your instincts, and update them in the same change whenever behaviour moves.

## State
Nothing is committed. Only `084286f feat: init setup` exists; everything since is uncommitted. `rtk yarn run lint` and `rtk yarn run build` pass. Yarn only, always through `rtk`: `rtk yarn run dev|build|lint`.

## Architecture
```
src/App.tsx                 selection screen + focused view, all state
src/state.ts                localStorage, URL parsing, initial selection
src/usePip.ts               Document Picture-in-Picture lifecycle
src/theme.ts                Mantine theme: palette tuples, variantColorResolver
src/index.css               binds Mantine colour vars to product tokens
src/App.css                 only what Mantine props cannot express
src/components/MitView.tsx  phase tabs + assignments; normal AND compact (PiP)
src/data/schema.ts          Zod + validateCatalog(); build-time contract
src/data/resolve.ts         generic action name + job -> ability + icon
data/fights/dmu/            fight.json + ikuya.json (generated, committed)
data/icons.json             action name -> icon filename (generated)
data/jobs.json              jobs, roles, per-job meaning of generic names
public/icons/               32 PNGs, 240K (generated from XIVAPI)
scripts/import_ikuya.py     spreadsheet -> JSON
scripts/fetch_icons.py      XIVAPI -> icons + icons.json
```
The `mit-catalog` Vite plugin reads `data/**`, runs `validateCatalog`, exposes `virtual:mit-catalog`, and emits a static `index.html` per sheet plus `404.html`. **Invalid data fails the build** — no runtime fetch, no runtime validation.

## Invariants — do not regress
1. **No third-party requests after load.** XIVAPI is build-time only; icons are committed.
2. **Every mechanic renders, assigned or not.** Blank rows are load-bearing: DMU P1 has `Light of Judgment` twice and three `Double-Trouble Trap`s, so hiding unassigned ones makes it ambiguous which one you cover.
3. **A job is always required** before a plan renders.
4. **`(GNB/DRK)` is a constraint, not a hint.** Job not in the list → drop the line entirely; the mechanic still renders, blank. No job chosen → drop nothing.
5. **Text must stand alone.** ~8 of 34 action names have no icon by design; icon-only mode falls back to text.
6. **One component renders both views.** `MitView` takes `compact`. Never fork it.
7. **Actions flow horizontally**, wrapping only when out of room. Only notes and carry-overs take a full row.
8. **Slots are opaque IDs.** `positionsForSheet` derives seats; `slotIdFor` resolves job-keyed columns.
9. **Prefer Mantine props over CSS** (DESIGN.md §2 lists the exceptions).
10. **No horizontal page scroll, ever.**

## Gotchas that cost time
- **Mantine class names are hashed.** Never target `mantine-*-input` from CSS — it silently does nothing. Add a hook via `classNames` in `theme.ts` (see `control-input`).
- **Fix wrong Mantine defaults in `variantColorResolver`**, not at call sites. Three already live there; `filled` needed one because Mantine can't measure luminance of a CSS variable and defaults to white text at 2.5:1.
- **Python `str.replace` replaces ALL occurrences** — one scripted edit matched inside a `.compact` selector and duplicated a rule. Grep after editing.
- **Verify game data against XIVAPI, don't trust recall.** 21 job LB3 names written from memory were all wrong.

## Verified
Converted data matches the source spreadsheet exactly (0 mismatches across names, order, times, per-slot assignments, carry-over flags, footnotes). Job resolution checked across MT/GNB, MT/WAR, D3/DNC, SGE. Contrast passes both themes. Build-time icon validation fails correctly on missing/malformed entries.

## NOT verified — do this first
**Everything visual since the "warm cast colour" change.** The Chrome extension disconnected partway through and never returned, so the last third of the session is verified only by build, lint, data simulation and reading markup. Unchecked: horizontal action flow and wrapping, warm cast colour in both themes, the normalised control row (`--control-h: 36px`), icon-only theme picker, new footer and headline, job-required gating, and PiP after all of it.

Run `rtk yarn run dev`, open `/dmu/ikuya/`, check both themes plus a ~400px window. Nudge `--control-h` in `src/App.css` if 36px reads wrong.

## Open
- Nothing committed; the user hasn't asked for one. Ask first.
- Only one fight and one sheet exist — anything assuming exactly one is a latent bug.
- SE icon assets committed under the FFXIV Materials Usage License with attribution in README and footer; worth the user's own review before going public.

## Working style
Terse. The user gives rapid, specific visual corrections and often reverses an earlier decision — follow the latest instruction, say plainly when it contradicts something documented, then update the doc. Verify in the browser rather than asserting. Don't commit unless asked.
