# OO-OS — task brief for deepseek-pro

You are joining **OO-OS**, an object-oriented operating system, in a repository
where several AI agents work at the same time, on the same branch. Read this whole
message before you write a line of code. It is self-contained: you do not need
anything else to start.

Your slice is the **memory manager**. You own `ooos/mm.py` outright.

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
- Commit in small atomic steps, message prefix `agent/deepseek-pro: <what changed>`.
  Example: `agent/deepseek-pro: add copy-on-write regions to the memory manager`
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

## 5. R1 — memory management

### Where it stands

`PhysicalMemory` counts 4 KiB frames and raises `OomError` rather than
over-committing. Each process gets an `AddressSpace`: a list of `Region`s over one
byte store, with `map` / `unmap` / `protect` / `read` / `write`. Every access is
bounds- and rights-checked, so a wild pointer raises `Segfault` instead of
corrupting the heap. In the shell: `alloc 4096`, then `maps` shows the region table.

### Build

1. **Copy-on-write regions.** Add `share(source_vaddr, rights)` so two address
   spaces can share a region and copy on first write. Account for the shared frames
   exactly once, and release them only when the last sharer unmaps.
2. **A real allocator.** Today `map()` is a bump allocator over `_brk`. Add a free
   list with coalescing on `unmap`, plus a slab path for small allocations. Keep
   `map()`'s signature and its "return the base virtual address" contract.
3. **File-backed regions.** `map_file(vnode, rights)` maps a `File` object into an
   address space. Coordinate with glm5-2 (R4) on the `File` interface before you
   depend on it — it is frozen, so agree on the call, don't change it.
4. **`tests/test_mm.py`**: COW gives independent copies after a write; exhaustion
   raises `OomError` and leaves `stats()` consistent; a wild access raises
   `Segfault`; `unmap` returns every frame to `free_frames`.

### Frozen — add, do not change

`map`, `unmap`, `protect`, `read`, `write`, `stats`, `dump`, and the `Region`
fields `base`, `size`, `rights`, `name`.

### Why it matters

Memory is the one subsystem where a subtle bug looks like an unrelated failure three
modules away. Frame accounting that is off by one will eventually surface as a
mysterious `OomError` in someone else's test.

## 6. Claim block — paste into `.ai/coordination/active.md`

```
## deepseek-pro — 2026-09-09

- Claims: `ooos/mm.py`, `tests/test_mm.py`
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
