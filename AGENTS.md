# AGENTS.md

Guidance for coding agents working in this repo.

## What this is

**XIVMits** — a static site that renders community-maintained FFXIV mitigation sheets in a role-focused, phase-by-phase view. Pick a fight → pick a sheet → pick your role/job → see only what *you* press, with an optional always-on-top Picture-in-Picture window.

It is a **viewer, not a planner**. No accounts, no backend, no database, no editor.

Read before non-trivial work:

- [DESIGN.md](DESIGN.md) — design tokens, components, responsive rules, PiP styling, anti-patterns
- [packages/core/src/schema.ts](packages/core/src/schema.ts) — the build-time data contract; the schema *is* the spec

**Non-goals:** mit planner, spreadsheet editor, collaborative planning, accounts, backend, ACT/FFLogs integration, live Google Sheets sync, comments. Do not add them because they seem natural.

## Stack

React 19 + TypeScript + Vite 8, plain CSS with custom properties. React Compiler is on via the Babel plugin in `vite.config.ts` — do not hand-write `useMemo` / `useCallback` for things the compiler handles. Oxlint, not ESLint. Deploys to GitHub Pages.

**Mantine is the design system.** `@mantine/core` + `@mantine/hooks` own the palette, scale, and component appearance; `@tabler/icons-react` supplies icons. Build UI from Mantine components and style props and reach for CSS only when no prop expresses the rule — `apps/web/src/App.css` is down to the handful of cases that qualify, each with a comment saying why. See the Mantine note at the top of DESIGN.md before adding to it.

No Tailwind, no CSS-in-JS, no second UI library, no state-management library. React state + `localStorage` only.

## Commands

Always use Yarn for dependency installation, dependency changes, and package scripts. Run shell commands through RTK. Do not use npm, npx, pnpm, or Bun, and do not create their lockfiles. Keep `yarn.lock` as the only package-manager lockfile.

**Yarn 4**, pinned by `packageManager` in the root `package.json` and run
through Corepack, with `nodeLinker: node-modules` (see `.yarnrc.yml`) — not
Plug'n'Play. CI installs with `--immutable`, the Yarn 4 spelling of the old
`--frozen-lockfile`. Workspace packages depend on each other with
`"workspace:^"`.

This is a Yarn workspace. Run every script from the repo root; the root
`package.json` delegates into `apps/*` and `packages/*`.

```bash
rtk yarn install       # install every workspace
rtk yarn run dev       # vite dev server for apps/web
rtk yarn run build     # tsc -b && vite build in apps/web
rtk yarn run lint      # oxlint over the whole repo
rtk yarn run typecheck # tsc -b in every workspace
rtk yarn run preview   # serve apps/web/dist/
rtk yarn run test      # node --test in packages/core and packages/encounter-data
```

Run `rtk yarn run lint`, `rtk yarn run build`, and `rtk yarn run test` before declaring work done. Tests are Node's built-in runner; they cover the schema contract (`packages/core`) and validate the committed catalog (`packages/encounter-data`).

## Layout

