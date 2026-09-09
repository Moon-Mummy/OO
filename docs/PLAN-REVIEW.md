# Plan review — 7 model proposals for OO

Purpose: turn seven independent model proposals into one spec we can actually build.

**Status: waiting on contents.** The seven files (`deepseek-pro.md`, `fable-5.md`,
`gimni-3.8flash.md`, `glm5-2.md`, `minimax-m3.md`, `qwenmax.md`, `sonnet-5.md`) were attached
in chat but are not readable from the agent sandbox. They need to be pasted into chat (or
committed into `docs/proposals/`) before this review can be filled in.

## Where they go

Once available, each proposal is stored verbatim at:

    docs/proposals/<model>.md

Nothing gets rewritten or paraphrased before scoring — the raw text is the record.

## Scoring rubric

Each proposal scores 0–3 per axis. No axis is weighted twice.

| Axis | 0 | 3 |
|---|---|---|
| **Clarity** | Vague, buzzwords, no concrete artefacts | Names files, types, commands |
| **Scope discipline** | Wants to build everything | A first milestone shippable in a day |
| **Testability** | No way to tell if it works | Explicit acceptance criteria / tests |
| **Parallel-safety** | Everything in one shared file | Clean file boundaries split across agents |
| **Stack fit** | Exotic deps, heavy toolchain | Boring, installable, matches the chosen stack |
| **Originality** | Generic boilerplate | Does something the other six missed |

## Comparison table

| Model | Stack | First milestone | Clarity | Scope | Test | Parallel | Fit | Original | Total /18 |
|---|---|---|---|---|---|---|---|---|---|
| deepseek-pro | | | | | | | | | |
| fable-5 | | | | | | | | | |
| gimni-3.8flash | | | | | | | | | |
| glm5-2 | | | | | | | | | |
| minimax-m3 | | | | | | | | | |
| qwenmax | | | | | | | | | |
| sonnet-5 | | | | | | | | | |

## Merge rules

1. **Convergence wins.** If ≥4 of 7 propose the same thing, it goes in the spec without debate.
2. **Take the best part, not the whole plan.** Merge per-section, not per-model. Credit each
   section to its source model in the merged spec.
3. **Contradictions get logged, not averaged.** A disagreement (e.g. class-based vs
   prototype-based object model) becomes an explicit decision record with the vote split.
4. **Uniqueness gets a look.** Anything only one model proposed is either the best idea in the
   set or a bad one — argue it explicitly rather than dropping it.

## Output

The merge produces:

- `docs/SPEC.md` — the single spec we build from (with per-section attribution).
- `docs/DECISIONS.md` — every contradiction, the options, and the ruling.
- `.ai/coordination/active.md` — claim map derived from the spec's file layout.
