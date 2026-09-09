"""The object table — the heart of OO-OS.

Every kernel resource (file, directory, endpoint, console, process, address space)
is a :class:`KernelObject` living in one flat :class:`ObjectTable`. Objects are
addressed by opaque integer ids; the outside world reaches them only through
capabilities, so an object id is never a security token by itself.
"""

from __future__ import annotations

from typing import Any, Callable, ClassVar, Dict, Iterator, Optional

from .errors import NoSuchMethod, ObjectNotFound

_METHOD_CACHE: Dict[type, Dict[str, Callable]] = {}


def _public_methods(cls: type) -> Dict[str, Callable]:
    """Introspect the public callables of a class (cached per class)."""
    cached = _METHOD_CACHE.get(cls)
    if cached is None:
        cached = {}
        for klass in reversed(cls.__mro__):
            for name, attr in vars(klass).items():
                if name.startswith("_") or not callable(attr):
                    continue
                cached[name] = attr
        _METHOD_CACHE[cls] = dict(sorted(cached.items()))
    return cached


class KernelObject:
    """Base class for everything the kernel owns.

    Public (non-underscore) callables are the object's interface, invocable
    through a capability. Subclasses declare ``interface`` to name their type.
    """

    interface: ClassVar[str] = "object"

    def __init__(self, name: str = "") -> None:
        self.oid: int = 0
        self.name = name
        self.refcount = 0
        self.destroyed = False
        self.kernel: Any = None

    # -- lifecycle ---------------------------------------------------------

    def bind(self, kernel: Any) -> None:
        """Called by the object table when the object is inserted."""
        self.kernel = kernel

    def destroy(self) -> None:
        """Release the object. Idempotent; subclasses override to free resources."""
        self.destroyed = True

    # -- invocation --------------------------------------------------------

    def methods(self) -> Dict[str, Callable]:
        """Public method map for this object's class."""
        return _public_methods(type(self))

    def invoke(self, method: str, *args: Any, **kwargs: Any) -> Any:
        """Dispatch a method call. Rights are checked one layer up, in syscalls."""
        if self.destroyed:
            raise ObjectNotFound(f"object {self.oid} was destroyed")
        fn = self.methods().get(method)
        if fn is None:
            raise NoSuchMethod(
                f"{self.interface} object has no method '{method}' "
                f"(have: {', '.join(self.methods()) or 'none'})"
            )
        return fn(self, *args, **kwargs)

    def describe(self) -> str:
        return f"<{self.interface} oid={self.oid} name={self.name!r}>"

    def __repr__(self) -> str:
        return self.describe()


class ObjectTable:
    """Flat kernel-wide table of objects, keyed by opaque object id."""

    def __init__(self, kernel: Any = None) -> None:
        self.kernel = kernel
        self._objects: Dict[int, KernelObject] = {}
        self._next_oid = 1

    def add(self, obj: KernelObject) -> int:
        """Insert *obj*, assign it an id, and return that id."""
        oid = self._next_oid
        self._next_oid += 1
        obj.oid = oid
        obj.refcount = 0
        self._objects[oid] = obj
        obj.bind(self.kernel)
        return oid

    def get(self, oid: int) -> KernelObject:
        try:
            obj = self._objects[oid]
        except KeyError:
            raise ObjectNotFound(f"no object with oid={oid}") from None
        if obj.destroyed:
            raise ObjectNotFound(f"object {oid} was destroyed")
        return obj

    def remove(self, oid: int) -> None:
        obj = self._objects.pop(oid, None)
        if obj is not None:
            obj.destroy()

    def __len__(self) -> int:
        return len(self._objects)

    def __iter__(self) -> Iterator[KernelObject]:
        return iter(list(self._objects.values()))

    def stats(self) -> Dict[str, Any]:
        by_type: Dict[str, int] = {}
        for obj in self:
            by_type[obj.interface] = by_type.get(obj.interface, 0) + 1
        return {"objects": len(self), "by_type": dict(sorted(by_type.items()))}

    def find_by_name(self, name: str) -> Optional[KernelObject]:
        for obj in self:
            if obj.name == name:
                return obj
        return None
