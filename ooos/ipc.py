"""IPC — message passing between objects.

Endpoints are kernel objects, so they are reached by capability and can be
passed between processes (that is the *only* way to acquire authority in OO-OS).
Send is non-blocking up to a bounded queue; receive is available both
non-blocking (:meth:`Endpoint.recv`) and blocking (:func:`ooos.api.recv`).
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any, Deque, List, Tuple

from .errors import EndpointClosed, WouldBlock
from .objects import KernelObject


@dataclass(slots=True)
class Message:
    """A message plus any capabilities riding along with it."""

    sender: int = 0
    data: Any = None
    caps: Tuple[Any, ...] = ()

    def __str__(self) -> str:
        return f"<msg from tid={self.sender} data={self.data!r} caps={len(self.caps)}>"


class Endpoint(KernelObject):
    """A bounded message queue with a capability-controlled handle."""

    interface = "endpoint"

    def __init__(self, name: str = "", capacity: int = 64) -> None:
        super().__init__(name)
        self.capacity = capacity
        self.queue: Deque[Message] = deque()
        self.waiters: List[int] = []
        self.closed = False
        self.sent = 0
        self.received = 0
        self.dropped = 0

    # -- kernel-object interface ------------------------------------------

    def send(self, data: Any = None, caps: Tuple[Any, ...] = (), sender: int = 0) -> int:
        """Enqueue a message. Returns the new queue depth.

        Raises :class:`~ooos.errors.EndpointClosed` or :class:`WouldBlock` when
        the queue is full (OO-OS never silently drops a message).
        """
        if self.closed:
            raise EndpointClosed(f"endpoint {self.oid} is closed")
        if len(self.queue) >= self.capacity:
            self.dropped += 1
            raise WouldBlock(f"endpoint {self.oid} is full ({self.capacity})")
        self.queue.append(Message(sender=sender, data=data, caps=tuple(caps)))
        self.sent += 1
        self._wake_waiter()
        return len(self.queue)

    def recv(self) -> Message:
        """Pop the next message, or raise :class:`WouldBlock` if empty."""
        if self.closed and not self.queue:
            raise EndpointClosed(f"endpoint {self.oid} is closed")
        if not self.queue:
            raise WouldBlock(f"endpoint {self.oid} is empty")
        self.received += 1
        return self.queue.popleft()

    def close(self) -> None:
        """Close the endpoint and release every blocked receiver."""
        self.closed = True
        while self.waiters and self.kernel is not None:
            tid = self.waiters.pop(0)
            self.kernel.sched.wake(tid, None)

    def stats(self) -> dict:
        return {
            "oid": self.oid,
            "name": self.name,
            "depth": len(self.queue),
            "capacity": self.capacity,
            "sent": self.sent,
            "received": self.received,
            "dropped": self.dropped,
            "waiters": len(self.waiters),
            "closed": self.closed,
        }

    def destroy(self) -> None:
        self.close()
        super().destroy()

    # -- internals ---------------------------------------------------------

    def _wake_waiter(self) -> None:
        """Hand the oldest blocked receiver the message we just queued."""
        while self.waiters and self.kernel is not None:
            tid = self.waiters.pop(0)
            thread = self.kernel.sched.threads.get(tid)
            if thread is None or thread.state is not thread.state.BLOCKED:
                continue
            try:
                message = self.recv()
            except WouldBlock:
                return
            self.kernel.sched.wake(tid, message)
            return
