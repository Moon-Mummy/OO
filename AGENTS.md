# AGENTS.md — rules for AI agents working in this repo

**This is OO-OS**: an object-oriented operating system. Every resource is an
object; every reference is a capability. Read `docs/SPEC.md` before changing
kernel code, and `docs/DECISIONS.md` before relitigating a decision.

Several AI agents work here at the same time, on the same branch. These rules are
what keeps that from turning into a merge war.

## Branch rules (hard)

- Active branch: `arena/01a084f5-oo` (branched from `main` @ `46bc308`).
- Work only on that branch. Never create, switch to, or push another branch.
- Never force-push; never rebase or amend pushed history; never rewrite `main`.
- `git pull --rebase origin arena/01a084f5-oo` before starting and before pushing.
- Never touch or rewrite `.git`. Never delete or move the repository root.
- No secrets, tokens, or credentials in committed files.

## Before you write code

```bash
python -m ooos.boot --demo     # see it work
python -m pytest -q            # 21 tests, must stay green
python -m ooos.web --port 8000 # browser terminal on :8000
```

Python 3.11+, zero runtime dependencies, `pytest` for tests.

## Coordination (hard)

- **Claim before you edit.** Add your paths to `.ai/coordination/active.md` under
  your agent name, and release them when done. Unclaimed paths are free; claimed
  paths belong to the claimer.
- Claim the narrowest path you can. `ooos/vfs.py` is a claim; `ooos/*` is not.
- **Interfaces listed in `docs/SPEC.md` are frozen.** Add freely; rename or
  re-signature only after proposing it in `.ai/coordination/active.md` and getting
  a reply.
- Commit small and atomically. Message prefix: `agent/<your-name>: <what changed>`.
- Push at natural checkpoints, not once at the end of a long run.
- Every change ships with tests. No commits of build output or generated data.

## Claim map

| Agent | Owns | Slice |
|---|---|---|
| Arena agent | `ooos/capability.py`, `ooos/objects.py`, `ooos/clock.py`, `ooos/requests.py`, `ooos/api.py`, `ooos/console.py`, `ooos/kernel.py`, `ooos/boot.py`, `ooos/web/**`, `docs/**`, `tests/test_boot_smoke.py`, `tests/test_capabilities.py` | baseline + coordination |
| deepseek-pro | `ooos/mm.py`, `tests/test_mm.py` | R1 memory |
| fable-5 | `ooos/sched.py`, `tests/test_sched.py` | R2 scheduling |
| gimni-3.8flash | `ooos/ipc.py`, `tests/test_ipc.py` | R3 IPC |
| glm5-2 | `ooos/vfs.py`, `tests/test_vfs.py` | R4 VFS |
| minimax-m3 | `ooos/syscalls.py`, `docs/ABI.md`, `tests/test_syscalls.py` | R5 ABI |
| qwenmax | `ooos/user/**`, `tests/test_userland.py` | R6 userland |
| sonnet-5 | `tests/**` (except the two above), `.github/workflows/ci.yml` | R7 tests & CI |

Unassigned slices (R8 persistence, R9 hardware port, R10 networking, R11 multicore)
are open — claim one in the coordination log first.

## Log format

    ## <agent-name> — YYYY-MM-DD
    - Claims: `path/a/**`, `path/b.py`
    - Did: one line per change
    - Next: what you intend to do
    - Blocked on / asking <other agent>: question, if any

## House style

- Type hints on public functions; docstrings explain *why*, not syntax.
- Errors are `ooos.errors.OoosError` subclasses, never bare Python exceptions.
- Determinism is a feature: no wall clock, no real threads, no unseeded RNG.
- Prefer adding a new file over rewriting someone else's.
