# OO-OS — task brief for minimax-m3

You are joining **OO-OS**, an object-oriented operating system, in a repository
where several AI agents work at the same time, on the same branch. Read this whole
message before you write a line of code. It is self-contained: you do not need
anything else to start.

Your slice is the **syscall ABI** — the contract every user program and every other agent compiles against. You own `ooos/syscalls.py` and `docs/ABI.md`.

## 1. What OO-OS is

An object-oriented operating system. Two rules define it:

1. **Every resource is an object** — files, directories, IPC endpoints, the console,
   address spaces. One flat kernel object table; nothing lives outside it.
2. **Every reference is a capability** — an unforgeable `(object id, rights)` pair
   held in a per-process table. User code never names an object directly, it names a
   capability *index*, exactly like a file descriptor. There is no ambient authority:
   hold no capability, see no object.

It is a microkernel design that runs in userspace on a **virtual clock**, so every
run is deterministic and testable with pytest. Python 3.11+, zero runtime
dependencies. The baseline already boots, schedules processes, allocates paged
memory, passes capabilities between processes, and runs a 30-command shell.

It is **not** a bootable kernel yet — that is deliberate (see `docs/DECISIONS.md` D1).

## 2. Repository facts

- GitHub: `Moon-Mummy/OO`. Branch: **`arena/01a084f5-oo`** (base commit `46bc308`).
- Current tip: `b525ad9` — pull it before you start.

```
ooos/            the kernel
  objects.py       object table + method dispatch
  capability.py    Rights, Capability
  clock.py         virtual clock
  sched.py         processes, threads, round-robin scheduler
  mm.py            frame accounting, address spaces
  ipc.py           endpoints, message passing
  vfs.py           files and directories as objects
  syscalls.py      the user ABI (synchronous, rights-checked)
  console.py       the terminal — itself a kernel object
  kernel.py        wiring, boot, panic, stats
  requests.py      thread -> scheduler request types
  api.py           blocking helpers (sleep/recv/read_line/waitpid)
  boot.py          CLI entry point
  user/            userland: init, shell, sample programs
  web/             browser terminal (stdlib http.server)
docs/            SPEC.md  DECISIONS.md  ROADMAP.md  HANDOFF.md  ABI.md (yours, R5)
tests/           pytest
.ai/coordination/active.md   live claim log — read it, then add your section
```

Get it running first:

```bash
git clone https://github.com/Moon-Mummy/OO && cd OO
git checkout arena/01a084f5-oo && git pull --rebase
python -m ooos.boot --demo              # scripted tour
python -m ooos.boot --script "ls /; ps; exit"
python -m ooos.web --port 8000          # browser terminal
python -m pytest -q                     # 21 tests, all green
```

## 3. Hard rules

- Work **only** on `arena/01a084f5-oo`. Never create, switch to, or push another branch.
- Never force-push; never rebase or amend pushed history; never rewrite `main`.
- `git pull --rebase origin arena/01a084f5-oo` before you start **and** before you push.
- Commit in small atomic steps, message prefix `agent/minimax-m3: <what changed>`.
  Example: `agent/minimax-m3: add copy-on-write regions to the memory manager`
- **Claim your paths in `.ai/coordination/active.md` before editing them.** Do not
  edit another agent's claimed paths — ask in that file instead.
- **The interfaces listed in `docs/SPEC.md` are frozen.** You may add to a module;
  you may not rename or change the signature of anything public in it. If you must
  break one, stop and propose it in `.ai/coordination/active.md` and wait for a reply.
- Every change ships with tests. `python -m pytest -q` must stay green.
- No secrets or credentials in committed files. No build output, no generated datasets.

## 4. House style

- Type hints on public functions; docstrings explain *why*, not syntax.
- Errors are `ooos.errors.OoosError` subclasses, never bare Python exceptions.
- Determinism is a feature: no wall clock, no real threads, no unseeded RNG.
- Prefer adding a new file over rewriting someone else's.
- Read `docs/DECISIONS.md` before relitigating a design choice — each record says
  why it was made, what it costs, and when to revisit it.

## 5. R5 — the syscall ABI

### Where it stands

`Syscalls` holds a name → handler table, auto-built from its public methods, so
adding a syscall means adding a method. Every syscall is **synchronous** and takes
the process first; blocking lives entirely in `ooos/api.py` and is expressed as
`yield from` (D6). Required rights are derived from the method name by
`_RIGHTS_FOR_METHOD`: `write` needs WRITE, `spawn` needs EXEC, `grant` needs GRANT,
everything else needs READ. There are about 40 syscalls today; `syscalls` in the
shell prints the live table.

### Build

1. **`docs/ABI.md`** — freeze every syscall: name, argument order, types, return
   type, and which `OoosError` it can raise. This document is the deliverable the
   other six agents will actually read, so write it for someone who has not opened
   the source.
2. **Version negotiation.** A `kernel_version()` syscall returning
   `(major, minor, patch)`, plus a documented promise about what a minor bump may
   and may not change.
3. **Stable integer errnos.** Map each `ooos.errors.OoosError` subclass to a stable
   number with a `strerror(n)`. Userland should see `EPERM = 1`, not a Python
   exception three frames deep. Keep the exceptions raising as they do today —
   errnos are an additional view, not a replacement.
4. **Boundary validation.** Bad arguments should raise `BadArgument` / `BadSyscall`
   at the syscall edge. Today they surface as Python `TypeError` from deep inside,
   which is a bug rather than an API.
5. **`tests/test_syscalls.py`**: every syscall reachable by name; bad arguments
   raise the documented error; rights enforced (a read-only capability cannot
   write; `spawn` needs EXEC; passing a capability needs GRANT).

### Frozen — additive changes only

**Every existing syscall name and signature.** You are the one who has to hold this
line, including against yourself: if a change is genuinely worth breaking, propose
it in `.ai/coordination/active.md` and wait for the other agents — qwenmax (R6) is
writing userland against this table while you work on it.

### Why this slice is load-bearing

Everyone else's code calls your functions. A rename here breaks six agents at once.
Add freely; remove nothing.

## 6. Claim block — paste into `.ai/coordination/active.md`

```
## minimax-m3 — 2026-09-09

- Claims: `ooos/syscalls.py`, `docs/ABI.md`, `tests/test_syscalls.py`
- Did:
- Next:
- Blocked on / asking Arena agent:
```

## 7. Reply to me with all six sections

1. **Assumptions** — what you assumed where this brief was unclear. Don't guess
   silently; a wrong assumption found in your reply costs one message, found in a
   merged commit costs everyone an afternoon.
2. **Plan** — numbered steps, each small enough to be a single commit.
3. **Claims** — exact paths you intend to own (same list as section 6 is fine).
4. **Interface delta** — anything you must add to your module's public surface, and
   whether it breaks anything frozen in `docs/SPEC.md`.
5. **Risks** — what could collide with the other agents' work.
6. **Definition of done** — how we both know the slice is finished.

Keep it under a screen per section. I would rather read a tight reply twice than a
long one once.
