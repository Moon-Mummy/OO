# Handoff brief — for the other AI models

You are joining **OO-OS**, an object-oriented operating system, in a repository
where several AI agents work at the same time on the same branch.

Send **Part A** to every model. Then send that model's **Part B** block.

---

## Part A — paste this to everyone

```
You are working on OO-OS with another AI agent (me), in the same repository, at
the same time, on the same branch. Read this before writing anything.

## What OO-OS is

An object-oriented operating system. Two rules define it:
  1. Every resource is an object (file, directory, endpoint, console, address
     space). One flat kernel object table, nothing outside it.
  2. Every reference is a capability — an unforgeable (object id, rights) pair in
     a per-process table. No ambient authority: if you hold no capability for an
     object, it does not exist for you.

It is a microkernel design that runs in userspace on a virtual clock, so every
run is deterministic and testable with pytest. Python 3.11+, zero runtime
dependencies. The baseline boots, schedules, allocates memory, passes messages and
runs a shell. It is NOT a bootable kernel yet (docs/DECISIONS.md D1).

## Repository facts

- Repo: Moon-Mummy/OO on GitHub. Branch: arena/01a084f5-oo (base commit 46bc308).
- Layout:
    ooos/         the kernel: capability.py objects.py clock.py sched.py mm.py
                  ipc.py vfs.py syscalls.py console.py kernel.py boot.py
    ooos/user/    userland: init.py shell.py programs.py
    ooos/web/     browser terminal (stdlib http.server)
    docs/         SPEC.md DECISIONS.md ROADMAP.md HANDOFF.md
    tests/        pytest
- Quickstart:
    python -m ooos.boot --demo              # scripted tour
    python -m ooos.boot --script "ls /; ps; exit"
    python -m ooos.web --port 8000          # browser terminal
    python -m pytest -q                     # 21 tests, all green

## Hard rules

- Work ONLY on arena/01a084f5-oo. Never create, switch to, or push another branch.
- Never force-push; never rebase or amend pushed history; never rewrite main.
- git pull --rebase origin arena/01a084f5-oo before you start and before you push.
- Commit in small atomic steps, message prefix: agent/<your-name>: <what changed>.
  Example: agent/glm5-2: add symlink support to the VFS
- No secrets in committed files. No build output, no generated datasets.
- Claim file paths in .ai/coordination/active.md BEFORE editing them, and release
  them when done. Do not edit another agent's claimed paths; ask instead.
- The interfaces listed in docs/SPEC.md are FROZEN. You may add to a module; you
  may not rename or change the signature of anything public in it. If you need to
  break one, stop and propose it in .ai/coordination/active.md first.
- Every change ships with tests. python -m pytest -q must stay green.

## House style

- Type hints on public functions; docstrings say what and why, not what-for-what.
- Errors are ooos.errors.OoosError subclasses, never bare Python exceptions.
- Prefer adding new files over rewriting someone else's.
- Determinism is a feature: never read the wall clock, never use real threads,
  never call random without a seeded RNG.

## Reply to me with all six sections

1. Assumptions — what you assumed where the brief was unclear.
2. Plan — numbered steps, each small enough to be one commit.
3. Claims — exact paths you intend to own, paste-ready for .ai/coordination/active.md.
4. Interface delta — anything you must add to your module's public surface.
5. Risks — what could collide with the other agents' work.
6. Definition of done — how we both know the slice is finished.
```

---

## Part B — per-model assignments

### deepseek-pro — R1, memory management

```
Your slice: ooos/mm.py (plus tests/test_mm.py). You own it.

Today: PhysicalMemory counts 4 KiB frames and raises OomError; AddressSpace is a
list of Regions over one bytearray, with map/unmap/protect/read/write. Every
access is bounds- and rights-checked, so a wild pointer is a Segfault.

Build:
  1. Copy-on-write regions: share a region between two address spaces, copy on
     first write. Add a share(source_vaddr, rights) method.
  2. Slab allocator for small allocations, and a free list instead of pure bump
     allocation. Keep map()'s signature.
  3. File-backed regions: map a File object into an address space.
  4. tests/test_mm.py covering COW, OomError on exhaustion, Segfault on wild
     access, and frame accounting after unmap.

Frozen: map, unmap, protect, read, write, stats, dump. Add, don't change.
Demo target: in the shell, `alloc 4096` then `maps` should show region types.
```

### fable-5 — R2, scheduling

```
Your slice: ooos/sched.py (plus tests/test_sched.py). You own it.

Today: threads are Python generators; each yield is a scheduling point; round
robin with a 4-step slice; one step == one tick on a virtual clock, which is what
makes runs reproducible. Requests are sleep / recv / waitpid / read_line /
exit_thread in ooos/requests.py, wrapped by ooos/api.py.

Build:
  1. Priorities with aging. Keep round-robin as the default policy, selectable
     with a --policy flag on boot.
  2. Thread join and detach, plus a per-process thread limit.
  3. Deadlock diagnosis: when nothing is runnable, print WHY — which thread waits
     on which endpoint or pid — instead of halting silently.
  4. tests/test_sched.py: round-robin fairness, sleep ordering, waitpid reaping,
     tick determinism (two identical runs give identical tick counts).

Frozen: create_process, create_thread, step, run, wake, kill_process, ps.
Do NOT introduce real threads or wall-clock time — determinism is the property
the whole test suite rests on (docs/DECISIONS.md D3).
```

### gimni-3.8flash — R3, IPC

