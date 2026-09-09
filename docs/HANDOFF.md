# Handoff — ready-to-send briefs

**One file per model. Open it, copy it, paste it into that model's chat. Don't
assemble anything** — each file is self-contained: what OO-OS is, how to run it,
the branch rules, that model's slice, its claim block, and the reply format.

| Model | Slice | File |
|---|---|---|
| deepseek-pro | R1 — memory management (COW, slabs, file-backed regions) | [`handoff/deepseek-pro.md`](handoff/deepseek-pro.md) |
| fable-5 | R2 — scheduling (priorities, join, deadlock diagnosis) | [`handoff/fable-5.md`](handoff/fable-5.md) |
| gimni-3.8flash | R3 — IPC (backpressure, reply channels, revocation) | [`handoff/gimni-3.8flash.md`](handoff/gimni-3.8flash.md) |
| glm5-2 | R4 — VFS (per-directory capabilities, links, hostfs, `/proc`) | [`handoff/glm5-2.md`](handoff/glm5-2.md) |
| minimax-m3 | R5 — syscall ABI (versioning, errnos, `docs/ABI.md`) | [`handoff/minimax-m3.md`](handoff/minimax-m3.md) |
| qwenmax | R6 — userland (`ls -l`, `grep`, pipes, `edit`) | [`handoff/qwenmax.md`](handoff/qwenmax.md) |
| sonnet-5 | R7 — tests and CI (fixtures, determinism property test, workflow) | [`handoff/sonnet-5.md`](handoff/sonnet-5.md) |

Send them in any order, all at once, or one at a time. The slices are disjoint by
construction: no two models are told to edit the same file, so they cannot collide
even if they all start immediately.

## If you only send one

Send [`handoff/glm5-2.md`](handoff/glm5-2.md) — per-directory capabilities (D5) is
the biggest gap in the security model right now.

## What each brief asks the model to send back

All seven end with the same six-section reply request, so their answers are
comparable: **assumptions**, **plan**, **claims**, **interface delta**, **risks**,
**definition of done**. When a reply comes back, paste it into
`.ai/coordination/active.md` under that model's section.

## Regenerating the briefs

The seven files share a preamble (repo facts, branch rules, house style) that is
generated from one source so the copies cannot drift:

```bash
python3 tools/make_handoff.py
```

Edit the shared text or a model's slice in `tools/make_handoff.py`, re-run, commit.
The generator stamps in the current commit hash and test count, so a brief always
tells a model which tip to pull.

## Rules every brief states

- Work only on `arena/01a084f5-oo`; never force-push; pull --rebase before starting
  and before pushing.
- Commit as `agent/<model>: <what changed>`.
- Claim paths in `.ai/coordination/active.md` before editing them.
- Interfaces in `docs/SPEC.md` are frozen — additive changes only, breaking changes
  get proposed first.
- Tests must stay green; every change ships with tests.
- Determinism is a feature: no wall clock, no real threads, no unseeded RNG.
