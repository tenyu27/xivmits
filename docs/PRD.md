# XIVMits — PRD

**Domain:** xivmits.com · **Platform:** static web on GitHub Pages · **Version:** V1
**Audience:** FFXIV Savage / Ultimate raiders · **Free, no accounts, no backend**

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
XIVMits

Fight       [Dancing Mad (Ultimate)  ▾]
Mit Sheet   [Community Standard      ▾]
Role / Job  [H2 · Sage               ▾]

[View Mits]
```

Each selector unlocks the next; `View Mits` unlocks when complete. Selections apply immediately where practical — the button may become unnecessary, but V1 keeps it for clarity.

### Fight

Top-level encounter: id, name, optional shortName, type (Savage / Ultimate / Criterion / Other). Category filtering not needed while the encounter count is small.

### Mit Sheet

One encounter may have several sheets — each is one complete party plan agreed on by a group or the community.

Examples: Community Standard, Week 1 Sheet, Melee LB Strat, NAUR Static.

Metadata: id, fightId, name, optional author/source link/description, updated date, phases, slots, assignments. Dropdown shows the short name; details (`Updated Sep 7, 2026`) appear underneath after selection.

### Role / Job

Sheets may be position-based or job-based. Positions: MT, OT, H1, H2, M1, M2, R1, R2. A sheet may map jobs to positions.

Display both when available (**H2 · SGE**), job alone when the plan is job-based (**SGE**). One data model covers both — no separate interfaces.

---

## 5. Focused Mit View

Primary screen.

```text
Dancing Mad (Ultimate)
Community Standard

H2 · SGE                         Open PiP

P1   P2   [P3]   P4   P5

ULTIMATE RELATIVITY
Kerachole

SHELL CRUSHER
Holos + Panhaima

APOCALYPSE
Kerachole
```

Readability over density.

### Phase navigation

The most important interaction. Must stay visible, obvious, compact, usable in PiP and on mobile.

Requirements: one click changes phase; no route transition, spinner, server request, or slowing animation; current phase strongly indicated; selection persists where practical.

Optional (not required for launch): number keys → phase N, ←/→ → prev/next.

### Flexible phase naming

Don't assume P1–P4. Each phase has a short label plus optional long name: `P1, P2A, P2B, Intermission, P3, Enrage` or `P3 — Ultimate Relativity`. Short label drives tabs and PiP; long name is the page heading.

### Mechanics

Fields: id, phase, name, order; optional time and note.

Raiders identify actions by mechanic name, not timestamp. Hierarchy: **mechanic name → mitigation → optional timestamp** — never timestamp-first.

### Assignments

An assignment ties a mechanic to a slot and carries one or more plain-text actions. Ability IDs are not required in V1.

### Assigned-only philosophy

Show mechanics where *this* player has an assignment. If a phase has six damage events and SGE covers three, show those three. Maximizes glanceability. An optional "show all mechanics" toggle is a future addition.

### Ability icons

Icons aid recognition in combat, but cost asset-management and mapping work.

- **V1:** text ability names must work perfectly.
- **V1.1:** add legally usable icon assets.

The UI must never depend on icons to be understandable.

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
│ Holos · Panhaima             │
│                              │
│ APOCALYPSE                   │
│ Kerachole                    │
└──────────────────────────────┘
```

**Keep:** large mechanic names, large mit names/icons, phase buttons, high contrast, minimal chrome.
**Drop:** fight/sheet selection, explanatory text, metadata, source links, footer, extra controls.

Phase switching stays available in PiP, and main window + PiP stay synchronized in both directions.

**Support:** feature-detect `"documentPictureInPicture" in window`. Supported → show **Open PiP**. Unsupported → hide it or say *"Picture-in-Picture isn't supported by this browser."* The normal view must remain fully functional without PiP.

---

## 7. Persistence & Sharing

`localStorage` remembers local selections: `lastFight`, `lastSheetByFight`, `lastRoleBySheet`, `lastPhaseBySheet`. At minimum persist role/job. Nothing is uploaded; no account.

Sheets get stable URLs:

```text
xivmits.com/dmu/community/
xivmits.com/dmu/community/?role=H2&phase=P3   # optional
```

The URL identifies encounter + sheet. Role stays local so the whole group shares one link; query params exist for direct links. Keep URL state human-readable.

**Workflow:** raid lead posts one link in Discord → everyone opens it → first visit asks *"Who are you?"* → they pick **H2 · SGE** → remembered locally → future visits land straight on their assignments. Zero signup.

---

## 8. Design

Mobile-first and responsive: desktop (primary + PiP launch), small second monitor, mobile, tablet. Reading your own assignments must never require horizontal scrolling.

Aesthetic: simple, dark-first, clean, high contrast, utilitarian, slightly game-adjacent without being themed. WTFDIG is the reference point — content selection ahead of decoration.

Avoid: hero illustrations, decorative gradients, complex nav, dashboard cards, marketing sections, heavy animation, ornamental borders.

Themes: prefer system / dark / light; dark-only acceptable for the earliest prototype. Dark mode needs excellent contrast.

**Accessibility:** semantic buttons, keyboard-accessible selectors, visible focus states, adequate contrast, no color-only information, scalable text, ability names readable without icons.

**Empty states:** no assignments for this role/phase → *"No assigned mits for this phase."* No sheet data → *"No mitigation data available for this phase."* Never an unexplained empty list.

**Errors:** invalid URL → show encounter selection. Invalid sheet → *"Mit sheet not found."* + **Choose another sheet**. Stored role missing → clear it and re-prompt. PiP unsupported → normal page still works. Malformed data → build-time validation fails deployment.

