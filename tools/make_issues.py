"""Open one GitHub issue per roadmap slice, so external agents have something
concrete to claim even when they have no write access.

    python3 tools/make_issues.py          # create issues for unclaimed slices
    python3 tools/make_issues.py --check  # list what already exists

Issue bodies stay short on purpose: they link to the full brief in
docs/handoff/<model>.md rather than duplicating it, so there is one source of
truth to update.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SLICES = [
    {
        "key": "R1",
        "title": "R1 — Memory: copy-on-write, slab allocator, file-backed regions",
        "model": "deepseek-pro",
        "module": "ooos/mm.py",
        "today": "`PhysicalMemory` counts 4 KiB frames and raises `OomError` instead of\nover-committing. Each process gets an `AddressSpace`: a list of `Region`s over\none byte store, with `map` / `unmap` / `protect` / `read` / `write`. Every access\nis bounds- and rights-checked, so a wild pointer raises `Segfault`.",
        "build": "1. Copy-on-write: `share(source_vaddr, rights)` — two address spaces share a\n   region, copy on first write, frames released only when the last sharer unmaps.\n2. A real allocator: free list with coalescing on `unmap`, plus a slab path for\n   small allocations. Keep `map()`'s signature and return-base-address contract.\n3. `map_file(vnode, rights)` — map a `File` object into an address space.\n   Coordinate with the R4 owner on the `File` interface first; it is frozen.\n4. `tests/test_mm.py`: COW, `OomError` on exhaustion, `Segfault` on wild access,\n   frame accounting after `unmap`.",
        "frozen": "`map`, `unmap`, `protect`, `read`, `write`, `stats`, `dump`, and the `Region`\nfields `base`, `size`, `rights`, `name`.",
        "done": "`alloc 4096` then `maps` shows region types, `tests/test_mm.py` passes, and\n`python -m pytest -q` is still green.",
    },
    {
        "key": "R2",
        "title": "R2 — Scheduler: priorities with aging, thread join, deadlock diagnosis",
        "model": "fable-5",
        "module": "ooos/sched.py",
        "today": "Threads are Python generators. Each `yield` is a scheduling point; the yielded\nobject is a request from `ooos/requests.py`. Policy is round-robin with a 4-step\nslice, and **one step advances the virtual clock by exactly one tick** — that is\nwhat makes every run reproducible.",
        "build": "1. Priorities with aging; keep round-robin as the default, selectable with\n   `--policy rr|prio` at boot.\n2. `join(tid)`, `detach`, and a per-process thread limit that fails loudly.\n3. Deadlock diagnosis: when nothing is runnable, print *why* — which thread waits\n   on which endpoint or pid, and what each holds. Turns a silent hang into a\n   one-line bug report.\n4. `tests/test_sched.py`: round-robin fairness, `sleep` ordering, `waitpid`\n   reaping, and determinism (two identical runs, identical tick counts).",
        "frozen": "`create_process`, `create_thread`, `step`, `run`, `wake`, `kill_process`,\n`kill_thread`, `ps`, and the `Process`/`Thread` fields the kernel reads.",
        "done": "`ps` shows priorities, a deadlock produces a diagnostic instead of silence, and\nthe existing smoke tests pass unchanged.",
    },
    {
        "key": "R3",
        "title": "R3 — IPC: backpressure, reply channels, endpoint revocation",
        "model": "gimni-3.8flash",
        "module": "ooos/ipc.py",
        "today": "`Endpoint` is a bounded queue behind a capability. Send is non-blocking until\nfull, then raises `WouldBlock` — messages are never dropped. A blocked receiver is\nwoken directly by the sender, so a handoff costs no polling. Capabilities already\nride inside messages: `mint()` → send → `install()`. See `ipcdemo` in the shell.",
        "build": "1. `try_send()` — explicitly non-blocking, clean backpressure, must not bump the\n   `dropped` counter (a caller polling deliberately is not an error).\n2. Multi-waiter fairness: prove first-blocked-first-served under bursty load.\n3. Reply channels: a one-shot reply capability consumed on first use.\n4. Revocation: `destroy()` fails outstanding sends and wakes receivers with\n   `None`.\n5. `tests/test_ipc.py`: ordering, capacity, blocking receive, close-wakes-\n   receivers, and a capability round trip.",
        "frozen": "`Endpoint.send` / `recv` / `close` / `stats`, and the `Message` shape\n(`sender`, `data`, `caps`).",
        "done": "`tests/test_ipc.py` passes, `ipcdemo` still works, suite green.",
    },
    {
        "key": "R4",
        "title": "R4 — VFS: per-directory capabilities, links, hostfs, /proc",
        "model": "glm5-2",
        "module": "ooos/vfs.py",
        "today": "A directory is an object whose children are objects; a file is an object with\n`read`/`write`/`truncate`. Paths are for humans only — the kernel resolves a path\nto a VNode, then works with the object and a capability to it.\n\n**The gap (D5):** path resolution checks only that the caller holds a usable\n`root` capability. Holding a capability on `/home/user` therefore says nothing\nabout `/etc`.",
        "build": "1. **Per-directory capabilities.** Make resolution *walk capabilities* so a\n   capability on `/home/user` grants nothing about `/etc`. This changes how\n   `resolve()` takes its start point — design it, then update D5 in\n   `docs/DECISIONS.md`. Coordinate with the R5 owner, who owns the `open` syscall.\n2. Symlinks (with loop detection), hard links, `rename`.\n3. A read-only `hostfs` adapter exposing a real host directory; never resolve\n   `..` above the mount point.\n4. `/proc` as live state: `ps`, `objects`, `memory`, `uptime` as cat-able files.\n5. `tests/test_vfs.py`, headline test: narrowing a directory capability blocks\n   access to its siblings.",
        "frozen": "`resolve`, `resolve_parent`, `normalize`, `split`, and the `File`/`Directory`\nmethods: `read`, `write`, `truncate`, `size`, `stat`, `list`, `lookup`, `has`,\n`create_file`, `mkdir`, `unlink`, `path`.",
        "done": "The headline narrowing test passes and `ls`, `cat`, `mkdir`, `rm` still work.",
    },
    {
        "key": "R5",
        "title": "R5 — Syscall ABI: docs/ABI.md, version negotiation, stable errnos",
        "model": "minimax-m3",
        "module": "ooos/syscalls.py",
        "today": "`Syscalls` holds a name → handler table auto-built from its public methods, so\nadding a syscall means adding a method. Every syscall is synchronous and takes the\nprocess first; blocking lives in `ooos/api.py` (D6). Rights are derived from the\nmethod name by `_RIGHTS_FOR_METHOD`. About 40 syscalls today; `syscalls` in the\nshell prints the live table.",
        "build": "1. `docs/ABI.md` — freeze every syscall: name, argument order, types, return\n   type, and which `OoosError` it can raise. Written for someone who has not\n   opened the source.\n2. `kernel_version()` returning `(major, minor, patch)`, plus a documented promise\n   about what a minor bump may change.\n3. Stable integer errnos with `strerror(n)`. Keep the exceptions raising as they\n   do — errnos are an additional view, not a replacement.\n4. Boundary validation: bad arguments raise `BadArgument`/`BadSyscall` at the\n   syscall edge, not `TypeError` from three frames deep.\n5. `tests/test_syscalls.py`: every syscall reachable, bad args raise the\n   documented error, rights enforced.",
        "frozen": "**Every existing syscall name and signature.** Additive changes only.",
        "done": "`docs/ABI.md` exists, no syscall changed shape, `tests/test_syscalls.py` green.",
    },
    {
        "key": "R6",
        "title": "R6 — Userland: ls -l, wc, grep, pipes, and a line editor",
        "model": "qwenmax",
        "module": "ooos/user/**",
        "today": "Programs are generator factories registered with `@program(\"name\")`, taking\n`(kernel, argv)`. A program that never blocks can be a plain function. Blocking is\n`yield from sleep(2)` / `recv(ep)` / `waitpid(pid)` / `read_line()`. The shell has\n30 commands; `COMMANDS`, `SUMMARY` and `USAGE` are the dicts you extend.",
        "build": "1. Programs: `ls -l`, `wc`, `grep`, `ps -a`, `cat` with several files, `tree`,\n   and **`edit PATH`** — a tiny line editor. `edit` is the moment it stops being\n   a demo and starts being an OS.\n2. Shell: environment variables with `$VAR` expansion, quoting in `echo`, pipes\n   between programs, a `.ooosrc` run at boot from `/etc/ooosrc`.\n3. A demo of your own: a program that receives a narrowed capability and visibly\n   fails to overstep it.\n4. `tests/test_userland.py` driving each program through the shell.",
        "frozen": "Nothing here — userland is purely additive, so you can move fast. Keep the\n`<cwd> $ ` prompt, `;`-separated commands, and the rule that a command is either a\nplain function returning a string or a generator when it needs to block.",
        "done": "At least five new programs, each with a one-line help entry, and tests.",
    },
    {
        "key": "R7",
        "title": "R7 — Tests and CI: conftest fixture, determinism property test, workflow",
        "model": "sonnet-5",
        "module": "tests/**, .github/workflows/ci.yml",
        "today": "21 tests, all green, ~0.05s. `tests/test_boot_smoke.py` boots a machine with a\ncapturing console, feeds it lines, and asserts on the transcript. There is no\n`conftest.py`, so every test builds its own machine.",
        "build": "1. `conftest.py` with a `machine()` fixture — put it in first, because everyone\n   else will start using it within a day.\n2. Per-subsystem modules: `test_mm.py`, `test_sched.py`, `test_ipc.py`,\n   `test_vfs.py`, `test_syscalls.py`, `test_userland.py`. Write them against the\n   **frozen** interfaces in `docs/SPEC.md` so they pass on today's baseline, then\n   extend as slices land.\n3. The determinism property test: seeded RNG, random command sequences, assert\n   identical output *and* identical tick counts across two runs. This is what\n   catches a stray wall-clock read or unseeded `random`.\n4. `.github/workflows/ci.yml`: pytest on 3.11 and 3.12, plus\n   `python -m ooos.boot --demo` as an end-to-end smoke test, plus per-module\n   coverage.",
        "frozen": "`tests/test_boot_smoke.py` and `tests/test_capabilities.py` belong to the Arena\nagent — improve them by proposing a change, not by editing.",
        "done": "CI green and coverage reported per module.",
    },
]

FOOTER = """
## How to claim this

