# XIVMits — Design System

**Stack:** React + TypeScript + Vite, plain CSS with custom properties (no Tailwind, no component library)
**Themes:** system / light / dark, dark-primary
**Accent:** blue
**Scope:** homepage selection, focused mit view, Picture-in-Picture

Companion to [PRD.md](./PRD.md). The PRD defines *what* ships; this defines *how it looks*.

---

## 1. Principles

1. **Cheatsheet, not app.** Content first. No hero art, decorative gradients, dashboard cards, or marketing sections.
2. **Glanceable under pressure.** Read mid-pull, at 40% window size, over a game. Mechanic name and mit name are the two things that must be legible instantly.
3. **Dark first.** Most sessions run beside FFXIV. Light mode is complete, not an afterthought.
4. **Blue is for state, not decoration.** Accent marks the current phase, focus, and the primary action — nothing else.
5. **No motion that delays reading.** Transitions ≤ 150ms, only on color and opacity. Phase switching is instant.
6. **Nothing depends on color alone.** Selected states carry weight, background, and border changes too.

---

## 2. Color Tokens

All colors are CSS custom properties on `:root`. Light is the base definition; dark overrides only what changes. Never define a color solely inside a media query.

```css
:root {
  color-scheme: light;

  /* Surfaces */
  --bg:            #f7f8fa;   /* page */
  --surface:       #ffffff;   /* cards, selects, phase bar */
  --surface-alt:   #eef0f4;   /* hover, inset rows */
  --border:        #d8dce4;
  --border-strong: #b9c0cc;

  /* Text */
  --text:          #14181f;   /* mechanic names, headings */
  --text-muted:    #5a6473;   /* labels, metadata */
  --text-faint:    #8b94a3;   /* timestamps, disabled */

  /* Accent — blue */
  --accent:         #2563eb;
  --accent-hover:   #1d4ed8;
  --accent-active:  #1e40af;
  --accent-soft:    #e6efff;  /* selected-tab fill */
  --accent-border:  #93b4fb;
  --on-accent:      #ffffff;

  /* Status */
  --danger:  #b42318;
  --warning: #b25000;

  /* Focus */
  --focus-ring: var(--accent);
}

:root:not([data-theme="light"]) { }          /* base guard, see below */

@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) { /* dark token block */ }
}

:root[data-theme="dark"] { /* same dark token block */ }
```

Dark token block (used by both selectors above):

```css
color-scheme: dark;

--bg:            #0d1117;
--surface:       #161b22;
--surface-alt:   #1f2630;
--border:        #2b3542;
--border-strong: #3d4959;

--text:          #e8edf4;
--text-muted:    #9aa6b6;
--text-faint:    #6b7787;

--accent:        #60a5fa;
--accent-hover:  #7db6fb;
--accent-active: #93c5fd;
--accent-soft:   #16273f;
--accent-border: #2f5c99;
--on-accent:     #0d1117;

--danger:  #f97066;
--warning: #f79009;
```

**Theme resolution.** `data-theme="light" | "dark"` on `<html>` wins; absent, `prefers-color-scheme` decides. Persist the user's choice in `localStorage` under `theme` (`system` | `light` | `dark`) and apply it before first paint via an inline script in `index.html` to avoid a flash.

**Contrast.** All body text ≥ 4.5:1 on its surface; mechanic names and mit names ≥ 7:1. Accent-on-surface ≥ 4.5:1 in both themes; verify after any accent change.

---

## 3. Typography

System stack — no webfont downloads, no layout shift, no third-party request after load.

```css
--font-sans: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto,
             "Helvetica Neue", Arial, sans-serif;
--font-mono: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
```

| Token | Size | Weight | Tracking | Use |
|---|---|---|---|---|
| `--fs-xs` | 0.75rem | 500 | +0.02em | timestamps, updated date |
| `--fs-sm` | 0.875rem | 500 | normal | selector labels, sheet metadata |
| `--fs-base` | 1rem | 400 | normal | body, notes |
| `--fs-mech` | 0.875rem | 700 | +0.06em | mechanic name (uppercase) |
| `--fs-mit` | 1.125rem | 600 | normal | mitigation action names |
| `--fs-lg` | 1.25rem | 600 | normal | phase heading, fight name |
| `--fs-xl` | 1.5rem | 700 | -0.01em | wordmark |

Line height: 1.2 headings, 1.5 body. Mechanic names are uppercase via `text-transform`, never in the data. Timestamps use `--font-mono` at `--fs-xs` in `--text-faint`.

Never set a font size below 0.75rem. Text scales with the user's root size — no `px` font sizes.

---

## 4. Space, Radius, Elevation

4px base scale: `--sp-1: 4px` … `--sp-2: 8px`, `--sp-3: 12px`, `--sp-4: 16px`, `--sp-5: 24px`, `--sp-6: 32px`, `--sp-7: 48px`.

Radius: `--r-sm: 4px` (chips, tabs), `--r-md: 8px` (selects, buttons, cards), `--r-lg: 12px` (page container). Nothing fully rounded except a focus dot.

Elevation is borders, not shadows. One shadow exists — dropdown menus: `0 4px 16px rgb(0 0 0 / 0.12)` light, `0 4px 16px rgb(0 0 0 / 0.5)` dark. No shadows on cards, buttons, or the phase bar.

Content width caps at `--w-max: 720px`, centered. The focused view is a reading column, not a full-bleed layout.

