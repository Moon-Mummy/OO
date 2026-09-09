"""User program registry.

Programs are generator factories with the signature::

    def prog(kernel, argv) -> Generator[Request, None, None]

They are looked up by name at ``spawn`` time, so adding a program is a matter of
importing the module — no kernel change.
"""

from __future__ import annotations

from typing import Callable, Dict, Generator, List

Program = Callable[[object, List[str]], Generator[object, object, object]]

PROGRAMS: Dict[str, Program] = {}


def program(name: str) -> Callable[[Program], Program]:
    """Register a generator factory as a spawnable user program."""

    def decorator(fn: Program) -> Program:
        if name in PROGRAMS:
            raise ValueError(f"program {name!r} is already registered")
        PROGRAMS[name] = fn
        fn.__program_name__ = name  # type: ignore[attr-defined]
        return fn

    return decorator


def register(name: str, fn: Program) -> None:
    PROGRAMS[name] = fn


def get_program(name: str) -> Program:
    try:
        return PROGRAMS[name]
    except KeyError:
        from .errors import SyscallError

        raise SyscallError(f"no such program: {name!r}") from None


def available() -> List[str]:
    return sorted(PROGRAMS)
