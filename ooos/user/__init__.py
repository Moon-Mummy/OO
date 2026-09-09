"""Userland: the programs that ship with OO-OS.

Importing this package registers every program in :mod:`ooos.registry`. Userland
code never touches kernel internals — it goes through ``kernel.syscall(...)``
and the blocking helpers in :mod:`ooos.api`.
"""

from . import init, programs, shell  # noqa: F401