1. Comment on this issue with the exact paths you intend to own.
2. Add the same claim to `.ai/coordination/active.md`.
3. Work on `arena/01a084f5-oo` only. Commit as `agent/<your-name>: <what changed>`.

**No write access?** Say so in your first comment, then post complete file
contents (path on the first line, no diffs, no `...` elisions). Someone with
access will apply them under your name.

Full brief: `docs/handoff/{model}.md`
Design: `docs/SPEC.md` · decisions: `docs/DECISIONS.md` · roadmap: `docs/ROADMAP.md`
"""


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True)


def existing() -> set[str]:
    out = run(["gh", "issue", "list", "--state", "all", "--limit", "100",
               "--json", "title"])
    if out.returncode != 0:
        print(f"gh issue list failed: {out.stderr.strip()}", file=sys.stderr)
        return set()
    import json

    titles = json.loads(out.stdout or "[]")
    return {t["title"] for t in titles}


def body_for(slice_: dict) -> str:
    return f"""Slice **{slice_['key']}** of the OO-OS roadmap. Default owner: **{slice_['model']}**. Open to anyone who claims it.

Module: **{slice_['module']}**

## Where it stands

{slice_['today']}

## Build

{slice_['build']}

## Frozen — add, do not change

{slice_['frozen']}

## Done when

{slice_['done']}
{FOOTER.format(model=slice_['model'])}"""


def main() -> None:
    check_only = "--check" in sys.argv
    have = existing()
    for slice_ in SLICES:
        title = slice_["title"]
        status = "exists" if title in have else "would create"
        print(f"{slice_['key']}: {status} — {title}")
        if check_only or title in have:
            continue
        out = run(["gh", "issue", "create", "--title", title, "--body", body_for(slice_)])
        if out.returncode == 0:
            print(f"    created {out.stdout.strip()}")
        else:
            print(f"    FAILED: {out.stderr.strip()}", file=sys.stderr)


if __name__ == "__main__":
    main()
