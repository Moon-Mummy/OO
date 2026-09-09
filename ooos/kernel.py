"""The kernel object that wires everything together.

A kernel is cheap to build and fully self-contained: ``Kernel().boot()`` gives you
a machine with a filesystem, a console, an init process and a shell, with no
global state anywhere.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .capability import ALL, Capability, Rights, RW
from .clock import VirtualClock
from .console import Console
from .errors import BadCapability, KernelPanic
from .mm import DEFAULT_PHYSICAL_FRAMES, MemoryManager
from .objects import KernelObject, ObjectTable
from .sched import Scheduler
from .syscalls import Syscalls
from .vfs import MemFS, VNode

BANNER = (
    "OO-OS 0.1.0 — object-oriented operating system\n"
    "  every resource is an object, every reference is a capability\n"
)


class Kernel:
    """One machine. Owns the clock, memory, objects, processes and syscalls."""

    def __init__(
        self,
        console: Optional[Console] = None,
        frames: int = DEFAULT_PHYSICAL_FRAMES,
        slice_size: int = 4,
    ) -> None:
        self.clock = VirtualClock()
        self.console = console or Console()
        self.mm = MemoryManager(frames)
        self.objects = ObjectTable(self)
        self.sched = Scheduler(self, slice_size=slice_size)
        self.syscalls = Syscalls(self)
        self.fs: Optional[MemFS] = None
        self.booted = False
        self.panicked: Optional[str] = None
        self.trace: List[str] = []

    # -- boot ---------------------------------------------------------------

    def boot(self, entry: str = "init", argv: Optional[List[str]] = None) -> Any:
        """Build the machine and start *entry* as pid 1."""
        from . import user  # imports the program registry entries

        self.fs = MemFS()
        self.console.bind(self)
        root_oid = self.objects.add(self.fs.root)
        console_oid = self.objects.add(self.console)

        from .registry import get_program

        caps = {
            0: Capability(root_oid, ALL, "root"),
            1: Capability(console_oid, RW, "console"),
        }
        proc = self.sched.create_process(
            "init", get_program(entry), argv=list(argv or []), caps=caps
        )
        proc.cwd = "/"
        self.booted = True
        return proc

    # -- runtime ------------------------------------------------------------

    def run(self, max_steps: int = 1_000_000) -> int:
        if not self.booted:
            raise KernelPanic("kernel.run() called before boot()")
        return self.sched.run(max_steps=max_steps)

    def syscall(self, name: str, *args: Any) -> Any:
        """Issue a syscall on behalf of the currently running process."""
        proc = self.current_process()
        if proc is None:
            raise KernelPanic(f"syscall {name!r} with no current process")
        return self.syscalls.call(proc, name, *args)

    def current_process(self):
        return self.sched.current_process()

    def current_tid(self) -> int:
        thread = self.sched.current
        return thread.tid if thread is not None else 0

    def intern(self, obj: KernelObject) -> int:
        """Ensure *obj* is in the object table; return its oid."""
        if obj.oid and obj in self.objects:
            return obj.oid
        return self.objects.add(obj)

    def resolve_path(self, proc: Any, path: str) -> VNode:
        """Resolve *path* for *proc*, checking the process holds a root capability."""
        if self.fs is None:
            raise KernelPanic("filesystem not mounted")
        cap = proc.caps.get(0)
        if cap is None:
            raise BadCapability(f"pid {proc.pid} has no root capability")
        cap.require(Rights.READ)
        return self.fs.resolve(path, proc.cwd)

    def panic(self, message: str) -> None:
        """Halt the machine with a message."""
        self.panicked = message
        self.console.write(f"\n[kernel] PANIC: {message}\n")
        raise KernelPanic(message)

    # -- introspection ------------------------------------------------------

    def stats(self) -> Dict[str, Any]:
        stats: Dict[str, Any] = {
            "version": "0.1.0",
            "ticks": self.clock.now,
            "panicked": self.panicked,
        }
        stats.update(self.sched.stats())
        stats.update(self.objects.stats())
        stats.update(self.mm.stats())
        stats["syscalls"] = self.syscalls.count
        return stats

    def describe(self) -> str:
        return f"<OO-OS kernel ticks={self.clock.now} {self.objects.stats()}>"