---

## 9. Data Architecture

Data lives in the repo, split per encounter/sheet to reduce merge conflicts and ease contributions:

```text
data/fights/
  dmu/
    fight.json
    community.json
    naur.json
  fru/
    fight.json
    sheet-a.json
```

### Fight

```json
{
  "id": "dmu",
  "name": "Dancing Mad (Ultimate)",
  "shortName": "DMU",
  "phases": [
    { "id": "p1", "label": "P1", "name": "Phase 1" },
    { "id": "p2", "label": "P2", "name": "Phase 2" },
    { "id": "p3", "label": "P3", "name": "Phase 3" }
  ]
}
```

### Mit sheet

```json
{
  "id": "community",
  "fightId": "dmu",
  "name": "Community Standard",
  "updated": "2026-09-07",

  "slots": [
    { "id": "MT", "job": "WAR" },
    { "id": "OT", "job": "PLD" },
    { "id": "H1", "job": "SCH" },
    { "id": "H2", "job": "SGE" },
    { "id": "M1", "job": "VPR" },
    { "id": "M2", "job": "DRG" },
    { "id": "R1", "job": "DNC" },
    { "id": "R2", "job": "PCT" }
  ],

  "phases": [
    {
      "id": "p3",
      "mechanics": [
        {
          "id": "ultimate-relativity",
          "name": "Ultimate Relativity",
          "time": "0:23",
          "assignments": { "H2": ["Kerachole"] }
        },
        {
          "id": "shell-crusher",
          "name": "Shell Crusher",
          "time": "1:14",
          "assignments": { "H2": ["Holos", "Panhaima"] }
        },
        {
          "id": "apocalypse",
          "name": "Apocalypse",
          "time": "1:58",
          "assignments": { "H2": ["Kerachole"] }
        }
      ]
    }
  ]
}
```

### Validation

Zod schema at build time, or typed TS data objects. Check: fight exists, phase IDs valid, slot IDs valid, mechanic IDs unique, assignment arrays valid, phase ordering deterministic. Broken plans fail CI.

### Content management

No admin UI in V1. Sheets are added by editing data files → commit → PR → merge → GitHub Actions rebuild + deploy. An editor UI would need persistence infrastructure and greatly expand scope; the maintainer count is small enough that repo-managed content is simpler.

### Spreadsheet conversion

No runtime Google Sheets integration. Existing spreadsheets are converted manually into XIVMits data — avoiding Google APIs, auth, CORS, inconsistent sheet structures, runtime deps, and backend.

A maintainer-only script may later take CSV / Sheet exports → JSON → commit → Pages.

### Source attribution

Each sheet may carry a source (`Source: Community Standard Spreadsheet`) and a **View original sheet** link — useful for the full party plan, verification, and discussion. Original stays secondary to the focused view.

Show a subtle `Updated Sep 7, 2026` so users can judge currency. Keep it out of PiP.

---

## 10. Technology & Hosting

**Stack:** React + TypeScript + Vite. Small footprint, simple static build, easy Pages deploy, good state handling, renders cleanly into the Document PiP DOM, no server assumptions. Astro or vanilla TS would also work.

**Styling:** Tailwind or plain CSS / CSS Modules. No heavyweight component libraries.

**State:** React state + localStorage. No Redux.

**Hosting:** GitHub Pages, custom domain `xivmits.com` with HTTPS.

```text
repo → GitHub Actions → npm install → npm run build → dist/ → GitHub Pages → https://xivmits.com
```

**Routing:** all fights and sheets are known at build time, so **generate static routes** (`/dmu/community/index.html`) for clean URLs. Hash routing (`/#/dmu/community`) is simplest but uglier; an SPA fallback redirect works but adds needless cleverness.

**Performance:** small compressed bundle; no required third-party requests after load; no spinner on phase or role change; PiP opens immediately after interaction; fight data bundled or fetched as small static JSON. Phase and role switching are entirely client-side.

**Offline:** not needed for V1. A service worker / PWA could later cache recent sheets — a natural enhancement, not a launch blocker.

**Search:** not needed in V1. Dropdowns suffice until the encounter count grows.

---

## 11. V1 Scope

Three screens:

1. **Selection** — name, fight, sheet, role/job.
2. **Focus view** — fight, sheet, role/job, phase tabs, assignments, Open PiP, change role/sheet.
3. **PiP** — role/job, phase tabs, assignments.

That's the whole application.

| Feature | V1 |
|---|---:|
| Fight selection | Yes |
| Multiple mit sheets per fight | Yes |
| Role selection + job labels | Yes |
| Phase switching | Yes |
| Role-focused assignments | Yes |
| Mechanic names, multiple mits per mechanic | Yes |
| Optional timestamps | Yes |
| Picture-in-Picture (+ phase switching) | Yes, where supported |
| Local role persistence | Yes |
| Shareable sheet URLs | Yes |
| Mobile responsive | Yes |
| Source sheet link | Yes |
| GitHub Pages hosting | Yes |
| Accounts / backend / database | No |
| User-created plans / mit planner | No |
| Google Sheets live sync | No |
| ACT integration / auto fight tracking | No |
| Community comments / FFLogs / damage calc | No |

---

## 12. Future

Only after the core viewer proves useful:

- ability icons;
- CSV / Google Sheet → JSON converter (maintainer-side);
- PWA / offline mode;
- URL role presets;
- keyboard shortcuts;
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
