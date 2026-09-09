# AGENTS.md — rules for AI agents working in this repo

More than one AI agent may work in this repository at the same time, on the same branch.
Follow these rules so we don't clobber each other.

## Branch rules (hard)

- Active branch: `arena/01a084f5-oo` (branched from `main` @ `46bc308`).
- Do all work on `arena/01a084f5-oo`. Do not create, switch to, or push other branches.
- Never force-push, never rebase shared history, never amend commits that are already pushed.
- `git pull --rebase origin arena/01a084f5-oo` before starting each work block and before pushing.
- Never touch or rewrite `.git`. Never delete or move the repository root.
- No secrets, tokens, or credentials in committed files.

## Coordination (hard)

- Before editing a file, **claim it** in `.ai/coordination/active.md` under your agent name.
  Unclaimed files are free game; claimed files belong to the claimer until they release them.
- Claim the narrowest path you can (a directory is fine, `*` is not).
- Prefer adding new files over rewriting files someone else owns. If you must change a
  claimed file, say so in `active.md` and wait for a reply.
- Keep commits small and atomic. Message prefix: `agent/<your-name>: <what changed>`.
- Push at natural checkpoints (end of a work block), not once at the end of a long run.
- Don't commit build output, dependencies, or large generated datasets.

## Log format

Each agent keeps a dated section in `.ai/coordination/active.md`:

    ## <agent-name> — YYYY-MM-DD
    - Claims: `path/a/**`, `path/b.py`
    - Did: one line per change
    - Next: what you intend to do
    - Blocked on / asking <other agent>: question, if any
