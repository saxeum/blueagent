"""The example config, exercised the way a host would: a pydantic-ai agent built
from each entry, calling `greet` through it.

`.mcp.json.example` claims an external host can connect. These tests make that
claim checkable, so an edit to the command or to the `/mcp` path fails here
rather than at somebody's first connection.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from fastmcp.client.transports import StdioTransport
from pydantic import BaseModel, Field
from pydantic_ai import Agent, AgentRunResult
from pydantic_ai.mcp import MCPToolset
from pydantic_ai.messages import ModelResponse, ToolCallPart
from pydantic_ai.models.test import TestModel

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / ".mcp.json.example"
PLACEHOLDER = "/absolute/path/to/blueagent"


class StdioEntry(BaseModel):
    """A host spawns this; `uv` resolves the workspace from `--directory`."""

    command: str
    args: list[str]


class HttpEntry(BaseModel):
    type: str
    url: str


class Entries(BaseModel):
    http: HttpEntry = Field(alias="greetmcp-http")
    stdio: StdioEntry = Field(alias="greetmcp-stdio")


class Config(BaseModel):
    servers: Entries = Field(alias="mcpServers")


def load() -> Config:
    """Validating, not just parsing: a missing or renamed entry fails here."""
    return Config.model_validate_json(EXAMPLE.read_text(encoding="utf-8"))


def tool_names(result: AgentRunResult[str]) -> list[str]:
    return [
        part.tool_name
        for message in result.all_messages()
        if isinstance(message, ModelResponse)
        for part in message.parts
        if isinstance(part, ToolCallPart)
    ]


async def greet_through(toolset: MCPToolset[object]) -> AgentRunResult[str]:
    # `object`, not `None`: pydantic-ai's constructor defaults `deps_type` to
    # `object`, so a `MCPToolset[None]` parameter is rejected as a mismatch.
    return await Agent(TestModel(), toolsets=[toolset]).run("greet someone")


def test_example_declares_what_a_host_needs() -> None:
    config = load().servers

    assert config.stdio.command == "uv"
    assert PLACEHOLDER in config.stdio.args
    assert "--package" in config.stdio.args
    assert config.stdio.args[-1] == "--stdio"
    # The non-obvious half: FastMCP serves streamable HTTP under /mcp, so a base
    # URL without the path looks right and connects nowhere.
    assert urlsplit(config.http.url).path == "/mcp"
    assert config.http.type == "http"


def test_stdio_entry_lets_a_pydantic_ai_agent_call_greet(tmp_path: Path) -> None:
    entry = load().servers.stdio
    args = [str(ROOT) if arg == PLACEHOLDER else arg for arg in entry.args]

    async def check() -> None:
        # A host spawns from its own cwd, not this checkout, so do the same: the
        # entry has to carry `--directory` for `uv` to find the workspace.
        transport = StdioTransport(command=entry.command, args=args, cwd=str(tmp_path))
        result = await greet_through(MCPToolset(transport))
        assert tool_names(result) == ["greet"]
        assert "Hello," in result.output

    asyncio.run(check())


def test_http_entry_lets_a_pydantic_ai_agent_call_greet(server_url: str) -> None:
    """The live fixture supplies host and port; the path under test is the example's."""

    configured = urlsplit(load().servers.http.url)
    live = urlsplit(server_url)
    url = urlunsplit((live.scheme, live.netloc, configured.path, "", ""))

    async def check() -> None:
        result = await greet_through(MCPToolset(url))
        assert tool_names(result) == ["greet"]
        assert "Hello," in result.output

    asyncio.run(check())
