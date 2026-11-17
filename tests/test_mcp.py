"""MCP server tests: driven through the protocol by an SDK client."""

from __future__ import annotations

import asyncio
from importlib.metadata import version

import pytest
from fastmcp import Client
from pydantic import BaseModel


class ToolSchema(BaseModel):
    """The parts of a tool's JSON Schema worth asserting on."""

    properties: dict[str, object]
    required: list[str]


def test_initialize_reports_this_servers_identity(server_url: str) -> None:
    """Not the FastMCP library version, which is what a default server reports."""

    async def check() -> None:
        async with Client(server_url) as client:
            # This client negotiates the modern `server/discover` era, where there
            # is no InitializeResult; the metadata lives on the client itself.
            info = client.server_info
            assert info is not None
            assert info.name == "greetmcp"
            assert info.version == version("greetmcp")

    asyncio.run(check())


def test_initialize_advertises_instructions(server_url: str) -> None:
    """An agent that only sees schemas needs to be told what the server is for."""

    async def check() -> None:
        async with Client(server_url) as client:
            instructions = client.instructions
            assert instructions is not None
            assert "greet" in instructions
            assert "name" in instructions

    asyncio.run(check())


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
