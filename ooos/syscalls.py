"""The syscall layer — the ABI every user program compiles against.

Two rules shape this module:

1. **Every syscall is synchronous.** Anything that can block (sleeping, waiting
   for a message, waiting for a child) is expressed by yielding a request from
   :mod:`ooos.api`, never by a syscall that blocks.
2. **Every syscall takes a process first.** User programs normally call
   ``kernel.syscall(name, *args)``, which supplies the current process.

Object access always goes through a capability, and the required right is derived
from the method name, so a mistake here is a loud failure rather than a
privilege escalation.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple

from .capability import Capability, Rights, RW, format_rights, parse_rights
from .errors import (
    BadArgument,
    BadSyscall,
    IsADirectory,
    NotADirectory,
    NotFound,
    SyscallError,
)
from .ipc import Endpoint
from .registry import get_program
from .vfs import Directory, File, normalize

#: Capability labels a child inherits at spawn. Everything else must be passed
#: explicitly through a message — that is the whole point of the design.
BOOTSTRAP_LABELS = frozenset({"root", "console", "mailbox"})

#: Rights required by method name; anything unlisted needs READ.
_RIGHTS_FOR_METHOD: Dict[str, Rights] = {
    "write": Rights.WRITE,
    "truncate": Rights.WRITE,
    "send": Rights.WRITE,
    "close": Rights.WRITE,
    "create_file": Rights.WRITE,
    "mkdir": Rights.WRITE,
    "unlink": Rights.WRITE,
    "spawn": Rights.EXEC,
    "exec": Rights.EXEC,
    "grant": Rights.GRANT,
    "restrict": Rights.GRANT,
    "destroy": Rights.DESTROY,
}


class Syscalls:
    """Dispatch table bound to one kernel."""

    def __init__(self, kernel: Any) -> None:
        self.kernel = kernel
        self.table: Dict[str, Callable[..., Any]] = {
            name: getattr(self, name)
            for name in dir(type(self))
            if not name.startswith("_") and name not in ("call", "names")
        }
        self.count = 0

    def call(self, proc: Any, name: str, *args: Any) -> Any:
        handler = self.table.get(name)
        if handler is None:
            raise BadSyscall(f"no such syscall: {name!r} (try: {', '.join(self.names())})")
        self.count += 1
        return handler(proc, *args)

    def names(self) -> List[str]:
        return sorted(self.table)

    # -- objects & capabilities --------------------------------------------

    def invoke(self, proc, cap_index: int, method: str, *args: Any) -> Any:
        """Invoke *method* on the object referenced by capability *cap_index*."""
        cap = proc.cap(int(cap_index))
        obj = self.kernel.objects.get(cap.oid)
        cap.require(_RIGHTS_FOR_METHOD.get(method, Rights.READ))
        return obj.invoke(method, *args)

    def caps(self, proc) -> List[str]:
        return proc.cap_table()

    def handle(self, proc, cap_index: int) -> Any:
        """Return the object behind *cap_index* (after a READ check).

        Programs need this to block on an object (``yield from recv(ep)``); it is
        a handle, not authority — the rights check already happened.
        """
        cap = proc.cap(int(cap_index))
        cap.require(Rights.READ)
        return self.kernel.objects.get(cap.oid)

    def label(self, proc, cap_index: int, label: str) -> str:
        """Name a capability. Labelled bootstrap caps are inherited by children."""
        cap = proc.cap(int(cap_index))
        proc.caps[int(cap_index)] = cap.with_label(str(label))
        return label

    def mint(self, proc, cap_index: int, spec: Optional[str] = None) -> Capability:
        """Return the capability object itself, for passing inside a message."""
        cap = proc.cap(int(cap_index))
        return cap.restrict(parse_rights(spec)) if spec else cap

    def install(self, proc, cap: Capability) -> int:
        """Install a capability received in a message into the process table."""
        if not isinstance(cap, Capability):
            raise BadArgument("install needs a capability, got {type(cap).__name__}")
        return proc.add_cap(cap)

    def restrict(self, proc, cap_index: int, spec: str) -> str:
        """Narrow a capability to the rights in *spec* (in place)."""
        cap = proc.cap(int(cap_index))
        cap.require(Rights.GRANT)
        narrowed = cap.restrict(parse_rights(spec))
        proc.caps[int(cap_index)] = narrowed
        return format_rights(narrowed.rights)

    def drop(self, proc, cap_index: int) -> str:
        return str(proc.drop_cap(int(cap_index)))

    def stat(self, proc, cap_index: int) -> dict:
        return self.invoke(proc, cap_index, "stat")

    def objects(self, proc) -> dict:
        return self.kernel.objects.stats()

    # -- filesystem ---------------------------------------------------------

    def open(self, proc, path: str) -> int:
        """Resolve *path* and return a new capability index for it."""
        node = self.kernel.resolve_path(proc, path)
        oid = self.kernel.intern(node)
        return proc.add_cap(Capability(oid, RW, node.name or path))

    def close(self, proc, cap_index: int) -> str:
        return str(proc.drop_cap(int(cap_index)))

    def ls(self, proc, path: str = ".") -> List[str]:
        node = self.kernel.resolve_path(proc, path)
        if isinstance(node, Directory):
            return node.list()
        return [node.name or path]

    def read(self, proc, cap_index: int, length: int = -1) -> bytes:
        node = self._file_for(proc, cap_index)
        return node.read(0, int(length))

    def read_path(self, proc, path: str) -> bytes:
        node = self.kernel.resolve_path(proc, path)
        if isinstance(node, Directory):
            raise IsADirectory(f"{path} is a directory")
        return node.read()

    def write(self, proc, cap_index: int, data: bytes) -> int:
        node = self._file_for(proc, cap_index)
        cap = proc.cap(int(cap_index))
        cap.require(Rights.WRITE)
        return node.write(-1, bytes(data))

    def write_path(self, proc, path: str, data: bytes = b"") -> int:
        """Truncate-and-write *path*; returns the number of bytes written."""
        payload = bytes(data)
        self.kernel.fs.write(path, payload, proc.cwd)
        return len(payload)

    def mkdir(self, proc, path: str) -> str:
        self.kernel.fs.mkdir(path, proc.cwd)
        return normalize(path, proc.cwd)

    def touch(self, proc, path: str) -> str:
        parent, name = self.kernel.fs.resolve_parent(path, proc.cwd)
        if parent.has(name):
            return normalize(path, proc.cwd)
        parent.create_file(name)
        return normalize(path, proc.cwd)

    def rm(self, proc, path: str) -> str:
        parent, name = self.kernel.fs.resolve_parent(path, proc.cwd)
        node = parent.unlink(name)
        if node.oid:
            self.kernel.objects.remove(node.oid)
        return normalize(path, proc.cwd)

    def stat_path(self, proc, path: str) -> dict:
        node = self.kernel.resolve_path(proc, path)
        return node.stat()

    def cwd(self, proc) -> str:
        return proc.cwd

    def chdir(self, proc, path: str) -> str:
        node = self.kernel.resolve_path(proc, path)
        if not isinstance(node, Directory):
            raise NotADirectory(f"{path} is not a directory")
        proc.cwd = normalize(path, proc.cwd)
        return proc.cwd

    # -- processes ----------------------------------------------------------

    def spawn(self, proc, name: str, argv: Optional[List[str]] = None) -> int:
        """Start a registered program as a child of *proc*."""
        entry = get_program(name)
        inherited = {
            idx: cap for idx, cap in proc.caps.items() if cap.label in BOOTSTRAP_LABELS
        }
        child = self.kernel.sched.create_process(
            name, entry, parent=proc, argv=list(argv or []), caps=inherited
        )
        return child.pid

    def kill(self, proc, pid: int) -> bool:
        return self.kernel.sched.kill_process(int(pid), status=1)

    def exit(self, proc, status: int = 0) -> bool:
        return self.kernel.sched.kill_process(proc.pid, status=int(status))

    def ps(self, proc) -> List[dict]:
        return self.kernel.sched.ps()

    def pid(self, proc) -> int:
        return proc.pid

    # -- ipc ----------------------------------------------------------------

    def endpoint(self, proc, name: str = "") -> int:
        """Create an IPC endpoint.

        Endpoint capabilities carry GRANT so a channel holder can delegate along
        it; tighten with ``restrict`` before handing one to code you don't trust.
        """
        ep = Endpoint(name or f"ep-{proc.pid}")
        oid = self.kernel.intern(ep)
        return proc.add_cap(Capability(oid, RW | Rights.GRANT, ep.name))

    def send(self, proc, cap_index: int, data: Any = None, caps: Tuple[Any, ...] = ()) -> int:
        """Send *data*, optionally carrying capabilities to the receiver."""
        ep = self._endpoint_for(proc, cap_index)
        cap = proc.cap(int(cap_index))
        cap.require(Rights.WRITE)
        if caps:
            cap.require(Rights.GRANT)
        sender = self.kernel.current_tid()
        return ep.send(data, tuple(caps), sender)

    def recv(self, proc, cap_index: int) -> Any:
        ep = self._endpoint_for(proc, cap_index)
        cap = proc.cap(int(cap_index))
        cap.require(Rights.READ)
        return ep.recv()

    def endpoint_stats(self, proc, cap_index: int) -> dict:
        return self._endpoint_for(proc, cap_index).stats()

    # -- memory -------------------------------------------------------------

    def alloc(self, proc, size: int, rights: str = "rw") -> int:
        space = self._space(proc)
        return space.map(int(size), parse_rights(rights), f"{proc.name}:alloc")

    def free(self, proc, vaddr: int) -> int:
        return self._space(proc).unmap(int(vaddr)) or 0

    def poke(self, proc, vaddr: int, data: bytes) -> int:
        return self._space(proc).write(int(vaddr), bytes(data))

    def peek(self, proc, vaddr: int, length: int) -> bytes:
        return self._space(proc).read(int(vaddr), int(length))

    def maps(self, proc) -> str:
        return self._space(proc).dump()

    def memory(self, proc) -> dict:
        return self.kernel.mm.stats()

    # -- misc ---------------------------------------------------------------

    def print(self, proc, text: str = "") -> int:
        """Write to the console. Requires the process to hold the console cap."""
        found = proc.cap_by_label("console")
        if found is None:
            raise SyscallError(
                f"pid {proc.pid} has no console capability — it cannot print"
            )
        _, cap = found
        cap.require(Rights.WRITE)
        console = self.kernel.objects.get(cap.oid)
        return console.write(text)

    def now(self, proc) -> int:
        return self.kernel.clock.now

    def syscalls(self, proc) -> List[str]:
        return self.names()

    def kernel_stats(self, proc) -> dict:
        return self.kernel.stats()

    # -- helpers ------------------------------------------------------------

    def _file_for(self, proc, cap_index: int) -> File:
        cap = proc.cap(int(cap_index))
        obj = self.kernel.objects.get(cap.oid)
        if not isinstance(obj, File):
            raise IsADirectory(f"capability {cap_index} is not a file")
        return obj

    def _endpoint_for(self, proc, cap_index: int) -> Endpoint:
        cap = proc.cap(int(cap_index))
        obj = self.kernel.objects.get(cap.oid)
        if not isinstance(obj, Endpoint):
            raise BadArgument(f"capability {cap_index} is not an endpoint")
        return obj

    def _space(self, proc):
        if proc.address_space is None:
            raise SyscallError(f"pid {proc.pid} has no address space")
        return proc.address_space
