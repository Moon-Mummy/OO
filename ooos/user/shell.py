"""The OO-OS shell.

A user program like any other: it runs as a process, prints through the console
capability, and blocks with ``yield from read_line()``. Commands are plain
functions returning a string, or generator functions when they need to block.
"""

from __future__ import annotations

import shlex
from typing import Any, Callable, Dict, Generator, List, Optional

from ..api import exit_thread, read_line, recv, sleep, waitpid
from ..errors import OoosError
from ..registry import program

Command = Callable[["Shell", List[str]], Any]


class Shell:
    """One interactive shell session bound to one process."""

    def __init__(self, kernel: Any, proc: Any) -> None:
        self.k = kernel
        self.proc = proc
        self.history: List[str] = []
        self.last_status = 0

    # -- plumbing -----------------------------------------------------------

    def out(self, text: str = "") -> None:
        self.k.syscall("print", text)

    def prompt(self) -> str:
        return f"{self.proc.cwd} $ "

    def run(self) -> Generator[object, object, None]:
        """The shell's main loop — a generator, so it yields while waiting."""
        while True:
            self.out(self.prompt())
            line = yield from read_line()
            if line is None:
                break
            self.history.append(line)
            yield from self.run_line(line)
        self.out("\n")

    def run_line(self, line: str) -> Generator[object, object, None]:
        """Run a line, which may hold several ``;``-separated commands."""
        for chunk in line.split(";"):
            chunk = chunk.strip()
            if chunk:
                yield from self.run_one(chunk)

    def run_one(self, chunk: str) -> Generator[object, object, None]:
        try:
            argv = shlex.split(chunk, comments=True)
        except ValueError as exc:
            self.out(f"sh: parse error: {exc}\n")
            return
        if not argv:
            return
        name, args = argv[0], argv[1:]
        handler = COMMANDS.get(name)
        if handler is None:
            self.out(f"sh: {name}: command not found (try 'help')\n")
            self.last_status = 127
            return
        try:
            result = handler(self, args)
            if isinstance(result, Generator):
                result = yield from result
        except OoosError as exc:
            self.out(f"{name}: {exc}\n")
            self.last_status = 1
            return
        except (ValueError, IndexError, TypeError) as exc:
            self.out(f"{name}: {exc}\nusage: {USAGE.get(name, name)}\n")
            self.last_status = 2
            return
        self.last_status = 0
        if result:
            text = str(result)
            self.out(text if text.endswith("\n") else text + "\n")


# ---------------------------------------------------------------------------
# commands
# ---------------------------------------------------------------------------


def _cmd_help(sh: Shell, argv: List[str]) -> str:
    width = max(len(name) for name in COMMANDS)
    lines = ["commands:"]
    for name in sorted(COMMANDS):
        lines.append(f"  {name:<{width}}  {SUMMARY.get(name, '')}")
    lines.append("")
    lines.append("separate commands with ';' — objects are reached by capability index")
    return "\n".join(lines)


def _cmd_ls(sh: Shell, argv: List[str]) -> str:
    path = argv[0] if argv else "."
    entries = sh.k.syscall("ls", path)
    return "  ".join(entries) if entries else "(empty)"


def _cmd_cd(sh: Shell, argv: List[str]) -> str:
    sh.k.syscall("chdir", argv[0] if argv else "/")
    return ""


def _cmd_pwd(sh: Shell, argv: List[str]) -> str:
    return sh.k.syscall("cwd")


def _cmd_cat(sh: Shell, argv: List[str]) -> str:
    if not argv:
        raise ValueError("cat needs a path")
    data = sh.k.syscall("read_path", argv[0])
    return data.decode("utf-8", errors="replace").rstrip("\n")


def _cmd_echo(sh: Shell, argv: List[str]) -> str:
    return " ".join(argv)


def _cmd_write(sh: Shell, argv: List[str]) -> str:
    if len(argv) < 2:
        raise ValueError("write needs a path and text")
    written = sh.k.syscall("write_path", argv[0], " ".join(argv[1:]).encode())
    return f"wrote {written} bytes to {argv[0]}"


def _cmd_mkdir(sh: Shell, argv: List[str]) -> str:
    if not argv:
        raise ValueError("mkdir needs a path")
    sh.k.syscall("mkdir", argv[0])
    return ""


def _cmd_touch(sh: Shell, argv: List[str]) -> str:
    if not argv:
        raise ValueError("touch needs a path")
    sh.k.syscall("touch", argv[0])
    return ""


