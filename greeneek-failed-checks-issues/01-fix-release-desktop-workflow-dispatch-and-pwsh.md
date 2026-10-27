# fix(release): pass --tag on workflow_dispatch in release-desktop.yml and use pwsh on Windows (blocks desktop-v0.3.4/v0.3.5 & leaves main red)

- **Target Repository:** `Mostafa-Taher-git/Greeneek`
- **Labels:** `bug`, `build`, `desktop`

---

## Problem

The consolidated desktop release workflow (`.github/workflows/release-desktop.yml`) currently fails whenever triggered via `workflow_dispatch` on `main`, which:

1. **Leaves `main` (`d8b4a95`) showing failed check runs (`Linux x64` and `Windows x64`)** from [`Desktop release #5`](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/40490521106).
2. **Blocks backfilling missing GitHub Releases for `desktop-v0.3.4` (`87ef47f`) and `desktop-v0.3.5` (`fddab5c`)**, neither of which currently has a published GitHub Release (`desktop-v0.3.3` jumps straight to `desktop-v0.3.6`).

### Root cause 1 — Unconditional `prepare-release-assets.mjs` step without `--tag` breaks every `workflow_dispatch`

In `.github/workflows/release-desktop.yml` (`linux` lines 109–111 and `windows` lines 169–171), `prepare-release-assets.mjs` is invoked **twice** — first unconditionally without `--tag`, and only second conditionally with `--tag`:

```yaml
      - run: node apps/desktop/scripts/prepare-release-assets.mjs --dist .staging/app/dist
      - if: startsWith(needs.gate.outputs.ref, 'desktop-')
        run: node apps/desktop/scripts/prepare-release-assets.mjs --dist .staging/app/dist --tag "${{ needs.gate.outputs.ref }}"
```

Inside `apps/desktop/scripts/prepare-release-assets.mjs` (`lines 23–26, 46–50`):

```js
function parseDesktopVersion(input) {
  const match = /^desktop-v(\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?)$/.exec(input.trim())
  return match ? match[1] : input
}

function main() {
  const tag = argumentValue('--tag') ?? process.env.GITHUB_REF_NAME ?? ''
  const manifest = JSON.parse(readFileSync(path.join(root, 'package.json'), 'utf8'))
  const version = tag ? parseDesktopVersion(tag) : (argumentValue('--version') ?? manifest.version)
```

- On a tag `push` (`desktop-v0.3.6`), `GITHUB_REF_NAME` is `"desktop-v0.3.6"`, so `parseDesktopVersion` extracts `"0.3.6"` and step 1 succeeds (running step 2 redundantly afterward).
- On a `workflow_dispatch` run on `main` (e.g. [`Desktop release #4`](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/40490081317) and [`Desktop release #5`](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/40490521106)), GitHub sets `GITHUB_REF_NAME="main"`. Step 1 runs without `--tag`, resolves `version = "main"`, searches `.staging/app/dist` for `Greeneek-Desktop-main-linux-amd64.deb` / `Greeneek-Desktop-main-windows-x64.exe`, and crashes with `Error: Missing release assets` before the `--tag` step ever executes.

### Root cause 2 — `shell: bash` inside the `windows-2025` job violates `.github/AGENTS.md`

`.github/AGENTS.md` explicitly mandates:

> *Run Windows steps under native `pwsh`, never Bash, so packaged binaries see the real Win32 environment (`PATHEXT`, `.cmd` shims, backslash paths).*

However, `.github/workflows/release-desktop.yml` still declares `shell: bash` in two `windows` (`runs-on: windows-2025`) steps:
- `Stage the desktop app when the tag tree does not` (`lines 153–158`)
- `Assert updater channel files` (`lines 163–168`)

### Historical release check debt across `desktop-v0.2.*` and `desktop-v0.3.*`

