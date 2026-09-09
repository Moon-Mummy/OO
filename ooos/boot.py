"""Boot an OO-OS machine.

    python -m ooos.boot                 # interactive shell (when stdin is a tty)
    python -m ooos.boot --demo          # scripted tour
    python -m ooos.boot --script "ls /; cat /etc/motd; exit"
    echo "ps; exit" | python -m ooos.boot
"""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from .console import Console
from .kernel import Kernel
from .mm import DEFAULT_PHYSICAL_FRAMES

DEMO_SCRIPT: List[str] = [
    "ls /",
    "cat /etc/motd",
    "mkdir /tmp/demo; write /tmp/demo/hello.txt hello from OO-OS; cat /tmp/demo/hello.txt",
    "spawn counter 3 --wait",
    "spawn hello OO-OS; ps",
    "ipcdemo",
    "caps; objects",
    "memory",
    "uptime",
    "exit",
]


def build_kernel(frames: int = DEFAULT_PHYSICAL_FRAMES, writer=None) -> Kernel:
    """Create a kernel with a console that writes to *writer* (default: stdout)."""
    console = Console(writer=writer)
    kernel = Kernel(console=console, frames=frames)
    kernel.boot()
    return kernel


def run_scripted(kernel: Kernel, lines: List[str], max_steps: int = 1_000_000) -> str:
    """Feed *lines* to the console, close input, and run until the machine halts."""
    kernel.console.feed(lines)
    kernel.console.close()
    kernel.run(max_steps=max_steps)
    return ""


def run_interactive(kernel: Kernel, max_steps: int = 1_000_000) -> None:
    """Run until the machine blocks on input, then hand it a real line."""
    while True:
        kernel.run(max_steps=max_steps)
        console = kernel.console
        if console.waiters and not console.eof:
            try:
                line = input()
            except (EOFError, KeyboardInterrupt):
                console.close()
                continue
            console.push(line)
        else:
            break


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="ooos", description="OO-OS — an object-oriented operating system"
    )
    parser.add_argument("--demo", action="store_true", help="run the scripted tour")
    parser.add_argument("--script", metavar="CMDS", help="';'-separated commands to run")
    parser.add_argument(
        "--frames", type=int, default=DEFAULT_PHYSICAL_FRAMES, help="physical frames"
    )
    parser.add_argument(
        "--slice", type=int, default=4, help="scheduler time slice in steps"
    )
    parser.add_argument(
        "--max-steps", type=int, default=1_000_000, help="runaway-kernel guard"
    )
    args = parser.parse_args(argv)

    console = Console()
    kernel = Kernel(console=console, frames=args.frames, slice_size=args.slice)
    kernel.boot()

    if args.script:
        run_scripted(kernel, [c for c in args.script.split(";") if c.strip()], args.max_steps)
    elif args.demo:
        run_scripted(kernel, DEMO_SCRIPT, args.max_steps)
    elif sys.stdin.isatty():
        run_interactive(kernel, args.max_steps)
    else:
        run_scripted(kernel, sys.stdin.read().splitlines(), args.max_steps)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
