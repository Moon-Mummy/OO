# OO-OS — task brief for fable-5

You are joining **OO-OS**, an object-oriented operating system, in a repository
where several AI agents work at the same time, on the same branch. Read this whole
message before you write a line of code. It is self-contained: you do not need
anything else to start.

Your slice is the **scheduler**. You own `ooos/sched.py` outright.

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
- Commit in small atomic steps, message prefix `agent/fable-5: <what changed>`.
  Example: `agent/fable-5: add copy-on-write regions to the memory manager`
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

## 5. R2 — scheduling

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
rest on it (D3). If you need time to pass, advance the virtual clock.

## 6. Claim block — paste into `.ai/coordination/active.md`

```
## fable-5 — 2026-09-09

- Claims: `ooos/sched.py`, `tests/test_sched.py`
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
