# Design System: XIVMits

Companion to [AGENTS.md](./AGENTS.md), which defines *what* ships; this defines *how it looks*.

**Stack:** React + TypeScript + Vite, Mantine, plain CSS custom properties. **Themes:** system / light / dark, dark-primary. **Accent:** one blue. **Scope:** homepage selection, focused mit view, Picture-in-Picture.

**Mantine owns the system.** The palette, scale, and component appearance come from `@mantine/core`; `src/theme.ts` holds the Mantine colour tuples and `src/index.css` aliases the product tokens (`--bg`, `--text`, `--accent`, …) onto Mantine's generated variables so the two cannot drift. Build UI from Mantine components and style props (`p`, `mt`, `c`, `fw`, `fz`, `maw`); write a CSS rule only when no prop expresses it. Fix a wrong Mantine default in `variantColorResolver`, never at the call site.

---

## 1. Visual Theme & Atmosphere

A cheatsheet, not an app. Content first — no hero art, decorative gradients, dashboard cards, or marketing sections. It is read mid-pull, at 40% window size, over a running game, so the mechanic name and the mit name must be legible instantly. Dark-first, because most sessions sit beside FFXIV; light mode is complete, not an afterthought. Calm and structural: assignments are told apart by rules and whitespace, not boxes. Nothing moves in a way that delays reading.

Density **Daily-App Balanced** (4). Variance **Predictable Symmetric** (2) — a reading column, not an asymmetric layout. Motion **Static Restrained** (1).

---

## 2. Color Palette & Roles

Defined once as Mantine tuples in `src/theme.ts`, aliased to tokens in `src/index.css`. Never hardcode a hex anywhere else.

| Token | Light | Dark | Role |
|---|---|---|---|
| `--bg` | `#f7f8fa` | `#0d1117` | page |
| `--surface` | `#ffffff` | `#161b22` | selects, raised rows |
| `--surface-alt` | `#eef0f4` | `#1f2630` | hover, timestamp chip |
| `--border` | `#d8dce4` | `#2b3542` | rules, control borders |
| `--text` | `#14181f` | `#e8edf4` | ability names |
| `--text-secondary` | `#3d4653` | `#b3bfcd` | mechanic (cast) names |
| `--text-muted` | `#5a6473` | `#9aa6b6` | labels, notes, metadata |
| `--text-faint` | `#697383` | `#929faf` | timestamps |
| `--accent` | `#2563eb` | `#60a5fa` | current phase, focus, primary action |
| `--accent-strong` | `#1d4ed8` | `#60a5fa` | selected phase-tab text, personal-mit tag |
| `--accent-soft` | `#e6efff` | `#16273f` | selected-tab fill |
| `--accent-border` | `#93b4fb` | `#1e40af` | selected-tab / outline-button / personal-row edge |

- **One accent, and it means state** — current phase, focus, primary action, spliced personal-mit rows. Never decoration.
- **Warm neutrals** (`sand` tuple) are used only to set the cast name apart from the ability by hue. They are neutrals, not a second accent.
- **Contrast is the acceptance criterion.** Body text ≥ 4.5:1 on its surface; mechanic and ability names ≥ 7:1. `--text-faint` sits darker than a stock grey ramp would (a stock `#8b94a3` fails at 3.06:1); `--accent-strong` exists because `--accent` on `--accent-soft` lands at 4.47:1. Re-measure both themes after any palette change.
- Theme resolution is Mantine's: `defaultColorScheme="auto"`, `localStorageColorSchemeManager` keyed `xivmits-color-scheme`, `data-mantine-color-scheme` on `<html>`. The pre-paint script in `index.html` reads the same key — change it in both places or the theme flashes.
- Never pure `#000000`. Define every colour on bare `:root` before either dark block.

---

## 3. Typography Rules

