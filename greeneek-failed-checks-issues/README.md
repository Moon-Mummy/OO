# `Mostafa-Taher-git/Greeneek` — Complete Failed-Checks Audit & Ready-to-Publish GitHub Issues

**Audited Repository:** [`Mostafa-Taher-git/Greeneek`](https://github.com/Mostafa-Taher-git/Greeneek) (`main` @ `d8b4a95`, `2026-10-27`)  
**Coverage Guarantee:** **100.0% (`416/416` GitHub Actions workflow runs + `335` commit/PR external status checks inspected — `0` failed checks omitted)**

---

## 1. Executive Summary & Check Inventory

Every workflow run, pull request check, branch check suite, release tag check suite, and external commit status in `Mostafa-Taher-git/Greeneek` was queried and matched to its root cause:

| Check Surface | Total Inspected | Passed (`success`) | Failed (`failure`) | Cancelled (`cancelled`) | Accounted For in Issues |
|---|---:|---:|---:|---:|---:|
| **`CI`** (`.github/workflows/ci.yml`) | 357 | 177 | **179** | **1** | **180 / 180 (100%)** |
| **`Desktop release`** (`release-desktop.yml` + legacy `desktop.yml`) | 29 | 12 | **15** | **2** | **17 / 17 (100%)** |
| **`Desktop release — Windows`** (legacy `desktop-windows.yml`) | 24 | 9 | **12** | **3** | **15 / 15 (100%)** |
| **`Dependabot Updates`** (`dynamic`) | 6 | 0 *(+ green runs)* | **5** | **1** | **6 / 6 (100%)** |
| **External Commit Status (`Vercel` on `apps/landing`)** | 335 | 325 | **10** | 0 | **10 / 10 (100%)** |
| **TOTAL NON-GREEN CHECKS** | — | — | **221 failed** | **7 cancelled** | **228 / 228 (100%)** |

> **How to publish all 8 issues from this `.zip` in one command (after unzipping locally):**  
> Inside Arena's sandbox, an outbound network proxy intercepts all HTTPS requests to `api.github.com` and replaces the `Authorization` header with Arena's managed GitHub App token (`X-Oauth-Client-Id: Iv23lifFg4c9eT1T6hLC`), which only has `"issues": "read"` permission (`HTTP 403 — Resource not accessible by integration`).  
> Unzip `greeneek-failed-checks-issues.zip` on **your own machine** (where `gh auth login` is logged into GitHub) and run **one** command:
>
> **Windows PowerShell (`pwsh`, no `jq` needed):**
> ```powershell
> pwsh ./greeneek-failed-checks-issues/open-all-issues.ps1
> ```
>
> **Linux / macOS / WSL / Git Bash:**
> ```bash
> bash ./greeneek-failed-checks-issues/open-all-issues.sh
> ```
> *(Preview first with `-DryRun` on PowerShell or `--dry-run` on Bash — or open any of the `01-*.md` .. `08-*.md` files directly to copy-paste into GitHub Issues.)*

---

## 2. Live / Active Failures Requiring Action Today (`main` @ `d8b4a95`)

1. **🔴 `main` HEAD (`d8b4a95`) is currently showing red `Linux x64` & `Windows x64` check runs (`Desktop release #5`, plus `#4` and `#2` today) — and `desktop-v0.3.4` & `desktop-v0.3.5` have NO published GitHub Releases**  
   - **Root cause:** `.github/workflows/release-desktop.yml` (`lines 109, 169`) runs `node apps/desktop/scripts/prepare-release-assets.mjs --dist .staging/app/dist` unconditionally *before* the `--tag` step. On `workflow_dispatch` on `main`, `GITHUB_REF_NAME` is `"main"`, so `prepare-release-assets.mjs` resolves `version = "main"` and crashes looking for `Greeneek-Desktop-main-*`. In addition, two steps in the `windows-2025` job (`lines 154, 165`) still declare `shell: bash` in violation of `.github/AGENTS.md`.
2. **🔴 Open PR #87 (`@earendil-works/pi-ai` `0.84.2 → 0.87.1`) — All checks have failed ([`CI #183`](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/40128309126))**  
   - **Root cause:** 9 breaking TypeScript/lint errors in `packages/llm/llm-pi-ai/src/catalog.ts` (`thinking.budget`, `deferredToolsMode`, `OpenAIResponsesCompat`, `supportsToolReferences`, `mistral-conversations`), `replay.ts` (`JsonObject`, content union), and `tests/catalog.spec.ts` (`TranscriptContext`).
3. **🔴 Open PR #88 (`@anthropic-ai/sdk` `0.93.0 → 0.128.0`) — All checks have failed ([`CI #184`](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/40128456255))**  
   - **Root cause:** Branched from `267a3a5` while `main` had un-regenerated Cordis catalog JSDoc on `AgentPresets.resolve()` (`packages/typert/generator/tests/cordis-catalog.spec.ts:78`). Needs rebase onto `d8b4a95` + pre-push catalog guard.
4. **🔴 Open PR #89 (`@lexical/headless` `0.49.0 → 0.51.0`) — All checks have failed ([`CI #185`](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/40128565672))**  
   - **Root cause:** `.github/dependabot.yml` lacks `groups:` for `lexical` + `@lexical/*`, creating conflicting `0.51.0` vs `0.49.0` `LexicalEditor` / `LexicalNodeConfig` nominal types in `packages/client/ui-conversation/tests/lexical-editor-core.client.spec.tsx:45,47`. Also `.github/dependabot.yml` specifies non-existent labels `kind/dependency` and `area/infra`.
5. **🟠 Live latent workflow & test hazards still present on `main` (`d8b4a95`):**
   - `.github/workflows/ci.yml:22` and `release-desktop.yml:78,139` still duplicate `version: 11.7.0` on `pnpm/action-setup@v4` alongside `package.json#packageManager` — the exact misconfiguration that caused **`[CI] Import rebranded DeepSeek Harness #5`** and 33 other `ERR_PNPM_BAD_PM_VERSION` failures whenever `packageManager` changes.
   - `actions/checkout@v4`, `actions/setup-node@v4`, and `pnpm/action-setup@v4` emit Node.js 20 deprecation warnings on every job.
   - `packages/test-support/session-snapshot/src/harness.ts` (`lines 606–672`) still has 3 async `harvestSessionLogs` helpers (`waitForPersistedChildTurnEnd`, `waitForPersistedGoalPhase`, `waitForPersistedInboxMessage`) using raw `vi.waitFor` instead of `waitForPersistedRecord` (the same timeout-masking bug fixed for `waitForTurnEnd` after `CI #209`).
   - `Brand sweep` exists only inline in `.github/workflows/ci.yml` (`lines 32–44`) and is missing from `lefthook.yml`, causing 12 `main` CI breakages.
   - `apps/landing/vercel.json` has no `ignoreCommand`, causing Vercel to run (and fail 10 times) even on unrelated PRs.

---

## 3. All 8 Prepared GitHub Issues (Zero Omissions)

| # | Prepared Issue File | Proposed Title | Labels | Checks Covered |
|---:|---|---|---|---:|
| **1** | [`01-fix-release-desktop-workflow-dispatch-and-pwsh.md`](./01-fix-release-desktop-workflow-dispatch-and-pwsh.md) | `fix(release): pass --tag on workflow_dispatch in release-desktop.yml and use pwsh on Windows (blocks desktop-v0.3.4/v0.3.5 & leaves main red)` | `bug`, `build`, `desktop` | **27 failed + 5 cancelled** |
| **2** | [`02-fix-llm-pi-ai-0.87.1-pr-87.md`](./02-fix-llm-pi-ai-0.87.1-pr-87.md) | `fix(llm-pi-ai): adapt catalog, compat table, and transcript replay to @earendil-works/pi-ai 0.87.1 (failing CI #183 on PR #87)` | `bug`, `dependencies`, `llm` | **1 active failed (PR #87)** |
| **3** | [`03-fix-dependabot-lockstep-groups-lexical-pr-89.md`](./03-fix-dependabot-lockstep-groups-lexical-pr-89.md) | `fix(deps): group lockstep package families in dependabot.yml to prevent split-version typecheck failures (failing CI #185 on PR #89)` | `bug`, `dependencies`, `ui`, `build` | **9 failed (incl. PR #89)** |
| **4** | [`04-fix-ci-catalog-drift-and-rebase-pr-88.md`](./04-fix-ci-catalog-drift-and-rebase-pr-88.md) | `fix(ci): rebase PR #88 (@anthropic-ai/sdk) past main catalog drift and guard generated catalogs pre-push (CI #184 + 32 CI runs)` | `bug`, `build`, `dependencies` | **33 failed (incl. PR #88)** |
| **5** | [`05-fix-ci-duplicate-pnpm-pin-node20-actions-dependabot-dynamic.md`](./05-fix-ci-duplicate-pnpm-pin-node20-actions-dependabot-dynamic.md) | `fix(ci): remove duplicate pnpm version pin in workflows and upgrade Node 20 actions (CI #5..#38, #41 & Dependabot #2, #5, #22, #34, #94)` | `bug`, `build`, `tech-debt` | **40 failed + 1 cancelled (incl. CI #5)** |
| **6** | [`06-fix-test-support-session-snapshot-waitfor-and-flaky-lanes.md`](./06-fix-test-support-session-snapshot-waitfor-and-flaky-lanes.md) | `fix(test-support): migrate remaining session-snapshot vi.waitFor log pollers to waitForPersistedRecord (CI #188, #209 + 52 test-lane CI runs)` | `bug`, `build`, `tech-debt` | **54 failed + 1 cancelled** |
| **7** | [`07-chore-ci-brand-sweep-lint-gitleaks-lefthook-parity.md`](./07-chore-ci-brand-sweep-lint-gitleaks-lefthook-parity.md) | `chore(ci): share Brand sweep & full lint gates between ci.yml and lefthook.yml to stop main hygiene breakages (47 failed CI runs)` | `build`, `security`, `cleanup` | **47 failed** |
| **8** | [`08-chore-landing-vercel-ignore-command-and-ci-build.md`](./08-chore-landing-vercel-ignore-command-and-ci-build.md) | `chore(landing): scope Vercel builds to apps/landing changes and verify landing build in CI (10 failed Vercel status checks)` | `build`, `ui`, `cleanup` | **10 failed Vercel checks** |

**Total:** `27 + 1 + 9 + 33 + 40 + 54 + 47 = 211/211` failed GitHub Actions runs + `7/7` cancelled GitHub Actions runs + `10/10` failed `Vercel` commit status checks = **228 / 228 (100.0%)**.
