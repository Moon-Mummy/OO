"""Smoke tests: boot a machine, type commands, assert on the transcript.

These guard the vertical slice. Subsystem-level tests belong next to each
subsystem — see the claim map in AGENTS.md.
"""

from __future__ import annotations

import pytest

from ooos.console import Console
from ooos.kernel import Kernel


def machine(lines=None, frames=64):
    """Boot a machine, feed it *lines*, close stdin, run to halt."""
    out: list[str] = []
    console = Console(writer=out.append)
    kernel = Kernel(console=console, frames=frames)
    kernel.boot()
    for line in lines or []:
        console.push(line)
    console.close()
    kernel.run()
    return kernel, "".join(out)


def test_machine_boots_and_halts():
    kernel, out = machine(["exit"])
    assert "OO-OS 0.1.0" in out
    assert kernel.panicked is None
    # init reaps the shell, then halts: nothing is left running
    assert kernel.sched.alive_threads() == []


def test_lists_root_directory():
    _, out = machine(["ls /", "exit"])
    for entry in ("bin/", "etc/", "home/", "motd", "proc/"):
        assert entry in out


def test_reads_a_file():
    _, out = machine(["cat /etc/motd", "exit"])
    assert "welcome to OO-OS" in out


def test_writes_then_reads_back():
    _, out = machine(
        ["mkdir /tmp/t", "write /tmp/t/a.txt round trip", "cat /tmp/t/a.txt", "exit"]
    )
    assert "round trip" in out


def test_spawn_runs_a_child_process():
    kernel, out = machine(["spawn hello world --wait", "exit"])
    assert "hello, world" in out
    assert "exited with status 0" in out


def test_sleep_consumes_virtual_ticks():
    kernel, out = machine(["sleep 5", "exit"])
    assert "slept 5 ticks" in out
    assert kernel.clock.now > 5


def test_capability_table_is_visible():
    _, out = machine(["caps", "exit"])
    assert "root" in out
    assert "console" in out


def test_capability_passing_demo():
    _, out = machine(["ipcdemo", "exit"])
    assert "installed talker endpoint" in out
    assert "received 'ping from ipcdemo'" in out


def test_memory_allocation_is_bounds_checked():
    _, out = machine(["alloc 1024", "maps", "exit"])
    assert "mapped 1024 bytes at 0x00000000" in out
    assert "1p" in out  # one page


def test_unknown_command_reports_cleanly():
    _, out = machine(["definitely-not-a-command", "exit"])
    assert "command not found" in out


def test_segfault_on_unmapped_memory():
    _, out = machine(["peek 0xdeadbeef 4", "exit"])
    assert "unmapped address" in out


def test_every_run_is_deterministic():
    first, out1 = machine(["spawn counter 3 --wait", "ps", "exit"])
    second, out2 = machine(["spawn counter 3 --wait", "ps", "exit"])
    assert out1 == out2
    assert first.clock.now == second.clock.now
