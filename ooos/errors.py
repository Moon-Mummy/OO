"""OO-OS error hierarchy.

One base class, narrow subclasses. The kernel never raises bare Python exceptions
across the syscall boundary — everything is an :class:`OoosError`.
"""

from __future__ import annotations


class OoosError(Exception):
    """Base class for every OO-OS error."""


class KernelPanic(OoosError):
    """Unrecoverable kernel condition. Halts the machine."""


# --- capabilities -----------------------------------------------------------


class CapabilityError(OoosError):
    """Base class for capability faults."""


class BadCapability(CapabilityError):
    """Capability index does not exist in the calling process."""


class NotPermitted(CapabilityError):
    """Capability exists but lacks the rights required by the method."""


# --- objects ----------------------------------------------------------------


class ObjectError(OoosError):
    """Base class for object faults."""


class ObjectNotFound(ObjectError):
    """Object id is not in the object table (or object was destroyed)."""


class NoSuchMethod(ObjectError):
    """Object exists but does not expose that method."""


# --- filesystem -------------------------------------------------------------


class FsError(OoosError):
    """Base class for filesystem faults."""


class NotFound(FsError):
    """Path does not resolve."""


class NotADirectory(FsError):
    """A path component was a file where a directory was required."""


class IsADirectory(FsError):
    """Operation requires a file but got a directory."""


class AlreadyExists(FsError):
    """Link target already present."""


# --- ipc --------------------------------------------------------------------


class IpcError(OoosError):
    """Base class for IPC faults."""


class WouldBlock(IpcError):
    """Non-blocking receive on an empty endpoint."""


class EndpointClosed(IpcError):
    """Operation on a closed endpoint."""


# --- memory -----------------------------------------------------------------


class OomError(OoosError):
    """Physical memory exhausted."""


class Segfault(OoosError):
    """Address outside the address space, or rights violation."""


# --- syscalls ---------------------------------------------------------------


class SyscallError(OoosError):
    """Base class for syscall faults."""


class BadSyscall(SyscallError):
    """No such syscall."""


class BadArgument(SyscallError):
    """Syscall got arguments it cannot use."""
