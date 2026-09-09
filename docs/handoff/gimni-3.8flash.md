# OO-OS — task brief for gimni-3.8flash

You are joining **OO-OS**, an object-oriented operating system, in a repository
where several AI agents work at the same time, on the same branch. Read this whole
message before you write a line of code. It is self-contained: you do not need
anything else to start.

Your slice is **IPC**. You own `ooos/ipc.py` outright.

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
- Commit in small atomic steps, message prefix `agent/gimni-3.8flash: <what changed>`.
  Example: `agent/gimni-3.8flash: add copy-on-write regions to the memory manager`
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

## 5. R3 — IPC

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
— `scheduler.wake()` is theirs.

## 6. Claim block — paste into `.ai/coordination/active.md`

```
## gimni-3.8flash — 2026-09-09

- Claims: `ooos/ipc.py`, `tests/test_ipc.py`
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
