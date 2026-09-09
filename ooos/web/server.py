"""Stdlib-only HTTP server for the OO-OS web terminal.

No dependencies beyond the standard library, because an OS that needs a package
manager to boot is not an OS.

    python -m ooos.web --port 8000
"""

from __future__ import annotations

import argparse
import json
import os
import re
import threading
import uuid
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

from ..console import Console
from ..kernel import Kernel

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
MAX_SESSIONS = 64


class Session:
    """One kernel, one output buffer, one human."""

    def __init__(self, session_id: str) -> None:
        self.id = session_id
        self.buffer: List[str] = []
        self.lock = threading.Lock()
        self.kernel = Kernel(console=Console(writer=self._write))
        self.kernel.boot()
        self.finished = False

    def _write(self, text: str) -> None:
        self.buffer.append(text)

    # -- driving ------------------------------------------------------------

    def start(self) -> Tuple[str, bool]:
        return self._pump()

    def execute(self, line: str) -> Tuple[str, bool]:
        if self.finished:
            return ("", True)
        self.kernel.console.push(line)
        return self._pump()

    def _pump(self) -> Tuple[str, bool]:
        """Run the machine until it blocks on us again."""
        with self.lock:
            self.kernel.run(max_steps=200_000)
            text = "".join(self.buffer)
            self.buffer.clear()
            console = self.kernel.console
            blocked_on_us = bool(console.waiters) and not console.eof
            self.finished = not blocked_on_us and not self.kernel.sched.alive_threads()
            return text, self.finished

    def reset(self) -> Tuple[str, bool]:
        self.kernel = Kernel(console=Console(writer=self._write))
        self.kernel.boot()
        self.buffer.clear()
        self.finished = False
        return self.start()

    def snapshot(self) -> dict:
        return {"id": self.id, "finished": self.finished, "stats": self.kernel.stats()}


class SessionStore:
    """Bounded map of live sessions (so a stray bot cannot eat the box)."""

    def __init__(self, limit: int = MAX_SESSIONS) -> None:
        self.limit = limit
        self.lock = threading.Lock()
        self.sessions: Dict[str, Session] = {}

    def create(self) -> Session:
        with self.lock:
            if len(self.sessions) >= self.limit:
                oldest = next(iter(self.sessions))
                self.sessions.pop(oldest, None)
            session = Session(uuid.uuid4().hex[:12])
            self.sessions[session.id] = session
            return session

    def get(self, session_id: str) -> Optional[Session]:
        with self.lock:
            return self.sessions.get(session_id)


STORE = SessionStore()

ROUTES = [
    (re.compile(r"^/api/session$"), "session"),
    (re.compile(r"^/api/session/([A-Za-z0-9]+)/exec$"), "exec"),
    (re.compile(r"^/api/session/([A-Za-z0-9]+)/reset$"), "reset"),
    (re.compile(r"^/api/session/([A-Za-z0-9]+)$"), "snapshot"),
]


class Handler(BaseHTTPRequestHandler):
    server_version = "OO-OS/0.1.0"

    # -- plumbing -----------------------------------------------------------

    def _send(self, status: HTTPStatus, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, status: HTTPStatus, payload: dict) -> None:
        self._send(status, json.dumps(payload).encode("utf-8"), "application/json")

    def _body(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if not length:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return {}

    def log_message(self, fmt: str, *args) -> None:
        # Quieter than the default: one line per request, no DNS lookups.
        print(f"[ooos.web] {self.address_string()} {fmt % args}", flush=True)

    # -- verbs --------------------------------------------------------------

    def do_GET(self) -> None:  # noqa: N802 - required name
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            self._serve_static("index.html")
            return
        for pattern, name in ROUTES:
            match = pattern.match(path)
            if match and name == "snapshot":
                session = STORE.get(match.group(1))
                if session is None:
                    self._send_json(HTTPStatus.NOT_FOUND, {"error": "no such session"})
                    return
                self._send_json(HTTPStatus.OK, session.snapshot())
                return
        if path.startswith("/static/"):
            self._serve_static(os.path.basename(path))
            return
        self._send_json(HTTPStatus.NOT_FOUND, {"error": f"no route for {path}"})

    def do_POST(self) -> None:  # noqa: N802 - required name
        path = urlparse(self.path).path
        for pattern, name in ROUTES:
            match = pattern.match(path)
            if not match:
                continue
            if name == "session":
                session = STORE.create()
                out, done = session.start()
                self._send_json(HTTPStatus.OK, {"id": session.id, "out": out, "done": done})
                return
            session = STORE.get(match.group(1))
            if session is None:
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "no such session"})
                return
            payload = self._body()
            if name == "exec":
                out, done = session.execute(str(payload.get("line", "")))
                self._send_json(HTTPStatus.OK, {"out": out, "done": done})
                return
            if name == "reset":
                out, done = session.reset()
                self._send_json(HTTPStatus.OK, {"out": out, "done": done})
                return
        self._send_json(HTTPStatus.NOT_FOUND, {"error": f"no route for {path}"})

    def _serve_static(self, filename: str) -> None:
        safe = os.path.basename(filename)
        path = os.path.join(STATIC_DIR, safe)
        if not os.path.isfile(path):
            self._send_json(HTTPStatus.NOT_FOUND, {"error": f"no such file: {safe}"})
            return
        with open(path, "rb") as handle:
            body = handle.read()
        content_type = "text/html; charset=utf-8"
        if safe.endswith(".css"):
            content_type = "text/css; charset=utf-8"
        elif safe.endswith(".js"):
            content_type = "application/javascript; charset=utf-8"
        self._send(HTTPStatus.OK, body, content_type)


def build_server(host: str = "0.0.0.0", port: int = 8000) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), Handler)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="ooos.web", description="OO-OS web terminal")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(argv)

    server = build_server(args.host, args.port)
    print(f"OO-OS web terminal on http://{args.host}:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nhalting", flush=True)
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