- **Font:** the system UI stack, set once as `fontFamily` / `fontFamilyMonospace` in `src/theme.ts`. No webfonts — no download, no layout shift, no third-party request after load. (This is a utility, not a creative context; a display face would cost load and legibility for nothing.)
- **Scale:** Mantine `fontSizes` via `fz`. `xs` 0.75rem (timestamps, metadata, footer), `sm` 0.875rem (labels, notes, cast names), `md` 1rem (body), `lg` 1.25rem (phase heading, fight name, PiP ability names), `xl` 1.5rem (wordmark). Two literals sit off the scale on purpose: ability names `1.125rem`, PiP cast name `0.9375rem` — tuned against their own view. Selection headline is `h1` at 2rem/650.
- **Weight-driven hierarchy:** 700 cast names, 600 ability names, 650 headings, 400 notes and carry-over labels. Line height 1.2 headings, 1.5 body.
- **Mono for aligned numbers:** timestamps use `ff="monospace"` with `tabular-nums` so a column of `0:23` / `1:14` aligns on the right edge. When a fight sets `phase.start`, the chip leads with the absolute pull time and trails a dimmed phase-relative one, like `6:18 3:01`. Phases that start at `0:00` show one time.
- Headings and ability names set `overflow-wrap: anywhere` — FFXIV mechanic names are long and sometimes unspaced; nothing pushes the page sideways.
- **Never** below 0.75rem, never in `px`. Mechanic names are uppercased with `text-transform`, never in the data.

---

## 4. Component Stylings

- **Phase tabs:** one button per phase, source order. Rest transparent with `--text-muted` and a `--border`; hover `--surface-alt`; selected carries `--accent-soft` fill + `--accent` text + `--accent-border` + weight 700 + a 2px `--accent` bottom bar (four cues, so it survives grayscale) and `aria-current="true"`. 40×40 minimum. Overflow scrolls horizontally (`scroll-snap`, hidden scrollbar, selected tab scrolled into view); the row never wraps and never scrolls the page. Sticky to the viewport top with an opaque body background.
- **Buttons:** Mantine `Button` at the default radius. Three variants, no fourth — `filled` (primary, contrast-computed label), `outline` (`Pop out`, `Change fight/sheet`), `subtle`+`color="gray"` (recovery action inside an error alert). Set the variant, never the colours. Only one filled button on screen at a time. No outer glow, no custom cursor.
- **Selectors:** real `<select>` (`NativeSelect`) with the label above. The disabled *option text* says why it is locked (“Pick a fight first”), so the reason survives without colour. Selection screen: three selects stack full-width at every breakpoint (matches step order). Focused view: two fixed control rows, one gap between every control, each row wrapping only if it runs out of width. Row 1 (what you are reading): role, job, a “Mits” segmented `All` / `Party` (on `All` the plan picker follows — other-tank for a paired sheet, or P3 boss + P5 invuln for a job-keyed one; on `Party` those are hidden). When the sheet ships `tankMits.priorities`, an info glyph beside the P3 boss / P5 invuln label opens a tooltip listing the suggested job order for each side, the viewer’s own job pulled out in `--accent`. Row 2 (how the page is drawn): display, layout, and last the Notes toggle. Label above in one style, one shared 36px height, bottom-aligned.
- **Assignment entry:** the ability is the largest thing (it is what you press). The cast name is a smaller, warmer, lower-contrast heading row above it, carrying the timestamp; abilities are indented beneath on a 2px rule that binds them to it. Neither is dimmed and neither is uppercased — they are told apart *structurally*. Timestamp is a bordered mono chip, not faint text. Actions flow horizontally and wrap only when they run out of room; a carry-over run starts a new row and its actions dim to weight 500 behind one “Still active” marker; notes take full-width rows last. Entries separate with `lg` padding and a `1px --border` rule — not cards, none above the first or below the last.
- **Notes have four scopes, each shown once.** The *phase* note (`phase.note`) is the always-on block under the phase heading — an info glyph plus rules that apply to everyone, one per line (`pre-line`). A *scoped* phase note (`phase.scopedNote`) sits in the same place but renders only for a viewer whose seat presses one of its `abilities` this phase (targeted mit: Reprisal / Addle / Feint / Dismantle) and is hidden by the notes toggle. A *mechanic* note is an all-role aside under one cast (“avoid HP-restoring abilities here”, “use late into the castbar”), rendered whether or not you press anything. An *action* note sits on its own ability and carries only what is specific to that press — including a rule that only some jobs care about (“all mechanics require shields” rides the first SCH/SGE action of the phase). The importer routes each rule to the narrowest scope that still covers everyone it applies to, rather than stamping it on every action.
- **Tank personal-mit rows:** the tank job’s plan rows splice into the party timeline right below the party mechanic each names, marked two ways so the distinction never rests on colour alone: a `--accent-border` left edge down the block, and a leading `xs` uppercase `--accent-strong` “Personal” tag with a person glyph. Which plan: a paired sheet (TOP) picks it by the chosen co-tank; a job-keyed sheet (DMU) has one plan per job whose rows carry branch tags — `seat` (`MT`/`OT`), `boss` (`Chaos`/`Exdeath`, P3), `invuln` (`1`/`2`, P5) — and the “P3 boss” / “P5 invuln” selectors choose which show (default by seat — MT Exdeath / 2nd, OT Chaos / 1st — then free to toggle); an untagged row always shows. A row may carry a `tag` — a short per-row call like `Close hit` / `Far hit` / `1st hit` / `Solo` / `Avoid` lifted out of the note — a small `--accent-soft` pill right after the mechanic name, always visible (never behind the notes toggle). A `plain` row shows it in its own heading; a `bar` row has no heading, so its tag hoists onto the party mechanic name it sits under. An `alts` line (“P1 Double Invuln”) renders as a labelled sub-row of the same action markup. A plan's phase note renders like a normal phase note at the top when unanchored, or as its own edged row at its `noteAfter` anchor; `noteInvuln` limits it to one P5 invuln order. An empty-action row is a marker that only names the buster.
- **Empty state:** centered, dimmed, `fz="md"`, `py="xl"`. No skeletons, no spinners — data is bundled, nothing loads.

