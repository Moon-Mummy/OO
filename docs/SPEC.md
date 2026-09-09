# OO-OS 0.1.0 — specification

**OO-OS is an object-oriented operating system.** Two sentences define it:

1. **Every resource is an object** — files, directories, endpoints, the console,
   address spaces. There is one flat kernel object table and nothing outside it.
2. **Every reference is a capability** — an unforgeable `(object id, rights)` pair
   held in a per-process table. User code never names an object directly; it names
   a capability *index*, exactly like a file descriptor. There is no ambient
   authority: no object is reachable unless you hold a capability for it.

This is a **microkernel design running in userspace on a virtual clock**. It boots,
schedules, allocates, passes messages and runs a shell — and because time is a
counter and not a wall clock, every run is reproducible.

## Why userspace

A bootable kernel is a late-stage target, not a starting point. Running in
userspace on a virtual clock buys:

- **Determinism** — the same program with the same inputs produces the same
  tick-by-tick trace. Tests can assert on exact timings.
- **Testability** — no QEMU, no cross-compiler, no ring transitions. `pytest` is
  the test harness.
- **Parallelism** — several agents can own disjoint subsystems and never need
  hardware to check their work.
- **Focus** — the interesting part of an OO OS is the object/capability model,
  not the boot sector.

The port to real hardware is tracked as `docs/ROADMAP.md` item R7.

## Architecture

```
        userland          shell  hello  counter  talker  ipcdemo
           │                    (generator programs)
   ────────┼───────────────────────────────────────────────────────
    syscall layer         ooos/syscalls.py   (synchronous, rights-checked)
           │
        kernel            clock · objects · scheduler · memory
           │
     ┌─────┼──────┬───────────┬──────────┐
   VFS   IPC   Console   AddressSpace   Process/Thread
```

| Module | Owns | Interface currently frozen |
|---|---|---|
| `ooos/capability.py` | `Rights`, `Capability`, parsing/formatting | yes |
| `ooos/objects.py` | `KernelObject`, `ObjectTable`, method dispatch | yes |
| `ooos/clock.py` | `VirtualClock` | yes |
| `ooos/requests.py` | thread → scheduler request types | yes |
| `ooos/api.py` | blocking helpers (`sleep`, `recv`, `read_line`, …) | yes |
| `ooos/sched.py` | `Thread`, `Process`, `Scheduler` | yes |
| `ooos/mm.py` | `PhysicalMemory`, `AddressSpace`, `MemoryManager` | yes |
| `ooos/ipc.py` | `Endpoint`, `Message` | yes |
| `ooos/vfs.py` | `File`, `Directory`, `MemFS`, path resolution | yes |
| `ooos/syscalls.py` | the syscall table (the user ABI) | yes |
| `ooos/console.py` | `Console` (a kernel object) | yes |
| `ooos/kernel.py` | wiring, boot, panic, stats | yes |
| `ooos/user/*` | programs, shell, init | no — additive |
| `ooos/web/*` | browser terminal | no — additive |

"Frozen" means: you may add, you may not rename or change the signature of
anything public in a minor version. Breakage needs a decision record.

## The object model

```python
class KernelObject:
    interface: ClassVar[str]      # "file", "dir", "endpoint", "console", …
    oid: int                      # assigned by the object table
    def methods(self) -> dict     # public callables = the object's interface
    def invoke(self, method, *args)
```

Any public (non-underscore) callable on a subclass *is* a method of that object's
interface. `invoke` raises `NoSuchMethod` rather than failing mysteriously, and
`ObjectNotFound` if the object was destroyed. Objects are bound to the kernel when
inserted (`bind()`), which is how an endpoint reaches the scheduler to wake a
blocked receiver.

## The capability model

```python
@dataclass(frozen=True)
class Capability:
    oid: int
    rights: Rights = READ | WRITE
    label: str = ""
```

Rights are `READ | WRITE | EXEC | GRANT | DESTROY`, written as `"rw"`, `"rwx"`, …
Each process holds `caps: dict[int, Capability]`. The syscall layer derives the
right it needs from the method name (see `_RIGHTS_FOR_METHOD` in
`ooos/syscalls.py`): `write` needs WRITE, `spawn` needs EXEC, `grant` needs GRANT,
everything else needs READ. A missing right raises `NotPermitted`.

