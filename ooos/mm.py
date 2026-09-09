"""Memory management.

A paged allocator over a simulated physical store. Address spaces are per-process
and every access is bounds- and rights-checked, so a wild pointer raises
:class:`~ooos.errors.Segfault` instead of corrupting the heap.

This is the *reference* allocator: flat, page-accounted, deterministic. It is
deliberately simple so that copy-on-write, swapping and slab allocation can be
layered on by whoever owns this module without touching its interface.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from .capability import Rights, RW, format_rights
from .errors import OomError, Segfault

PAGE_SIZE = 4096
DEFAULT_PHYSICAL_FRAMES = 4096  # 16 MiB of simulated RAM


def pages_for(size: int) -> int:
    return (max(0, size) + PAGE_SIZE - 1) // PAGE_SIZE


@dataclass(slots=True)
class Region:
    """A contiguous mapped range inside an address space."""

    base: int
    size: int
    rights: Rights = RW
    name: str = "anon"

    @property
    def end(self) -> int:
        return self.base + self.size

    @property
    def pages(self) -> int:
        return pages_for(self.size)

    def contains(self, vaddr: int, length: int = 1) -> bool:
        return self.base <= vaddr and vaddr + length <= self.end

    def __str__(self) -> str:
        return (
            f"0x{self.base:08x}-0x{self.end:08x} {format_rights(self.rights)} "
            f"{self.pages}p {self.name}"
        )


class PhysicalMemory:
    """Frame accounting for the machine. No real bytes live here."""

    def __init__(self, frames: int = DEFAULT_PHYSICAL_FRAMES) -> None:
        self.total = frames
        self.used = 0
        self.peak = 0
        self.allocations = 0
        self.failures = 0

    @property
    def free(self) -> int:
        return self.total - self.used

    def alloc(self, pages: int) -> None:
        if pages <= 0:
            return
        if pages > self.free:
            self.failures += 1
            raise OomError(
                f"out of memory: need {pages} frames, {self.free} free "
                f"({self.total} total)"
            )
        self.used += pages
        self.peak = max(self.peak, self.used)
        self.allocations += 1

    def release(self, pages: int) -> None:
        self.used = max(0, self.used - pages)

    def stats(self) -> Dict[str, int]:
        return {
            "total_frames": self.total,
            "used_frames": self.used,
            "free_frames": self.free,
            "peak_frames": self.peak,
            "allocations": self.allocations,
            "failures": self.failures,
        }


class AddressSpace:
    """One process's view of memory: a list of regions over one byte store."""

    def __init__(self, mm: "MemoryManager", owner: str = "") -> None:
        self.mm = mm
        self.owner = owner
        self.regions: List[Region] = []
        self.bytes = bytearray()
        self._brk = 0

    # -- mapping -----------------------------------------------------------

    def map(self, size: int, rights: Rights = RW, name: str = "anon") -> int:
        """Map *size* bytes; return the base virtual address."""
        if size <= 0:
            raise ValueError("size must be positive")
        self.mm.physical.alloc(pages_for(size))
        base = self._brk
        self.regions.append(Region(base, size, rights, name))
        self._brk += size
        self.bytes.extend(b"\x00" * size)
        return base

    def unmap(self, vaddr: int) -> None:
        """Unmap the region starting at *vaddr* and return its frames."""
        region = self.region_at(vaddr)
        if region is None:
            raise Segfault(f"0x{vaddr:08x} is not mapped")
        self.mm.physical.release(region.pages)
        self.regions.remove(region)
        self.bytes[region.base : region.end] = b"\x00" * region.size

    def region_at(self, vaddr: int) -> Region | None:
        for region in self.regions:
            if region.contains(vaddr, 1):
                return region
        return None

    def protect(self, vaddr: int, rights: Rights) -> None:
        region = self.region_at(vaddr)
        if region is None:
            raise Segfault(f"0x{vaddr:08x} is not mapped")
        region.rights = rights

    # -- access ------------------------------------------------------------

    def _check(self, vaddr: int, length: int, rights: Rights) -> Region:
        if vaddr < 0 or length < 0:
            raise Segfault(f"negative access at 0x{vaddr:08x} len={length}")
        region = self.region_at(vaddr)
        if region is None:
            raise Segfault(f"unmapped address 0x{vaddr:08x}")
        if not region.contains(vaddr, length):
            raise Segfault(
                f"access 0x{vaddr:08x}+{length} crosses region {region}"
            )
        if not (rights & region.rights) == rights:
            raise Segfault(
                f"0x{vaddr:08x} needs {format_rights(rights)}, "
                f"region is {format_rights(region.rights)}"
            )
        return region

    def read(self, vaddr: int, length: int) -> bytes:
        self._check(vaddr, length, Rights.READ)
        return bytes(self.bytes[vaddr : vaddr + length])

    def write(self, vaddr: int, data: bytes) -> int:
        self._check(vaddr, len(data), Rights.WRITE)
        self.bytes[vaddr : vaddr + len(data)] = data
        return len(data)

    # -- introspection -----------------------------------------------------

    @property
    def mapped_bytes(self) -> int:
        return sum(r.size for r in self.regions)

    @property
    def mapped_pages(self) -> int:
        return sum(r.pages for r in self.regions)

    def stats(self) -> Dict[str, object]:
        return {
            "owner": self.owner,
            "regions": len(self.regions),
            "mapped_bytes": self.mapped_bytes,
            "mapped_pages": self.mapped_pages,
        }

    def dump(self) -> str:
        if not self.regions:
            return "  (empty)"
        return "\n".join(f"  {r}" for r in self.regions)


class MemoryManager:
    """Owns physical memory and every address space in the system."""

    def __init__(self, frames: int = DEFAULT_PHYSICAL_FRAMES) -> None:
        self.physical = PhysicalMemory(frames)
        self.spaces: Dict[str, AddressSpace] = {}

    def create_space(self, owner: str) -> AddressSpace:
        space = AddressSpace(self, owner)
        self.spaces[owner] = space
        return space

    def destroy_space(self, owner: str) -> None:
        space = self.spaces.pop(owner, None)
        if space is not None:
            self.physical.release(space.mapped_pages)
            space.regions.clear()

    def stats(self) -> Dict[str, object]:
        phys = self.physical.stats()
        phys["address_spaces"] = len(self.spaces)
        return phys