---

## 5. Layout Principles

- One reading column, `Container size={720}`, centered. The layout does not change shape across breakpoints — only padding and spacing — so the desktop view (used during pulls) and the phone view (used between them) teach each other.
- Breakpoints: `< 768px` single column, `Container` padding `md`, tighter action spacing, heading actions wrap below the fight name; `≥ 768px` column capped at 720px, phase tabs usually fit without scrolling.
- Reading your assignments never requires horizontal scroll at any width. Wide content (an overflowing phase row) scrolls inside its own `overflow-x` container, never the body.
- Elevation is borders, not shadows. The only shadow in the app is the OS-drawn `<select>` popup.
- **All-phases layout:** every phase stacked in one scrolling column; a sticky `--accent-border` splitter opens each phase; the tab bar stops being sticky and becomes jump-nav with no selected state. Persists to `localStorage`, shares its phase with by-phase mode.
- **Cheatsheet view:** not a picked layout — a **Cheatsheet** button (by `Source`) navigates the same tab to `?view=cheatsheet` with the reader's role, job, and tank branch in the query, forced to the `grid` layout. It is its own bare shell: no site header or footer, no 720px column — it spans the viewport so more phase columns fit across — no phase tab bar, no PiP. One slim line of `fight · seat job · sheet` and a `Full view` button back, then the grid: **one column per phase, side by side**, each a top-down list of that phase's mechanics so the mits read along the timeline the way they land. Each column is only as wide as its content needs (min `9rem`, capped `14rem` so a long mechanic name wraps rather than stretching the column), tight inline padding, a divider between; columns never wrap to a second line. The strip is its own scroll pane that flexes to fill the height left under the title line (no reserved band at the bottom), `overflow: auto` — sideways when the columns overrun, and down its own height, with each phase heading pinned to the top of the pane as its column scrolls. Never the body. Each mechanic: a `0.75rem` name (no timestamp — space is scarcer here) with a hairline rule between steps, icons below flowing left-to-right; an unassigned mechanic is just its dimmed name — no icon row — like the unassigned rows in the other layouts. Icons only, always — it is the densest view — and never notes. Space is folded, not spent — personal mit and carry-overs never take their own cell. A personal-mit run sits in the mechanic's cell behind an `--accent-border` splitter + person glyph — the splitter always leads, even when the run starts the cell (a `bar` row folds into the party cell above it; a `plain` personal mechanic keeps its own name but renders its icons the same way). Carry-over icons sit behind a `--border` splitter and the same forward arrow the other views use, dimmed.
- Full-height uses `100dvh`, never `100vh`.
- Also verify: a ~400px second-monitor window, tablet portrait, 200% browser zoom.

