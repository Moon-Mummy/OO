# Handoff brief for the second AI model

Copy everything inside the fence below and paste it to the other model as its first message.
Replace the one line marked `<<<` with the concrete task you want it to do.

---

You are working with another AI agent (me) in the same Git repository, at the same time, on the
same branch. Read this whole message before you write any code.

## 1. Repository facts

- Repo: `Moon-Mummy/OO` (GitHub; `gh` and `git` are authenticated in your sandbox).
- Active branch: `arena/01a084f5-oo`, branched from `main` @ `46bc30890bf7781e45b3c4960c209c6e5882a9b3`.
- Current state: essentially empty. One commit, one file (`README.md`, containing `# OO`).
  There is no spec, no code, no build system, no framework yet.

## 2. Read these first

- `AGENTS.md` in the repo root — branch rules and the coordination protocol. Follow it exactly.
- `.ai/coordination/active.md` — the live claim log. Read it, then add your own section.

## 3. Hard rules

- Work only on `arena/01a084f5-oo`. Never create, switch to, or push any other branch.
- Never force-push, never rebase/amend pushed history, never rewrite `main`.
- `git pull --rebase origin arena/01a084f5-oo` before you start and again before you push.
- Commit in small atomic chunks, message prefix `agent/<your-name>: <what changed>`.
- No secrets or credentials in committed files. No build output, dependencies, or big datasets.
- Claim file paths in `.ai/coordination/active.md` before editing them. Don't edit paths I
  have claimed; if you need one, ask in that file or in your reply.

## 4. Your task

<<< ONE LINE: the concrete outcome you want from this model. Default: "Draft the project
spec and proposed repo scaffold for OO (what it is, who uses it, tech stack, file layout,
first milestone). Do NOT write implementation code or run installs yet — post the plan and
wait for approval." >>>

## 5. What to send back to me (required format)

Reply with all six sections, so I can act on it without a second round trip:

1. **Assumptions** — what you assumed where the brief was unclear (list them, don't guess silently).
2. **Plan** — numbered steps, each one small enough to be a single commit.
3. **Claims** — exact file paths/directories you intend to own, formatted so I can paste them
   into `.ai/coordination/active.md`.
4. **Interface contract** — if our work touches: file paths, function/type names, config keys,
   env var names, ports, and data shapes we must both agree on. I'll mirror these exactly.
5. **Risks / collisions** — anything you see that could conflict with parallel work.
6. **Definition of done** — how we both know this slice is finished.

## 6. Working style

- Ask at most three high-value clarifying questions; then proceed with stated assumptions.
- Prefer adding new files over editing mine.
- Push at the end of each work block, not only at the very end.
- If you see my commit conflict with yours, stop, say so, and propose the merge — don't
  silently overwrite.
