"""Generate one self-contained handoff file per model, in docs/handoff/.

The briefs share a preamble (repo facts, branch rules, house style) and differ in
the slice each model owns. Keeping the shared part in ONE place is the point: when
the repo changes, edit this file and re-run, instead of hand-fixing seven copies
that have already drifted.

    python3 tools/make_handoff.py
"""

from __future__ import annotations

import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "docs" / "handoff"

HEADER = """\
# OO-OS — task brief for {model}

You are joining **OO-OS**, an object-oriented operating system, in a repository
where several AI agents work at the same time, on the same branch. Read this whole
message before you write a line of code. It is self-contained: you do not need
anything else to start.

{gfreeting}

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
- Current tip: `{commit}` — pull it before you start.

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
python -m pytest -q                     # {tests} tests, all green
```

## 3. Hard rules

- Work **only** on `arena/01a084f5-oo`. Never create, switch to, or push another branch.
- Never force-push; never rebase or amend pushed history; never rewrite `main`.
- `git pull --rebase origin arena/01a084f5-oo` before you start **and** before you push.
- Commit in small atomic steps, message prefix `agent/{model}: <what changed>`.
  Example: `agent/{model}: add copy-on-write regions to the memory manager`
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

"""

FOOTER = """
## 6. Claim block — paste into `.ai/coordination/active.md`

```
## {model} — {date}

- Claims: {claims}
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
"""

MODELS = {
    "deepseek-pro": {
        "title": "R1 — memory management",
        "claims": "`ooos/mm.py`, `tests/test_mm.py`",
        "greeting": "Your slice is the **memory manager**. You own `ooos/mm.py` outright.",
        "body": """\
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
mysterious `OomError` in someone else's test.""",
    },
    "fable-5": {
        "title": "R2 — scheduling",
        "claims": "`ooos/sched.py`, `tests/test_sched.py`",
        "greeting": "Your slice is the **scheduler**. You own `ooos/sched.py` outright.",
        "body": """\
### Where it stands

Threads are Python generators. Each `yield` is a scheduling point; the yielded
object is a request (`Sleep`, `Recv`, `WaitPid`, `ReadLine`, `ExitThread`) defined in
`ooos/requests.py` and wrapped by `ooos/api.py`. Policy is round-robin with a 4-step
time slice, and **one scheduler step advances the virtual clock by exactly one
tick** — that is what makes every run reproducible and every test assertable.

### Build

1. **Priorities with aging.** Add a priority to `Thread`, schedule the highest
   runnable priority first, and age long-waiting threads so nothing starves. Keep
   round-robin as the default, selectable at boot with `--policy rr|prio`.
2. **Thread lifecycle.** `join(tid)`, `detach`, and a per-process thread limit that
   fails loudly rather than silently dropping a spawn.
3. **Deadlock diagnosis.** Today, when nothing is runnable the machine just stops.
   Detect that state and print *why*: which thread is waiting on which endpoint or
   pid, and what each one holds. This is the single most useful thing you can add —
   it turns a silent hang into a one-line bug report.
4. **`tests/test_sched.py`**: round-robin fairness; `sleep(n)` ordering across
   threads; `waitpid` reaping and its `(pid, status)` return; determinism — two
   identical runs produce identical tick counts.

### Frozen — add, do not change

`create_process`, `create_thread`, `step`, `run`, `wake`, `kill_process`,
`kill_thread`, `ps`, and the `Process`/`Thread` fields the rest of the kernel reads.

### Hard constraint

**No real threads, no wall clock, no `time.sleep`.** Determinism is not a nicety
here — the entire test suite, and the other agents' ability to reproduce your bugs,
rest on it (D3). If you need time to pass, advance the virtual clock.""",
    },
    "gimni-3.8flash": {
        "title": "R3 — IPC",
        "claims": "`ooos/ipc.py`, `tests/test_ipc.py`",
        "greeting": "Your slice is **IPC**. You own `ooos/ipc.py` outright.",
        "body": """\
### Where it stands

`Endpoint` is a bounded queue with a capability in front of it. Send is
non-blocking until the queue is full, then it raises `WouldBlock` — messages are
never silently dropped. A blocked receiver is woken *directly by the sender*
(`Endpoint._wake_waiter` → `scheduler.wake`), so a handoff costs no polling.

The interesting part already works end to end: a capability can ride inside a
message. The sender calls `mint(cap_index)` to detach a capability, sends it, and
the receiver calls `install(message.caps[0])` to adopt it. See `talker` and
`ipcdemo` in `ooos/user/programs.py` — run `ipcdemo` in the shell to watch it.

### Build

1. **`try_send()`** — an explicitly non-blocking variant with clean backpressure
   semantics. It must not increment the `dropped` counter: a caller polling
   deliberately is not an error.
2. **Multi-waiter fairness.** Prove first-blocked-first-served under load. Today
   `Endpoint` pops the oldest waiter; verify it holds when several threads block on
   one endpoint and messages arrive in bursts.
3. **Reply channels.** `send` optionally carries a one-shot reply capability that
   is consumed on first use and refused afterwards.
4. **Revocation.** `destroy()` on the endpoint object must fail outstanding sends
   and wake every blocked receiver with `None` (which is how a receiver learns the
   endpoint died).
5. **`tests/test_ipc.py`**: message ordering, capacity limits, blocking receive,
   close-wakes-receivers, and a capability round trip (`mint` → send → `install` →
   use the received capability).

### Frozen — add, do not change

`Endpoint.send` / `recv` / `close` / `stats`, and the `Message` shape
(`sender`, `data`, `caps`).

### Note on scheduling

`Endpoint` reaches the scheduler through `self.kernel.sched`, bound by the object
table at insertion time. If you need a new wake path, coordinate with fable-5 (R2)
— `scheduler.wake()` is theirs.""",
    },
    "glm5-2": {
        "title": "R4 — the virtual filesystem",
        "claims": "`ooos/vfs.py`, `tests/test_vfs.py`",
        "greeting": "Your slice is the **VFS**. You own `ooos/vfs.py` outright.",
        "body": """\
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
`.ai/coordination/active.md` if you'd rather they used a different call.""",
    },
    "minimax-m3": {
        "title": "R5 — the syscall ABI",
        "claims": "`ooos/syscalls.py`, `docs/ABI.md`, `tests/test_syscalls.py`",
        "greeting": "Your slice is the **syscall ABI** — the contract every user program and every other agent compiles against. You own `ooos/syscalls.py` and `docs/ABI.md`.",
        "body": """\
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
Add freely; remove nothing.""",
    },
    "qwenmax": {
        "title": "R6 — userland",
        "claims": "`ooos/user/**`, `tests/test_userland.py`",
        "greeting": "Your slice is **userland** — the programs people actually run. You own `ooos/user/**`, and nothing there is frozen, so you can move fast.",
        "body": """\
### Where it stands

Programs are generator factories registered by name:

```python
@program("hello")
def hello(kernel, argv):
    kernel.syscall("print", f"hello, {argv[0] if argv else 'world'}\\n")
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
reaching into kernel internals — the whole point of userland is that it can't.""",
    },
    "sonnet-5": {
        "title": "R7 — tests and CI",
        "claims": "`tests/**` (except `test_boot_smoke.py` and `test_capabilities.py`), `.github/workflows/ci.yml`",
        "greeting": "Your slice is **tests and CI**. You own `tests/**` — **except** `tests/test_boot_smoke.py` and `tests/test_capabilities.py`, which are mine and guard the vertical slice. Improve those two by proposing a change, not by editing them.",
        "body": """\
### Where it stands

{n} tests, all green, about 0.05s. `tests/test_boot_smoke.py` boots a machine with a
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
contract is a test that will get deleted, and deservedly so.""",
    },
}

