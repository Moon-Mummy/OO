# chore(ci): share Brand sweep & full lint gates between ci.yml and lefthook.yml to stop main hygiene breakages (47 failed CI runs)

- **Target Repository:** `Mostafa-Taher-git/Greeneek`
- **Labels:** `build`, `security`, `cleanup`

---

## Problem

**47 failed `CI` runs** failed in static hygiene gates — **`Brand sweep` (12 runs)**, **`Secret scan (gitleaks)` (3 runs)**, and **`Run pnpm lint` (32 general lint runs + 5 `PageEntry[]`/`DocsPage[]` runs = 37 runs; 5 Dependabot package-upgrade lint runs are tracked in the Dependabot grouping issue, leaving 47 runs here)** — primarily because **key CI gates in `.github/workflows/ci.yml` are absent from local Git hooks (`lefthook.yml`) and `main` has no required status-check ruleset**.

### Concrete local-vs-CI gate gaps on `main` (`d8b4a95`)

1. **`Brand sweep` exists only inline in `.github/workflows/ci.yml` (`lines 32–44`), not in `scripts/` or `lefthook.yml`**:
   ```yaml
   - name: Brand sweep
     run: |
       hits=$(git grep -niE 'deepseek|\bdsh\b' -- \
         ':!THIRD_PARTY_NOTICES.md' \
         ':!README.md' \
         ':!vendor/**' \
         ':!pnpm-lock.yaml' \
         ':!.github/workflows/ci.yml' || true)
   ```
   Because `lefthook.yml` never runs this check locally (neither on staged files in `pre-commit` nor in `pre-push`), commits touching `.agents/notes/` or docs repeatedly passed local hooks (`lint`, `typecheck`) and then failed `Brand sweep` on `main` — including **8 runs in the last few days alone** (`CI #199`–`#204`, `#207`, `#208`, plus `#42`, `#45`, `#46`, `#47`).
2. **Staged `.oxlintrc.staged.json` vs full `pnpm lint` gap**:
   - `lefthook.yml` runs `scripts/run-oxlint.ts --config .oxlintrc.staged.json` only on `*.{ts,tsx,mts,cts,mjs}` in `pre-commit` and runs `pnpm run typecheck` in `pre-push`, whereas CI runs full `pnpm lint` (including repo-wide lint/doc/type-aware rules). As recently as [`CI #214`](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/40381758691) and [`CI #215`](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/40381940788), pushes to `main` failed `Run pnpm lint`.
3. **`Secret scan (gitleaks)` (`CI #128`, `#130`, `#134`)**:
   - Triggered across both `main` (`#128`, `#134`) and unrelated Dependabot PR `#46` (`#130`) when `fetch-depth: 0` history contained flagged high-entropy/fixture tokens prior to cleanup.

## Affected Failed Checks (47 failed runs)

<details open>
<summary>Complete ledger of all 47 Brand sweep, gitleaks, and pnpm lint CI runs</summary>