def _cmd_rm(sh: Shell, argv: List[str]) -> str:
    if not argv:
        raise ValueError("rm needs a path")
    sh.k.syscall("rm", argv[0])
    return ""


def _cmd_stat(sh: Shell, argv: List[str]) -> str:
    target = argv[0] if argv else "."
    info = sh.k.syscall("stat", int(target)) if target.isdigit() else sh.k.syscall(
        "stat_path", target
    )
    return "\n".join(f"{key:>8}: {value}" for key, value in info.items())


def _cmd_caps(sh: Shell, argv: List[str]) -> str:
    return "\n".join(sh.k.syscall("caps"))


def _cmd_objects(sh: Shell, argv: List[str]) -> str:
    info = sh.k.syscall("objects")
    lines = [f"{'objects':>10}: {info['objects']}"]
    lines += [f"{name:>10}: {count}" for name, count in info["by_type"].items()]
    return "\n".join(lines)


def _cmd_ps(sh: Shell, argv: List[str]) -> str:
    rows = sh.k.syscall("ps")
    lines = [
        f"{'PID':>4} {'NAME':<14} {'STATE':<8} {'THR':>3} {'TICKS':>6} {'CAPS':>4}  CWD"
    ]
    for row in rows:
        lines.append(
            f"{row['pid']:>4} {row['name']:<14} {row['state']:<8} "
            f"{row['threads']:>3} {row['ticks']:>6} {row['caps']:>4}  {row['cwd']}"
        )
    return "\n".join(lines)


def _cmd_kill(sh: Shell, argv: List[str]) -> str:
    if not argv:
        raise ValueError("kill needs a pid")
    pid = int(argv[0])
    ok = sh.k.syscall("kill", pid)
    return f"killed {pid}" if ok else f"no such process {pid}"


def _cmd_spawn(sh: Shell, argv: List[str]) -> Generator[object, object, str]:
    if not argv:
        raise ValueError("spawn needs a program name")
    wait = "--wait" in argv
    args = [a for a in argv[1:] if a != "--wait"]
    pid = sh.k.syscall("spawn", argv[0], args)
    if wait:
        result = yield from waitpid(pid)
        return f"pid {pid} exited with status {result[1]} at tick {sh.k.syscall('now')}"
    return f"spawned {argv[0]} as pid {pid}"


def _cmd_sleep(sh: Shell, argv: List[str]) -> Generator[object, object, str]:
    ticks = int(argv[0]) if argv else 1
    start = sh.k.syscall("now")
    yield from sleep(ticks)
    return f"slept {ticks} ticks (tick {start} -> {sh.k.syscall('now')})"


def _cmd_endpoint(sh: Shell, argv: List[str]) -> str:
    index = sh.k.syscall("endpoint", argv[0] if argv else "")
    return f"endpoint created at cap {index}"


def _cmd_send(sh: Shell, argv: List[str]) -> str:
    if len(argv) < 2:
        raise ValueError("send needs a cap index and a payload")
    depth = sh.k.syscall("send", int(argv[0]), " ".join(argv[1:]))
    return f"sent (queue depth {depth})"


def _cmd_recv(sh: Shell, argv: List[str]) -> Generator[object, object, str]:
    if not argv:
        raise ValueError("recv needs a cap index")
    index = int(argv[0])
    endpoint = sh.k.syscall("handle", index)
    message = yield from recv(endpoint)
    if message is None:
        return "endpoint closed"
    return str(message)


def _cmd_ipcdemo(sh: Shell, argv: List[str]) -> Generator[object, object, str]:
    pid = sh.k.syscall("spawn", "ipcdemo")
    result = yield from waitpid(pid)
    return f"ipcdemo (pid {pid}) exited with {result[1]}"


def _cmd_alloc(sh: Shell, argv: List[str]) -> str:
    size = int(argv[0]) if argv else 4096
    rights = argv[1] if len(argv) > 1 else "rw"
    vaddr = sh.k.syscall("alloc", size, rights)
    return f"mapped {size} bytes at 0x{vaddr:08x}"


def _cmd_free(sh: Shell, argv: List[str]) -> str:
    sh.k.syscall("free", int(argv[0], 0))
    return f"unmapped 0x{int(argv[0], 0):08x}"


def _cmd_poke(sh: Shell, argv: List[str]) -> str:
    if len(argv) < 2:
        raise ValueError("poke needs an address and data")
    written = sh.k.syscall("poke", int(argv[0], 0), " ".join(argv[1:]).encode())
    return f"wrote {written} bytes"


