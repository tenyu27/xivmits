# XIVMits — Design System

**Stack:** React + TypeScript + Vite, plain CSS with custom properties (no Tailwind, no CSS-in-JS)
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
7. **Structure over containers.** Assignments are separated by rules and space, not boxed in cards. A border that only decorates is a border to delete.

---

## 2. Mantine

Mantine is the design system. It owns the palette, the scale, and the component
appearance; we write CSS only where a Mantine prop cannot express the rule.

**The palette lives in `src/theme.ts`**, as Mantine colour tuples:

| Tuple | Role |
|---|---|
| `accent` | the blue. `primaryShade` is 6 in light, 4 in dark |
| `dark` | dark-mode surfaces and text, replacing Mantine's stock greys |
| `gray` | light-mode surfaces and text |

`src/index.css` then aliases the product tokens (`--bg`, `--text`, `--accent`, …)
onto the variables Mantine generates from those tuples. That direction matters:
Mantine is the source of truth, the tokens are a readable alias, and the two
cannot drift. It also means the tokens are real CSS variables, which the PiP
document and the pre-paint script both need.

**Build UI from Mantine components and props**: `Container`, `Stack`, `Group`,
`Box` for layout; `Text`, `Title`, `Anchor` for type; `Button`, `NativeSelect`
for controls. Use the style props (`p`, `mt`, `c`, `fw`, `fz`, `maw`) rather
than a stylesheet rule. Spacing props resolve to the theme scale, so `gap="lg"`
is 24px in both places it is used.

**Variant colours are resolved in the theme, not overridden per component.**
`variantColorResolver` in `src/theme.ts` handles the three cases where Mantine's
defaults miss this system:

- `filled` — Mantine resolves theme colours to CSS variables and so cannot
  measure their luminance; it falls back to white text, which is 2.5:1 on the
  dark-mode accent. The resolver points it at `--mantine-primary-color-contrast`,
  which `autoContrast` computes correctly (8.3:1).
- `outline` — Mantine picks `accent[0]`, far too pale to read as accent.
- `subtle` on gray — Mantine picks a near-white; `Change fight/sheet` should recede.

If a Mantine default is wrong, fix it in the theme so every instance moves
together. Do not patch it at the call site.

**What stays in `App.css`**, and why each one cannot be a prop:

| Rule | Why |
|---|---|
| `.phase-tabs` + selected state | the 2px bar is a `::after` pseudo-element |
| `.phase-bar` sticky | positional, and needs the opaque body background |
| `.phase-splitter` sticky + `.mit-view.list` overrides | positional; opaque body background; `:first-of-type` selector |
| `.assignments` list reset and dividers | `li + li` sibling selector |
| `.mechanic-name` uppercase | `text-transform` has no style prop |
| `.compact` / `.pip-body` | descendant overrides on a portalled tree |

That list is the budget. A new rule needs a reason of the same kind.

## 3. Color Tokens

Defined once as Mantine tuples in `src/theme.ts` (§2), aliased to product tokens
in `src/index.css`. Never hardcode a hex value anywhere else.

| Token | Light | Dark | Use |
|---|---|---|---|
| `--bg` | `#f7f8fa` | `#0d1117` | page |
| `--surface` | `#ffffff` | `#161b22` | selects, raised rows |
| `--surface-alt` | `#eef0f4` | `#1f2630` | hover |
| `--border` | `#d8dce4` | `#2b3542` | rules, control borders |
| `--text` | `#14181f` | `#e8edf4` | ability names |
| `--text-secondary` | `#3d4653` | `#b3bfcd` | mechanic (cast) names |
| `--text-muted` | `#5a6473` | `#9aa6b6` | labels, notes, metadata |
| `--text-faint` | `#697383` | `#929faf` | timestamps |
| `--accent` | `#2563eb` | `#60a5fa` | current phase, focus, primary action |
| `--accent-strong` | `#1d4ed8` | `#60a5fa` | selected phase-tab text |
| `--accent-soft` | `#e6efff` | `#16273f` | selected-tab fill |
| `--accent-border` | `#93b4fb` | `#1e40af` | selected-tab and outline-button border |