| Failed Check Run | Trigger | Ref / PR / Tag | Commit | Failing Job & Step | Diagnostic / Title | Status |
|---|---|---|---|---|---|---|
| [CI #215](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/40381940788) | `push` | `main` | `a3ca01b` | `ci (22)` → `Run pnpm lint` | Process completed with exit code 1. | ⚪ Historical |
| [CI #214](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/40381758691) | `push` | `main` | `761569c` | `ci (22)` → `Run pnpm lint` | Process completed with exit code 1. | ⚪ Historical |
| [CI #208](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/40253803623) | `push` | `main` | `0435a14` | `ci (22)` → `Brand sweep` | Process completed with exit code 1. | ⚪ Historical |
| [CI #207](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/40253349183) | `push` | `main` | `240ae91` | `ci (22)` → `Brand sweep` | Process completed with exit code 1. | ⚪ Historical |
| [CI #204](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/40241259971) | `push` | `main` | `40f2538` | `ci (22)` → `Brand sweep` | Process completed with exit code 1. | ⚪ Historical |
| [CI #203](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/40240871405) | `push` | `main` | `c72b067` | `ci (22)` → `Brand sweep` | Process completed with exit code 1. | ⚪ Historical |
| [CI #202](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/40234675062) | `push` | `main` | `18db750` | `ci (22)` → `Brand sweep` | Process completed with exit code 1. | ⚪ Historical |
| [CI #201](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/40229742407) | `push` | `main` | `66941ad` | `ci (22)` → `Brand sweep` | Process completed with exit code 1. | ⚪ Historical |
| [CI #200](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/40226657795) | `push` | `main` | `7cc1aab` | `ci (22)` → `Brand sweep` | Process completed with exit code 1. | ⚪ Historical |
| [CI #199](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/40226140761) | `push` | `main` | `75fd3ce` | `ci (22)` → `Brand sweep` | Process completed with exit code 1. | ⚪ Historical |
| [CI #190](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/40181167311) | `push` | `main` | `d88d44b` | `ci (22)` → `Run pnpm lint` | Process completed with exit code 1. | ⚪ Historical |
| [CI #181](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/40106951158) | `push` | `main` | `1ab9ca2` | `ci (22)` → `Brand sweep` | Process completed with exit code 1. | ⚪ Historical |
| [CI #173](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/40034215137) | `push` | `main` | `52b9a2a` | `ci (22)` → `Brand sweep` | Process completed with exit code 1. | ⚪ Historical |
| [CI #172](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/40033166693) | `push` | `main` | `390471f` | `ci (22)` → `Brand sweep` | Process completed with exit code 1. | ⚪ Historical |
| [CI #169](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/40016718994) | `push` | `main` | `449df98` | `ci (22)` → `Run pnpm lint` | Process completed with exit code 1. | ⚪ Historical |
| [CI #146](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34756169129) | `push` | `main` | `88e6c8f` | `ci (22)` → `Run pnpm lint` | Process completed with exit code 1. | ⚪ Historical |
| [CI #135](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34596239211) | `push` | `main` | `f9943b7` | `ci (22)` → `Brand sweep` | Process completed with exit code 1. | ⚪ Historical |
| [CI #134](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34594242668) | `push` | `main` | `b3dfef6` | `ci (22)` → `Secret scan (gitleaks)` | ERROR: Unexpected exit code [1] | ⚪ Historical |
| [CI #130](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34508041526) | `pull_request` | PR #46 (closed) | `7e86529` | `ci (22)` → `Secret scan (gitleaks)` | ERROR: Unexpected exit code [1] | ⚪ Historical |
| [CI #128](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34507621683) | `push` | `main` | `c1d1889` | `ci (22)` → `Secret scan (gitleaks)` | fix(tests): single React copy, act-flushed timers, drop obsolete cases | ⚪ Historical |
| [CI #126](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34444991097) | `push` | `main` | `68203b1` | `ci (22)` → `Run pnpm lint` | Process completed with exit code 1. | ⚪ Historical |
| [CI #125](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34438249690) | `push` | `main` | `3cce5d0` | `ci (22)` → `Run pnpm lint` | Process completed with exit code 1. | ⚪ Historical |
| [CI #124](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34434696513) | `push` | `main` | `64a48f3` | `ci (22)` → `Run pnpm lint` | Process completed with exit code 1. | ⚪ Historical |
| [CI #123](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34433185570) | `push` | `main` | `558387a` | `ci (22)` → `Run pnpm lint` | Process completed with exit code 1. | ⚪ Historical |
| [CI #122](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34429851301) | `push` | `main` | `9d2ed5b` | `ci (22)` → `Run pnpm lint` | Process completed with exit code 1. | ⚪ Historical |
| [CI #121](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34428979579) | `push` | `main` | `f4d62ce` | `ci (22)` → `Run pnpm lint` | Process completed with exit code 1. | ⚪ Historical |
| [CI #120](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34428157305) | `push` | `main` | `84068fc` | `ci (22)` → `Run pnpm lint` | Process completed with exit code 1. | ⚪ Historical |
| [CI #119](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34426991201) | `push` | `main` | `fbf70cb` | `ci (22)` → `Run pnpm lint` | Process completed with exit code 1. | ⚪ Historical |
| [CI #118](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34426533955) | `push` | `main` | `fe0a314` | `ci (22)` → `Run pnpm lint` | Process completed with exit code 1. | ⚪ Historical |
| [CI #117](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34425605422) | `push` | `main` | `b796ec0` | `ci (22)` → `Run pnpm lint` | Process completed with exit code 1. | ⚪ Historical |
| [CI #116](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34420311609) | `push` | `main` | `119935f` | `ci (22)` → `Run pnpm lint` | Process completed with exit code 1. | ⚪ Historical |
| [CI #115](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34413906692) | `push` | `main` | `1d3c0a3` | `ci (22)` → `Run pnpm lint` | Process completed with exit code 1. | ⚪ Historical |
| [CI #114](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34413782024) | `pull_request` | PR #49 (merged) | `5ea58c5` | `ci (22)` → `Run pnpm lint` | Process completed with exit code 1. | ⚪ Historical |
| [CI #108](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34394527283) | `push` | `main` | `c13840f` | `ci (22)` → `Run pnpm lint` | Process completed with exit code 1. | ⚪ Historical |
| [CI #86](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34323695583) | `push` | `main` | `f49d2db` | `ci (22)` → `Run pnpm lint` | Process completed with exit code 1. | ⚪ Historical |
| [CI #85](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34321242701) | `push` | `main` | `efccd51` | `ci (22)` → `Run pnpm lint` | Process completed with exit code 1. | ⚪ Historical |
| [CI #84](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34320903095) | `push` | `main` | `958b85c` | `ci (22)` → `Run pnpm lint` | Process completed with exit code 1. | ⚪ Historical |
| [CI #83](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34320449383) | `push` | `main` | `f1357be` | `ci (22)` → `Run pnpm lint` | Process completed with exit code 1. | ⚪ Historical |
| [CI #82](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34320147921) | `push` | `main` | `8e0e2fb` | `ci (22)` → `Run pnpm lint` | Process completed with exit code 1. | ⚪ Historical |
| [CI #81](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34317557132) | `pull_request` | PR #40 (closed) | `76e3bbd` | `ci (22)` → `Run pnpm lint` | Type 'PageEntry[]' is not assignable to type 'DocsPage[]'. | ⚪ Historical |
| [CI #80](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34317542446) | `pull_request` | PR #38 (closed) | `92aa1bb` | `ci (22)` → `Run pnpm lint` | Type 'PageEntry[]' is not assignable to type 'DocsPage[]'. | ⚪ Historical |
| [CI #79](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34317534612) | `pull_request` | PR #37 (closed) | `129950e` | `ci (22)` → `Run pnpm lint` | Type 'PageEntry[]' is not assignable to type 'DocsPage[]'. | ⚪ Historical |
| [CI #78](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34317528930) | `pull_request` | PR #41 (closed) | `40f5138` | `ci (22)` → `Run pnpm lint` | Type 'PageEntry[]' is not assignable to type 'DocsPage[]'. | ⚪ Historical |
| [CI #77](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34317273214) | `push` | `main` | `a4b5124` | `ci (22)` → `Run pnpm lint` | Type 'PageEntry[]' is not assignable to type 'DocsPage[]'. | ⚪ Historical |
| [CI #42](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33982723978) | `push` | `main` | `c25c382` | `ci (22)` → `Run pnpm lint` | Process completed with exit code 1. | ⚪ Historical |
| [CI #40](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33977437220) | `push` | `main` | `2c7cd99` | `ci (22)` → `Run pnpm lint` | Process completed with exit code 1. | ⚪ Historical |
| [CI #39](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33971277725) | `push` | `main` | `0d2c1e4` | `ci (22)` → `Run pnpm lint` | Process completed with exit code 1. | ⚪ Historical |

</details>

## Work

- [ ] Extract `Brand sweep` from inline YAML in `.github/workflows/ci.yml` (`lines 32–44`) into a standalone script (e.g. `scripts/verify-brand-sweep.mjs` or `scripts/check-brand-sweep.sh`), invoke that single script from both `.github/workflows/ci.yml` and `lefthook.yml` (`pre-commit` / `pre-push`), and add unit coverage if placed under `scripts/*.ts`.
- [ ] Run `pnpm run lint` alongside `pnpm run typecheck` in `lefthook.yml` `pre-push` (or document why if intentionally omitted) so `.oxlintrc.staged.json` vs full `.oxlintrc.json` deltas are caught before `git push`.
- [ ] Configure a GitHub branch ruleset on `main` requiring `ci (22)` to pass before refs update, preventing broken `lint` / `Brand sweep` commits from landing on `main` and breaking concurrent PRs (as happened in `CI #78`–`#81` and `CI #130`).

## Acceptance criteria

- [ ] `Brand sweep` logic lives in one script shared by `lefthook.yml` and `.github/workflows/ci.yml` (no duplicated regex/pathspecs).
- [ ] Local `pre-push` hooks reject both brand-sweep violations and full `pnpm lint` failures before commits reach `origin/main`.

## References

- `.github/workflows/ci.yml` (`lines 29–46`)
- `lefthook.yml` (`lines 1–39`)
- Roadmap tracking: #86 (`#79 — CI parity`, `#83 — verification-gate scripts`)
