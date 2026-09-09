"""Capabilities — the only way to name an object in OO-OS.

A capability is an unforgeable (oid, rights) pair held in a per-process table.
User code never sees an object id; it sees a capability *index* into its own table,
exactly like a file descriptor. There is no ambient authority: if you hold no
capability for an object, the object does not exist as far as you are concerned.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Flag, auto

from .errors import NotPermitted


class Rights(Flag):
    """What a capability holder may do with an object."""

    NONE = 0
    READ = auto()
    WRITE = auto()
    EXEC = auto()
    GRANT = auto()
    DESTROY = auto()


#: Common combinations.
RW = Rights.READ | Rights.WRITE
RWX = Rights.READ | Rights.WRITE | Rights.EXEC
ALL = Rights.READ | Rights.WRITE | Rights.EXEC | Rights.GRANT | Rights.DESTROY

_RIGHT_CHARS = {
    "r": Rights.READ,
    "w": Rights.WRITE,
    "x": Rights.EXEC,
    "g": Rights.GRANT,
    "d": Rights.DESTROY,
}


def parse_rights(spec: str) -> Rights:
    """Parse a rights string like ``"rw"``, ``"rwx"`` or ``""``.

    Unknown characters raise :class:`ValueError` — typos in a rights spec are a
    security bug, not something to silently drop.
    """
    rights = Rights.NONE
    for ch in spec.strip().lower():
        if ch in "- ":
            continue
        if ch not in _RIGHT_CHARS:
            raise ValueError(f"unknown right {ch!r} (use any of 'rwxgd')")
        rights |= _RIGHT_CHARS[ch]
    return rights


#: Canonical display order for rights.
_RIGHTS_ORDER = ("r", "w", "x", "g", "d")


def format_rights(rights: Rights) -> str:
    """Render rights as a compact string, e.g. ``"rw---"``."""
    return "".join(
        ch if _RIGHT_CHARS[ch] in rights else "-" for ch in _RIGHTS_ORDER
    )


@dataclass(frozen=True, slots=True)
class Capability:
    """A reference to a kernel object plus the rights it carries."""

    oid: int
    rights: Rights = RW
    label: str = ""

    def allows(self, required: Rights) -> bool:
        return (required & self.rights) == required

    def require(self, required: Rights) -> None:
        if not self.allows(required):
            raise NotPermitted(
                f"capability {self.label or self.oid} has "
                f"{format_rights(self.rights)}, needs {format_rights(required)}"
            )

    def restrict(self, mask: Rights) -> "Capability":
        """Return a copy carrying only the intersection with *mask*."""
        return replace(self, rights=self.rights & mask)

    def with_label(self, label: str) -> "Capability":
        return replace(self, label=label)

    def __str__(self) -> str:
        name = f"{self.label} " if self.label else ""
        return f"<cap {name}oid={self.oid} {format_rights(self.rights)}>"
