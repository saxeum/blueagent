"""MCP server tests: driven through the protocol by an SDK client."""

from __future__ import annotations

import asyncio
from importlib.metadata import version

import pytest
from fastmcp import Client
from mcp_types import TextContent
from pydantic import BaseModel, Field


class ToolSchema(BaseModel):
    """The parts of a tool's JSON Schema worth asserting on."""

    properties: dict[str, object]
    required: list[str]


class StringSchema(BaseModel):
    """A constrained string property as JSON Schema spells it.

    The aliases are required, not defaulted: a schema that lost its constraints
    should fail validation here rather than assert against zeros.
    """

    type: str
    min_length: int = Field(alias="minLength")
    max_length: int = Field(alias="maxLength")
    pattern: str = ""


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


def test_greet_declares_read_only_annotations(server_url: str) -> None:
    """Hosts gate auto-approval on these hints; undeclared means 'treat as risky'."""

    async def check() -> None:
        async with Client(server_url) as client:
            tools = {tool.name: tool for tool in await client.list_tools()}
            annotations = tools["greet"].annotations
            assert annotations is not None
            assert annotations.read_only_hint is True
            assert annotations.open_world_hint is False
            assert annotations.destructive_hint is not True

    asyncio.run(check())


@pytest.mark.parametrize(
    ("name", "reason"),
    [("", "at least 1 character"), ("x" * 81, "at most 80 characters"), ("   ", "validation")],
)
def test_name_constraints_are_enforced(server_url: str, name: str, reason: str) -> None:
    """The limits are in the schema, so a bad name fails validation with a reason."""

    async def check() -> None:
        async with Client(server_url) as client:
            result = await client.call_tool("greet", {"name": name}, raise_on_error=False)
            assert result.is_error is True
            block = result.content[0]
            assert isinstance(block, TextContent)
            text = block.text.lower()
            assert reason in text or "validation error" in text

    asyncio.run(check())


def test_name_constraints_appear_in_the_schema(server_url: str) -> None:
    async def check() -> None:
        async with Client(server_url) as client:
            tools = {tool.name: tool for tool in await client.list_tools()}
            properties = ToolSchema.model_validate(tools["greet"].input_schema).properties
            schema = StringSchema.model_validate(properties["name"])
            assert schema.min_length == 1
            assert schema.max_length == 80
            assert schema.pattern

    asyncio.run(check())


def test_surrounding_whitespace_is_trimmed(server_url: str) -> None:
    async def check() -> None:
        async with Client(server_url) as client:
            result = await client.call_tool("greet", {"name": "  Ada  "})
            assert result.structured_content == {"message": "Hello, Ada!"}

    asyncio.run(check())


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Ada", "Hello, Ada!"),
        ("Grace", "Hello, Grace!"),
        # Multi-word, hyphenated and accented names must pass the schema's pattern:
        # it means "contains a non-space character", not "is a single token".
        ("George Treacy", "Hello, George Treacy!"),
        ("Mary Jane Watson-Parker", "Hello, Mary Jane Watson-Parker!"),
        ("José Álvarez", "Hello, José Álvarez!"),
    ],
)
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