---

## 5. Components

### Selector (fight / sheet / role)

Native `<select>` styled with `--surface`, `1px solid --border`, `--r-md`, min height 44px. Label above in `--fs-sm` / `--text-muted`. Disabled state: `--surface-alt` background, `--text-faint` text, `cursor: not-allowed` — and the label reads why it's locked (e.g. *"Pick a fight first"*), never color alone.

Stacked vertically at every breakpoint. Selects go full width; do not put three of them in a row on desktop — the vertical stack matches the step order.

### Primary button (`View Mits`, `Open PiP`)

`--accent` fill, `--on-accent` text, `--r-md`, min height 44px, horizontal padding `--sp-5`. Hover `--accent-hover`, active `--accent-active`, disabled `--surface-alt` / `--text-faint`. `Open PiP` is a secondary variant: transparent fill, `--accent` text and border.

### Phase tabs

A horizontal row of buttons, one per phase, in source order.

- Rest: transparent fill, `--text-muted`, `1px solid --border`.
- Hover: `--surface-alt`.
- **Selected:** `--accent-soft` fill, `--accent` text, `1px solid --accent-border`, weight 700, plus a 2px `--accent` bottom bar. Weight + fill + bar means the state survives color blindness and grayscale.
- `aria-current="true"` on the selected tab.

Minimum touch target 40×40. When the row overflows: `overflow-x: auto`, `scroll-snap-type: x proximity`, hidden scrollbar, and the selected tab scrolled into view. The row never wraps to two lines and never causes page-level horizontal scroll.

### Assignment entry

```text
ULTIMATE RELATIVITY          0:23
Kerachole
```

Mechanic name in `--fs-mech` uppercase `--text-muted`; timestamp right-aligned, mono, `--text-faint`. Mitigation actions below in `--fs-mit` `--text`. Multiple actions join with a middot separator (`Holos · Panhaima`) or stack on narrow widths. Entries separate with `--sp-5` and a `1px solid --border` rule — not cards.

Optional icons (V1.1) sit 20px inline before the action name and must be removable without changing the layout's meaning.

### Empty state

Centered, `--text-muted`, `--fs-base`, `--sp-7` vertical padding. Copy per PRD §8.

---

## 6. Responsive

Mobile-first. Three breakpoints, no more.

| Width | Layout |
|---|---|
| `< 480px` | Single column, page padding `--sp-4`, phase tabs scroll horizontally, actions stack on their own lines |
| `480–767px` | Same, padding `--sp-5`, actions may sit inline with the mechanic name |
| `≥ 768px` | Content column capped at `--w-max`, centered, padding `--sp-6`; phase tabs fit without scrolling in most fights |

Reading personal assignments must never require horizontal scrolling at any width. Wide content (an overflowing phase row) scrolls inside its own container, never the body.

Also verify: a ~400px-wide second-monitor browser window, tablet portrait, and 200% browser zoom.

---

## 7. Picture-in-Picture

A separate, denser stylesheet — not the site scaled down.

- Target 320–480px wide, 240–360px tall. Layout must survive down to 280px.
- Copy the same CSS custom properties into the PiP document, then override sizes only.
- Header: role/job label left, phase tabs right, on one line. Nothing else — no fight name, sheet name, metadata, links, or footer.
- Bump mechanic name to 0.9375rem and mit names to 1.25rem; drop spacing one step (`--sp-5` → `--sp-3`).
- Hide timestamps, notes, and source links by default.
- Force maximum contrast: `--bg` / `--text` only, no `--surface-alt` fills except the selected phase tab.
- Phase tabs keep a 32px minimum height — clickable, still compact.
- PiP always renders in the resolved theme of the opener; it does not follow the PiP window's own preference.

---

## 8. Motion

| Interaction | Treatment |
|---|---|
| Phase switch | None. Instant content swap, no fade, no slide |
| Hover / focus | `background-color`, `border-color`, `color` — 120ms `ease-out` |
| Button press | 80ms |
| PiP open | No entrance animation |

Never animate `height`, `transform`, or layout on the assignment list. Honor `prefers-reduced-motion: reduce` by dropping all transitions to `0ms`.

---

## 9. Accessibility

- Every control is a real `<button>` or `<select>`. No clickable `<div>`.
- Focus ring: `outline: 2px solid var(--focus-ring); outline-offset: 2px`. Never remove it; `:focus-visible` is fine.
- Phase tabs are a `role="tablist"` with arrow-key navigation; assignments are the tab panel with `aria-live="polite"`.
- Landmarks: `<header>`, `<main>`, `<nav>` for the phase bar.
- All information available without color: selected phase carries weight + fill + bar; disabled selectors carry text.
- Full keyboard path: selectors → View Mits → phase tabs → Open PiP.
- Text remains readable at 200% zoom with no clipping or horizontal scroll.
- The theme toggle is a labeled 3-state control (System / Light / Dark), not an icon-only guess.

---

## 10. Anti-Patterns

Do not ship: hero illustrations or screenshots; decorative gradients or glassmorphism; card grids for assignments; skeleton loaders (data is bundled — nothing loads); spinners on phase or role change; toasts; modals other than native `<select>`; icon-only buttons without labels; FFXIV-themed ornamental borders, scroll textures, or job-color backgrounds; a second accent color; text below 0.75rem; animation on the assignment list.