**Delegation.** A child process inherits only the bootstrap capabilities —
`root`, `console`, `mailbox`. Everything else must arrive inside a message:

```python
own = kernel.syscall("mint", cap_index)      # detach the capability object
kernel.syscall("send", mailbox, "hi", (own,))  # requires GRANT on the channel
...
index = kernel.syscall("install", message.caps[0])   # receiver adopts it
```

`restrict` narrows a capability; nothing widens one. `ooos/user/programs.py`
(`talker`, `ipcdemo`) is a working demonstration of this whole path.

## Scheduling

Threads are Python **generators**. One `yield` = one scheduling point:

| Yield | Effect |
|---|---|
| `yield` (bare) | keep running if the time slice is not exhausted |
| `yield from yield_cpu()` | move to the back of the ready queue |
| `yield from sleep(n)` | block until `now + n`; the clock jumps to the next deadline when idle |
| `yield from recv(endpoint)` | block until a message lands; the endpoint wakes the thread directly |
| `yield from waitpid(pid)` | block until a child exits |
| `yield from read_line()` | block until console input arrives (EOF terminates the thread) |

Policy is round-robin with a 4-step time slice (`--slice`). One scheduler step
advances the virtual clock by exactly one tick, which is what makes runs
reproducible. A run that exceeds `--max-steps` panics instead of hanging.

Processes exit when their last thread exits; the parent is woken with
`(pid, status)`; uncaught `OoosError` faults the thread and is reported on the
console rather than killing the machine.

## Memory

`PhysicalMemory` counts 4 KiB frames and raises `OomError` rather than
over-committing. Each process gets an `AddressSpace` — a list of `Region`s over a
byte store — with `map` / `unmap` / `protect` / `read` / `write`. Every access is
bounds- and rights-checked, so a wild pointer is a `Segfault`, not corruption.
`maps` prints the region table from the shell.

## IPC

`Endpoint` is a bounded queue with a capability in front of it. Send is
non-blocking until the queue is full (then `WouldBlock` — messages are never
silently dropped). Receivers blocked on an empty endpoint are woken by the sender
directly, so a handoff costs no polling. Capabilities ride along with messages.

## Filesystem

A directory is an object whose children are objects; a file is an object with
`read`/`write`/`truncate`. Paths exist only for humans: the kernel resolves a path
to a VNode, then works with the object and a capability to it. Opening a path
mints a capability — there is no separate descriptor table.

*Known limitation (D5):* path resolution checks the root capability only.
Per-directory narrowing is the natural next step and is reserved for whoever owns
`ooos/vfs.py`.

## Syscalls

Every syscall is **synchronous and takes the process first**. Blocking lives in
`ooos/api.py`, never in a syscall. User programs normally call
`kernel.syscall(name, *args)`, which supplies the current process.

Groups: objects & capabilities (`invoke`, `handle`, `caps`, `restrict`, `mint`,
`install`, `label`, `drop`, `stat`, `objects`), filesystem (`open`, `ls`, `read`,
`write`, `read_path`, `write_path`, `mkdir`, `touch`, `rm`, `stat_path`, `cwd`,
`chdir`), processes (`spawn`, `kill`, `exit`, `ps`, `pid`), IPC (`endpoint`,
`send`, `recv`, `endpoint_stats`), memory (`alloc`, `free`, `poke`, `peek`,
`maps`, `memory`), misc (`print`, `now`, `syscalls`, `kernel_stats`).

`syscalls` in the shell prints the live table.

## Userland

Programs are generator factories registered by name:

```python
@program("hello")
def hello(kernel, argv):
    kernel.syscall("print", "hello\n")
```

A program that never blocks can be a plain function. Run one with
`spawn hello world` (add `--wait` to block until it exits).

## Non-goals (for now)

Preemption by interrupt, real time, hardware drivers, multi-core, persistence,
users and authentication, a network stack, a bootable image. Each is a roadmap
item, not an oversight.
