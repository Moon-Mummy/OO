# OO-OS — task brief for glm5-2

You are joining **OO-OS**, an object-oriented operating system, in a repository
where several AI agents work at the same time, on the same branch. Read this whole
message before you write a line of code. It is self-contained: you do not need
anything else to start.

Your slice is the **VFS**. You own `ooos/vfs.py` outright.

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
- Commit in small atomic steps, message prefix `agent/glm5-2: <what changed>`.
  Example: `agent/glm5-2: add copy-on-write regions to the memory manager`
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

## 5. R4 — the virtual filesystem

### Where it stands

A directory is an object whose children are objects; a file is an object with
`read` / `write` / `truncate` / `size` / `stat`. Paths exist only for humans: the
kernel resolves a path to a VNode, then works with the object and a capability to
it. Opening a path mints a capability — there is no separate descriptor table.
`MemFS` seeds a conventional tree (`/bin`, `/etc`, `/home/user`, `/proc`, `/tmp`).

### Build

1. **D5, the important one: per-directory capabilities.** Today path resolution
   checks only that the caller holds a usable `root` capability (D5). Change it so
   resolution *walks capabilities*: holding a capability on `/home/user` must grant
   nothing about `/etc`. This changes how `resolve()` takes its start point, so
   design it deliberately and update `docs/DECISIONS.md` D5 when you do. Coordinate
   with minimax-m3 (R5) — the syscall surface for `open` is theirs.
2. **Links and rename.** Symlinks (with loop detection), hard links, and `rename`.
3. **A `hostfs` adapter.** Expose a real host directory as a read-only VFS subtree,
   so the OS can read files that actually exist. Guard it: never resolve `..` above
   the mount point.
4. **`/proc` as live state.** `ps`, `objects`, `memory`, `uptime` as files a program
   can `cat`. It is the cheapest possible demonstration that "everything is a file,
   and every file is an object".
5. **`tests/test_vfs.py`**: the headline test is that narrowing a directory
   capability blocks access to its siblings. Also cover path normalisation
   (`.`/`..`/trailing slashes) and the error hierarchy (`NotFound`, `NotADirectory`,
   `IsADirectory`, `AlreadyExists`).

### Frozen — add, do not change

`resolve`, `resolve_parent`, `normalize`, `split`, and the `File` / `Directory`
method names the shell and syscall layer already call: `read`, `write`, `truncate`,
`size`, `stat`, `list`, `lookup`, `has`, `create_file`, `mkdir`, `unlink`, `path`.

### Note

deepseek-pro (R1) wants `map_file(vnode, rights)` to depend on `File`. Your
interface is frozen precisely so they can build against it — reply to them in
`.ai/coordination/active.md` if you'd rather they used a different call.

## 6. Claim block — paste into `.ai/coordination/active.md`

```
## glm5-2 — 2026-09-09

- Claims: `ooos/vfs.py`, `tests/test_vfs.py`
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
