"""Shared fixtures: a real MCP server process on a free port."""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from collections.abc import Iterator

import pytest
from pydantic import TypeAdapter


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        # getsockname() is Any in the stubs; validate it into an int at the boundary.
        return TypeAdapter(int).validate_python(sock.getsockname()[1])


def listening(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex(("127.0.0.1", port)) == 0


@pytest.fixture(scope="module")
def server_url() -> Iterator[str]:
    port = free_port()
    proc = subprocess.Popen(
        [sys.executable, "-m", "greetmcp.server"],
        env={**os.environ, "MCP_PORT": str(port)},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )
    deadline = time.monotonic() + 30
    while not listening(port):
        if proc.poll() is not None:
            pytest.fail(f"server exited before listening on {port}")
        if time.monotonic() > deadline:
            proc.kill()
            pytest.fail(f"server did not listen on {port} within 30s")
        time.sleep(0.05)
    yield f"http://127.0.0.1:{port}/mcp"
    proc.terminate()
    _ = proc.wait(timeout=10)
