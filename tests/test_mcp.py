"""MCP tests: a real server process, driven through the protocol by an SDK client."""

from __future__ import annotations

import asyncio
import os
import socket
import subprocess
import sys
import time
from collections.abc import Iterator

import pytest
from fastmcp import Client
from pydantic import BaseModel, TypeAdapter


class ToolSchema(BaseModel):
    """The parts of a tool's JSON Schema worth asserting on."""

    properties: dict[str, object]
    required: list[str]


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
        [sys.executable, "-m", "newmcp.my_server"],
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


def test_tools_list_exposes_greet(server_url: str) -> None:
    async def check() -> None:
        async with Client(server_url) as client:
            tools = {tool.name: tool for tool in await client.list_tools()}
            assert "greet" in tools
            greet = tools["greet"]
            assert greet.description == "Greet someone by name."
            assert greet.input_schema["required"] == ["name"]
            schema = ToolSchema.model_validate(greet.output_schema)
            assert set(schema.properties) == {"message"}
            assert schema.required == ["message"]
            # Model output, not FastMCP's {"result": ...} wrapper around a bare str.
            assert "x-fastmcp-wrap-result" not in (greet.output_schema or {})

    asyncio.run(check())


@pytest.mark.parametrize(("name", "expected"), [("Ada", "Hello, Ada!"), ("Grace", "Hello, Grace!")])
def test_call_greet(server_url: str, name: str, expected: str) -> None:
    async def check() -> None:
        async with Client(server_url) as client:
            result = await client.call_tool("greet", {"name": name})
            assert result.is_error is False
            assert result.structured_content == {"message": expected}

    asyncio.run(check())


def test_unknown_tool_is_an_error(server_url: str) -> None:
    """Proves a passing call above is not simply 'any 200 counts'."""

    async def check() -> None:
        async with Client(server_url) as client:
            result = await client.call_tool("nope", {"name": "Ada"}, raise_on_error=False)
            assert result.is_error is True

    asyncio.run(check())
