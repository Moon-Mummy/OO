"""pid 1 — mount nothing, print a banner, run a shell, reap it, halt."""

from __future__ import annotations

from typing import Generator, List

from ..api import exit_thread, waitpid
from ..registry import program


@program("init")
def init_main(kernel, argv: List[str]) -> Generator[object, object, object]:
    kernel.syscall("print", "OO-OS 0.1.0 — object-oriented operating system\n")
    kernel.syscall("print", "  every resource is an object, every reference is a capability\n")
    kernel.syscall("print", "  type 'help' for commands, 'exit' to halt\n\n")

    pid = kernel.syscall("spawn", "shell", list(argv))
    result = yield from waitpid(pid)
    status = result[1] if result else 0
    kernel.syscall("print", f"\n[init] shell (pid {pid}) exited with {status}; halting\n")
    yield from exit_thread(status)
