#!/usr/bin/env python3
"""Tiny static server that mimics Netlify's clean-URL resolution and 404 page.

Usage: python3 build/serve.py <root-dir> <port>
"""
import http.server
import mimetypes
import posixpath
import socketserver
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()
PORT = int(sys.argv[2])


class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):  # keep the console readable
        sys.stderr.write("%s %s\n" % (self.address_string(), fmt % args))

    def resolve(self, path: str):
        path = urllib.parse.unquote(path.split("?", 1)[0].split("#", 1)[0])
        rel = posixpath.normpath(path).lstrip("/")
        base = (ROOT / rel).resolve()
        if ROOT not in base.parents and base != ROOT:
            return None
        for candidate in (base, base / "index.html", base.with_suffix(".html")):
            if candidate.is_file():
                return candidate
        return None

    def send_file(self, target: Path, status: int = 200):
        data = target.read_bytes()
        ctype = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype in ("application/xml", "application/javascript"):
            ctype += "; charset=utf-8"
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    def do_GET(self):
        target = self.resolve(self.path)
        if target:
            return self.send_file(target)
        fallback = ROOT / "404.html"
        if fallback.is_file():
            return self.send_file(fallback, status=404)
        self.send_error(404)

    do_HEAD = do_GET


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


with Server(("127.0.0.1", PORT), Handler) as httpd:
    print(f"serving {ROOT} on http://127.0.0.1:{PORT}", flush=True)
    httpd.serve_forever()
