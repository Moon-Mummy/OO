# OUTPUT-FORMAT.md — the anti-prose protocol

Two models in a row answered a work request with a *description of the repo*.
Neither produced a file, a commit, or a claim. That is not stubbornness — it is
what a language model does when the request is open-ended and the reward for
"helpful summary" outweighs the reward for "shipped change".

So stop asking for work. **Ask a question that cannot be answered with prose.**

---

```
Stop. I need one word before anything else.

Do you have write access to the GitHub repository Moon-Mummy/OO — that is, can you
run `git push` and have it land?

Answer with exactly one word: YES or NO.

Do not explain. Do not summarise the repo. Do not describe what you would do.
One word.

--- if YES ---

  git clone https://github.com/Moon-Mummy/OO && cd OO
  git checkout arena/01a084f5-oo && git pull --rebase
  # pick ONE of these and do the first step only:
  #   R1 ooos/mm.py        R2 ooos/sched.py   R3 ooos/ipc.py
  #   R4 ooos/vfs.py       R5 ooos/syscalls.py
  #   R6 ooos/user/**      R7 tests/** + CI
  # issues: github.com/Moon-Mummy/OO/issues
  git commit -m "agent/<your-name>: <what changed>"
  git push origin arena/01a084f5-oo

Then reply with ONE line: the commit hash. Nothing else.

--- if NO ---

Reply with exactly one fenced code block containing one complete file you want
added to OO-OS. Format:

```
# ooos/user/example.py
<complete contents — no "...", no "rest unchanged", no elisions>
```

Rules for that block:
- It must be complete and runnable as-is.
- No prose before it. No prose after it. No bullet points explaining it.
- If it needs a test, that is a second block in your next message, not this one.

--- if you can do neither ---

Reply with exactly one word: BLOCKED.
```

---

## Why this works

| Ask | What you get back |
|---|---|
| "Help build this OS" | An essay about operating systems |
| "Here is my progress" | A summary of *your* progress, restated |
| "Pick a slice and ship it" | A plan, then a summary of the plan |
| **"YES or NO"** | One word, and then the only path left is to act |

The pattern: every previous prompt allowed an English sentence as a valid answer,
and English is the cheapest thing a model can produce. This one makes prose an
invalid response — which is uncomfortable for the model, and that discomfort is
the point.

## If they do send a file

Apply it, run the suite, and push under their agent name:

```bash
# paste the file in, then:
python -m pytest -q
git add -A
git commit -m "agent/<model>: <what changed>"
git push origin arena/01a084f5-oo
```

Then close the matching issue (R1–R7) with the commit hash.

## If they say BLOCKED

They are chat-only. Stop asking them to build. Use them for what chat-only models
are actually good at — reviewing a design, finding a bug in a specific function,
or drafting the text of `docs/ABI.md` — and let someone with access apply it.

## The seven issues

Every slice now has a home on GitHub: `github.com/Moon-Mummy/OO/issues`. A model
with no access can still comment on an issue, and a human contributor can pick one
up without reading a single doc in this repo.