**Theme resolution** is Mantine's. `MantineProvider` runs `defaultColorScheme="auto"`
with a `localStorageColorSchemeManager` keyed `xivmits-color-scheme`, and stamps
`data-mantine-color-scheme` on `<html>`. An inline script in `index.html` applies
the same stored value before first paint, so there is no flash — **if you change
that storage key, change it in both places.**

**Contrast.** Body text ≥ 4.5:1 on its surface; mechanic and mit names ≥ 7:1.
Measured, both themes:

| | Light | Dark |
|---|---|---|
| Mechanic / mit name | 21:1 | 16.1:1 |
| Note, muted text | 6.0:1 | 7.7:1 |
| Timestamp | 4.8:1 | 7.0:1 |
| Selected phase tab | 5.8:1 | 5.9:1 |
| Primary button label | 8.3:1 | 8.3:1 |

Two of those are the reason for tokens that look arbitrary: `--text-faint` is
darker than a stock grey ramp would place it (`#8b94a3` measures 3.06:1 on
white), and `--accent-strong` exists because `--accent` on `--accent-soft` lands
at 4.47:1 — just under the bar. Re-measure after any palette change; the numbers
above are the acceptance criteria, not decoration.

## 4. Typography

System stack, set once as `fontFamily` / `fontFamilyMonospace` in `src/theme.ts` —
no webfont downloads, no layout shift, no third-party request after load.

Sizes come from Mantine's `fontSizes` scale via the `fz` prop:

| Mantine token | Size | Use |
|---|---|---|
| `xs` | 0.75rem | timestamps, metadata, footer, phase counter |
| `sm` | 0.875rem | selector labels, notes, mechanic names |
| `md` | 1rem | body |
| `lg` | 1.25rem | phase heading, fight name, PiP mit names |
| `xl` | 1.5rem | wordmark, focused-view fight name |

Two sizes sit off the scale deliberately and are passed as literals: mit names
at `1.125rem` and the PiP mechanic name at `0.9375rem`. Both are tuned against
the other text in their own view, not against a general ramp. The
selection-screen headline is `h1` from `theme.headings` at 2rem/650.

Weights: 700 mechanic names, 600 mit names, 650 headings, 400 notes and
carry-over labels. Line height 1.2 headings, 1.5 body.

Mechanic names are uppercased with `text-transform`, never in the data — the
JSON keeps them as written so a converter round-trips and a screen reader says
the name, not the shout.

Timestamps use `ff="monospace"` at `xs` in `--text-faint`. Mono matters: `0:23`
and `1:14` must align down the right edge, and a proportional font makes a
column of times ragged.

Headings and mit names set `overflow-wrap: anywhere`. FFXIV mechanic names are
long, compound, and occasionally unspaced; nothing may push the page sideways.

Never set a font size below 0.75rem, and never in `px` — text must scale with
the user's root size.

---

## 5. Space, Radius, Elevation

Mantine's scale, from `src/theme.ts`. Use the spacing props (`p`, `m`, `gap`),
not raw values.

| Token | Value |
|---|---|
| `xs` | 4px |
| `sm` | 8px |
| `md` | 16px |
| `lg` | 24px |
| `xl` | 32px |

Radius: `sm` 4px (tabs), `md` 8px (selects, buttons — the theme default), `lg`
12px. Nothing fully rounded.

Elevation is borders, not shadows. No shadows on controls, rows, or the phase
bar; the only one in the app is the native `<select>` popup, which the OS draws.

Content width caps at 720px via `Container size={720}`, centered. The focused
view is a reading column, not a full-bleed layout.

---

## 6. Components

### Header

Wordmark left, theme control right, separated from the page by a bottom rule. The wordmark is `XIV` at weight 750 and `Mits` at 450 in the same size — the weight change does the work a second color would otherwise do, and it survives grayscale. It links to the site root and is the only always-present navigation.

The theme control is an icon-only `SegmentedControl size="xs"` — monitor, sun, moon — driven by Mantine's `useMantineColorScheme` (`auto` / `light` / `dark`). It reuses the `.display-picker` styling so it reads as the same kind of control as the display picker below it.

