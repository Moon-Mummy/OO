# Decision records

Every decision here was made to unblock parallel work. Each one is reversible —
say the word, and it becomes a new record superseding the old one.

## D1 — Userspace simulation first, bootable kernel later

**Decision.** Build the kernel as a userspace program on a virtual clock. Keep a
hardware port as a later, separate milestone.

**Why.** Several agents work in one branch at once. They need to run and test
their subsystems without QEMU, a cross-compiler, or ring transitions. A virtual
clock also makes every run reproducible, so tests can assert on exact timings.

**Cost.** No real interrupts, no real preemption, no drivers yet.

**Revisit when.** The object model is stable and someone wants to take R7
(a real boot target) from `docs/ROADMAP.md`.

## D2 — Capabilities, not ACLs or Unix users

**Decision.** Authority is carried by unforgeable `(oid, rights)` pairs in a
per-process table. There is no ambient authority and no global namespace of names.

**Why.** "Object-oriented OS" is the premise, and capabilities are what make
object references safe to pass around. They also make the security model
testable: `tests/test_capabilities.py` exercises it directly.

**Cost.** Programs must be written to receive authority, not assume it.

**Alternatives rejected.** ACLs (need a user identity we don't have), plain
integer handles (forgeable, therefore not a security model).

## D3 — Cooperative threads as generators, one tick per step

**Decision.** Threads are Python generators. `yield` is the scheduling point; one
scheduler step advances the virtual clock by exactly one tick.

**Why.** No OS threads, no locks, no signals, fully deterministic. A deadlock is
detected as "nothing runnable and no timers pending" instead of a hang.

**Cost.** A user program that forgets to yield monopolises the CPU until its time
slice runs out at the next `yield` — there is no true preemption.

**Mitigation.** `--max-steps` panics instead of hanging; `ps` shows thread states.

## D4 — Python 3.11+, zero runtime dependencies

**Decision.** Core depends on nothing; `pytest` is the only dev dependency; the
web terminal is stdlib `http.server`.

**Why.** Every model that might work on this repo can read and write Python, and
`pip install -e .` is not a barrier to entry.

**Cost.** Slower than Rust/C; not suitable for a real boot target without a
rewrite.

**Alternatives rejected.** Rust (correct, but a much higher bar for
contributors), TypeScript (fine, but the capability story is weaker).

## D5 — Paths resolve via the root capability (per-directory rights deferred)

**Decision.** Path resolution checks that the caller holds a usable `root`
capability. Individual directories along the path are not yet capability-checked.

**Why.** Per-directory narrowing changes the VFS interface, and the VFS owner
should design it. Blocking on it would stall the boot path.

**Cost.** Directory-level confinement is not enforceable yet.

**Owner.** Whoever owns `ooos/vfs.py`.

## D6 — Syscalls are synchronous; blocking is `yield from`

**Decision.** No syscall ever blocks. Anything that waits is a request yielded to
the scheduler from `ooos/api.py`.

**Why.** It keeps the syscall table trivially testable and makes every blocking
point visible in the source — you can see where a program waits by looking for
`yield from`.

**Cost.** Programs must be generators to block.

## D7 — Endpoint capabilities carry GRANT

**Decision.** A newly created endpoint capability carries `rw--g`: the holder may
delegate along the channel.

**Why.** Capability passing is the mechanism the IPC demo is built around; making
every program call `restrict` before delegating adds ceremony without safety in a
single-user system.

**Cost.** A program can hand out more than it should unless the creator narrows
the capability first.

**Revisit when.** There is more than one mutually distrusting user.

## D8 — One branch, claim-before-edit

**Decision.** All agents work on `arena/01a084f5-oo` and claim paths in
`.ai/coordination/active.md` before editing them.

**Why.** The user asked for several models to collaborate in one repo. Merging
seven branches of half-finished work is worse than serialising seven disjoint
subsystems.

**Cost.** Agents must pull and rebase often.
