"""The in-thread API — what a user program ``yield from``s.

These are generator functions, so they compose: a program calls
``yield from sleep(5)`` and the request propagates up to the scheduler, which
resumes the generator later with the result.

    def main(kernel, argv):
        for i in range(3):
            kernel.print(f"tick {i}")
            yield from sleep(2)
"""

from __future__ import annotations

from typing import Any, Generator

from .requests import ExitThread, ReadLine, Recv, Sleep, WaitPid, YieldCPU

Request = Any


def yield_cpu() -> Generator[Request, None, None]:
    """Cooperatively give up the rest of the time slice."""
    yield YieldCPU()


def sleep(ticks: int = 1) -> Generator[Request, None, None]:
    """Block for *ticks* virtual ticks."""
    ticks = int(ticks)
    if ticks > 0:
        yield Sleep(ticks)


def recv(endpoint: Any) -> Generator[Request, None, Any]:
    """Block until a message arrives; return the :class:`~ooos.ipc.Message`."""
    return (yield Recv(endpoint))


def waitpid(pid: int = -1) -> Generator[Request, None, Any]:
    """Block until child *pid* (or any child) exits. Returns ``(pid, status)``."""
    return (yield WaitPid(pid))


def read_line() -> Generator[Request, None, str]:
    """Block until the console yields a line of input."""
    return (yield ReadLine())


def exit_thread(status: int = 0) -> Generator[Request, None, None]:
    """Terminate the calling thread."""
    yield ExitThread(int(status))
