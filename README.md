# OO-OS

**An object-oriented operating system.** Two rules, and everything else follows:

1. **Every resource is an object** — files, directories, IPC endpoints, the
   console, address spaces. One flat kernel object table, nothing outside it.
2. **Every reference is a capability** — an unforgeable `(object id, rights)` pair
   in a per-process table. No ambient authority: hold no capability, see no object.

It boots, schedules processes, allocates paged memory, passes messages and runs a
shell — in userspace, on a virtual clock, so every run is deterministic and
testable with pytest.

```
$ python -m ooos.boot --demo
OO-OS 0.1.0 — object-oriented operating system
  every resource is an object, every reference is a capability
  type 'help' for commands, 'exit' to halt

/ $ ls /
bin/  etc/  home/  motd  proc/  tmp/
/ $ spawn counter 3 --wait
[counter pid=3] 0 @ tick 7
[counter pid=3] 1 @ tick 10
[counter pid=3] 2 @ tick 13
[counter pid=3] done
pid 3 exited with status 0 at tick 17
/ $ ipcdemo
[ipcdemo] spawned talker pid=6, waiting for a capability
[ipcdemo] <msg from tid=6 data='hello from talker (pid 6)' caps=1>
[ipcdemo] installed talker endpoint at cap 3
[talker] received 'ping from ipcdemo'
/ $ caps
0: root oid=1 rwxgd
1: console oid=2 rw---
```

## Run it

```bash
python -m ooos.boot                              # interactive shell (tty)
python -m ooos.boot --demo                       # scripted tour
python -m ooos.boot --script "ls /; ps; exit"    # one-shot
echo "cat /etc/motd; exit" | python -m ooos.boot # piped
python -m ooos.web --port 8000                   # browser terminal
python -m pytest -q                              # 21 tests
```

Python 3.11+, zero runtime dependencies. `pip install -e '.[dev]'` for pytest.

## Try these

| Command | What it shows |
|---|---|
| `help` | every command |
| `caps` | your process's capability table |
| `objects` | the kernel object table, by type |
| `ps` | process table |
| `spawn counter 5 --wait` | a blocking program that yields the CPU |
| `ipcdemo` | capability passing between two processes |
| `alloc 4096; maps; memory` | paged memory, checked on every access |
| `peek 0xdeadbeef 4` | a segfault, caught and reported |
| `stat /etc/motd` | an object's metadata |
| `uptime` | kernel statistics |

## How it works

| Module | Responsibility |
|---|---|
| `ooos/objects.py` | the object table and method dispatch |
| `ooos/capability.py` | rights and capabilities |
| `ooos/clock.py` | the virtual clock |
| `ooos/sched.py` | processes, threads, round-robin on generator `yield`s |
| `ooos/mm.py` | frame accounting, address spaces, bounds/rights checks |
| `ooos/ipc.py` | endpoints and message passing |
| `ooos/vfs.py` | files and directories as objects |
| `ooos/syscalls.py` | the synchronous, rights-checked user ABI |
| `ooos/console.py` | the terminal — itself a kernel object |
| `ooos/kernel.py` | wiring, boot, panic, stats |
| `ooos/user/` | init, shell, sample programs |
| `ooos/web/` | browser terminal (stdlib only) |

A user program is a generator factory:

```python
@program("hello")
def hello(kernel, argv):
    kernel.syscall("print", f"hello, {argv[0] if argv else 'world'}\n")
```

Blocking is explicit — `yield from sleep(2)`, `yield from recv(endpoint)`,
`yield from waitpid(pid)`. No syscall ever blocks (that is decision D6).

## Working here with other agents

Several AI agents develop this repo in parallel on branch `arena/01a084f5-oo`.

- `AGENTS.md` — branch rules, claim map, house style
- `.ai/coordination/active.md` — who owns which paths right now
- `docs/SPEC.md` — the design, and which interfaces are frozen
- `docs/DECISIONS.md` — D1–D8, each reversible with a word
- `docs/ROADMAP.md` — R1–R11, one slice per subsystem, built in parallel
- `docs/HANDOFF.md` — the brief to paste into another model

## Status

0.1.0 — the vertical slice works end to end: boot, shell, processes, memory, IPC,
VFS, capabilities, and a web terminal. Not yet: persistence, networking,
multi-core, and a bootable image (see `docs/ROADMAP.md`).