```text
apps/web/                        xivmits.com — the static viewer, deployed to GitHub Pages
  index.html
  vite.config.ts                 the mit-catalog plugin, React Compiler, per-sheet HTML emit
  src/
    App.tsx                      selection screen + focused view, Mantine theme, routing effects
    state.ts                     localStorage helpers, URL parsing, initial selection
    usePip.ts                    Document Picture-in-Picture lifecycle
    components/
      MitView.tsx                phase tabs + assignment list; `layout` = tabs / list / grid (cheatsheet), `compact` flag for PiP, `hideTabs` for the cheatsheet tab
    data/
      catalog.ts                 typed re-export of the virtual:mit-catalog module
      resolve.ts                 binds the catalog's icons/jobs onto the pure resolvers in @xivmits/core
    theme.ts                     Mantine theme: palette tuples, scale, variantColorResolver
    index.css                    binds Mantine's color variables and aliases product tokens
    App.css                      only what Mantine props cannot express (see DESIGN.md)
  public/                        static assets served at root (CNAME, favicon)
  public/icons/                  40×40 action icons from XIVAPI (generated, committed)

packages/core/                   @xivmits/core — runtime-agnostic domain logic, no React, no DOM
  src/schema.ts                  Zod schemas + validateCatalog(); the build-time contract
  src/resolve.ts                 generic action name + job -> concrete ability and icon
  src/index.ts                   resolvers + type-only re-export of the schema module

packages/encounter-data/         @xivmits/encounter-data — the canonical data, plus a Node loader
  fights/                        <fightId>/encounter.json + <fightId>/sheets/<sheetId>.json
  icons.json                     action name → icon filename (generated, committed)
  abilities.json                 the ability registry: id → name, icon, game action id (generated)
  jobs.json                      jobs, their roles, and what generic names mean per job
  src/index.ts                   loadCatalog() / readFightFiles() and the on-disk path constants

scripts/                         maintainer-side tooling; never runs at build or runtime
  fflogs.py                      FFLogs v2 client, credentials from a gitignored .env
  workbook.py                    fetch a Google Sheet as xlsx, resolve tabs by name
  normalize_sheet.py             bind a sheet's rows onto the encounter's mechanic ids
  import_*.py                    one per published mit sheet
  fetch_icons.py                 XIVAPI → icons + abilities.json
```

Work in progress on the `remodel` branch, and what is deliberately
unfinished, is written up in [docs/REMODEL.md](docs/REMODEL.md).

## The encounter is the fight; a sheet is an overlay

`encounter.json` is the source of truth for a fight's timeline. Its mechanics,
ids, `time`s and `fflogs.abilityIds` are reconciled against real FFLogs reports
and **an importer never writes them** — `normalize_sheet.bind_sheet` maps a
workbook's rows onto the mechanics already on file and fails loudly on a row it
cannot match, rather than inventing one. A mit sheet carries no names and no
times: each row is `{mechanicId, note?, assignments}`, referencing the encounter
the way an action references an ability.

Mechanic ids come from the log, not the spreadsheet: `p<phase>-<slug of the
primary FFLogs ability name>-<occurrence>`. The primary ability is the cast bar
where one exists, else the damage ability. `minor: true` marks a mechanic the
encounter records for completeness — chip damage, markers — which stays out of a
sheet's grid unless that sheet assigns it.

Ability ids work the same way. `abilities.json` is keyed by an id derived from
the real in-game name, so every wording a sheet uses collapses onto one entry
(`Feint (Chaos)`, `Vengeance` for Damnation, `Spreadlo` for Deployment Tactics),
and `action` holds the game's Action row id — the same number FFLogs reports as
`abilityGameID`. `names` maps each sheet wording to its ability, and
`validateCatalog` fails the build on an action with no entry.

`@xivmits/core` splits its entry points on purpose. `@xivmits/core` exports the
resolvers plus *types only* from the schema; `@xivmits/core/schema` exports
`validateCatalog` and the Zod schemas. That keeps Zod out of the browser bundle
— the site validates at build time, so nothing in `apps/web/src` may import
`@xivmits/core/schema`.

The catalog is built by the `mit-catalog` Vite plugin in `apps/web/vite.config.ts`: it calls `loadCatalog()` from `@xivmits/encounter-data`, which reads `packages/encounter-data/fights/**.json` and runs `validateCatalog`, and exposes the result as the virtual module `virtual:mit-catalog`. That same plugin emits a static `index.html` per sheet plus `404.html`. **Invalid data fails the build** — there is no runtime fetch and no runtime validation.

## Conventions