It carries no visible "Theme" label: three unambiguous glyphs in the header corner need no heading, and it is set once and never touched again. The names live in `aria-label` / `title` instead (§10).

The focused-view heading puts `Change fight/sheet` on the right. `Pop out` sits
at the right edge of the sticky phase row, where it stays visible while the
phase tabs scroll horizontally. Neither action sits among the role, job,
display and notes settings.

### Footer

One rule and two rows. The first row pairs `Made by tenyu` with the Ko-fi coffee
icon on the left and `Have a question or feedback?` on the right. A tooltip
shows `Support on Ko-fi` when the icon is hovered or focused. The feedback link
opens the project Google Form. The second row carries the Square Enix
trademark notice in `--text-faint`, required because the app ships SE icon
assets. There is no site map.

Persistence is not called out in the footer. The selection screen's subheadline
says what the tool does instead, which is what a first-time visitor needs before
picking a role.

### Selector (fight / sheet / role)

Mantine `NativeSelect` with a `label` — a real `<select>`, styled by the theme. Disabled state comes from Mantine, and the *option text* says why it is locked (*"Pick a fight first"*), so the reason survives without color.

On the **selection screen** the three selects stack vertically at every breakpoint and go full width — the vertical stack matches the step order, so three-across on desktop is wrong even though it fits.

On the **focused view** the role select sits in the settings row, capped at 280px. It is no longer a step in a sequence there; it is one control among the view's tools.

### Control row

The role, job, display and notes controls sit in one row and must read
as one set. That means a single pattern, applied to all of them:

- **Label above, always** — same size (`sm`), same colour (`--text-muted`), same
  weight. `SegmentedControl` and `Switch` get theirs from `Input.Wrapper` so the
  markup matches the selects rather than merely resembling them.
- **One height** — `--control-h: 36px` on every control box. The switch is
  shorter than an input, so it centres inside that height instead of hanging off
  the baseline.
- **Bottom-aligned** (`align="flex-end"`), so the control boxes line up whether
  or not a label sits above them.

Mantine's class names are hashed, so anything the row needs to size is given a
stable hook from the theme (`control-input`) rather than a guessed selector.

### Primary button (`View Mits`, `Pop out`)

Mantine `Button` at the theme's default radius. Hover, active, and disabled
states come from Mantine. Three variants, and no fourth:

| Mantine variant | Use | Treatment |
|---|---|---|
| `filled` (default) | `View Mits` | accent fill, contrast-computed label |
| `variant="outline"` | `Pop out`, `Change fight/sheet` | transparent fill, `--accent` text and border |
| `variant="subtle" color="gray"` | `Change fight/sheet` in the error alert | no fill or border, `--text-muted` |

All three are theme-resolved (§2) — set the variant, never the colors. Only one
accent-filled button is ever on screen at a time; the secondary actions in the
focused view are outline, and the subtle variant is left for the recovery action
inside an error alert, where it should stay quiet.

### Phase tabs

A horizontal row of buttons, one per phase, in source order.

- Rest: transparent fill, `--text-muted`, `1px solid --border`.
- Hover: `--surface-alt`.
- **Selected:** `--accent-soft` fill, `--accent` text, `1px solid --accent-border`, weight 700, plus a 2px `--accent` bottom bar. Weight + fill + bar means the state survives color blindness and grayscale.
- `aria-current="true"` on the selected tab.

Minimum touch target 40×40. When the row overflows: `overflow-x: auto`, `scroll-snap-type: x proximity`, hidden scrollbar, and the selected tab scrolled into view on change. The row never wraps to two lines and never causes page-level horizontal scroll.

The bar is **sticky to the top of the viewport** with an opaque `--mantine-color-body` and `z-index: 1`. Scrolling a long phase must never cost you the ability to leave it. Because the scroll container is inset, the tab row carries 4px padding with a matching negative margin — without it the focus ring on the first and last tab clips against the overflow edge.

### Layout: by phase / all phases

A two-option `SegmentedControl` in the control row, styled like the display picker. **By phase** is the default — one phase at a time, the tab bar switching it. **All phases** stacks every phase into one scrolling column so the whole fight reads top to bottom.

