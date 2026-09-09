# Roadmap

Seven slices, one per subsystem, designed to be built **in parallel without
touching each other's files**. Each row names the module to deepen, the interface
you must not break, and a definition of done.

| # | Slice | Module to deepen | Must not break | Suggested owner |
|---|---|---|---|---|
| R1 | Paged memory | `ooos/mm.py` | `map`, `unmap`, `protect`, `read`, `write`, `stats`, `dump` | deepseek-pro |
| R2 | Scheduling | `ooos/sched.py` | `create_process`, `create_thread`, `step`, `run`, `wake`, `kill_process`, `ps` | fable-5 |
| R3 | IPC | `ooos/ipc.py` | `send`, `recv`, `close`, `stats` on `Endpoint`; `Message` shape | gimni-3.8flash |
| R4 | VFS | `ooos/vfs.py` | `resolve`, `resolve_parent`, `File`/`Directory` method names | glm5-2 |
| R5 | ABI | `ooos/syscalls.py` | every existing syscall name and signature (additive only) | minimax-m3 |
| R6 | Userland | `ooos/user/*` | nothing — purely additive | qwenmax |
| R7 | Tests & CI | `tests/**`, `.github/workflows/ci.yml` | `tests/test_boot_smoke.py`, `tests/test_capabilities.py` | sonnet-5 |

## R1 — Paged memory management

- Copy-on-write regions (`fork`-style sharing without a `fork`).
- Slab allocator for small objects; a free-list instead of pure bump allocation.
- `mmap`-style file-backed regions: map a `File` object into an address space.
- **Done when:** `tests/test_mm.py` covers COW, exhaustion (`OomError`), and
  rights enforcement, and `maps` in the shell shows region types.

## R2 — Scheduling

- Priority scheduling with aging (keep round-robin as the default policy).
- Thread `join`, `detach`, and per-process thread limits.
- Deadlock detection: when nothing is runnable, report *why* (which thread waits
  on which endpoint) instead of silently halting.
- **Done when:** `ps` shows priorities, a deadlock produces a diagnostic rather
  than silence, and the existing smoke tests still pass unchanged.

## R3 — IPC

- Non-blocking send with backpressure (`try_send`), and multi-waiter fairness
  (first blocked, first served — today `Endpoint` wakes the oldest waiter, verify
  it under load).
- Reply channels: send carrying a one-shot reply capability.
- Endpoint capability revocation (`destroy` on the endpoint object).
- **Done when:** `tests/test_ipc.py` covers ordering, capacity, blocking receive,
  and close-wakes-receivers.

## R4 — VFS

- **D5: per-directory capabilities** — resolve a path by walking capabilities, so
  holding a capability on `/home/user` grants nothing about `/etc`.
- Symlinks, hard links, and rename.
- A `hostfs` adapter that exposes a real directory as a VFS subtree (read-only
  first), plus `/proc` as live kernel statistics.
- **Done when:** `tests/test_vfs.py` proves that narrowing a directory capability
  blocks access to its siblings.

## R5 — The syscall ABI

- Version negotiation: `kernel_version()` syscall plus a `docs/ABI.md` that
  freezes names and argument order.
- Error codes: map `OoosError` subclasses to stable integer errnos, with
  `strerror`.
- Argument validation at the boundary (today a bad argument surfaces as a Python
  exception several frames deep).
- **Done when:** `docs/ABI.md` exists, every syscall has documented arguments and
  errors, and no existing syscall changed shape.

## R6 — Userland

- Programs: `ls -l`, `wc`, `grep`, `ps -a`, `cat` with multiple files.
- Shell features: environment variables and `$VAR` expansion, quoting in `echo`,
  pipes between programs, and a `.ooosrc` run at boot.
- A tiny text editor (`edit PATH`) for a real "it's an OS" moment.
- **Done when:** at least five new programs, each with a one-line help entry.

## R7 — Tests and CI

- Per-subsystem test modules: `test_mm.py`, `test_sched.py`, `test_ipc.py`,
  `test_vfs.py`, `test_syscalls.py`, `test_userland.py`.
- Property/hypothesis test: for any random command sequence, two runs produce
  identical output and identical tick counts.
- GitHub Actions: `pytest` on 3.11 and 3.12, plus `python -m ooos.boot --demo`
  as a smoke test.
- **Done when:** CI is green and coverage is reported per module.

## Later (not yet assigned)

- R8: persistence — snapshot the object table to disk, restore on boot.
- R9: a real boot target (the hardware port deferred by D1).
- R10: networking — a `NetEndpoint` object with a socket-backed transport.
- R11: multi-core — multiple schedulers sharing one object table.
