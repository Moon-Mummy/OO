"""A browser terminal for OO-OS.

Runs one kernel per session on the server and pumps it one line of input at a
time. The kernel is unchanged — it just writes to a socket instead of a tty.
"""

from .server import Session, main

__all__ = ["Session", "main"]