In **all phases**:

- A **phase splitter** opens each phase: its label in `--accent-strong` weight 700, the long name beside it dimmed, on a 2px `--accent-border` rule. It is sticky to the top of the viewport (`z-index: 2`, opaque body) so you always know which phase you are scrolled into. The first splitter has no top margin.
- The tab bar stops being sticky (`.mit-view.list .phase-bar`) and becomes a jump nav — clicking a tab scrolls that phase's splitter to the top. No tab carries the selected fill or bar here; none of them is "the current phase" when every phase is on screen. Entering the view scrolls to the phase you were last reading.
- The choice persists in `localStorage` (`layout`) and the stored phase is shared with by-phase mode, so toggling keeps your place.

### Phase heading

Phase name at `fz="lg"`, alone. It carried an `N assigned` count; the count went
when the list started showing every mechanic, since "assigned" stopped being the
thing the list was filtered by.

### Assignment entry

```text
Shell Crusher                                [ 1:14 ]
│ ▣ Holos   ▣ Kerachole   ▣ Zoe Shields
│ ▣ Panhaima
│   Cast before the second hit lands.
│ ↳ Still active  ▣ Heart of Light
```

Nothing else sits in the entry. The sheet's updated date, author and source
version do not appear anywhere in the viewer.

**The ability is the largest thing in the entry** — it is what you press. The
cast is a smaller, warmer, lower-contrast label above it: enough to find your
place in the phase, never enough to compete with the thing you act on. Neither
is muted, and neither is uppercased — mechanic names are proper nouns and read worse shouted. They are
told apart *structurally* instead: the cast is a full-width heading row carrying
the timestamp, and the abilities are indented beneath it against a 2px rule that
visually binds them to it. Structure survives grayscale and small sizes in a way
a colour difference does not.

| | Size | Weight | Colour |
|---|---|---|---|
| Cast (mechanic) | 0.9375rem (0.875rem in PiP) | 700 | `--text-secondary` |
| Ability | 1.125rem (1rem in PiP) | 600 | `--text` |
| Timestamp | `sm` mono | 700 | `--text` on `--surface-alt` |

The cast is separated from the ability **two ways at once**: it is a step lower
in contrast, and it is a *warm* neutral where the ability text is cool. Hue is
what makes them tell apart instantly; contrast alone kept reading as the same
kind of text. It is deliberately not `--text-muted`, which reads as annotation
and loses the cast among its own notes.

Measured, the cast is 1.9× (light) and 1.6× (dark) less contrasted than the
ability, while staying 1.6× / 1.3× above note text.

The warm neutrals live in the `sand` tuple in `src/theme.ts` and are used for
nothing else. They are neutrals, not a second accent — §11 still holds.

The cast is the **largest** thing in the entry. You scan for the cast to find
your place in the fight, then read the ability under it — so the size order
follows the reading order, and the indent under it does the grouping.

**Timestamp** is a bordered chip, not faint grey text — at 15.6:1 (light) and
10.6:1 (dark) it is findable at a glance, which is the whole reason it exists.
`font-variant-numeric: tabular-nums` and `flex: 0 0 auto` keep a column of times
aligned and uncompressed. It shows in PiP too.

**Actions flow horizontally and wrap only when they run out of room**, so a
phase fits in fewer rows and more of it is visible at once. One exception starts
a new row:

- the start of a **carry-over run**, which moves below the press-now row; its
  carry-over actions share that row and wrap only when they run out of room.

After all actions and carry-overs render, enabled notes take full-width rows
below them in source order. A note never splits actions that fit side by side.

The risk of an inline row is that `Kerachole  Zoe Shields` reads as one
oddly-named ability. The icon does the separating in `icon + text` mode; in
`text` mode there is no artwork, so the column gap widens to `xl`. A middot
between items would be better typography, but CSS cannot see where a flex row
wraps and the glyph would strand at the start of a wrapped line.

Entries separate with `lg` padding and a `1px solid --border` rule between them — not cards, and no rule above the first or below the last.

