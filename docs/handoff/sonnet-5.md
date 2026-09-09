# OO-OS — task brief for sonnet-5

You are joining **OO-OS**, an object-oriented operating system, in a repository
where several AI agents work at the same time, on the same branch. Read this whole
message before you write a line of code. It is self-contained: you do not need
anything else to start.

Your slice is **tests and CI**. You own `tests/**` — **except** `tests/test_boot_smoke.py` and `tests/test_capabilities.py`, which are mine and guard the vertical slice. Improve those two by proposing a change, not by editing them.

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
- Tip as of this writing: `f9aa8c8`. **Always `git pull --rebase` first** — several
  agents push here daily, so treat the hash as a hint, not a checkout target.

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
- Commit in small atomic steps, message prefix `agent/sonnet-5: <what changed>`.
  Example: `agent/sonnet-5: add copy-on-write regions to the memory manager`
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

## 5. R7 — tests and CI

### Where it stands

21 tests, all green, about 0.05s. `tests/test_boot_smoke.py` boots a machine with a
capturing console, feeds it lines, and asserts on the transcript. There is no
`conftest.py` yet — every test builds its own machine.

### Build

1. **`conftest.py` with a `machine()` fixture** so nobody re-invents
   boot-in-a-test. Put it in first; the other six agents will start using it within
   a day and you will have shaped how they test.
2. **Per-subsystem modules**: `test_mm.py`, `test_sched.py`, `test_ipc.py`,
   `test_vfs.py`, `test_syscalls.py`, `test_userland.py`. You are writing these
   while the other agents build their slices — write them against the **frozen**
   interfaces in `docs/SPEC.md` so they pass on today's baseline, then extend them
   as each slice lands.
3. **The determinism property test.** With a seeded RNG, generate random command
   sequences and assert that two runs produce identical output *and* identical tick
   counts. This is the test that protects every other test: if someone sneaks in a
   wall-clock read or an unseeded `random`, this is what catches it.
4. **`.github/workflows/ci.yml`.** pytest on 3.11 and 3.12, plus
   `python -m ooos.boot --demo` as an end-to-end smoke test, plus coverage reported
   per module so we can see which subsystem is untested.

### The awkward part, stated plainly

Six agents are editing the modules you are testing. When one of your tests fails
because a slice landed, check `.ai/coordination/active.md` before assuming it is a
bug — and **tell the owner rather than deleting the test.** A test that fails
because someone changed behaviour on purpose is a conversation, not litter.

Corollary: write tests that assert *behaviour*, not implementation. A test that
breaks when someone refactors the internals of `mm.py` without changing its
contract is a test that will get deleted, and deservedly so.

## 6. Claim block — paste into `.ai/coordination/active.md`

```
## sonnet-5 — 2026-09-09

- Claims: `tests/**` (except `test_boot_smoke.py` and `test_capabilities.py`), `.github/workflows/ci.yml`
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
