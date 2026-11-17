"""MCP server tests: driven through the protocol by an SDK client."""

from __future__ import annotations

import asyncio

import pytest
from fastmcp import Client
from pydantic import BaseModel


class ToolSchema(BaseModel):
    """The parts of a tool's JSON Schema worth asserting on."""

    properties: dict[str, object]
    required: list[str]


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
