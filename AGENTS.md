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

No Tailwind, no CSS-in-JS, no component library, no state-management library. React state + `localStorage` only.

## Commands

```bash
npm run dev       # vite dev server
npm run build     # tsc -b && vite build
npm run lint      # oxlint
npm run preview   # serve dist/
```

Run `npm run lint` and `npm run build` before declaring work done. There is no test setup yet; if you add one, document it here.

## Layout

```text
src/           app code
public/        static assets served at root
docs/          PRD.md, DESIGN.md
data/          fight + mit sheet JSON (per PRD §9; not yet created)
```

`src/` still holds the untouched Vite starter (`App.tsx`, `App.css`, `index.css`, `assets/`). It is scaffolding — replace it, don't build around it. The starter's purple `--accent` in `index.css` is **not** the product accent; DESIGN.md defines the real blue token set.

## Conventions

- **TypeScript throughout.** `verbatimModuleSyntax` is on — use `import type` for type-only imports. `noUnusedLocals` / `noUnusedParameters` are errors.
- **CSS custom properties only** for color, spacing, radius, and type size. Never hardcode a hex value in a component stylesheet; add or reuse a token from DESIGN.md §2.
- **Theming** is `data-theme="light" | "dark"` on `<html>`, falling back to `prefers-color-scheme`. Every color needs a definition on bare `:root` — never define one solely inside a media query.
- **Semantic elements.** Real `<button>` and `<select>`; no clickable `<div>`. Keep visible focus rings.
- **Mit sheet data is repo data**, validated at build time. Malformed data fails the build rather than shipping.

## Guardrails

- **Do not expand scope.** PRD §3 lists the non-goals — planner, editor, accounts, backend, ACT/FFLogs integration, live Google Sheets sync, comments. Do not add them because they seem natural.
- **Phase switching stays instant** — client-side, no spinner, no route transition, no animation.
- **PiP is progressive enhancement.** Feature-detect `"documentPictureInPicture" in window`; the normal view must work fully without it.
- **No horizontal page scroll**, at any width, ever. Overflowing rows scroll inside their own container.
- **No third-party network requests after load.** System fonts, bundled data, no CDN.
- Check DESIGN.md §10 before adding visual flourish — hero images, gradients, skeletons, spinners, toasts, and job-color theming are explicitly out.

## Notes

- This directory is not yet a git repository. Do not run `git init`, commit, or push unless asked.
- Ability icons are V1.1. Text ability names must work perfectly on their own; nothing may depend on an icon to be understandable.