```
Your slice: ooos/ipc.py (plus tests/test_ipc.py). You own it.

Today: Endpoint is a bounded queue behind a capability. Send is non-blocking
until full (then WouldBlock — messages are never dropped). A blocked receiver is
woken directly by the sender. Capabilities ride along inside messages: the sender
calls mint() to detach a capability, the receiver calls install() to adopt it.
See talker/ipcdemo in ooos/user/programs.py for a working end-to-end demo.

Build:
  1. try_send() non-blocking variant with explicit backpressure, plus a
     WouldBlock path that does not increment the dropped counter when the caller
     is polling deliberately.
  2. Multi-waiter fairness: prove first-blocked-first-served under load.
  3. Reply channels: send carrying a one-shot reply capability that is consumed
     on first use.
  4. Endpoint revocation: destroy() on the endpoint object must fail outstanding
     sends and wake receivers with None.
  5. tests/test_ipc.py covering ordering, capacity, blocking receive, and
     close-wakes-receivers.

Frozen: Endpoint.send/recv/close/stats, the Message shape (sender, data, caps).
```

### glm5-2 — R4, the VFS

```
Your slice: ooos/vfs.py (plus tests/test_vfs.py). You own it.

Today: a directory is an object whose children are objects; a file is an object
with read/write/truncate. Paths are for humans only — the kernel resolves a path
to a VNode, then works with the object and a capability to it. Opening a path
mints a capability.

Build:
  1. D5, the important one: per-directory capabilities. Resolve a path by walking
     capabilities so that holding a capability on /home/user grants nothing about
     /etc. This changes how resolve() takes its start point — design it, and
     update docs/DECISIONS.md D5 when you do.
  2. Symlinks, hard links, rename.
  3. A read-only hostfs adapter exposing a real directory as a VFS subtree.
  4. /proc as live kernel statistics (processes, objects, memory, uptime).
  5. tests/test_vfs.py proving that narrowing a directory capability blocks
     access to its siblings.

Frozen: resolve, resolve_parent, and the File/Directory method names that the
shell and syscall layer already call (read, write, truncate, size, stat, list,
lookup, create_file, mkdir, unlink, path).
```

### minimax-m3 — R5, the syscall ABI

```
Your slice: ooos/syscalls.py, plus docs/ABI.md. You own it.

Today: Syscalls holds a name -> handler table, auto-built from public methods.
Every syscall is synchronous and takes the process first; blocking lives in
ooos/api.py and is expressed as yield from (docs/DECISIONS.md D6). Rights are
derived from the method name by _RIGHTS_FOR_METHOD.

Build:
  1. Version negotiation: a kernel_version() syscall, and docs/ABI.md freezing
     every name, argument order, and return type.
  2. Stable integer errnos: map each ooos.errors.OoosError subclass to a number,
     with strerror(n). Userland should be able to see EPERM = n, not a Python
     exception.
  3. Argument validation at the boundary — today a bad argument surfaces as a
     Python exception several frames deep, which is a bug, not an API.
  4. tests/test_syscalls.py: every syscall reachable, bad arguments raise
     BadArgument/BadSyscall, and rights are enforced (a read-only capability
     cannot write).

Frozen: every existing syscall name and signature. Additive changes only. If you
must break one, propose it in .ai/coordination/active.md and wait.
```

### qwenmax — R6, userland

```
Your slice: ooos/user/* (plus tests/test_userland.py). You own it. Nothing here
is frozen — it is purely additive, so you can move fast.

Today: programs are generator factories registered with @program("name"), taking
(kernel, argv). A program that never blocks can be a plain function. Blocking is
`yield from sleep(n) / recv(ep) / waitpid(pid) / read_line()`. The shell
(ooos/user/shell.py) has 30 commands; COMMANDS, SUMMARY and USAGE are the three
dicts you extend.

Build:
  1. Programs: ls -l, wc, grep, ps -a, cat with several files, edit (a tiny
     line editor — the "it's an OS" moment).
  2. Shell: environment variables with $VAR expansion, quoting in echo, pipes
     between programs, a .ooosrc run at boot.
  3. tests/test_userland.py driving each new program through the shell.

Keep: the prompt format `<cwd> $ `, the `;`-separated command syntax, and the
rule that a command is either a plain function returning a string or a generator
function when it needs to block.
```

### sonnet-5 — R7, tests and CI

```
Your slice: tests/** and .github/workflows/ci.yml. You own them — EXCEPT
tests/test_boot_smoke.py and tests/test_capabilities.py, which are mine and guard
the vertical slice. Improve them by proposing a change, not by editing directly.

Today: 21 tests, all green, ~0.05s. tests/test_boot_smoke.py boots a machine with
a capturing console, feeds it lines, and asserts on the transcript;
tests/test_capabilities.py covers the security model.

Build:
  1. Per-subsystem modules: test_mm.py, test_sched.py, test_ipc.py, test_vfs.py,
     test_syscalls.py, test_userland.py. You will be writing these while the
     other agents build their slices — write them against the FROZEN interfaces
     in docs/SPEC.md so they pass on the baseline, then extend as each slice
     lands.
  2. A determinism property test: for any random command sequence (seeded RNG!),
     two runs produce identical output AND identical tick counts.
  3. .github/workflows/ci.yml: pytest on 3.11 and 3.12, plus
     `python -m ooos.boot --demo` as a smoke test, plus coverage per module.
  4. A conftest.py with a `machine()` fixture so nobody re-invents boot-in-a-test.

Note: the other six agents are editing the modules you are testing. When one of
your tests fails because a slice landed, check .ai/coordination/active.md before
assuming it is a bug — and tell the owner rather than deleting the test.
```
