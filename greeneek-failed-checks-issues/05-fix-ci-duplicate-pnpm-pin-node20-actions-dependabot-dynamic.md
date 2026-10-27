# fix(ci): remove duplicate pnpm version pin in workflows and upgrade Node 20 actions (CI #5..#38, #41 & Dependabot #2, #5, #22, #34, #94)

- **Target Repository:** `Mostafa-Taher-git/Greeneek`
- **Labels:** `bug`, `build`, `tech-debt`

---

## Problem

This issue tracks three closely related CI / workflow-infrastructure check failures (**40 failed workflow runs + 1 cancelled dynamic run**), including [`CI #5` — **Import rebranded DeepSeek Harness**](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33712871035) (PR #11) and two **still-live hazards** in `.github/workflows/ci.yml` and `.github/workflows/release-desktop.yml` on `main` (`d8b4a95`).

### 1. Live latent bug: duplicate `pnpm` version pin in workflows (`CI #5`–`#38`, 34 failed runs)

In [`CI #5` (`Import rebranded DeepSeek Harness`)](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33712871035) through [`CI #38`](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33951262149) (34 consecutive pushes and PRs), `pnpm/action-setup` failed immediately at step 3 with:

```text
Error: Multiple versions of pnpm specified:
  - version 9.15.4 in the GitHub Action config with the key "version"
  - version pnpm@11.7.0 in the package.json with the key "packageManager"
Remove one of these versions to avoid version mismatch errors like ERR_PNPM_BAD_PM_VERSION
```

Instead of removing `with: version:` from the workflow as `pnpm/action-setup` instructs, the earlier fix bumped the workflow YAML literal to `version: 11.7.0`. **Both `.github/workflows/ci.yml` (`line 22`) and `.github/workflows/release-desktop.yml` (`lines 78, 139`) still hardcode `version: 11.7.0` alongside `"packageManager": "pnpm@11.7.0"` in `package.json` today.** Consequently:
- Every Dependabot `pnpm` update (e.g. PR #40 `bump pnpm from 11.7.0 to 11.21.0`) or the planned `#64` upgrade (`pnpm 11.28.5` in #86) that updates `package.json#packageManager` will immediately fail `pnpm/action-setup` again unless `with: version:` is removed from both workflows.
- [`CI #41`](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33982376196) subsequently failed at `Run pnpm install --frozen-lockfile` while reconciling the lockfile transition.

### 2. Live warning on every workflow run: deprecated Node 20 GitHub Actions

Every single job in `CI` and `Desktop release` currently emits GitHub's runner warning:

```text
Node.js 20 is deprecated. The following actions target Node.js 20 but are being forced to run on Node.js 24:
actions/checkout@v4, actions/setup-node@v4, pnpm/action-setup@v4.
```

(PR #90 is currently open for `actions/download-artifact@v7`, while `actions/checkout`, `actions/setup-node`, `actions/upload-artifact`, and `pnpm/action-setup` remain on `@v4` across `ci.yml` and `release-desktop.yml`.)

### 3. `Dependabot Updates` (`dynamic`) workflow failures (5 failed + 1 cancelled)

Five scheduled/dynamic `Dependabot Updates` runs failed at the workflow runner/updater layer:
- [`uv in /python/sdk #94`](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/37367740623) — `The job was not acquired by Runner of type hosted even after multiple attempts`
- [`npm_and_yarn in / for immer #34`](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34317368232) — `Dependabot encountered an error performing the update`
- [`npm_and_yarn in / for koffi #22`](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34129146309) — `Dependabot encountered an error performing the update`
- [`github_actions in /. #5`](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33612981907) & [`github_actions in /. #2`](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33595238564) — `Dependabot encountered an error performing the update` (notice `/.` directory prior to `.github/dependabot.yml` normalization to `/`)
- Cancelled dynamic run: [`npm_and_yarn in /. #129`](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/39161646673)

## Affected Failed Checks (40 failed + 1 cancelled runs)

| Failed Check Run | Trigger | Ref / PR / Tag | Commit | Failing Job & Step | Diagnostic / Title | Status |
|---|---|---|---|---|---|---|
| [uv in /python/sdk - Update #1611248478 #94](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/37367740623) | `dynamic` | `main` | `58e24d9` | `Dependabot` → `(job-level)` | The job was not acquired by Runner of type hosted even after multiple attempts | ⚪ Historical |
| [npm_and_yarn in / for immer - Update #1565390694 #34](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34317368232) | `dynamic` | `main` | `a4b5124` | `Dependabot` → `Run Dependabot` | Dependabot encountered an error performing the update | ⚪ Historical |
| [npm_and_yarn in / for koffi - Update #1561870886 #22](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34129146309) | `dynamic` | `main` | `ef74389` | `Dependabot` → `Run Dependabot` | Dependabot encountered an error performing the update | ⚪ Historical |
| [CI #41](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33982376196) | `push` | `main` | `da80041` | `ci (22)` → `Run pnpm install --frozen-lockfile` | Process completed with exit code 1. | ⚪ Historical |
| [CI #38](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33951262149) | `push` | `main` | `7471420` | `ci (20)` → `Run pnpm/action-setup@v4` | Error: Multiple versions of pnpm specified: | ⚪ Historical |
| [CI #37](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33915145653) | `pull_request` | PR #35 (closed) | `d3cd319` | `ci (20)` → `Run pnpm/action-setup@v4` | Error: Multiple versions of pnpm specified: | ⚪ Historical |
| [CI #36](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33915048385) | `pull_request` | PR #34 (closed) | `dec44b5` | `ci (20)` → `Run pnpm/action-setup@v4` | Error: Multiple versions of pnpm specified: | ⚪ Historical |
| [CI #35](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33914950583) | `pull_request` | PR #33 (closed) | `f2f21bc` | `ci (20)` → `Run pnpm/action-setup@v4` | Error: Multiple versions of pnpm specified: | ⚪ Historical |
| [CI #34](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33914800114) | `pull_request` | PR #32 (closed) | `47b7179` | `ci (20)` → `Run pnpm/action-setup@v4` | Error: Multiple versions of pnpm specified: | ⚪ Historical |
| [CI #33](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33914712610) | `pull_request` | PR #31 (closed) | `0dc91b6` | `ci (20)` → `Run pnpm/action-setup@v4` | Error: Multiple versions of pnpm specified: | ⚪ Historical |
| [CI #32](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33854823714) | `push` | `main` | `7ff7af0` | `ci (20)` → `Run pnpm/action-setup@v4` | Error: Multiple versions of pnpm specified: | ⚪ Historical |
| [CI #31](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33854602948) | `push` | `main` | `947c253` | `ci (20)` → `Run pnpm/action-setup@v4` | Error: Multiple versions of pnpm specified: | ⚪ Historical |
| [CI #30](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33854392162) | `pull_request` | PR #30 (merged) | `2640346` | `ci (20)` → `Run pnpm/action-setup@v4` | Error: Multiple versions of pnpm specified: | ⚪ Historical |
| [CI #29](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33852297111) | `push` | `main` | `5c3f730` | `ci (20)` → `Run pnpm/action-setup@v4` | Error: Multiple versions of pnpm specified: | ⚪ Historical |
| [CI #28](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33852018267) | `pull_request` | PR #29 (merged) | `cb8714f` | `ci (20)` → `Run pnpm/action-setup@v4` | Error: Multiple versions of pnpm specified: | ⚪ Historical |
| [CI #27](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33837235437) | `push` | `main` | `af86a30` | `ci (20)` → `Run pnpm/action-setup@v4` | Error: Multiple versions of pnpm specified: | ⚪ Historical |
| [CI #26](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33837185882) | `pull_request` | PR #28 (merged) | `28199a8` | `ci (20)` → `Run pnpm/action-setup@v4` | Error: Multiple versions of pnpm specified: | ⚪ Historical |
| [CI #25](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33718440735) | `push` | `main` | `70fe963` | `ci (20)` → `Run pnpm/action-setup@v4` | Error: Multiple versions of pnpm specified: | ⚪ Historical |
| [CI #24](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33718161864) | `pull_request` | PR #27 (merged) | `8e58e99` | `ci (20)` → `Run pnpm/action-setup@v4` | Error: Multiple versions of pnpm specified: | ⚪ Historical |
| [CI #23](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33717438502) | `pull_request` | PR #27 (merged) | `4216cf2` | `ci (20)` → `Run pnpm/action-setup@v4` | Error: Multiple versions of pnpm specified: | ⚪ Historical |
| [CI #22](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33714856830) | `pull_request` | PR #27 (merged) | `54fe469` | `ci (20)` → `Run pnpm/action-setup@v4` | Error: Multiple versions of pnpm specified: | ⚪ Historical |
| [CI #21](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33714525107) | `pull_request` | PR #26 (closed) | `8151655` | `ci (20)` → `Run pnpm/action-setup@v4` | Error: Multiple versions of pnpm specified: | ⚪ Historical |
| [CI #20](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33714463388) | `pull_request` | PR #25 (closed) | `3ba5004` | `ci (20)` → `Run pnpm/action-setup@v4` | Error: Multiple versions of pnpm specified: | ⚪ Historical |
| [CI #19](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33714403901) | `pull_request` | PR #24 (closed) | `b6f38ee` | `ci (20)` → `Run pnpm/action-setup@v4` | Error: Multiple versions of pnpm specified: | ⚪ Historical |
| [CI #18](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33714336352) | `pull_request` | PR #23 (closed) | `078c0a3` | `ci (20)` → `Run pnpm/action-setup@v4` | Error: Multiple versions of pnpm specified: | ⚪ Historical |
| [CI #17](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33714266325) | `pull_request` | PR #22 (closed) | `8ed45f5` | `ci (20)` → `Run pnpm/action-setup@v4` | Error: Multiple versions of pnpm specified: | ⚪ Historical |
| [CI #16](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33713510329) | `pull_request` | PR #21 (closed) | `771a5fb` | `ci (20)` → `Run pnpm/action-setup@v4` | Error: Multiple versions of pnpm specified: | ⚪ Historical |
| [CI #15](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33713443896) | `pull_request` | PR #20 (closed) | `893ba40` | `ci (20)` → `Run pnpm/action-setup@v4` | Error: Multiple versions of pnpm specified: | ⚪ Historical |
| [CI #14](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33713373892) | `pull_request` | PR #19 (closed) | `3df2d66` | `ci (20)` → `Run pnpm/action-setup@v4` | Error: Multiple versions of pnpm specified: | ⚪ Historical |
| [CI #13](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33713311910) | `pull_request` | PR #18 (closed) | `fce6ff6` | `ci (20)` → `Run pnpm/action-setup@v4` | Error: Multiple versions of pnpm specified: | ⚪ Historical |
| [CI #12](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33713248501) | `pull_request` | PR #17 (closed) | `88c589e` | `ci (20)` → `Run pnpm/action-setup@v4` | Error: Multiple versions of pnpm specified: | ⚪ Historical |
| [CI #11](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33713183939) | `pull_request` | PR #16 (closed) | `02b0c50` | `ci (20)` → `Run pnpm/action-setup@v4` | Error: Multiple versions of pnpm specified: | ⚪ Historical |
| [CI #10](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33713168865) | `pull_request` | PR #15 (closed) | `5cb63b0` | `ci (20)` → `Run pnpm/action-setup@v6` | Error: Multiple versions of pnpm specified: | ⚪ Historical |
| [CI #9](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33713164910) | `pull_request` | PR #14 (closed) | `1fd2ac5` | `ci (20)` → `Run pnpm/action-setup@v4` | Error: Multiple versions of pnpm specified: | ⚪ Historical |
| [CI #8](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33713158702) | `pull_request` | PR #13 (closed) | `f07bff4` | `ci (20)` → `Run pnpm/action-setup@v4` | Error: Multiple versions of pnpm specified: | ⚪ Historical |
| [CI #7](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33713154331) | `pull_request` | PR #12 (closed) | `f876c16` | `ci (20)` → `Run pnpm/action-setup@v4` | Error: Multiple versions of pnpm specified: | ⚪ Historical |
| [CI #6](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33713114632) | `push` | `main` | `7071eea` | `ci (20)` → `Run pnpm/action-setup@v4` | Error: Multiple versions of pnpm specified: | ⚪ Historical |
| [CI #5](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33712871035) | `pull_request` | PR #11 (merged) | `6df25d9` | `ci (20)` → `Run pnpm/action-setup@v4` | Error: Multiple versions of pnpm specified: | ⚪ Historical |
| [github_actions in /. - Update #1551862882 #5](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33612981907) | `dynamic` | `main` | `3d6efdf` | `Dependabot` → `Run Dependabot` | Dependabot encountered an error performing the update | ⚪ Historical |
| [github_actions in /. - Update #1551412651 #2](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33595238564) | `dynamic` | `main` | `b66d30c` | `Dependabot` → `Run Dependabot` | Dependabot encountered an error performing the update | ⚪ Historical |

**Cancelled Dependabot dynamic run (for completeness):**
- [`npm_and_yarn in /. - Update #1650347704 #129`](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/39161646673) (`dynamic` on `main` @ `267a3a5`) — `cancelled`

## Work

- [ ] Remove redundant `with: version: 11.7.0` from `pnpm/action-setup` in `.github/workflows/ci.yml` (`line 22`) and `.github/workflows/release-desktop.yml` (`lines 78, 139`) so `package.json#packageManager` is the single source of truth.
- [ ] Upgrade Node-20-targeted workflow actions (`actions/checkout`, `actions/setup-node`, `pnpm/action-setup`, `actions/upload-artifact`, `actions/download-artifact` — see open PR #90) to their Node-24-native major versions across both `.github/workflows/ci.yml` and `.github/workflows/release-desktop.yml`.
- [ ] Verify `scripts/ci-workflow.spec.ts` assertions remain aligned after updating workflow action pins.

## Acceptance criteria

- [ ] Neither `ci.yml` nor `release-desktop.yml` duplicates `packageManager` via `pnpm/action-setup`'s `version` input.
- [ ] `CI` and `Desktop release` runs complete with zero Node.js 20 deprecation annotations.

## References

- Example cited in audit: [`CI #5` — Import rebranded DeepSeek Harness](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33712871035) (PR #11)
- `.github/workflows/ci.yml` (`lines 19–27`), `.github/workflows/release-desktop.yml` (`lines 31, 74–83, 135–144, 188–196`)
- Open PR #90 (`chore(deps): bump actions/download-artifact from 4 to 7`)
- Roadmap tracking: #86 (`#64 — Node 24.9 / pnpm 11.28.5`, `#79 — CI parity`)
