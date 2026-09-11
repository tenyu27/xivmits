# XIVMits

FFXIV raid mits at [xivmits.com](https://xivmits.com).

Mit spreadsheets show all eight players at once. XIVMits filters a community sheet down to your role and job, then lists your actions by phase. You can also open a compact, always-on-top window during pulls.

XIVMits is a viewer. It has no accounts, backend, or editor.

## Using it

1. Open the site or a sheet link such as `xivmits.com/dmu/ikuya/`.
2. Choose a fight, sheet, role, and job.
3. Read your assignments. Use the phase tabs for one phase at a time, or "All phases" for a single scrolling list of the whole fight.
4. Use "Pop out" for the compact, always-on-top window.

The site remembers your selections in this browser. It does not upload them.

The pop-out window needs a browser that supports the [Document Picture-in-Picture API](https://developer.mozilla.org/en-US/docs/Web/API/Document_Picture-in-Picture_API). The main viewer works without it.

## Repository layout

The repo is a Yarn 4 workspace (Corepack picks the version up from
`packageManager` in the root `package.json`). The site is one app in it; the domain model and
the fight data are separate packages so anything built later reads the same
data as the site rather than a copy of it.

```text
apps/
  web/                    xivmits.com — the static viewer (Vite + React)
packages/
  core/                   @xivmits/core — schemas, types, and the name/job resolvers
  encounter-data/         @xivmits/encounter-data — fight data, mit sheets, ability/icon/job maps
scripts/                  maintainer-side importers and the icon fetcher
```

`@xivmits/core` is runtime-agnostic: no React, no DOM, no build-tool
assumptions. `@xivmits/encounter-data` owns the canonical JSON and exposes a
`loadCatalog()` that validates it — apps import the package, they never fetch
the data over HTTP.

## Development

```bash
yarn install       # install every workspace
yarn dev           # vite dev server for apps/web
yarn build         # production build -> apps/web/dist
yarn lint          # oxlint
yarn typecheck     # tsc -b in every workspace
yarn test          # schema + catalog tests
```

## Deployment

`xivmits.com` is a static site on **GitHub Pages**. `.github/workflows/deploy.yml`
builds `apps/web` on a push to `main` and uploads `apps/web/dist`; the custom
domain comes from `apps/web/public/CNAME`. There is no server runtime.

## Credits

Each sheet credits its author and links to the source.

Ability icons and FINAL FANTASY XIV content are the property of SQUARE ENIX CO., LTD., used under the [FFXIV Materials Usage License](https://support.na.square-enix.com/rule.php?id=5382). Icon data is sourced via [XIVAPI](https://xivapi.com). XIVMits is an unofficial fan project and is not affiliated with or endorsed by Square Enix.