DATE = "2026-09-09"


def commit() -> str:
    import subprocess

    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        return out.stdout.strip()
    except Exception:
        return "HEAD"


def test_count() -> int:
    import subprocess

    try:
        out = subprocess.run(
            ["python3", "-m", "pytest", "-q", "--collect-only"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        for line in reversed(out.stdout.strip().splitlines()):
            if "test" in line and "collected" in line:
                return int(line.split()[0])
    except Exception:
        pass
    return 21


def render(model: str, spec: dict, commit_sha: str, tests: int) -> str:
    # .replace, not .format: some bodies contain literal Python braces in
    # code samples, and escaping all of them would make the text unreadable.
    body = spec["body"].replace("{n}", str(tests))
    parts = [
        HEADER.format(model=model, gfreeting=spec["greeting"], commit=commit_sha, tests=tests),
        f"## 5. {spec['title']}\n\n",
        textwrap.dedent(body).strip(),
        "\n",
        FOOTER.format(model=model, claims=spec["claims"], date=DATE),
    ]
    return "".join(parts)


def main() -> None:
    sha = commit()
    tests = test_count()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for model, spec in MODELS.items():
        path = OUT_DIR / f"{model}.md"
        path.write_text(render(model, spec, sha, tests), encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}")
    print(f"\n{len(MODELS)} briefs generated from tip {sha}, {tests} tests")


if __name__ == "__main__":
    main()
