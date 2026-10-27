# chore(landing): scope Vercel builds to apps/landing changes and verify landing build in CI (10 failed Vercel status checks)

- **Target Repository:** `Mostafa-Taher-git/Greeneek`
- **Labels:** `build`, `ui`, `cleanup`

---

## Problem

In addition to GitHub Actions check runs, the repository has a connected **Vercel** Git integration (`mostafa-web/landing`) that posts commit status checks (`context: "Vercel"`) and `Vercel Preview Comments` check runs on **every push and every pull request across the entire monorepo** — even when `apps/landing` is completely untouched (such as Python SDK, GitHub Actions, and root npm Dependabot PRs).

Inspecting commit statuses across all 270 `main` commits and 65 pull requests uncovered **10 failed `Vercel` deployment checks** (`state: "failure"`):
- **6 failed production/branch deployments on `main`** during landing-page iteration (`a4b5124` → `f49d2db`).
- **4 failed preview deployments on unrelated root Dependabot PRs** (`PR #37`, `PR #38`, `PR #40`, `PR #41`), because those PRs branched from `main` while `apps/landing` had a failing Vercel build and `apps/landing/vercel.json` had no `ignoreCommand` to skip unrelated commits!

### Current `apps/landing/vercel.json`

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "framework": "vite"
}
```

Furthermore, `apps/landing` is currently **not built or type-checked in `.github/workflows/ci.yml`**, so landing-app build regressions are only discovered post-push by external Vercel builds rather than by repository CI.

## Affected Failed Checks (10 failed `Vercel` commit status checks)

| Check Context | Ref / PR | Commit | Commit / PR Title | Vercel Deployment Inspection Target | Status |
|---|---|---|---|---|---|
| `Vercel` | `main` | [`f49d2db`](https://github.com/Mostafa-Taher-git/Greeneek/commit/f49d2db) | `fix(landing): drop DeepSeek from provider list...` | [`dpl_8H5wyZTh6N4T2sx9SyLYVg27cHm3`](https://vercel.com/mostafa-web/landing/8H5wyZTh6N4T2sx9SyLYVg27cHm3) | ⚪ Superseded on `main` |
| `Vercel` | `main` | [`efccd51`](https://github.com/Mostafa-Taher-git/Greeneek/commit/efccd51) | `fix(landing): brace remaining void-expression...` | [`dpl_AmQQZy1opn8TRPRLyPRtVXqbbL72`](https://vercel.com/mostafa-web/landing/AmQQZy1opn8TRPRLyPRtVXqbbL72) | ⚪ Superseded on `main` |
| `Vercel` | `main` | [`958b85c`](https://github.com/Mostafa-Taher-git/Greeneek/commit/958b85c) | `fix(landing): drop deprecated execCommand fallback...` | [`dpl_HUCEB5cxWqALUfedJZDj5tyCJmAU`](https://vercel.com/mostafa-web/landing/HUCEB5cxWqALUfedJZDj5tyCJmAU) | ⚪ Superseded on `main` |
| `Vercel` | `main` | [`f1357be`](https://github.com/Mostafa-Taher-git/Greeneek/commit/f1357be) | `fix(landing): satisfy repo oxlint rules for e...` | [`dpl_BaUdQkGfPeMa6xzXvQMp81FD672B`](https://vercel.com/mostafa-web/landing/BaUdQkGfPeMa6xzXvQMp81FD672B) | ⚪ Superseded on `main` |
| `Vercel` | `main` | [`8e0e2fb`](https://github.com/Mostafa-Taher-git/Greeneek/commit/8e0e2fb) | `docs(landing): app README with Vercel import...` | [`dpl_DboXX7VjD8qaBHTnePGJu59rwYGK`](https://vercel.com/mostafa-web/landing/DboXX7VjD8qaBHTnePGJu59rwYGK) | ⚪ Superseded on `main` |
| `Vercel` | `main` | [`a4b5124`](https://github.com/Mostafa-Taher-git/Greeneek/commit/a4b5124) | `chore(i18n): delink retired bilingual targets...` | [`dpl_7goSzoV1U23XF7indidydBFBYwnB`](https://vercel.com/mostafa-web/landing/7goSzoV1U23XF7indidydBFBYwnB) | ⚪ Superseded on `main` |
| `Vercel` | PR #41 (closed) | [`40f5138`](https://github.com/Mostafa-Taher-git/Greeneek/commit/40f5138) | `chore(deps-dev): bump jsdom and @types/jsdom` | [`dpl_8Qj79DE8MdcABM3CXXq6w84YdUWq`](https://vercel.com/mostafa-web/landing/8Qj79DE8MdcABM3CXXq6w84YdUWq) | ⚪ Closed PR |
| `Vercel` | PR #40 (closed) | [`76e3bbd`](https://github.com/Mostafa-Taher-git/Greeneek/commit/76e3bbd) | `chore(deps): bump pnpm from 11.7.0 to 11.21.0` | [`dpl_26ykDZV88UdLfEcqkvyKZsUGc1tc`](https://vercel.com/mostafa-web/landing/26ykDZV88UdLfEcqkvyKZsUGc1tc) | ⚪ Closed PR |
| `Vercel` | PR #38 (closed) | [`92aa1bb`](https://github.com/Mostafa-Taher-git/Greeneek/commit/92aa1bb) | `chore(deps): bump chokidar from 4.0.3 to 5.0.0` | [`dpl_FQZ7nkZvTQb3vakMB3ckjqkqmEW2`](https://vercel.com/mostafa-web/landing/FQZ7nkZvTQb3vakMB3ckjqkqmEW2) | ⚪ Closed PR |
| `Vercel` | PR #37 (closed) | [`129950e`](https://github.com/Mostafa-Taher-git/Greeneek/commit/129950e) | `chore(deps-dev): bump jscpd from 5.0.12 to 5.0.14` | [`dpl_2tqNSUkhoFuqWb84gtmikVuRh8wB`](https://vercel.com/mostafa-web/landing/2tqNSUkhoFuqWb84gtmikVuRh8wB) | ⚪ Closed PR |

## Work

- [ ] Add an `ignoreCommand` to `apps/landing/vercel.json` (e.g. `git diff --quiet HEAD^ HEAD -- .`) so Vercel skips builds on PRs and commits that do not modify `apps/landing/`.
- [ ] Add an `apps/landing` build/typecheck verification step to `.github/workflows/ci.yml` (or workspace build script) so landing-page build errors are caught deterministically in repository CI before reaching Vercel.

## Acceptance criteria

- [ ] Unrelated PRs (e.g. `.github/workflows/*`, `python/sdk/*`, or core `packages/*` changes) skip unnecessary Vercel rebuilds instead of failing on unrelated landing state.
- [ ] `apps/landing` `tsc` + `vite build` are verified in `CI` whenever `apps/landing/**` changes.

## References

- `apps/landing/vercel.json`
- `apps/landing/package.json`
- `.github/workflows/ci.yml`