**Action note.** `fz="sm"`, weight 400, dimmed, capped at `62ch`, below the complete action row. Multiple distinct notes retain source order. Identical note/link pairs shared by several actions render once per mechanic, and a shorter note is omitted when another note contains it in full. Weight and color must both drop: a note at the action's weight competes with the action. `noteLink` renders as an inline *Timing example* link with `white-space: nowrap` so the label never breaks across lines, and is hidden in PiP.

**Carry-over.** One return marker and `Still active` label at `fz="xs"` dimmed weight 400 precede each run of carry-over actions; the marker is not repeated for every action. The action names drop to dimmed weight 500. The run sits visibly below the live actions without disappearing. Never encode carry-over with color alone, and never hide it — the point is knowing the mechanic *is* covered. Icon mode keeps the single return marker and omits the text label.

**Ability icon.** 32px (26px in PiP), inline before the action name, after any
carry-over label, with `flex: 0 0 auto` so a missing icon cannot shift the text.
Carry-over icons drop to 50% opacity, matching the dimmed name.

In `icon + text` and `text` modes the icon is `alt=""` and `aria-hidden` — a
second encoding of the name beside it. In `icon` mode it is the only label left,
so it takes the action name as its `alt` and `title`. Not every action has an
icon, so **icon mode falls back to the action's text** rather than rendering an
empty row; see §6 Display modes.

### Display modes

A `SegmentedControl` (`Icon + text` / `Icon` / `Text`) and a `Notes` switch sit
with the role and job selectors. Both persist to `localStorage` and both apply
to the PiP window, because it renders the same component.

The picker is styled like the phase tabs — bordered container, `--accent-soft`
fill and `--accent-strong` label on the selected item — rather than Mantine's
default, whose unselected items have no boundary and read as static text. A
control that does not look pressable does not get pressed.

| Mode | Layout | Notes |
|---|---|---|
| `both` (default) | icon then name, stacked one per line | shown if the switch is on |
| `icon` | icons flow horizontally; carry-over runs start a new row with return markers | hidden, and the switch disables |
| `text` | name only, stacked | shown if the switch is on |

`icon` mode is the dense one — it is what a 320px PiP window wants. It hides
notes because a note has no line to attach to once the name is gone, which is
defensible only because a note is annotation and never load-bearing (§6,
Assignment entry). **An action with no icon still renders its text in this
mode.** Roughly a quarter of names have no icon, so the alternative is a blank
row, and a plan that silently omits assignments is worse than a dense one that
does not.

### Empty state

Centered, dimmed, `fz="md"`, `py="xl"`. Copy per PRD §8.

---

## 7. Responsive

Mobile-first. Three breakpoints, no more.

| Width | Layout |
|---|---|
| `< 480px` | Single column, `Container` padding `md`, tighter action spacing, heading actions wrap below the fight name, phase tabs scroll horizontally |
| `480–767px` | Same single column |
| `≥ 768px` | Content column capped at 720px, centered; phase tabs fit without scrolling in most fights |

The layout does not change shape across breakpoints — only padding and spacing. Actions always stack one per line; the reading column is the same column at every width. This is deliberate: the desktop view and the phone view have to teach each other, because a player checks the phone between pulls and the desktop during them.

Reading personal assignments must never require horizontal scrolling at any width. Wide content (an overflowing phase row) scrolls inside its own container, never the body.

Also verify: a ~400px-wide second-monitor browser window, tablet portrait, and 200% browser zoom.

---

## 8. Picture-in-Picture

A separate, denser stylesheet — not the site scaled down.

- Opens at 400×600px. Native browser resizing remains unrestricted, and the layout must survive down to 280px wide.
- Copy the same CSS custom properties into the PiP document, then override sizes only.
- Header: role/job label left and phase tabs right, on one line. No fight name, sheet name, metadata, links, or footer. The requested width and height set only the initial window size; native browser resizing remains unrestricted.
- Bump mechanic name to 0.9375rem and mit names to `lg`; drop entry spacing one step (`lg` → `sm`).
- Hide note links, the phase heading, and the sheet metadata row. **Keep timestamps, action notes, and carry-over markers** — those are combat information. Timestamps used to be hidden here; they earned their place once they became a legible chip rather than faint grey text.
- Force maximum contrast: `--bg` / `--text` only, no `--surface-alt` fills except the selected phase tab.
- Phase tabs keep a 32px minimum height and 32px min-width — clickable, still compact.
- PiP always renders in the resolved theme of the opener; it does not follow the PiP window's own preference, and it re-resolves when the opener's theme or the OS preference changes while open.

