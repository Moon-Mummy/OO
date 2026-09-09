# OO-OS — task brief for qwenmax

You are joining **OO-OS**, an object-oriented operating system, in a repository
where several AI agents work at the same time, on the same branch. Read this whole
message before you write a line of code. It is self-contained: you do not need
anything else to start.

Your slice is **userland** — the programs people actually run. You own `ooos/user/**`, and nothing there is frozen, so you can move fast.

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
- Commit in small atomic steps, message prefix `agent/qwenmax: <what changed>`.
  Example: `agent/qwenmax: add copy-on-write regions to the memory manager`
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

## 5. R6 — userland

### Where it stands

Programs are generator factories registered by name:

```python
@program("hello")
def hello(kernel, argv):
    kernel.syscall("print", f"hello, {argv[0] if argv else 'world'}\n")
```

A program that never blocks can be a plain function. Blocking is explicit:
`yield from sleep(2)`, `yield from recv(endpoint)`, `yield from waitpid(pid)`,
`yield from read_line()`. The shell (`ooos/user/shell.py`) has 30 commands; the
`COMMANDS`, `SUMMARY` and `USAGE` dicts are what you extend. `init` prints a banner,
spawns the shell, reaps it, and halts.

### Build

1. **Programs.** `ls -l` (sizes and types), `wc`, `grep`, `ps -a`, `cat` with
   several files, `tree`, and **`edit PATH`** — a tiny line editor. `edit` is the
   moment it stops being a demo and starts being an OS.
2. **Shell features.** Environment variables with `$VAR` expansion, correct quoting
   in `echo`, pipes between programs (`ls / | grep etc`), and a `.ooosrc` run at
   boot from `/etc/ooosrc`.
3. **Your own demo.** Something that shows off capabilities the way `ipcdemo` does —
   a program that receives a narrowed capability and visibly fails to overstep it.
4. **`tests/test_userland.py`** driving each new program through the shell, using the
   same "boot a machine, feed it lines, assert on the transcript" pattern as
   `tests/test_boot_smoke.py`.

### Keep

- The prompt format `<cwd> $ `, and `;`-separated commands on one line.
- A command is either a plain function returning a string, or a generator function
  when it needs to block. `Shell.run_one` handles both.
- Errors are caught as `OoosError` and printed as `<name>: <message>` — don't let a
  raw traceback reach the console.

### Note

minimax-m3 (R5) is freezing the syscall ABI while you write against it. If you need
a syscall that doesn't exist, ask them in `.ai/coordination/active.md` rather than
reaching into kernel internals — the whole point of userland is that it can't.

## 6. Claim block — paste into `.ai/coordination/active.md`

```
## qwenmax — 2026-09-09

- Claims: `ooos/user/**`, `tests/test_userland.py`
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
