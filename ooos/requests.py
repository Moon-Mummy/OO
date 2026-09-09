"""Requests a thread yields to the scheduler.

User programs are Python generators. Each ``yield`` hands the scheduler a request
object describing why the thread stopped. The scheduler is the only thing that
interprets these; nothing here knows about the scheduler, so there are no
import cycles.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class YieldCPU:
    """Give up the remainder of the current time slice."""


@dataclass(frozen=True, slots=True)
class Sleep:
    """Block until the virtual clock passes ``now + ticks``."""

    ticks: int = 1


@dataclass(frozen=True, slots=True)
class Recv:
    """Block until a message lands on ``endpoint``."""

    endpoint: Any = None


@dataclass(frozen=True, slots=True)
class WaitPid:
    """Block until a child process exits. ``pid=-1`` means any child."""

    pid: int = -1


@dataclass(frozen=True, slots=True)
class ReadLine:
    """Block until a line of console input is available (or EOF)."""


@dataclass(frozen=True, slots=True)
class ExitThread:
    """Terminate this thread with ``status``."""

    status: int = 0
