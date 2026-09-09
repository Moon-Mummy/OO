"""The virtual clock.

OO-OS never reads the wall clock. Time is an integer counter advanced by the
scheduler, which makes every run of the system bit-for-bit reproducible: same
program, same inputs, same tick-by-tick trace. Real time enters only at the
console, where a human types.
"""

from __future__ import annotations


class VirtualClock:
    """Monotonic tick counter. One scheduler step is one tick."""

    def __init__(self) -> None:
        self.now: int = 0
        self.ticks: int = 0

    def advance(self, n: int = 1) -> int:
        if n < 0:
            raise ValueError("time does not run backwards")
        self.now += n
        self.ticks += n
        return self.now

    def advance_to(self, when: int) -> int:
        """Jump to *when*, never backwards. Returns the new time."""
        if when > self.now:
            self.advance(when - self.now)
        return self.now

    def __repr__(self) -> str:
        return f"<clock now={self.now} ticks={self.ticks}>"
