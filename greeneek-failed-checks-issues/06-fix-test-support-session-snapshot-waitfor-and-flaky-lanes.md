# fix(test-support): migrate remaining session-snapshot vi.waitFor log pollers to waitForPersistedRecord (CI #188, #209 + 52 test-lane CI runs)

- **Target Repository:** `Mostafa-Taher-git/Greeneek`
- **Labels:** `bug`, `build`, `tech-debt`

---

## Problem

Across `CI` (`Run pnpm test -- --coverage --reporter=verbose`), **54 failed workflow runs** (plus 1 cancelled run `CI #101`) stem from timing-sensitive subprocess/shell/UI tests under V8 coverage instrumentation and snapshot/preset harness assertions — and **one latent `vi.waitFor` timeout-masking bug still remains on `main` (`d8b4a95`) today**.

### Live latent bug on `main` (`d8b4a95`): remaining `vi.waitFor` pollers in `packages/test-support/session-snapshot/src/harness.ts`

In [`CI #209`](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/40254789718) (on a pure docs commit `65ec3f0`, `docs(notes): speak the rebrand contract in the release notes`) and [`CI #188`](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/40138319290), `packages/test-support/session-snapshot/tests/harness.spec.ts` failed under runner load because `harvestSessionLogs(root)` took longer than a short timeout budget (`20ms`), causing `vi.waitFor` to discard the callback's diagnostic error and throw generic `Timed out in waitFor!`.

Commits `63f512f7` and `154c3e8e` fixed `waitForPersistedTitleAfterTurnEnd`, `waitForPersistedEventAfterTurnEnd` (via `waitForPersistedRecord` at `harness.ts:694`), and `waitForPersistedTurnEnd` (`harness.ts:576`). **However, three sibling async log-harvesting helpers in `packages/test-support/session-snapshot/src/harness.ts` still use raw `vi.waitFor` without `waitForPersistedRecord` or `.catch(() => { throw budgetError })`**:

1. `waitForPersistedChildTurnEnd` (`packages/test-support/session-snapshot/src/harness.ts:606–621`)
2. `waitForPersistedGoalPhase` (`packages/test-support/session-snapshot/src/harness.ts:632–648`)
3. `waitForPersistedInboxMessage` (`packages/test-support/session-snapshot/src/harness.ts:651–672`)

In addition, `packages/test-support/session-snapshot/tests/harness.spec.ts:70` sets:
```ts
const titleDiagnosticTimeoutMs = process.platform === 'win32' ? 5_000 : 20
```
While `waitForPersistedRecord` guarantees at least one completed poll before checking `Date.now() >= deadline`, migrating the three remaining `vi.waitFor` pollers onto `waitForPersistedRecord` eliminates the exact same class of load-induced `Timed out in waitFor!` failure before it hits `CI` again.

### Summary of all 54 test-lane failures covered by this audit

- **`packages/client/ui-agent-preset/tests/components.client.spec.tsx` (21 runs: `#87`, `#90`–`#107`, `#127`)** — `disables every pill while a switch is in flight` / `stages the picked preset on click` / `falls back to the id`.
- **`packages/terminal/terminal-bash/tests/local.spec.ts` (10 runs: `#129`, `#131`–`#139`)** — `terminal-bash pwsh real shell > bootstraps a persistent pwsh, persists state, and scrubs secrets` (real `pwsh` startup budget under coverage).
- **`scripts/install-lefthook.spec.ts` (9 runs: `#57`, `#59`–`#66`)** — `refuses dormant repository extensions before upgrading the repository format` (also broke 4 unrelated Dependabot PRs `#59`–`#62`).
- **`CI #1`–`#4` (`ci (20)`) & `#44`–`#46` (`ci (22)`) (7 runs)** — initial Node 20 / post-rebrand test suite stabilization runs.
- **`packages/preset/agent-presets/tests/shipped-root.spec.ts` (3 runs: `#196`–`#198`; `#195` also tripped `cordis-catalog.spec.ts`)** — preset roster & `web_fetch` invariants during v0.3.4 preset work.
- **`packages/test-support/session-snapshot/tests/harness.spec.ts` (2 runs: `#188`, `#209`)** — `waitForEventAfterTurnEnd` and `waitForTurnEnd` deadline/message races under coverage load.
- **`scripts/verify-source-plane.spec.ts` (2 runs: `#205`, `#206`)** — `scans the real tree without emitted output`.
- **Single-run test regressions (3 runs)**: `#43` (`scripts/ci-workflow.spec.ts`), `#76` (`scripts/project-doc-site.spec.ts`), `#144` (`packages/client/ui-theme/tests/elevation-styles.client.spec.ts`).