---

## 6. Motion & Interaction

| Interaction | Treatment |
|---|---|
| Phase switch | none — instant content swap, no fade or slide |
| Hover / focus | `background-color`, `border-color`, `color` only, 120ms `ease-out` |
| Button press | 80ms |
| PiP open | no entrance animation |

Never animate `height`, `transform`, or layout on the assignment list. `prefers-reduced-motion: reduce` drops every transition and `scroll-behavior` to `0`, globally.

**Picture-in-Picture** is the same `MitView` tree portalled with a `compact` flag, not a second app or a scaled-down site — one component, one branch. Every `<style>` is cloned into the PiP document and its body gets `.pip-body`; PiP-specific rules are `.compact` descendant overrides in `App.css`. Opens 400×600, must survive down to 280px wide. Header is role/job label + phase tabs on one line; no fight name, links, or footer. Keep timestamps, action notes, and carry-over markers — combat information. Force maximum contrast (`--bg` / `--text` only). Always renders in the opener’s resolved theme and re-resolves when it changes.

---

## 7. Accessibility

- Real `<button>` / `<select>` only — no clickable `<div>`. Focus ring `2px solid var(--focus-ring)` at `2px` offset, never removed (`:focus-visible` is fine).
- Phase tabs are a `role="tablist"` with roving `tabIndex` and ←/→/Home/End (automatic activation — nothing loads, so nothing is lost). Assignments are the `tabpanel` with `aria-live="polite"`. Landmarks: `<header>`, `<main>`, `<nav>`.
- Every state readable without colour: selected phase carries weight + fill + bar; disabled selects carry text; personal rows carry a tag.
- Theme toggle stays **3-state** (System / Light / Dark), icon-only with `role="img"` + `aria-label` + `title` per option. Icons elsewhere are always `aria-hidden` beside a text label.
- Readable at 200% zoom with no clipping or horizontal scroll.

---

## 8. Anti-Patterns (Banned)

Never ship: hero illustrations or screenshots; decorative gradients, glassmorphism, neon or outer-glow shadows; card grids for assignments; skeleton loaders or spinners on phase / role change; toasts; modals other than the native `<select>` popup; icon-only controls without an accessible name; FFXIV ornamental borders, scroll textures, or job-colour backgrounds; a second accent colour; text below 0.75rem; any animation on the assignment list; a webfont or any third-party request after load; a hardcoded hex outside `theme.ts`; pure `#000000`; emoji in UI copy.

Two that are specifically tempting:

- **Job colours.** Useful in-game, wrong here: the view already shows one player, so the colour would be constant and carry no information while costing the accent its meaning.
- **A density toggle.** PiP already *is* the dense mode. A third density to keep in sync buys less than making the two views excellent. (The `layout` axis — by-phase / all-phases, plus the forced `grid` behind the Cheatsheet button — changes *arrangement*, not density: `display` still owns density, so this stays closed.)

---

## 9. Adding to This System

1. Does an existing token cover it? Reuse beats adding.
2. Does it answer *“what do I need to mit during this phase?”* If not, it is secondary or cut.
3. Does it survive 280px wide, grayscale, and 200% zoom?
4. Does it work with no icons, no colour, and no motion?

A new colour token needs a contrast check in both themes and a definition on bare `:root` before either dark block. A new size needs a place in the type scale, not a one-off. Anything failing (3) or (4) is the wrong idea, not a style problem.