Across the current `Desktop release` workflow and the retired two-workflow split (`desktop.yml` + `desktop-windows.yml`), **27 failed runs** and **5 cancelled runs** occurred:
- **`desktop-v0.3.4` (`87ef47f`) & `desktop-v0.3.5` (`fddab5c`)**: still have **no GitHub Release** (`#24` failed pre-stage packaging; `#1` tag run on `desktop-v0.3.5` was cancelled; dispatches `#2`, `#4`, `#5` failed).
- **`desktop-v0.2.0` (`c0755d4`)**: published GitHub Release has **0 assets** (`assets: []`).
- **`desktop-v0.2.1` (`b796ec0`)**: **no GitHub Release** (`Linux x64` updater channel check failed in `#9`; `Windows x64` `#9` cancelled).
- **`desktop-v0.2.2`–`desktop-v0.2.4`**: Linux-only partial releases (`Windows x64` failed `dist:win` in `#10`–`#12`, which motivated the unified single-publisher `release-desktop.yml`).
- **`desktop-v0.2.5`**: published release still contains a stray `builder-debug.yml` diagnostic artifact.

## Affected Failed Checks (27 failed + 5 cancelled runs)

| Failed Check Run | Trigger | Ref / PR / Tag | Commit | Failing Job & Step | Diagnostic / Title | Status |
|---|---|---|---|---|---|---|
| [Desktop release #5](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/40490521106) | `workflow_dispatch` | `main` | `d8b4a95` | `Linux x64` → `Run node apps/desktop/scripts/prepare-release-assets.mjs --dist .staging/app/dist`; `Windows x64` → `Run node apps/desktop/scripts/prepare-release-assets.mjs --dist .staging/app/dist` | Process completed with exit code 1.; Process completed with exit code 1. | 🔴 Active |
| [Desktop release #4](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/40490081317) | `workflow_dispatch` | `main` | `505b1a0` | `Linux x64` → `Run node apps/desktop/scripts/prepare-release-assets.mjs --dist .staging/app/dist`; `Windows x64` → `Run node apps/desktop/scripts/prepare-release-assets.mjs --dist .staging/app/dist` | Process completed with exit code 1.; Process completed with exit code 1. | 🔴 Active |
| [Desktop release #2](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/40489643591) | `workflow_dispatch` | `main` | `505b1a0` | `Linux x64` → `Run pnpm --filter @greeneek/desktop run dist:linux`; `Windows x64` → `Run pnpm --filter @greeneek/desktop run dist:win` | Process completed with exit code 1.; Process completed with exit code 1. | 🔴 Active |
| [Desktop release — Windows #24](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34772828475) | `push` | tag `desktop-v0.3.4` | `87ef47f` | `Windows x64` → `Run pnpm --filter @greeneek/desktop run dist:win` | Process completed with exit code 1. | 🔴 Active |
| [Desktop release #24](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34772828441) | `push` | tag `desktop-v0.3.4` | `87ef47f` | `Linux x64` → `Run pnpm --filter @greeneek/desktop run dist:linux` | Process completed with exit code 1. | 🔴 Active |
| [Desktop release — Windows #23](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34771089953) | `push` | tag `desktop-v0.3.3` | `8e5f017` | `Windows x64` → `Run node apps/desktop/scripts/prepare-release-assets.mjs --dist .staging/app/dist` | Process completed with exit code 1. | ⚪ Historical |
| [Desktop release #23](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34771089932) | `push` | tag `desktop-v0.3.3` | `8e5f017` | `Linux x64` → `Run node apps/desktop/scripts/prepare-release-assets.mjs --dist .staging/app/dist` | Process completed with exit code 1. | ⚪ Historical |
| [Desktop release — Windows #20](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34756185289) | `push` | tag `desktop-v0.3.1` | `88e6c8f` | `Windows x64` → `Run pnpm build:lib:client` | Argument of type 'HTMLElement \| undefined' is not assignable to parameter of type 'Document \| Node \| Element \| | ⚪ Historical |
| [Desktop release #20](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34756185273) | `push` | tag `desktop-v0.3.1` | `88e6c8f` | `Linux x64` → `Run pnpm build:lib:client` | Argument of type 'HTMLElement \| undefined' is not assignable to parameter of type 'Document \| Node \| Element \| | ⚪ Historical |
| [Desktop release — Windows #12](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34428982356) | `push` | tag `desktop-v0.2.4` | `f4d62ce` | `Windows x64` → `Run pnpm --filter @greeneek/desktop run dist:win` | Process completed with exit code 1. | ⚪ Historical |
| [Desktop release — Windows #11](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34428156746) | `push` | tag `desktop-v0.2.3` | `84068fc` | `Windows x64` → `Run pnpm --filter @greeneek/desktop run dist:win` | Process completed with exit code 1. | ⚪ Historical |
| [Desktop release — Windows #10](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34426993549) | `push` | tag `desktop-v0.2.2` | `fbf70cb` | `Windows x64` → `Run pnpm --filter @greeneek/desktop run dist:win` | Process completed with exit code 1. | ⚪ Historical |
| [Desktop release #9](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34426228816) | `push` | tag `desktop-v0.2.1` | `b796ec0` | `Linux x64` → `Assert updater channel files` | Process completed with exit code 2. | ⚪ Historical |
| [Desktop release — Windows #8](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34369308124) | `push` | tag `desktop-v0.2.0` | `c0755d4` | `Windows x64` → `Run pnpm --filter @greeneek/desktop run dist:win` | Process completed with exit code 1. | ⚪ Historical |
| [Desktop release #8](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34369308058) | `push` | tag `desktop-v0.2.0` | `c0755d4` | `Linux x64` → `Run node apps/desktop/scripts/prepare-release-assets.mjs --dist ../.staging/app/dist --tag "desktop-v0.2.0"` | Process completed with exit code 1. | ⚪ Historical |
| [Desktop release #7](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34365811833) | `push` | tag `desktop-v0.2.0` | `915f727` | `Linux x64` → `Run node apps/desktop/scripts/prepare-release-assets.mjs --dist apps/desktop/.staging/app/dist --tag "desktop-v0.2.0"` | Process completed with exit code 1. | ⚪ Historical |
| [Desktop release — Windows #7](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34365811814) | `push` | tag `desktop-v0.2.0` | `915f727` | `Windows x64` → `Run pnpm --filter @greeneek/desktop run dist:win` | Process completed with exit code 1. | ⚪ Historical |
| [Desktop release #6](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34362413919) | `push` | tag `desktop-v0.2.0` | `88d2a98` | `Linux x64` → `Run node apps/desktop/scripts/prepare-release-assets.mjs --dist apps/desktop/.staging/app/dist --tag "desktop-v0.2.0"` | Process completed with exit code 1. | ⚪ Historical |
| [Desktop release — Windows #6](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34362413765) | `push` | tag `desktop-v0.2.0` | `88d2a98` | `Windows x64` → `Run pnpm --filter @greeneek/desktop run dist:win` | Process completed with exit code 1. | ⚪ Historical |
| [Desktop release #5](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34357763631) | `push` | tag `desktop-v0.2.0` | `725f720` | `Linux x64` → `Run node apps/desktop/scripts/prepare-release-assets.mjs --dist apps/desktop/.staging/app/dist` | Process completed with exit code 1. | ⚪ Historical |
| [Desktop release — Windows #5](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34357763611) | `push` | tag `desktop-v0.2.0` | `725f720` | `Windows x64` → `Run pnpm --filter @greeneek/desktop run dist:win` | Process completed with exit code 1. | ⚪ Historical |
| [Desktop release #4](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34349903821) | `push` | tag `desktop-v0.2.0` | `d41cdc9` | `Linux x64` → `Run node apps/desktop/scripts/prepare-release-assets.mjs --dist apps/desktop/.staging/app/dist` | Process completed with exit code 1. | ⚪ Historical |
| [Desktop release — Windows #4](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34349903818) | `push` | tag `desktop-v0.2.0` | `d41cdc9` | `Windows x64` → `Run pnpm --filter @greeneek/desktop run dist:win, Post Run actions/checkout@v4` | There is not enough space on the disk. : 'D:\a\_temp\_runner_file_commands\artifacts_73f04fec-1012-4bf6-af3e-4 | ⚪ Historical |
| [Desktop release — Windows #3](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34345015353) | `push` | tag `desktop-v0.2.0` | `5e1e6b8` | `Windows x64` → `Run pnpm --filter @greeneek/desktop run dist:win` | Process completed with exit code 1. | ⚪ Historical |
| [Desktop release #3](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34345015326) | `push` | tag `desktop-v0.2.0` | `5e1e6b8` | `Linux x64` → `Run node apps/desktop/scripts/prepare-release-assets.mjs --dist apps/desktop/.staging/app/dist` | Process completed with exit code 1. | ⚪ Historical |
| [Desktop release #2](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34336733185) | `push` | tag `desktop-v0.2.0` | `5e1e6b8` | `Linux x64` → `Run node apps/desktop/scripts/prepare-release-assets.mjs --dist apps/desktop/.staging/app/dist` | Process completed with exit code 1. | ⚪ Historical |
| [Desktop release #1](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34335781967) | `push` | tag `desktop-v0.2.0` | `894733d` | `Linux x64` → `Run pnpm build:lib:client` | Cannot find module '@greeneek/gnk-goal/remote' or its corresponding type declarations. | ⚪ Historical |

**Cancelled Desktop release runs (for completeness):**
- [`Desktop release #3`](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/40489779761) (`workflow_dispatch` on `main` @ `505b1a0`) — `cancelled`
- [`Desktop release #1`](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/40489747670) (`push` on `desktop-v0.3.5` @ `fddab5c`) — `cancelled` (leaving `desktop-v0.3.5` unpublished)
- [`Desktop release — Windows #9`](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34426228801) (`push` on `desktop-v0.2.1` @ `b796ec0`) — `cancelled`
- [`Desktop release — Windows #2`](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34336733223) (`push` on `desktop-v0.2.0` @ `5e1e6b8`) — `cancelled`
- [`Desktop release — Windows #1`](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/34335781962) (`push` on `desktop-v0.2.0` @ `894733d`) — `cancelled`

## Work

- [ ] Replace the duplicate `prepare-release-assets.mjs` steps in `.github/workflows/release-desktop.yml` (`linux` lines 109–111 and `windows` lines 169–171) with a single step that always passes `--tag "${{ needs.gate.outputs.ref }}"`.
- [ ] Harden `apps/desktop/scripts/prepare-release-assets.mjs` so `process.env.GITHUB_REF_NAME` is only treated as a tag when it matches `/^desktop-v/`, falling back to `--version` or `manifest.version` when `GITHUB_REF_NAME` is a branch name like `main`; add a unit test in `apps/desktop` covering `GITHUB_REF_NAME=main`.
- [ ] Convert the remaining `shell: bash` steps in the `windows` job of `.github/workflows/release-desktop.yml` (`lines 154, 165`) to native `pwsh` (`Test-Path` / `Get-ChildItem`) per `.github/AGENTS.md`.
- [ ] Re-dispatch `release-desktop.yml` for `desktop-v0.3.4` and `desktop-v0.3.5` (or explicitly document them as skipped pre-`v0.3.6` tags) and clean up empty/diagnostic historical release entries (`desktop-v0.2.0` empty release, `builder-debug.yml` on `desktop-v0.2.5`) if desired.

## Acceptance criteria

- [ ] `gh workflow run release-desktop.yml -f tag=desktop-v0.3.5` and `-f tag=desktop-v0.3.4` succeed on both `Linux x64` and `Windows x64` and publish complete asset sets.
- [ ] Zero steps in the `windows` job of `.github/workflows/release-desktop.yml` use `shell: bash`.
- [ ] `prepare-release-assets.mjs` succeeds when invoked under `GITHUB_REF_NAME=main` without `--tag` (using `manifest.version`) and with `--tag desktop-vX.Y.Z`.

## References

- `.github/workflows/release-desktop.yml` (`lines 109–111, 153–171`)
- `apps/desktop/scripts/prepare-release-assets.mjs` (`lines 23–55`)
- `.github/AGENTS.md` (Windows `pwsh` requirement)
- Relates to #86 (`#72` desktop packaging & release approval flow)
