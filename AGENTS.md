# AGENTS.md

Guidance for coding agents working in this repo.

## What this is

**XIVMits** — a static site that renders community-maintained FFXIV mitigation sheets in a role-focused, phase-by-phase view. Pick a fight → pick a sheet → pick your role/job → see only what *you* press, with an optional always-on-top Picture-in-Picture window.

It is a **viewer, not a planner**. No accounts, no backend, no database, no editor.

Read before non-trivial work:

- [docs/PRD.md](docs/PRD.md) — product scope, data model, feature matrix, non-goals
- [docs/DESIGN.md](docs/DESIGN.md) — design tokens, components, responsive rules, PiP styling, anti-patterns

## Stack

React 19 + TypeScript + Vite 8, plain CSS with custom properties. React Compiler is on via the Babel plugin in `vite.config.ts` — do not hand-write `useMemo` / `useCallback` for things the compiler handles. Oxlint, not ESLint. Deploys to GitHub Pages.

**Mantine is the design system.** `@mantine/core` + `@mantine/hooks` own the palette, scale, and component appearance; `@tabler/icons-react` supplies icons. Build UI from Mantine components and style props and reach for CSS only when no prop expresses the rule — `src/App.css` is down to the handful of cases that qualify, each with a comment saying why. Read DESIGN.md §2 before adding to it.

No Tailwind, no CSS-in-JS, no second UI library, no state-management library. React state + `localStorage` only.

## Commands

Always use Yarn for dependency installation, dependency changes, and package scripts. Run shell commands through RTK. Do not use npm, npx, pnpm, or Bun, and do not create their lockfiles. Keep `yarn.lock` as the only package-manager lockfile.

```bash
rtk yarn install     # install dependencies
rtk yarn run dev     # vite dev server
rtk yarn run build   # tsc -b && vite build
rtk yarn run lint    # oxlint
rtk yarn run preview # serve dist/
```

Run `rtk yarn run lint` and `rtk yarn run build` before declaring work done. There is no test setup yet; if you add one, document it here.

## Layout

```text
src/
  App.tsx            selection screen + focused view, Mantine theme, routing effects
  state.ts           localStorage helpers, URL parsing, initial selection
  usePip.ts          Document Picture-in-Picture lifecycle
  components/
    MitView.tsx      phase tabs + assignment list; renders both normal and compact (PiP)
  data/
    schema.ts        Zod schemas + validateCatalog(); the build-time contract
    catalog.ts       typed re-export of the virtual:mit-catalog module
    resolve.ts       generic action name + job -> concrete ability and icon
  theme.ts           Mantine theme: palette tuples, scale, variantColorResolver
  index.css          binds Mantine's color variables and aliases product tokens
  App.css            only what Mantine props cannot express (see DESIGN.md §2)
public/              static assets served at root
docs/                PRD.md, DESIGN.md
data/fights/         <fightId>/fight.json + <fightId>/<sheetId>.json (PRD §9)
data/icons.json      action name → icon filename (generated, committed)
data/jobs.json       jobs, their roles, and what generic names mean per job
public/icons/        40×40 action icons from XIVAPI (generated, committed)
scripts/             maintainer-side importers: spreadsheet → JSON, icon fetch
```

The catalog is built by the `mit-catalog` Vite plugin in `vite.config.ts`: it reads `data/fights/**.json`, runs `validateCatalog`, and exposes the result as the virtual module `virtual:mit-catalog`. That same plugin emits a static `index.html` per sheet plus `404.html`. **Invalid data fails the build** — there is no runtime fetch and no runtime validation.

## Conventions