- **TypeScript throughout.** `verbatimModuleSyntax` is on — use `import type` for type-only imports. `noUnusedLocals` / `noUnusedParameters` are errors.
- **Prefer Mantine props over CSS.** Layout is `Container` / `Stack` / `Group` / `Box`; type is `Text` / `Title`; spacing, size, and color come from props (`p`, `gap`, `fz`, `c`, `maw`). Write a CSS rule only when no prop expresses it.
- **The palette lives in `apps/web/src/theme.ts`**, as Mantine color tuples; `apps/web/src/index.css` aliases the product tokens onto Mantine's generated variables. Never hardcode a hex outside `theme.ts`. Fix a wrong Mantine default in `variantColorResolver`, not at the call site.
- **Theming is Mantine's.** `MantineProvider` uses `defaultColorScheme="auto"` with a `localStorageColorSchemeManager` keyed `xivmits-color-scheme`, and stamps `data-mantine-color-scheme` on `<html>`. The inline script in `index.html` applies the same stored value pre-paint — change the key in both places or you get a flash.
- **Semantic elements.** Real `<button>` and `<select>`; no clickable `<div>`. Keep visible focus rings.
- **Mit sheet data is repo data**, validated at build time. Malformed data fails the build rather than shipping. Schemas are `.strict()` — adding a field to the data means adding it to `packages/core/src/schema.ts` first.
- **Actions flow horizontally.** They wrap only when out of room; only notes and carry-overs take a full row. Anything that forces every action onto its own line is a regression.
- **One component renders both views.** `MitView` takes a `compact` flag for PiP. Never fork it — a PiP-only copy will drift.
- **Slots are opaque IDs**, not a fixed enum. A sheet may key assignments by position (`MT`, `P`), by job (`SGE`), or both in one sheet. Do not hardcode a role list anywhere.
- **A job is required** before the focused view will render a plan — generic names and job-qualified lines are unresolvable without it. Exception: a `melee` seat (`jobFree` in App.tsx) needs none, since every melee job mitigates the same; its job selector is disabled and shows `--`.
- **Role and job are separate selectors.** `positionsForSheet` turns a sheet's slots into seats (`MT`, `H`, `P`) and job options are filtered to that seat's role. Where a sheet keys a role by job (healer columns), the seat is a label and `slotIdFor` resolves the data column from the chosen job. `resolveAction` uses the job to turn `Party Mit` into `Heart of Light`. A trailing `(GNB/DRK)` is a *constraint* — if the viewer's job is not in that list the line is dropped, because it is someone else's assignment. The mechanic still renders, blank. With no job chosen nothing is dropped.

## Guardrails

- **Read DESIGN.md and `packages/core/src/schema.ts` before non-trivial work.** The schema is the data contract; DESIGN.md §4 is the component spec.
- **Every mechanic renders, assigned or not.** Blank rows are load-bearing: phases repeat mechanic names, so hiding the unassigned ones makes it ambiguous which occurrence you are covering. Do not "tidy" them away. The single exception is an encounter mechanic with `roles` — a tank buster is `['tank']` — whose *blank* row is dropped for other roles. It never hides an assignment: a sheet that assigns someone still shows them the row.
- **Do not expand scope.** See the non-goals list at the top of this file. Do not add them because they seem natural.
- **Phase switching stays instant** — client-side, no spinner, no route transition, no animation.
- **PiP is progressive enhancement.** Feature-detect `"documentPictureInPicture" in window`; the normal view must work fully without it.
- **No horizontal page scroll**, at any width, ever. Overflowing rows scroll inside their own container.
- **No third-party network requests after load.** System fonts, bundled data, no CDN.
- Check DESIGN.md §8 before adding visual flourish — hero images, gradients, skeletons, spinners, toasts, and job-color theming are explicitly out.

## Notes

- **Ability icons are decoration.** `packages/encounter-data/icons.json` maps action names to PNGs in `apps/web/public/icons/`, generated by `scripts/fetch_icons.py` from XIVAPI. A handful never resolve — `Party Mit (GNB/DRK)` and friends are decisions, not buttons — so text must always stand alone. Icons are `alt=""` / `aria-hidden` in a fixed 20px box. Never call XIVAPI at runtime.
- Three fights exist so far — `dmu` (two sheets, `ikuya` and `lpdu`), `top` (one sheet, `topmitty`) and `fru` (one sheet, `mitbutgood`). Anything that reads as if there is exactly one fight, or one sheet per fight, is a bug.
- Converter scripts in `scripts/` are per-sheet and maintainer-run by hand. They are not part of the build and are not shipped.
