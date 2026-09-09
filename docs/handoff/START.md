# START.md — the "you acknowledged, now work" message

Send this to any model that replies with a summary of the repo instead of a plan.
It works for all seven models — it does not assume which slice they picked.

---

```
Thanks — but what you sent me lists my own files back at me. That was section 0.
I need sections 1-6, and I need them before you write code, not after.

Verified just now: the branch tip is still my commit. Nothing from you has landed.
So we are at zero.

## Pick ONE slice. Reply with the letter and nothing else if you like.

  R1  ooos/mm.py        copy-on-write regions, slab allocator, file-backed maps
  R2  ooos/sched.py     priorities with aging, thread join, deadlock diagnosis
  R3  ooos/ipc.py       try_send backpressure, reply channels, revocation
  R4  ooos/vfs.py       per-directory capabilities (D5), links, hostfs, /proc
  R5  ooos/syscalls.py  docs/ABI.md, version negotiation, integer errnos
  R6  ooos/user/**      ls -l, wc, grep, pipes, edit (a line editor)
  R7  tests/**, CI      conftest.py, determinism property test, GitHub Actions

R4 is the one I would take: per-directory capabilities is the largest hole in the
security model right now. R6 is the one with the most visible payoff. Your call.

## Then, in this order

1. Post your claim block to .ai/coordination/active.md — exact paths, nothing
   vague. "ooos/vfs.py" is a claim; "the VFS" is not.
2. Send me the six sections: assumptions, plan (each step small enough to be one
   commit), claims, interface delta, risks, definition of done. Half a screen
   each. Do not send me a file listing.
3. Make ONE commit that does one real thing with a test for it. Not a scaffold,
   not a TODO, not a refactor of my code. One behaviour, one test, green suite.

## If you have repo access

  git clone https://github.com/Moon-Mummy/OO && cd OO
  git checkout arena/01a084f5-oo && git pull --rebase
  # do the work
  git commit -m "agent/<your-name>: <what changed>"
  git push origin arena/01a084f5-oo

## If you do NOT have repo access

Say so in your first line. Then paste complete file contents (not diffs, not
snippets, not "..." elisions) for every file you create or change, with the full
path at the top of each. I will apply them and push under your agent name.

## Rules that will get your work reverted

- Any branch other than arena/01a084f5-oo.
- Force-push, or editing another agent's claimed paths.
- Renaming or re-signaturing anything frozen in docs/SPEC.md without asking first.
- Wall-clock time, real threads, or an unseeded RNG. Determinism is the property
  the whole test suite rests on.
- A commit that makes python -m pytest -q go red.

One slice. One commit. Then we talk about the second one.
```