## Affected Failed Checks (54 failed + 1 cancelled runs)

<details open>
<summary>Complete ledger of all 54 failed test-lane CI runs</summary>

| Failed Check Run | Trigger | Ref / PR / Tag | Commit | Failing Job & Step | Diagnostic / Title | Status |
|---|---|---|---|---|---|---|
| [CI #209](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/40254789718) | `push` | `main` | `65ec3f0` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/test-support/session-snapshot/tests/harness.spec.ts > runScenario > waitForTurnEnd time | ⚪ Historical |
| [CI #206](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/40248539856) | `push` | `main` | `235378a` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] scripts/verify-source-plane.spec.ts > source-plane audit > scans the real tree without emitted o | ⚪ Historical |
| [CI #205](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/40248352427) | `push` | `main` | `c7d90da` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] scripts/verify-source-plane.spec.ts > source-plane audit > scans the real tree without emitted o | ⚪ Historical |
| [CI #198](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/40226015551) | `push` | `main` | `d3fe5d6` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/preset/agent-presets/tests/shipped-root.spec.ts > the shipped preset root > enables web | ⚪ Historical |
| [CI #197](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/40224196117) | `push` | `main` | `96f82f1` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/preset/agent-presets/tests/shipped-root.spec.ts > the shipped preset root > enables web | ⚪ Historical |
| [CI #196](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/40224096554) | `push` | `main` | `c1a3cd0` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/preset/agent-presets/tests/shipped-root.spec.ts > the shipped preset root > enables web | ⚪ Historical |
| [CI #188](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/40140394768) | `push` | `main` | `3b694b1` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/test-support/session-snapshot/tests/harness.spec.ts > runScenario > waitForEventAfterTu | ⚪ Historical |
| [CI #144](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34748356072) | `push` | `main` | `76c9b85` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/client/ui-theme/tests/elevation-styles.client.spec.ts > neutral solid borders are hairl | ⚪ Historical |
| [CI #139](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34603740919) | `push` | `main` | `d0a3fd7` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/terminal/terminal-bash/tests/local.spec.ts > terminal-bash pwsh real shell > bootstraps | ⚪ Historical |
| [CI #138](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34602187152) | `push` | `main` | `55c80f1` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/terminal/terminal-bash/tests/local.spec.ts > terminal-bash pwsh real shell > bootstraps | ⚪ Historical |
| [CI #137](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34600582032) | `push` | `main` | `b39eb21` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/terminal/terminal-bash/tests/local.spec.ts > terminal-bash pwsh real shell > bootstraps | ⚪ Historical |
| [CI #136](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34597684854) | `push` | `main` | `36100cd` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/terminal/terminal-bash/tests/local.spec.ts > terminal-bash pwsh real shell > bootstraps | ⚪ Historical |
| [CI #133](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34586564357) | `push` | `main` | `6230b9b` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/terminal/terminal-bash/tests/local.spec.ts > terminal-bash pwsh real shell > bootstraps | ⚪ Historical |
| [CI #132](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34524494398) | `pull_request` | PR #50 (closed) | `b27853d` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/terminal/terminal-bash/tests/local.spec.ts > terminal-bash pwsh real shell > bootstraps | ⚪ Historical |
| [CI #129](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34508040544) | `pull_request` | PR #44 (closed) | `f71cfe5` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/terminal/terminal-bash/tests/local.spec.ts > terminal-bash pwsh real shell > bootstraps | ⚪ Historical |
| [CI #127](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34453198020) | `push` | `main` | `f036815` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/client/ui-agent-preset/tests/components.client.spec.tsx > the new-session mode switcher | ⚪ Historical |
| [CI #107](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34393095934) | `push` | `main` | `8770b87` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/client/ui-agent-preset/tests/components.client.spec.tsx > the new-session mode switcher | ⚪ Historical |
| [CI #106](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34388982131) | `push` | `main` | `43ad464` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/client/ui-agent-preset/tests/components.client.spec.tsx > the new-session mode switcher | ⚪ Historical |
| [CI #105](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34386063381) | `push` | `main` | `b0cf7fa` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/client/ui-agent-preset/tests/components.client.spec.tsx > the new-session mode switcher | ⚪ Historical |
| [CI #104](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34386023364) | `pull_request` | PR #43 (merged) | `c08ee03` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/client/ui-agent-preset/tests/components.client.spec.tsx > the new-session mode switcher | ⚪ Historical |
| [CI #103](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34383183217) | `push` | `main` | `95e320c` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/client/ui-agent-preset/tests/components.client.spec.tsx > the new-session mode switcher | ⚪ Historical |
| [CI #102](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34383091265) | `pull_request` | PR #43 (merged) | `091462a` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/client/ui-agent-preset/tests/components.client.spec.tsx > the new-session mode switcher | ⚪ Historical |
| [CI #100](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34373743341) | `push` | `main` | `b04613b` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/client/ui-agent-preset/tests/components.client.spec.tsx > the new-session mode switcher | ⚪ Historical |
| [CI #99](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34369297914) | `push` | `main` | `c0755d4` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/client/ui-agent-preset/tests/components.client.spec.tsx > the new-session mode switcher | ⚪ Historical |
| [CI #98](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34365803420) | `push` | `main` | `915f727` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/client/ui-agent-preset/tests/components.client.spec.tsx > the new-session mode switcher | ⚪ Historical |
| [CI #97](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34362404104) | `push` | `main` | `88d2a98` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/client/ui-agent-preset/tests/components.client.spec.tsx > the new-session mode switcher | ⚪ Historical |
| [CI #96](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34357754399) | `push` | `main` | `725f720` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/client/ui-agent-preset/tests/components.client.spec.tsx > the new-session mode switcher | ⚪ Historical |
| [CI #95](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34350249832) | `pull_request` | PR #39 (closed) | `b3d43ab` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/client/ui-agent-preset/tests/components.client.spec.tsx > the new-session mode switcher | ⚪ Historical |
| [CI #94](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34349895369) | `push` | `main` | `d41cdc9` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/client/ui-agent-preset/tests/components.client.spec.tsx > the new-session mode switcher | ⚪ Historical |
| [CI #93](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34336726483) | `push` | `main` | `5e1e6b8` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/client/ui-agent-preset/tests/components.client.spec.tsx > the new-session mode switcher | ⚪ Historical |
| [CI #92](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34336065261) | `push` | `main` | `a7401f0` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/client/ui-agent-preset/tests/components.client.spec.tsx > the new-session mode switcher | ⚪ Historical |
| [CI #91](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34335777615) | `push` | `main` | `894733d` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/client/ui-agent-preset/tests/components.client.spec.tsx > the new-session mode switcher | ⚪ Historical |
| [CI #90](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34334089204) | `push` | `main` | `e3cd8ec` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/client/ui-agent-preset/tests/components.client.spec.tsx > the new-session mode switcher | ⚪ Historical |
| [CI #89](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34331099664) | `push` | `main` | `74249e6` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/client/ui-agent-preset/tests/components.client.spec.tsx > the new-session mode switcher | ⚪ Historical |
| [CI #88](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34327018755) | `push` | `main` | `6560f7c` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/client/ui-agent-preset/tests/components.client.spec.tsx > the new-session mode switcher | ⚪ Historical |
| [CI #87](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34325480510) | `push` | `main` | `69401f8` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/client/ui-agent-preset/tests/components.client.spec.tsx > the new-session mode switcher | ⚪ Historical |
| [CI #76](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34314546280) | `push` | `main` | `441c048` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] scripts/project-doc-site.spec.ts > docsPages locale routes > places the shared todo fragment ali | ⚪ Historical |
| [CI #66](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34178704966) | `push` | `main` | `86f835d` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] scripts/install-lefthook.spec.ts > worktree-local Lefthook installer > refuses dormant repositor | ⚪ Historical |
| [CI #65](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34176995707) | `push` | `main` | `a4562d0` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] scripts/install-lefthook.spec.ts > worktree-local Lefthook installer > refuses dormant repositor | ⚪ Historical |
| [CI #64](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34174920843) | `push` | `main` | `520c0fc` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] scripts/install-lefthook.spec.ts > worktree-local Lefthook installer > refuses dormant repositor | ⚪ Historical |
| [CI #63](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34164394261) | `push` | `main` | `694cf5b` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] scripts/install-lefthook.spec.ts > worktree-local Lefthook installer > refuses dormant repositor | ⚪ Historical |
| [CI #62](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34158272920) | `pull_request` | PR #36 (closed) | `01edb2e` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] scripts/install-lefthook.spec.ts > worktree-local Lefthook installer > refuses dormant repositor | ⚪ Historical |
| [CI #61](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34129368344) | `pull_request` | PR #35 (closed) | `bc42c5d` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] scripts/install-lefthook.spec.ts > worktree-local Lefthook installer > refuses dormant repositor | ⚪ Historical |
| [CI #60](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34129367746) | `pull_request` | PR #34 (closed) | `39a005e` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] scripts/install-lefthook.spec.ts > worktree-local Lefthook installer > refuses dormant repositor | ⚪ Historical |
| [CI #59](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34129367036) | `pull_request` | PR #31 (closed) | `2765897` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] scripts/install-lefthook.spec.ts > worktree-local Lefthook installer > refuses dormant repositor | ⚪ Historical |
| [CI #57](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34129024444) | `push` | `main` | `ef74389` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] scripts/install-lefthook.spec.ts > worktree-local Lefthook installer > refuses dormant repositor | ⚪ Historical |
| [CI #46](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33990152789) | `push` | `main` | `3170c21` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/terminal/terminal-bash/tests/local.spec.ts > terminal-bash pwsh real shell > bootstraps | ⚪ Historical |
| [CI #45](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33988497796) | `push` | `main` | `1a83656` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/terminal/terminal-bash/tests/local.spec.ts > terminal-bash pwsh real shell > bootstraps | ⚪ Historical |
| [CI #44](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33986262860) | `push` | `main` | `4e7aa79` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] packages/terminal/terminal-bash/tests/local.spec.ts > terminal-bash pwsh real shell > bootstraps | ⚪ Historical |
| [CI #43](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33983813443) | `push` | `main` | `1cc3d07` | `ci (22)` → `Run pnpm test -- --coverage --reporter=verbose` | [thread-safe] scripts/ci-workflow.spec.ts > Python release workflows > exposes the native wheel builder to the | ⚪ Historical |
| [CI #4](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33706639448) | `push` | `main` | `45a0e56` | `ci (20)` → `Run pnpm test -- --coverage --reporter=verbose` | Process completed with exit code 1. | ⚪ Historical |
| [CI #3](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33700705040) | `push` | `main` | `9b8def1` | `ci (20)` → `Run pnpm test -- --coverage --reporter=verbose` | Process completed with exit code 1. | ⚪ Historical |
| [CI #2](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33685821535) | `push` | `main` | `864e354` | `ci (20)` → `Run pnpm test -- --coverage --reporter=verbose` | Process completed with exit code 1. | ⚪ Historical |
| [CI #1](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/33672333390) | `push` | `main` | `7b132d2` | `ci (20)` → `Run pnpm test -- --coverage --reporter=verbose` | Process completed with exit code 1. | ⚪ Historical |

</details>

**Cancelled CI test run (for completeness):**
- [`CI #101`](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34372822653) (`push` on `main` @ `0c330a5`, `fix: add missing locale keys used by WorkspaceBrowser/Rows`) — `cancelled`

## Work

- [ ] Migrate `waitForPersistedChildTurnEnd` (`harness.ts:606`), `waitForPersistedGoalPhase` (`harness.ts:632`), and `waitForPersistedInboxMessage` (`harness.ts:651`) in `packages/test-support/session-snapshot/src/harness.ts` onto `waitForPersistedRecord` so slow `harvestSessionLogs` calls under coverage can never mask diagnostic messages with `Timed out in waitFor!`.
- [ ] Add 1ms-window regression tests in `packages/test-support/session-snapshot/tests/harness.spec.ts` for those three helpers (matching the test added in `154c3e8e` for `waitForTurnEnd`), maintaining 100% per-file coverage.
- [ ] Audit `packages/terminal/terminal-bash/tests/local.spec.ts` (`pwsh` real-shell bootstrap timeout) to ensure cold `pwsh` startup under Linux/Windows V8 coverage has explicit headroom.

## Acceptance criteria

- [ ] Zero `harvestSessionLogs` helpers in `packages/test-support/session-snapshot/src/harness.ts` rely on raw `vi.waitFor` without deadline-preserving error handling.
- [ ] `pnpm --filter @greeneek/gnk-test-session-snapshot test -- --coverage` passes at 100% statements/branches/functions/lines.

## References

- `packages/test-support/session-snapshot/src/harness.ts` (`lines 576–710`)
- `packages/test-support/session-snapshot/tests/harness.spec.ts` (`lines 69–71, 920–945, 1068–1095`)
- Prior fixes: `63f512f7`, `154c3e8e`
