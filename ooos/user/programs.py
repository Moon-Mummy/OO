"""Sample user programs.

Each one is a generator factory ``(kernel, argv) -> generator``. That is the
entire program ABI: syscalls are synchronous, blocking is ``yield from``.
"""

from __future__ import annotations

from typing import Generator, List

from ..api import recv, sleep, waitpid
from ..registry import program


@program("hello")
def hello(kernel, argv: List[str]) -> Generator[object, object, object]:
    """hello [name] — the obligatory first program."""
    name = argv[0] if argv else "world"
    kernel.syscall("print", f"hello, {name} (from pid {kernel.current_process().pid})\n")


@program("echo")
def echo(kernel, argv: List[str]) -> Generator[object, object, object]:
    """echo ARGS... — print the arguments."""
    kernel.syscall("print", " ".join(argv) + "\n")


@program("counter")
def counter(kernel, argv: List[str]) -> Generator[object, object, object]:
    """counter [n] — print a tick-stamped count, yielding the CPU between beats."""
    count = int(argv[0]) if argv else 3
    pid = kernel.current_process().pid
    for i in range(count):
        now = kernel.syscall("now")
        kernel.syscall("print", f"[counter pid={pid}] {i} @ tick {now}\n")
        yield from sleep(2)
    kernel.syscall("print", f"[counter pid={pid}] done\n")


@program("talker")
def talker(kernel, argv: List[str]) -> Generator[object, object, object]:
    """talker — hand this process's endpoint to the parent over the mailbox.

    Demonstrates capability passing: the parent learns about this process's
    endpoint only because we chose to send it.
    """
    proc = kernel.current_process()
    found = proc.cap_by_label("mailbox")
    if found is None:
        kernel.syscall("print", "[talker] no mailbox capability — nothing to do\n")
        return
    mailbox_index, _ = found

    own_index = kernel.syscall("endpoint", "talker")
    own_cap = kernel.syscall("mint", own_index)
    kernel.syscall("send", mailbox_index, f"hello from {proc.name} (pid {proc.pid})", (own_cap,))

    endpoint = kernel.syscall("handle", own_index)
    message = yield from recv(endpoint)
    kernel.syscall("print", f"[talker] received {message.data!r}\n")
    kernel.syscall("print", "[talker] bye\n")


@program("ipcdemo")
def ipcdemo(kernel, argv: List[str]) -> Generator[object, object, object]:
    """ipcdemo — spawn a child, receive a capability from it, talk to it."""
    mailbox_index = kernel.syscall("endpoint", "mailbox")
    kernel.syscall("label", mailbox_index, "mailbox")
    mailbox = kernel.syscall("handle", mailbox_index)

    pid = kernel.syscall("spawn", "talker")
    kernel.syscall("print", f"[ipcdemo] spawned talker pid={pid}, waiting for a capability\n")

    message = yield from recv(mailbox)
    kernel.syscall("print", f"[ipcdemo] {message}\n")
    if not message.caps:
        kernel.syscall("print", "[ipcdemo] no capability arrived — aborting\n")
        return

    talker_index = kernel.syscall("install", message.caps[0])
    kernel.syscall("print", f"[ipcdemo] installed talker endpoint at cap {talker_index}\n")
    depth = kernel.syscall("send", talker_index, "ping from ipcdemo")
    kernel.syscall("print", f"[ipcdemo] sent ping (queue depth {depth})\n")

    result = yield from waitpid(pid)
    kernel.syscall("print", f"[ipcdemo] talker exited with {result[1]}\n")
