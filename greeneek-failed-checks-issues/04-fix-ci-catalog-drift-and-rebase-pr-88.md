# fix(ci): rebase PR #88 (@anthropic-ai/sdk) past main catalog drift and guard generated catalogs pre-push (CI #184 + 32 CI runs)

- **Target Repository:** `Mostafa-Taher-git/Greeneek`
- **Labels:** `bug`, `build`, `dependencies`

---

## Problem

**Open PR #88** (`chore(deps): bump @anthropic-ai/sdk from 0.93.0 to 0.128.0`, branch `dependabot/npm_and_yarn/anthropic-ai/sdk-0.128.0` @ `1cab820`) is currently failing **All checks have failed** in [`CI #184`](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/40128456255) (`ci (22)` → `Run pnpm test -- --coverage --reporter=verbose`), **not** because of `@anthropic-ai/sdk`, but because Dependabot branched from `main` while a committed generated catalog artifact was out of sync with TypeScript JSDoc on `AgentPresets.resolve()`:

```text
FAIL [thread-safe] packages/typert/generator/tests/cordis-catalog.spec.ts > Typert-backed Cordis catalog > reproduces every committed catalog artifact byte for byte
AssertionError: expected '<!-- BEGIN GENERATED cordis-surface (…' to be '<!-- BEGIN GENERATED cordis-surface (…' // Object.is equality
```

### Systemic pattern across 33 failed `CI` runs

Across the repository's history, committed catalog freshness assertions (`cordis-catalog.spec.ts` **30 runs**, `gen-tool-catalog.spec.ts` **2 runs**, `gen-plugin-catalog.spec.ts` **1 run** = **33 failed `CI` runs**) have been the single largest cause of collateral PR breakages:

