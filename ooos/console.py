"""The console — a kernel object, like everything else.

It carries the line buffer for input and fans output out to a writer (stdout by
default, or a list-capturing sink in tests). Input arrives either from a script
(``feed``) or from a human at the keyboard; the scheduler parks threads on
``waiters`` until a line shows up.
"""

from __future__ import annotations

from collections import deque
from typing import Any, Callable, Deque, List

from .objects import KernelObject

#: Returned by :meth:`Console.get` when no line is buffered and input is still open.
NO_LINE = object()
#: Returned by :meth:`Console.get` once input is closed and the buffer is empty.
EOF = object()


class Console(KernelObject):
    """Character device backing the system terminal."""

    interface = "console"
    _NO_LINE = "NO_LINE"
    _EOF = "EOF"

    def __init__(self, writer: Callable[[str], None] | None = None) -> None:
        super().__init__("console")
        self.writer = writer or self._default_writer
        self._lines: Deque[str] = deque()
        self._eof = False
        self.waiters: List[int] = []
        self.history: List[str] = []
        self.bytes_written = 0
        self.lines_read = 0

    # -- kernel-object interface ------------------------------------------

    def write(self, text: str = "") -> int:
        """Write *text* to the terminal. Returns the number of characters."""
        text = str(text)
        self.bytes_written += len(text)
        self.writer(text)
        return len(text)

    def readline(self) -> str:
        """Non-blocking read. Returns ``""`` when nothing is available."""
        line = self.get()
        return line if isinstance(line, str) else ""

    def stats(self) -> dict:
        return {
            "buffered": len(self._lines),
            "eof": self._eof,
            "waiters": len(self.waiters),
            "bytes_written": self.bytes_written,
            "lines_read": self.lines_read,
        }

    # -- plumbing (used by the scheduler and by boot) ----------------------

    def feed(self, lines) -> None:
        """Queue scripted input lines."""
        for line in lines:
            self.push(line)

    def push(self, line: str) -> None:
        """Queue one input line and wake a thread blocked on :class:`ReadLine`."""
        self._lines.append(line.rstrip("\n"))
        self._wake_one()

    def close(self) -> None:
        """Signal end of input and release every waiter."""
        self._eof = True
        self._wake_one()

    def get(self) -> Any:
        """Pop a buffered line, or return ``NO_LINE`` / ``EOF``."""
        if self._lines:
            self.lines_read += 1
            line = self._lines.popleft()
            self.history.append(line)
            return line
        return EOF if self._eof else NO_LINE

    def has_pending(self) -> bool:
        return bool(self._lines)

    @property
    def eof(self) -> bool:
        return self._eof

    # -- internals ---------------------------------------------------------

    def _wake_one(self) -> None:
        if self.waiters and self.kernel is not None:
            tid = self.waiters.pop(0)
            line = self.get()
            self.kernel.sched.wake(tid, line)

    @staticmethod
    def _default_writer(text: str) -> None:
        import sys

        sys.stdout.write(text)
        sys.stdout.flush()
