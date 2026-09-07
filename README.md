# XIVMits

See your FFXIV mitigation assignments by phase at **[xivmits.com](https://xivmits.com)**.

Mit spreadsheets show all eight players at once. XIVMits filters a community sheet down to your role and job, then lists your actions by phase. You can also open a compact, always-on-top window during pulls.

XIVMits is a viewer. It has no accounts, backend, or editor.

## Using it

1. Open the site or a sheet link such as `xivmits.com/dmu/ikuya/`.
2. Choose a fight, sheet, role, and job.
3. Select a phase.
4. Use **Pop out** for the compact window.

The site remembers your selections in this browser. It does not upload them.

The pop-out window needs a browser that supports the [Document Picture-in-Picture API](https://developer.mozilla.org/en-US/docs/Web/API/Document_Picture-in-Picture_API). The main viewer works without it.

## Contributing a mit sheet

Sheets are plain JSON in `data/fights/`:

```text
data/fights/<fightId>/fight.json        the encounter and its phases
data/fights/<fightId>/<sheetId>.json    one complete party plan
```

Add or edit a file, then open a pull request. [The data contract](docs/PRD.md) lives in PRD section 9. [`src/data/schema.ts`](src/data/schema.ts) validates every sheet during the build, so malformed data fails CI.

Scripts in `scripts/` convert the original spreadsheets. Credit the author and link the source sheet.

After adding a sheet, refresh the ability icons:

```bash
python3 scripts/fetch_icons.py
```

The script resolves action names through [XIVAPI](https://xivapi.com), downloads new icons to `public/icons/`, updates `data/icons.json`, and removes unused icons. Commit the icons and map together. The deployed site never calls XIVAPI. The build fails if the map points to a missing file.

Instructions such as `Party Mit (GNB/DRK)` and `LB3` do not map to one ability, so they have no icon. Their text remains visible.

## Development

Use Yarn. `yarn.lock` is the only package lockfile.

```bash
yarn install
yarn run dev       # vite dev server; editing data/ hot-reloads
yarn run build     # tsc -b && vite build
yarn run lint      # oxlint
yarn run preview   # serve dist/
```

The site uses React 19, TypeScript, Vite 8, Mantine, and plain CSS. A Vite plugin compiles `data/fights/**` into the bundle and creates a static route for each sheet. The deployed viewer makes no network requests after it loads.

## Credits

Each sheet credits its author and links to the source.

Ability icons and FINAL FANTASY XIV content are the property of **SQUARE ENIX CO., LTD.**, used under the [FFXIV Materials Usage License](https://support.na.square-enix.com/rule.php?id=5382). Icon data is sourced via [XIVAPI](https://xivapi.com). XIVMits is an unofficial fan project and is not affiliated with or endorsed by Square Enix.

## Docs

- [docs/PRD.md](docs/PRD.md) — scope, navigation model, data architecture, non-goals
- [docs/DESIGN.md](docs/DESIGN.md) — tokens, components, responsive rules, PiP styling, anti-patterns
- [AGENTS.md](AGENTS.md) — conventions and guardrails for coding agents