def _cmd_peek(sh: Shell, argv: List[str]) -> str:
    if len(argv) < 2:
        raise ValueError("peek needs an address and a length")
    data = sh.k.syscall("peek", int(argv[0], 0), int(argv[1]))
    return f"{data!r}"


def _cmd_maps(sh: Shell, argv: List[str]) -> str:
    return "memory maps:\n" + sh.k.syscall("maps")


def _cmd_memory(sh: Shell, argv: List[str]) -> str:
    info = sh.k.syscall("memory")
    return "\n".join(f"{key:>14}: {value}" for key, value in info.items())


def _cmd_syscalls(sh: Shell, argv: List[str]) -> str:
    return "  ".join(sh.k.syscall("syscalls"))


def _cmd_uptime(sh: Shell, argv: List[str]) -> str:
    stats = sh.k.syscall("kernel_stats")
    return "\n".join(f"{key:>14}: {value}" for key, value in stats.items())


def _cmd_exit(sh: Shell, argv: List[str]) -> Generator[object, object, None]:
    status = int(argv[0]) if argv else 0
    yield from exit_thread(status)


COMMANDS: Dict[str, Command] = {
    "help": _cmd_help,
    "ls": _cmd_ls,
    "cd": _cmd_cd,
    "pwd": _cmd_pwd,
    "cat": _cmd_cat,
    "echo": _cmd_echo,
    "write": _cmd_write,
    "mkdir": _cmd_mkdir,
    "touch": _cmd_touch,
    "rm": _cmd_rm,
    "stat": _cmd_stat,
    "caps": _cmd_caps,
    "objects": _cmd_objects,
    "ps": _cmd_ps,
    "kill": _cmd_kill,
    "spawn": _cmd_spawn,
    "sleep": _cmd_sleep,
    "endpoint": _cmd_endpoint,
    "send": _cmd_send,
    "recv": _cmd_recv,
    "ipcdemo": _cmd_ipcdemo,
    "alloc": _cmd_alloc,
    "free": _cmd_free,
    "poke": _cmd_poke,
    "peek": _cmd_peek,
    "maps": _cmd_maps,
    "memory": _cmd_memory,
    "syscalls": _cmd_syscalls,
    "uptime": _cmd_uptime,
    "exit": _cmd_exit,
}

SUMMARY: Dict[str, str] = {
    "help": "list commands",
    "ls": "list a directory",
    "cd": "change directory",
    "pwd": "print working directory",
    "cat": "print a file",
    "echo": "print arguments",
    "write": "write text to a file",
    "mkdir": "create a directory",
    "touch": "create an empty file",
    "rm": "remove a file",
    "stat": "show an object's metadata",
    "caps": "list this process's capabilities",
    "objects": "kernel object table summary",
    "ps": "process table",
    "kill": "kill a process",
    "spawn": "start a program [--wait]",
    "sleep": "sleep N virtual ticks",
    "endpoint": "create an IPC endpoint",
    "send": "send a message to a capability",
    "recv": "blocking receive from a capability",
    "ipcdemo": "run the capability-passing demo",
    "alloc": "allocate memory [size] [rights]",
    "free": "unmap a region",
    "poke": "write bytes at an address",
    "peek": "read bytes at an address",
    "maps": "show this process's memory map",
    "memory": "physical memory statistics",
    "syscalls": "list the syscall table",
    "uptime": "kernel statistics",
    "exit": "halt the machine",
}

USAGE: Dict[str, str] = {
    "cat": "cat PATH",
    "write": "write PATH TEXT...",
    "mkdir": "mkdir PATH",
    "touch": "touch PATH",
    "rm": "rm PATH",
    "cd": "cd PATH",
    "stat": "stat PATH|CAP",
    "kill": "kill PID",
    "spawn": "spawn PROGRAM [ARGS...] [--wait]",
    "sleep": "sleep TICKS",
    "send": "send CAP TEXT...",
    "recv": "recv CAP",
    "alloc": "alloc [BYTES] [RIGHTS]",
    "free": "free ADDRESS",
    "poke": "poke ADDRESS TEXT...",
    "peek": "peek ADDRESS LENGTH",
    "exit": "exit [STATUS]",
}


@program("shell")
def shell_main(kernel, argv: List[str]) -> Generator[object, object, object]:
    """shell — the interactive command interpreter (pid 1 spawns this)."""
    shell = Shell(kernel, kernel.current_process())
    if argv:
        yield from shell.run_line("; ".join(argv))
    yield from shell.run()
