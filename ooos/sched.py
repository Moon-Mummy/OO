"""The scheduler — processes, threads, and the round-robin step loop.

Threads are Python generators. Each ``yield`` is a scheduling point: the thread
hands the scheduler a request (``sleep``, ``recv``, ``read_line``, ...) and is
resumed later by having the result *sent into* the generator. That gives us
preemption-free, fully reproducible multitasking with no threads, no locks and
no signals — the tick is virtual, so a test can assert on exact timings.
"""

from __future__ import annotations

import inspect
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Deque, Dict, Generator, List, Optional

from .capability import Capability, Rights, format_rights
from .console import EOF, NO_LINE
from .errors import KernelPanic, OoosError
from .mm import AddressSpace
from .requests import ExitThread, ReadLine, Recv, Sleep, WaitPid, YieldCPU

#: Steps a thread runs before it is moved to the back of the ready queue.
DEFAULT_SLICE = 4

Entry = Callable[[Any, List[str]], Generator[Any, Any, Any]]


def _one_shot(value: Any) -> Generator[Any, Any, Any]:
    """Wrap a plain function's result so non-blocking programs need no ``yield``."""
    return value
    yield  # pragma: no cover - unreachable; present only to make this a generator


class ThreadState(Enum):
    READY = "ready"
    RUNNING = "running"
    BLOCKED = "blocked"
    DEAD = "dead"


class ProcessState(Enum):
    RUNNING = "running"
    ZOMBIE = "zombie"


@dataclass
class Thread:
    tid: int
    name: str
    process: "Process"
    gen: Generator[Any, Any, Any]
    state: ThreadState = ThreadState.READY
    slice_left: int = DEFAULT_SLICE
    wake_at: Optional[int] = None
    blocked: Any = None
    pending: Any = None
    exit_status: int = 0
    steps: int = 0
    error: Optional[BaseException] = None

    def __str__(self) -> str:
        return f"<thread {self.tid} {self.name} {self.state.value}>"


@dataclass
class Process:
    pid: int
    name: str
    kernel: Any
    argv: List[str] = field(default_factory=list)
    caps: Dict[int, Capability] = field(default_factory=dict)
    threads: Dict[int, Thread] = field(default_factory=dict)
    state: ProcessState = ProcessState.RUNNING
    exit_status: int = 0
    parent: Optional["Process"] = None
    children: List[int] = field(default_factory=list)
    waiters: List[int] = field(default_factory=list)
    cwd: str = "/"
    address_space: Optional[AddressSpace] = None
    ticks: int = 0
    _next_cap: int = 0

    # -- capability table ---------------------------------------------------

    def add_cap(self, cap: Capability, index: Optional[int] = None) -> int:
        idx = self._next_cap if index is None else index
        self._next_cap = max(self._next_cap, idx + 1)
        self.caps[idx] = cap
        return idx

    def cap(self, index: int) -> Capability:
        try:
            return self.caps[index]
        except KeyError:
            from .errors import BadCapability

            raise BadCapability(f"pid {self.pid} has no capability {index}") from None

    def drop_cap(self, index: int) -> Capability:
        return self.caps.pop(index)

    def cap_by_label(self, label: str) -> Optional[tuple[int, Capability]]:
        for idx, cap in self.caps.items():
            if cap.label == label:
                return idx, cap
        return None

    def cap_table(self) -> List[str]:
        return [
            f"{idx}: {cap.label or '?'} oid={cap.oid} {format_rights(cap.rights)}"
            for idx, cap in sorted(self.caps.items())
        ]

    @property
    def alive(self) -> bool:
        return self.state is ProcessState.RUNNING

    def __str__(self) -> str:
        return f"<process {self.pid} {self.name} {self.state.value}>"