**Implementation.** The PiP document is not a second app. Every `<style>` and stylesheet link is cloned into the PiP head, its body gets `.pip-body`, and the same `MitView` is portalled in with `compact`. One component, one branch — so a change to the assignment list cannot ship to one view and not the other. Everything PiP-specific is a `.compact` descendant rule in `App.css`; there is no separate PiP stylesheet to drift.

---

## 9. Motion

| Interaction | Treatment |
|---|---|
| Phase switch | None. Instant content swap, no fade, no slide |
| Hover / focus | `background-color`, `border-color`, `color` — 120ms `ease-out` |
| Button press | 80ms |
| PiP open | No entrance animation |

Never animate `height`, `transform`, or layout on the assignment list. Honor `prefers-reduced-motion: reduce` by dropping all transitions to `0ms`.

---

## 10. Accessibility

- Every control is a real `<button>` or `<select>`. No clickable `<div>`.
- Focus ring: `outline: 2px solid var(--focus-ring); outline-offset: 2px`. Never remove it; `:focus-visible` is fine.
- Phase tabs are a `role="tablist"` with arrow-key navigation; assignments are the tab panel with `aria-live="polite"`.
- Landmarks: `<header>`, `<main>`, `<nav>` for the phase bar.
- All information available without color: selected phase carries weight + fill + bar; disabled selectors carry text.
- Full keyboard path: selectors → View Mits → phase tabs → Pop out.
- Text remains readable at 200% zoom with no clipping or horizontal scroll.
- The theme toggle stays a **3-state** control (System / Light / Dark) — never a 2-state flip, which strands anyone who wants to follow their OS. It is icon-only, so each option carries `role="img"` with an `aria-label` and a matching `title`; the accessible name is the label text the radio would otherwise have had.
- Phase tabs use roving `tabIndex`: the selected tab is the only one in the tab order, and ←/→/Home/End move between them. Arrow keys change the phase as they move, matching the automatic-activation tab pattern — there is nothing to load, so nothing is lost by activating on arrow.
- Icons are always `aria-hidden` and always accompany a text label.
- `prefers-reduced-motion: reduce` drops every transition and `scroll-behavior` to zero, globally.

---

## 11. Anti-Patterns

Do not ship: hero illustrations or screenshots; decorative gradients or glassmorphism; card grids for assignments; skeleton loaders (data is bundled — nothing loads); spinners on phase or role change; toasts; modals other than the native `<select>` popup; icon-only buttons without accessible names — the Ko-fi link has an `aria-label` and visible tooltip, and the theme picker carries `aria-label` and `title`; FFXIV-themed ornamental borders, scroll textures, or job-color backgrounds; a second accent color; text below 0.75rem; animation on the assignment list.

Two that are specifically tempting here:

- **Job colors.** FFXIV has a color per job and it is genuinely useful in-game. It is wrong here: the app already shows one player's assignments, so the color would be constant on screen and carry no information — while costing the accent its meaning and the design its contrast guarantees.
- **A density toggle.** PiP already *is* the dense mode. A third density to design, test, and keep in sync buys less than making the two existing views excellent.

---

## 12. Adding to This System

Before adding a component, token, or color, check in order:

1. Does an existing token cover it? Reuse beats adding.
2. Does it answer *"what do I need to mit during this phase?"* (PRD §1)? If not, it is secondary or cut.
3. Does it survive 280px wide, grayscale, and 200% zoom?
4. Does it work with no icons, no color, and no motion?

A new color token needs a contrast check in both themes and definitions on bare `:root` before either dark block. A new size needs a place in the type scale, not a one-off value. Anything failing (3) or (4) is not a style problem — it is the wrong idea.
