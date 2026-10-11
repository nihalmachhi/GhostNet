from __future__ import annotations

import socket
import urllib.request

BASE = "http://127.0.0.1"


def visit_http_decoy() -> None:
    """Exercise only the local GhostNet web decoy with harmless synthetic input."""
    for path in ("/", "/recover", "/token/demo-canary"):
        try:
            with urllib.request.urlopen(BASE + ":8081" + path, timeout=1) as response:
                print(path, response.status)
        except OSError as exc:
            print(path, "unavailable:", exc)


def visit_line_decoys() -> None:
    """Send benign protocol greetings to loopback-only toy services."""
    for port, payload in ((2222, b"demo\ndemo-password\n"), (5433, b"SELECT demo;\n")):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1) as stream:
                stream.settimeout(1)
                print(port, stream.recv(256).decode("utf-8", "replace").strip())
                stream.sendall(payload)
                print(port, stream.recv(256).decode("utf-8", "replace").strip())
        except OSError as exc:
            print(port, "unavailable:", exc)


if __name__ == "__main__":
    visit_http_decoy()
    visit_line_decoys()