- **TypeScript throughout.** `verbatimModuleSyntax` is on — use `import type` for type-only imports. `noUnusedLocals` / `noUnusedParameters` are errors.
- **Prefer Mantine props over CSS.** Layout is `Container` / `Stack` / `Group` / `Box`; type is `Text` / `Title`; spacing, size, and color come from props (`p`, `gap`, `fz`, `c`, `maw`). Write a CSS rule only when no prop expresses it — DESIGN.md §2 lists the ones that qualify and why.
- **The palette lives in `src/theme.ts`**, as Mantine color tuples; `src/index.css` aliases the product tokens onto Mantine's generated variables. Never hardcode a hex outside `theme.ts`. Fix a wrong Mantine default in `variantColorResolver`, not at the call site.
- **Theming is Mantine's.** `MantineProvider` uses `defaultColorScheme="auto"` with a `localStorageColorSchemeManager` keyed `xivmits-color-scheme`, and stamps `data-mantine-color-scheme` on `<html>`. The inline script in `index.html` applies the same stored value pre-paint — change the key in both places or you get a flash.
- **Semantic elements.** Real `<button>` and `<select>`; no clickable `<div>`. Keep visible focus rings.
- **Mit sheet data is repo data**, validated at build time. Malformed data fails the build rather than shipping. Schemas are `.strict()` — adding a field to the data means adding it to `src/data/schema.ts` and documenting it in PRD §9, in that order.
- **Actions flow horizontally.** They wrap only when out of room; only notes and carry-overs take a full row. Anything that forces every action onto its own line is a regression.
- **One component renders both views.** `MitView` takes a `compact` flag for PiP. Never fork it — a PiP-only copy will drift.
- **Slots are opaque IDs**, not a fixed enum. A sheet may key assignments by position (`MT`, `D3`), by job (`SGE`), or both in one sheet. Do not hardcode a role list anywhere.
- **A job is always required** before the focused view will render a plan; generic names and job-qualified lines are unresolvable without it.
- **Role and job are separate selectors.** `positionsForSheet` turns a sheet's slots into seats (`MT`, `H1`, `D3`) and job options are filtered to that seat's role. Where a sheet keys a role by job (healer columns), the seat is a label and `slotIdFor` resolves the data column from the chosen job. `resolveAction` uses the job to turn `Party Mit` into `Heart of Light`. A trailing `(GNB/DRK)` is a *constraint* — if the viewer's job is not in that list the line is dropped, because it is someone else's assignment. The mechanic still renders, blank. With no job chosen nothing is dropped.

## Guardrails

- **Read the two docs before non-trivial work.** They are current and specific; PRD §9 is the data contract and DESIGN.md §6 is the component spec.
- **Every mechanic renders, assigned or not.** Blank rows are load-bearing: phases repeat mechanic names, so hiding the unassigned ones makes it ambiguous which occurrence you are covering. Do not "tidy" them away.
- **Do not expand scope.** PRD §3 lists the non-goals — planner, editor, accounts, backend, ACT/FFLogs integration, live Google Sheets sync, comments. Do not add them because they seem natural.
- **Phase switching stays instant** — client-side, no spinner, no route transition, no animation.
- **PiP is progressive enhancement.** Feature-detect `"documentPictureInPicture" in window`; the normal view must work fully without it.
- **No horizontal page scroll**, at any width, ever. Overflowing rows scroll inside their own container.
- **No third-party network requests after load.** System fonts, bundled data, no CDN.
- Check DESIGN.md §11 before adding visual flourish — hero images, gradients, skeletons, spinners, toasts, and job-color theming are explicitly out.

## Notes

- **Ability icons are decoration.** `data/icons.json` maps action names to PNGs in `public/icons/`, generated by `scripts/fetch_icons.py` from XIVAPI. Only 26 of 34 DMU action names resolve — `Party Mit (GNB/DRK)` and friends are decisions, not buttons — so text must always stand alone. Icons are `alt=""` / `aria-hidden` in a fixed 20px box. Never call XIVAPI at runtime.
- Only one fight (`dmu`) and one sheet (`ikuya`) exist so far. Anything that reads as if there is exactly one of either is a bug waiting for the second one.
- Converter scripts in `scripts/` are per-sheet and maintainer-run by hand. They are not part of the build and are not shipped.
