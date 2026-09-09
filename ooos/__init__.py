"""OO-OS — an object-oriented operating system.

Everything in the kernel is an object. Every reference to an object is a capability.
Every operation is a method invocation on a capability.

This package is the reference implementation: a real microkernel design that runs in
userspace on top of a virtual clock, so it is deterministic and testable everywhere.

Start here:
    python -m ooos.boot            # interactive shell
    python -m ooos.boot --demo     # scripted demo
"""

__version__ = "0.1.0"
__all__ = ["__version__"]
