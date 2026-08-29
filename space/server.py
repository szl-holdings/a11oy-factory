"""A11oy Factory Space — Decision Cell Compiler. BIND_AS_A11OY_PACKAGE."""
from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from a11oy_factory.cells import CELLS, FRONTIERS, LYTE
from a11oy_factory.compiler import compile_cell

HTML = Path(__file__).with_name("index.html")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        return

    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "content-type")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            self._send(200, HTML.read_bytes(), "text/html; charset=utf-8")
            return
        if path in ("/health", "/healthz"):
            self._send(
                200,
                json.dumps(
                    {
                        "ok": True,
                        "service": "a11oy-factory",
                        "bind": "BIND_AS_A11OY_PACKAGE",
                        "admitted": ["lyte"],
                        "frontiers": [c.id for c in FRONTIERS],
                        "lambda_status": "Conjecture 1",
                        "energy": None,
                    }
                ).encode(),
                "application/json",
            )
            return
        if path == "/api/cells":
            cells = [CELLS[k].__dict__ for k in ["lyte"] + [f"N{n}" for n in range(1, 9)]]
            self._send(200, json.dumps(cells).encode(), "application/json")
            return
        self._send(404, b"not found", "text/plain")

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n) if n else b"{}"
        try:
            data = json.loads(raw.decode() or "{}")
        except Exception:
            data = {}
        if path == "/api/compile":
            rec = compile_cell(str(data.get("cell") or ""), signal=str(data.get("signal") or ""))
            self._send(200, json.dumps(rec.as_dict()).encode(), "application/json")
            return
        self._send(404, b"not found", "text/plain")


def main() -> None:
    port = int(os.environ.get("PORT", "7860"))
    httpd = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"a11oy-factory listening 0.0.0.0:{port} admitted={LYTE.id}", flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
