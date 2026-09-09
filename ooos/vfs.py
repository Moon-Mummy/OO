"""The virtual filesystem.

The filesystem is a tree of kernel objects: a directory is an object whose
children are objects, a file is an object with read/write. There is no separate
"file descriptor table" concept — opening a path just mints a capability.

Paths exist only for human convenience. The kernel resolves a path to a VNode,
then works with the object; per-directory capability narrowing is a planned
extension (see ``docs/DECISIONS.md`` D5).
"""

from __future__ import annotations

from typing import Dict, List

from .errors import AlreadyExists, IsADirectory, NotADirectory, NotFound
from .objects import KernelObject


def normalize(path: str, cwd: str = "/") -> str:
    """Collapse ``.``, ``..`` and duplicate slashes into an absolute path."""
    absolute = path.startswith("/")
    parts: List[str] = []
    base = [] if absolute else [p for p in cwd.split("/") if p]
    for part in path.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            if parts:
                parts.pop()
            elif not absolute and base:
                base.pop()
            continue
        parts.append(part)
    return "/" + "/".join(base + parts)


def split(path: str) -> List[str]:
    return [p for p in path.split("/") if p not in ("", ".")]


class VNode(KernelObject):
    """Base class for filesystem nodes."""

    interface = "vnode"

    def __init__(self, name: str = "", parent: "Directory | None" = None) -> None:
        super().__init__(name)
        self.parent = parent

    def stat(self) -> dict:
        return {"name": self.name, "type": self.interface, "size": 0, "oid": self.oid}


class File(VNode):
    """A byte-addressed file."""

    interface = "file"

    def __init__(self, name: str = "", parent: "Directory | None" = None, data: bytes = b"") -> None:
        super().__init__(name, parent)
        self.data = bytearray(data)

    def read(self, offset: int = 0, length: int = -1) -> bytes:
        if offset < 0:
            offset = max(0, len(self.data) + offset)
        end = len(self.data) if length < 0 else min(len(self.data), offset + length)
        return bytes(self.data[offset:end])

    def write(self, offset: int = -1, data: bytes = b"") -> int:
        """Write at *offset*; ``offset=-1`` appends. Returns bytes written."""
        data = bytes(data)
        if offset < 0:
            self.data.extend(data)
        else:
            if offset > len(self.data):
                self.data.extend(b"\x00" * (offset - len(self.data)))
            self.data[offset : offset + len(data)] = data
        return len(data)

    def truncate(self, size: int = 0) -> int:
        size = max(0, int(size))
        if size < len(self.data):
            del self.data[size:]
        else:
            self.data.extend(b"\x00" * (size - len(self.data)))
        return len(self.data)

    def size(self) -> int:
        return len(self.data)

    def stat(self) -> dict:
        info = super().stat()
        info["size"] = len(self.data)
        return info


class Directory(VNode):
    """A directory: a name → VNode map."""

    interface = "dir"

    def __init__(self, name: str = "", parent: "Directory | None" = None) -> None:
        super().__init__(name, parent)
        self.children: Dict[str, VNode] = {}

    def list(self) -> List[str]:
        """Entry names, directories suffixed with ``/``, sorted."""
        return sorted(
            f"{name}/" if isinstance(node, Directory) else name
            for name, node in self.children.items()
        )

    def lookup(self, name: str) -> VNode:
        try:
            return self.children[name]
        except KeyError:
            raise NotFound(f"{name!r} not found in {self.path()}") from None

    def has(self, name: str) -> bool:
        return name in self.children

    def create_file(self, name: str, data: bytes = b"") -> File:
        if name in self.children:
            raise AlreadyExists(f"{name!r} already exists in {self.path()}")
        node = File(name, self, data)
        self.children[name] = node
        return node

    def mkdir(self, name: str) -> "Directory":
        if name in self.children:
            raise AlreadyExists(f"{name!r} already exists in {self.path()}")
        node = Directory(name, self)
        self.children[name] = node
        return node

    def unlink(self, name: str) -> VNode:
        node = self.lookup(name)
        del self.children[name]
        return node

    def size(self) -> int:
        return len(self.children)

    def path(self) -> str:
        parts: List[str] = []
        node: VNode | None = self
        while node is not None and node.name:
            parts.append(node.name)
            node = node.parent
        return "/" + "/".join(reversed(parts))

    def stat(self) -> dict:
        info = super().stat()
        info["entries"] = len(self.children)
        return info


class MemFS:
    """An in-memory filesystem, seeded with a conventional Unix-ish tree."""

    def __init__(self) -> None:
        self.root = Directory("")
        self.seed()

    def seed(self) -> None:
        root = self.root
        root.mkdir("bin")
        root.mkdir("etc")
        root.mkdir("home")
        root.mkdir("tmp")
        root.mkdir("proc")
        home = root.lookup("home")
        home.mkdir("user")
        root.create_file(
            "motd",
            b"OO-OS 0.1.0 - an object-oriented operating system\n"
            b"everything is an object, every reference is a capability\n",
        )
        root.lookup("etc").create_file("motd", b"welcome to OO-OS\n")
        root.lookup("etc").create_file(
            "kernel.conf", b"tick.slice=4\nphys.frames=4096\nsched.policy=rr\n"
        )
        root.lookup("home").lookup("user").create_file(
            "notes.txt", b"the kernel is a graph of objects\n"
        )
        root.lookup("proc").create_file("version", b"OO-OS 0.1.0\n")

    def resolve(self, path: str, cwd: str = "/") -> VNode:
        """Resolve an absolute or relative path to a node."""
        node: VNode = self.root
        target = normalize(path, cwd)
        for part in split(target):
            if not isinstance(node, Directory):
                raise NotADirectory(f"{node.name or '/'} is not a directory")
            node = node.lookup(part)
        return node

    def resolve_parent(self, path: str, cwd: str = "/") -> tuple[Directory, str]:
        """Resolve the directory containing *path* plus its final component."""
        target = normalize(path, cwd)
        parts = split(target)
        if not parts:
            raise NotFound("cannot resolve the parent of /")
        node: VNode = self.root
        for part in parts[:-1]:
            if not isinstance(node, Directory):
                raise NotADirectory(f"{node.name or '/'} is not a directory")
            node = node.lookup(part)
        if not isinstance(node, Directory):
            raise NotADirectory(f"{node.name or '/'} is not a directory")
        return node, parts[-1]

    def mkdir(self, path: str, cwd: str = "/") -> Directory:
        parent, name = self.resolve_parent(path, cwd)
        return parent.mkdir(name)

    def write(self, path: str, data: bytes, cwd: str = "/") -> File:
        parent, name = self.resolve_parent(path, cwd)
        if not parent.has(name):
            return parent.create_file(name, data)
        node = parent.lookup(name)
        if isinstance(node, Directory):
            raise IsADirectory(f"{path} is a directory")
        node.write(-1, b"")  # type: ignore[attr-defined]
        node.truncate(0)  # type: ignore[attr-defined]
        node.write(-1, data)  # type: ignore[attr-defined]
        return node

    def walk(self, node: VNode | None = None, prefix: str = "/") -> List[str]:
        """Flatten the tree into a sorted list of paths (debug aid)."""
        node = node or self.root
        out: List[str] = []
        if isinstance(node, Directory):
            for name, child in sorted(node.children.items()):
                child_path = f"{prefix}{name}"
                out.append(child_path + "/" if isinstance(child, Directory) else child_path)
                out.extend(self.walk(child, child_path + "/"))
        return out