class Scheduler:
    """Round-robin scheduler over generator threads on a virtual clock."""

    def __init__(self, kernel: Any, slice_size: int = DEFAULT_SLICE) -> None:
        self.kernel = kernel
        self.slice_size = slice_size
        self.threads: Dict[int, Thread] = {}
        self.processes: Dict[int, Process] = {}
        self.ready: Deque[int] = deque()
        self.current: Optional[Thread] = None
        self._creating: Optional[Process] = None
        self._next_tid = 1
        self._next_pid = 1
        self.total_steps = 0

    # -- creation -----------------------------------------------------------

    def create_process(
        self,
        name: str,
        entry: Entry,
        *,
        parent: Optional[Process] = None,
        argv: Optional[List[str]] = None,
        caps: Optional[Dict[int, Capability]] = None,
    ) -> Process:
        pid = self._next_pid
        self._next_pid += 1
        proc = Process(
            pid=pid,
            name=name,
            kernel=self.kernel,
            argv=list(argv or []),
            parent=parent,
        )
        proc.address_space = self.kernel.mm.create_space(f"{name}:{pid}")
        if caps:
            for idx, cap in caps.items():
                proc.add_cap(cap, idx)
        if parent is not None:
            parent.children.append(pid)
        self.processes[pid] = proc

        # entry() runs before the thread exists, so expose the process through
        # the "creating" slot to let programs look themselves up.
        self._creating = proc
        try:
            gen = entry(self.kernel, proc.argv)
        finally:
            self._creating = None
        if not inspect.isgenerator(gen):
            gen = _one_shot(gen)
        self.create_thread(proc, gen, "main")
        return proc

    def create_thread(self, proc: Process, gen: Generator, name: str = "worker") -> Thread:
        tid = self._next_tid
        self._next_tid += 1
        thread = Thread(tid=tid, name=f"{proc.name}:{name}", process=proc, gen=gen)
        thread.slice_left = self.slice_size
        proc.threads[tid] = thread
        self.threads[tid] = thread
        self.ready.append(tid)
        return thread

    def current_process(self) -> Optional[Process]:
        # A process being constructed wins: syscalls made while its program
        # factory runs belong to *it*, not to whoever called spawn().
        if self._creating is not None:
            return self._creating
        return self.current.process if self.current is not None else None

    # -- execution ----------------------------------------------------------

    def step(self) -> bool:
        """Advance one thread by one step. Returns False if nothing is runnable."""
        self._wake_sleepers()
        thread = None
        while self.ready:
            candidate = self.threads.get(self.ready.popleft())
            if candidate is None or candidate.state is not ThreadState.READY:
                continue
            thread = candidate
            break
        if thread is None:
            return False

        thread.state = ThreadState.RUNNING
        self.current = thread
        self.kernel.clock.advance(1)
        thread.steps += 1
        thread.process.ticks += 1
        self.total_steps += 1

        value = thread.pending
        thread.pending = None
        try:
            request = thread.gen.send(value)
        except StopIteration:
            self._thread_exit(thread, 0)
            return True
        except OoosError as exc:
            self._thread_exit(thread, 1, error=exc)
            return True
        self._handle(thread, request)
        return True

    def run(self, max_steps: int = 1_000_000) -> int:
        """Run until every thread is dead or permanently blocked."""
        steps = 0
        while True:
            if not self.ready:
                deadline = self._next_deadline()
                if deadline is None:
                    break
                clock = self.kernel.clock
                if deadline <= clock.now:
                    clock.advance(1)
                else:
                    clock.advance_to(deadline)
                self._wake_sleepers()
                continue
            if not self.step():
                break
            steps += 1
            if steps >= max_steps:
                raise KernelPanic(f"runaway kernel: exceeded {max_steps} steps")
        self.current = None
        return steps

    # -- request handling ---------------------------------------------------

    def _handle(self, thread: Thread, request: Any) -> None:
        if request is None:
            # Bare `yield`: keep the CPU if the slice is not exhausted.
            thread.slice_left -= 1
            if thread.slice_left <= 0:
                thread.slice_left = self.slice_size
                self._ready(thread)
            else:
                thread.state = ThreadState.READY
                self.ready.appendleft(thread.tid)
            return

        if isinstance(request, YieldCPU):
            thread.slice_left = self.slice_size
            self._ready(thread)
            return

        if isinstance(request, Sleep):
            ticks = max(0, int(request.ticks))
            if ticks == 0:
                thread.state = ThreadState.READY
                self.ready.appendleft(thread.tid)
                return
            thread.state = ThreadState.BLOCKED
            thread.blocked = request
            thread.wake_at = self.kernel.clock.now + ticks
            return

        if isinstance(request, Recv):
            endpoint = request.endpoint
            try:
                message = endpoint.recv()
            except OoosError:
                message = None
            if message is not None:
                self.wake_now(thread, message)
                return
            endpoint.waiters.append(thread.tid)
            thread.state = ThreadState.BLOCKED
            thread.blocked = request
            return

        if isinstance(request, WaitPid):
            result = self._reap(thread.process, request.pid)
            if result is not None:
                self.wake_now(thread, result)
                return
            thread.process.waiters.append(thread.tid)
            thread.state = ThreadState.BLOCKED
            thread.blocked = request
            return

        if isinstance(request, ReadLine):
            line = self.kernel.console.get()
            if line is EOF:
                self._thread_exit(thread, 0)
                return
            if line is NO_LINE:
                self.kernel.console.waiters.append(thread.tid)
                thread.state = ThreadState.BLOCKED
                thread.blocked = request
                return
            self.wake_now(thread, line)
            return

        if isinstance(request, ExitThread):
            self._thread_exit(thread, request.status)
            return

        raise KernelPanic(
            f"thread {thread.tid} yielded an unknown request: {request!r}"
        )

    # -- state transitions --------------------------------------------------

    def _ready(self, thread: Thread) -> None:
        thread.state = ThreadState.READY
        self.ready.append(thread.tid)

    def wake(self, tid: int, value: Any = None) -> bool:
        """Resume a blocked thread, delivering *value* into its generator."""
        thread = self.threads.get(tid)
        if thread is None or thread.state is not ThreadState.BLOCKED:
            return False
        thread.pending = value
        thread.blocked = None
        thread.wake_at = None
        thread.state = ThreadState.READY
        self.ready.appendleft(tid)
        return True

    def wake_now(self, thread: Thread, value: Any) -> None:
        thread.pending = value
        thread.blocked = None
        thread.wake_at = None
        thread.state = ThreadState.READY
        self.ready.appendleft(thread.tid)

    def _wake_sleepers(self) -> None:
        now = self.kernel.clock.now
        for thread in list(self.threads.values()):
            if (
                thread.state is ThreadState.BLOCKED
                and thread.wake_at is not None
                and thread.wake_at <= now
            ):
                thread.wake_at = None
                thread.blocked = None
                thread.pending = None
                self._ready(thread)

    def _next_deadline(self) -> Optional[int]:
        deadlines = [
            t.wake_at
            for t in self.threads.values()
            if t.state is ThreadState.BLOCKED and t.wake_at is not None
        ]
        return min(deadlines) if deadlines else None

    def _thread_exit(self, thread: Thread, status: int, error: BaseException | None = None) -> None:
        thread.state = ThreadState.DEAD
        thread.exit_status = status
        if error is not None:
            thread.error = error
            self.kernel.console.write(f"\n[kernel] {thread.name} faulted: {error}\n")
        thread.process.threads.pop(thread.tid, None)
        self.threads.pop(thread.tid, None)
        if thread.tid in self.kernel.console.waiters:
            self.kernel.console.waiters.remove(thread.tid)
        if not thread.process.threads:
            self._process_exit(thread.process, status)

    def _process_exit(self, proc: Process, status: int) -> None:
        proc.state = ProcessState.ZOMBIE
        proc.exit_status = status
        if proc.address_space is not None:
            self.kernel.mm.destroy_space(proc.address_space.owner)
            proc.address_space = None
        # Waiters are queued on the *parent*, so that is who we wake.
        parent = proc.parent
        if parent is None:
            return
        for tid in list(parent.waiters):
            thread = self.threads.get(tid)
            if thread is None:
                parent.waiters.remove(tid)
                continue
            wanted = thread.blocked.pid if isinstance(thread.blocked, WaitPid) else -1
            result = self._reap(parent, wanted)
            if result is not None:
                parent.waiters.remove(tid)
                self.wake(tid, result)

    def _reap(self, proc: Process, pid: int) -> Optional[tuple[int, int]]:
        """Return ``(pid, status)`` for an exited child, or None to keep waiting."""
        if pid == -1:
            for child_pid in list(proc.children):
                child = self.processes.get(child_pid)
                if child is not None and child.state is ProcessState.ZOMBIE:
                    proc.children.remove(child_pid)
                    status = child.exit_status
                    self.processes.pop(child_pid, None)
                    return (child_pid, status)
            if not proc.children:
                return (-1, -1)
            return None
        child = self.processes.get(pid)
        if child is None or child.parent is not proc:
            return (pid, -1)
        if child.state is ProcessState.ZOMBIE:
            proc.children.remove(pid)
            status = child.exit_status
            self.processes.pop(pid, None)
            return (pid, status)
        return None

    # -- control ------------------------------------------------------------

    def kill_process(self, pid: int, status: int = 1) -> bool:
        proc = self.processes.get(pid)
        if proc is None or proc.state is ProcessState.ZOMBIE:
            return False
        for thread in list(proc.threads.values()):
            thread.state = ThreadState.DEAD
            thread.exit_status = status
            if thread.tid in self.kernel.console.waiters:
                self.kernel.console.waiters.remove(thread.tid)
            self.threads.pop(thread.tid, None)
        proc.threads.clear()
        self._process_exit(proc, status)
        return True

    def kill_thread(self, tid: int, status: int = 1) -> bool:
        thread = self.threads.get(tid)
        if thread is None:
            return False
        self._thread_exit(thread, status)
        return True

    # -- introspection ------------------------------------------------------

    def alive_threads(self) -> List[Thread]:
        return [t for t in self.threads.values() if t.state is not ThreadState.DEAD]

    def ps(self) -> List[dict]:
        rows = []
        for proc in sorted(self.processes.values(), key=lambda p: p.pid):
            states = sorted({t.state.value for t in proc.threads.values()}) or ["-"]
            rows.append(
                {
                    "pid": proc.pid,
                    "name": proc.name,
                    "state": proc.state.value,
                    "threads": len(proc.threads),
                    "tstates": ",".join(states),
                    "ticks": proc.ticks,
                    "caps": len(proc.caps),
                    "cwd": proc.cwd,
                }
            )
        return rows

    def stats(self) -> dict:
        return {
            "processes": len(self.processes),
            "threads": len(self.threads),
            "runnable": len(self.ready),
            "steps": self.total_steps,
            "ticks": self.kernel.clock.now,
        }
