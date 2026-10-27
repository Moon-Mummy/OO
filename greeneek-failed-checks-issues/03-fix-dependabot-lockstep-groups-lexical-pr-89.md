# fix(deps): group lockstep package families in dependabot.yml to prevent split-version typecheck failures (failing CI #185 on PR #89)

- **Target Repository:** `Mostafa-Taher-git/Greeneek`
- **Labels:** `bug`, `dependencies`, `ui`, `build`

---

## Problem

`.github/dependabot.yml` currently configures `npm`, `uv`, and `github-actions` updates **without `groups:` rules** for lockstep monorepo families (`lexical` + `@lexical/*`, `tailwindcss` + `@tailwindcss/*`, `@opentelemetry/*`, `vite` + `@vitejs/*`) and references two non-existent labels (`kind/dependency` and `area/infra`, whereas the repository's actual label set uses `dependencies` and `build`).

As a direct result, **open PR #89** (`chore(deps-dev): bump @lexical/headless from 0.49.0 to 0.51.0`, branch `dependabot/npm_and_yarn/lexical/headless-0.51.0` @ `e62750c`) is currently failing **All checks have failed** in [`CI #185`](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/40128565672) (`ci (22)` → `Run pnpm typecheck`).

### Exact `pnpm typecheck` failure on Open PR #89 (`CI #185`)

Because Dependabot bumped `@lexical/headless` (`0.49.0 → 0.51.0`) alone while `lexical` and `@lexical/react` stayed at `0.49.0`, pnpm resolves two distinct `LexicalEditor` / `LexicalNodeConfig` nominal class instances in `.pnpm`:

- `packages/client/ui-conversation/tests/lexical-editor-core.client.spec.tsx:45`:
  ```text
  Type 'import(".../node_modules/.pnpm/lexical@0.51.0_typescript@6.0.3/node_modules/lexical/dist/LexicalEditor").LexicalEditor'
  is not assignable to type
  'import(".../node_modules/.pnpm/lexical@0.49.0_typescript@6.0.3/node_modules/lexical/dist/LexicalEditor").LexicalEditor'.
  ```
- `packages/client/ui-conversation/tests/lexical-editor-core.client.spec.tsx:47`:
  ```text
  Type 'typeof ReferenceChipNode' is not assignable to type 'LexicalNodeConfig'.
  Type 'typeof TextRefNode' is not assignable to type 'LexicalNodeConfig'.
  ```

### Related Dependabot package-family & major-upgrade CI failures

The same ungrouped / major-bump configuration previously caused 8 additional Dependabot PR `CI` failures:
- [`CI #159`](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34779896456) (`bump vite from 5.4.21 to 8.2.1`, PR #61) — split Vite `5.4.21` vs `8.2.1` plugin types failed `pnpm lint`.
- [`CI #111`](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34399503253) (`tailwindcss 4.1.17 → 4.2.2`, PR #47) & [`CI #113`](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34399740338) (`@tailwindcss/vite 4.1.17 → 4.2.2`, PR #49) — split Tailwind v4 packages opened as separate PRs and failed `pnpm lint`.
- [`CI #112`](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34399616589) (`@opentelemetry/otlp-exporter-base`, PR #47), [`CI #109`](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34399225471) (`shiki 4.3.1 → 4.4.3`, PR #44), [`CI #110`](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34399378910) (`tailwind-merge 3.4.0 → 3.5.0`, PR #45) — failed `pnpm lint`.
- [`CI #69`](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34273120904) (`chokidar 4.0.3 → 5.0.0`, PR #38) — major bump broke `packages/experimental/webworker-runtime/tests/node/chokidar.spec.ts` (`waits for a write burst to stabilize before publishing one add`).
- [`CI #58`](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34129360641) (`js-yaml 4.2.0 → 5.2.3`, PR #30) — major bump removed `Schema.prototype.extend` (`Property 'extend' does not exist on type 'Schema'`).

Additionally, two stale Dependabot branches from closed PRs remain pushed on `origin`:
- `dependabot/npm_and_yarn/opentelemetry/api-logs-0.221.0` (`b58ab7c`)
- `dependabot/npm_and_yarn/publint-0.3.23` (`ff0c947`)

## Affected Failed Checks (9 failed runs)

| Failed Check Run | Trigger | Ref / PR / Tag | Commit | Failing Job & Step | Diagnostic / Title | Status |
|---|---|---|---|---|---|---|
| [CI #185](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/40128565672) | `pull_request` | PR #89 (open) | `e62750c` | `ci (22)` → `Run pnpm typecheck` | Type 'typeof TextRefNode' is not assignable to type 'LexicalNodeConfig'. | 🔴 Active |
| [CI #159](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34779896456) | `pull_request` | PR #53 (closed) | `0622dd7` | `ci (22)` → `Run pnpm lint` | Argument of type 'import("/home/runner/work/Greeneek/Greeneek/node_modules/.pnpm/vite@5.4.21_@types+node@26.2. | ⚪ Historical |
| [CI #113](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34399740338) | `pull_request` | PR #48 (closed) | `98bed4d` | `ci (22)` → `Run pnpm lint` | Process completed with exit code 1. | ⚪ Historical |
| [CI #112](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34399616589) | `pull_request` | PR #47 (closed) | `9752bfa` | `ci (22)` → `Run pnpm lint` | Process completed with exit code 1. | ⚪ Historical |
| [CI #111](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34399503253) | `pull_request` | PR #46 (closed) | `320b63f` | `ci (22)` → `Run pnpm lint` | Process completed with exit code 1. | ⚪ Historical |
| [CI #110](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34399378910) | `pull_request` | PR #45 (closed) | `daa0113` | `ci (22)` → `Run pnpm lint` | Process completed with exit code 1. | ⚪ Historical |
| [CI #109](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34399225471) | `pull_request` | PR #44 (closed) | `6998ecf` | `ci (22)` → `Run pnpm lint` | Process completed with exit code 1. | ⚪ Historical |
| [CI #69](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34273120904) | `pull_request` | PR #38 (closed) | `65fcb5c` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/experimental/webworker-runtime/tests/node/chokidar.spec.ts > 'Chokidar 4 from settings | ⚪ Historical |
| [CI #58](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34129360641) | `pull_request` | PR #33 (closed) | `eebb3c8` | `ci (22)` → `Run pnpm lint` | Property 'extend' does not exist on type 'Schema'. | ⚪ Historical |

## Work

- [ ] Add `groups:` to `.github/dependabot.yml` under `package-ecosystem: "npm"` so lockstep families update atomically in one PR:
  - `lexical`: `["lexical", "@lexical/*"]`
  - `tailwind`: `["tailwindcss", "@tailwindcss/*"]`
  - `opentelemetry`: `["@opentelemetry/*"]`
  - `vite`: `["vite", "@vitejs/*", "vitest", "@vitest/*"]`
- [ ] Replace non-existent labels `kind/dependency` and `area/infra` in `.github/dependabot.yml` (`lines 15–17, 25–27, 34–36`) with valid repository labels (`dependencies`, `build`).
- [ ] Upgrade `lexical` + all `@lexical/*` packages together to `0.51.0` (superseding/updating PR #89) and verify `packages/client/ui-conversation` passes `pnpm typecheck` and `pnpm test`.
- [ ] Prune the two orphaned branches (`dependabot/npm_and_yarn/opentelemetry/api-logs-0.221.0` and `dependabot/npm_and_yarn/publint-0.3.23`).

## Acceptance criteria

- [ ] `.github/dependabot.yml` groups `lexical`/`@lexical/*`, `tailwindcss`/`@tailwindcss/*`, `@opentelemetry/*`, and `vite`/`vitest` families and uses existing repo labels.
- [ ] PR #89 is resolved (either updated as a lockstep `lexical` `0.51.0` bump with green `CI` or superseded by the grouped Dependabot PR).
- [ ] No orphaned `dependabot/*` branches without open PRs remain on `origin`.

## References

- PR #89 (`chore(deps-dev): bump @lexical/headless from 0.49.0 to 0.51.0`)
- Failed check run: [`CI #185`](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/40128565672) / job [`120975174541`](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/40128565672/job/120975174541)
- `.github/dependabot.yml`