1. `lefthook.yml` automatically regenerates and stages `THIRD_PARTY_NOTICES.md` during `pre-commit`, **but has no hook or `pre-push` check for `cordis-catalog`, `tool-catalog`, or `plugin-catalog`**.
2. Because `main` does not enforce a branch-protection ruleset requiring `ci (22)` to pass before updating `main`, commits with un-regenerated catalogs landed on `main` (e.g. `CI #67`–`#75`, `#160`–`#162`, `#170`–`#182`, `#186`, `#191`, `#193`).
3. Every Dependabot PR opened during those windows — including completely unrelated Python (`pydantic` `#163`, `hatchling` `#167`–`#168`), GitHub Actions (`softprops/action-gh-release` `#164`, `actions/upload-artifact` `#165`, `actions/setup-node` `#166`), and SDK (`@anthropic-ai/sdk` `#184` on **open PR #88**) updates — immediately failed `CI` on `cordis-catalog.spec.ts`.

## Affected Failed Checks (33 failed runs)

| Failed Check Run | Trigger | Ref / PR / Tag | Commit | Failing Job & Step | Diagnostic / Title | Status |
|---|---|---|---|---|---|---|
| [CI #184](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/40128456255) | `pull_request` | PR #88 (open) | `1cab820` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/typert/generator/tests/cordis-catalog.spec.ts > Typert-backed Cordis catalog > reproduc | 🔴 Active |
| [CI #195](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/40214879934) | `push` | `main` | `625a9ba` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/preset/agent-presets/tests/shipped-root.spec.ts > the shipped preset root > supplies th | ⚪ Historical |
| [CI #193](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/40193405861) | `push` | `main` | `4cc0500` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/core/tools/tests/gen-tool-catalog.spec.ts > gen-tool-catalog collectToolCatalog > boots | ⚪ Historical |
| [CI #191](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/40182392531) | `push` | `main` | `6e13991` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] scripts/gen-plugin-catalog.spec.ts > gen-plugin-catalog > lists every workspace package in the c | ⚪ Historical |
| [CI #186](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/40135550773) | `push` | `main` | `085131b` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/core/tools/tests/gen-tool-catalog.spec.ts > gen-tool-catalog collectToolCatalog > boots | ⚪ Historical |
| [CI #182](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/40108702182) | `push` | `main` | `267a3a5` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/typert/generator/tests/cordis-catalog.spec.ts > Typert-backed Cordis catalog > reproduc | ⚪ Historical |
| [CI #171](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/40023116679) | `push` | `main` | `ebfdbd0` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/typert/generator/tests/cordis-catalog.spec.ts > Typert-backed Cordis catalog > reproduc | ⚪ Historical |
| [CI #170](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/40018902731) | `push` | `main` | `f861d1e` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/typert/generator/tests/cordis-catalog.spec.ts > Typert-backed Cordis catalog > reproduc | ⚪ Historical |
| [CI #168](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/39667429411) | `pull_request` | PR #61 (closed) | `f94a3f0` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/typert/generator/tests/cordis-catalog.spec.ts > Typert-backed Cordis catalog > reproduc | ⚪ Historical |
| [CI #167](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/39161652068) | `pull_request` | PR #60 (closed) | `8de2883` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/typert/generator/tests/cordis-catalog.spec.ts > Typert-backed Cordis catalog > reproduc | ⚪ Historical |
| [CI #166](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/37837298231) | `pull_request` | PR #59 (closed) | `fc993f2` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/typert/generator/tests/cordis-catalog.spec.ts > Typert-backed Cordis catalog > reproduc | ⚪ Historical |
| [CI #165](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/37679518100) | `pull_request` | PR #58 (closed) | `cf63a9d` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/typert/generator/tests/cordis-catalog.spec.ts > Typert-backed Cordis catalog > reproduc | ⚪ Historical |
| [CI #164](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/36477398099) | `pull_request` | PR #57 (closed) | `6ebb7e5` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/typert/generator/tests/cordis-catalog.spec.ts > Typert-backed Cordis catalog > reproduc | ⚪ Historical |
| [CI #163](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/36346761456) | `pull_request` | PR #56 (closed) | `e5a0dd0` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/typert/generator/tests/cordis-catalog.spec.ts > Typert-backed Cordis catalog > reproduc | ⚪ Historical |
| [CI #162](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34988109474) | `push` | `main` | `58e24d9` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/typert/generator/tests/cordis-catalog.spec.ts > Typert-backed Cordis catalog > reproduc | ⚪ Historical |
| [CI #75](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34310750585) | `push` | `main` | `1103feb` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/typert/generator/tests/cordis-catalog.spec.ts > Typert-backed Cordis catalog > reproduc | ⚪ Historical |
| [CI #74](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34306299752) | `push` | `main` | `c2e13df` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/typert/generator/tests/cordis-catalog.spec.ts > Typert-backed Cordis catalog > reproduc | ⚪ Historical |
| [CI #73](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34295007476) | `push` | `main` | `d7ac54e` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/typert/generator/tests/cordis-catalog.spec.ts > Typert-backed Cordis catalog > reproduc | ⚪ Historical |
| [CI #72](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34273484492) | `pull_request` | PR #41 (closed) | `7969367` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/typert/generator/tests/cordis-catalog.spec.ts > Typert-backed Cordis catalog > reproduc | ⚪ Historical |
| [CI #71](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34273364727) | `pull_request` | PR #40 (closed) | `6231520` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/typert/generator/tests/cordis-catalog.spec.ts > Typert-backed Cordis catalog > reproduc | ⚪ Historical |
| [CI #70](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34273237086) | `pull_request` | PR #39 (closed) | `11e0efc` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/typert/generator/tests/cordis-catalog.spec.ts > Typert-backed Cordis catalog > reproduc | ⚪ Historical |
| [CI #68](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34273009767) | `pull_request` | PR #37 (closed) | `2b0145b` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/typert/generator/tests/cordis-catalog.spec.ts > Typert-backed Cordis catalog > reproduc | ⚪ Historical |
| [CI #67](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34181394830) | `push` | `main` | `9a4ab78` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/typert/generator/tests/cordis-catalog.spec.ts > Typert-backed Cordis catalog > reproduc | ⚪ Historical |
| [CI #56](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34112260272) | `push` | `main` | `c7236f3` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/typert/generator/tests/cordis-catalog.spec.ts > Typert-backed Cordis catalog > reproduc | ⚪ Historical |
| [CI #55](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34103539242) | `push` | `main` | `a6857e0` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/typert/generator/tests/cordis-catalog.spec.ts > Typert-backed Cordis catalog > reproduc | ⚪ Historical |
| [CI #54](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34102150573) | `push` | `main` | `8e45267` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/typert/generator/tests/cordis-catalog.spec.ts > Typert-backed Cordis catalog > reproduc | ⚪ Historical |
| [CI #53](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34096714395) | `push` | `main` | `5d9e76f` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/typert/generator/tests/cordis-catalog.spec.ts > Typert-backed Cordis catalog > reproduc | ⚪ Historical |
| [CI #52](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34020866764) | `push` | `main` | `0be6524` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/typert/generator/tests/cordis-catalog.spec.ts > Typert-backed Cordis catalog > reproduc | ⚪ Historical |
| [CI #51](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34018122180) | `push` | `main` | `da7b714` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/typert/generator/tests/cordis-catalog.spec.ts > Typert-backed Cordis catalog > reproduc | ⚪ Historical |
| [CI #50](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34010765881) | `push` | `main` | `837e483` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/typert/generator/tests/cordis-catalog.spec.ts > Typert-backed Cordis catalog > reproduc | ⚪ Historical |
| [CI #49](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34005186396) | `push` | `main` | `fb99a16` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/typert/generator/tests/cordis-catalog.spec.ts > Typert-backed Cordis catalog > reproduc | ⚪ Historical |
| [CI #48](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33997619211) | `push` | `main` | `db72ae5` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/typert/generator/tests/cordis-catalog.spec.ts > Typert-backed Cordis catalog > reproduc | ⚪ Historical |
| [CI #47](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33997575861) | `push` | `main` | `84909a9` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/typert/generator/tests/cordis-catalog.spec.ts > Typert-backed Cordis catalog > reproduc | ⚪ Historical |

## Work

- [ ] Rebase open PR #88 (`@dependabot rebase` or manual rebase onto `main` @ `d8b4a95`, where `cordis-catalog.spec.ts` is green) and verify `@anthropic-ai/sdk@0.128.0` passes full `ci (22)` (`lint`, `typecheck`, `test --coverage`).
- [ ] Add a fast catalog freshness pre-push check (or auto-regeneration `pre-commit` job mirroring `third-party notices (staged)` in `lefthook.yml`) when surface/preset/tool/workspace-manifest files change (`gen-cordis-catalog`, `gen-tool-catalog`, `gen-plugin-catalog`).
- [ ] Enable a GitHub repository ruleset on `main` requiring `ci (22)` to pass before pushes/merges so transient catalog drift can never land on `main` and poison downstream Dependabot runs.

## Acceptance criteria

- [ ] Open PR #88 is rebased onto current `main` and its `ci (22)` check run turns green (or any genuine `@anthropic-ai/sdk` `0.128.0` API delta uncovered after rebase is fixed).
- [ ] Local `lefthook.yml` / gate scripts catch `cordis-catalog`, `tool-catalog`, and `plugin-catalog` drift before push.

## References

- Open PR #88 (`chore(deps): bump @anthropic-ai/sdk from 0.93.0 to 0.128.0`)
- Active failed check run: [`CI #184`](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/40128456255) / job [`120974834137`](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/40128456255/job/120974834137)
- `packages/typert/generator/tests/cordis-catalog.spec.ts`, `packages/core/tools/tests/gen-tool-catalog.spec.ts`, `scripts/gen-plugin-catalog.spec.ts`, `lefthook.yml`
