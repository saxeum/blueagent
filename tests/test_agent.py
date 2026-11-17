"""Agent tests: pydantic-ai driving the real MCP server, with no API key.

`TestModel` calls every exposed tool once, so this proves the chain
agent -> MCPToolset -> greet -> result without any provider being reachable.
"""

from __future__ import annotations

import asyncio

from pydantic_ai import AgentRunResult
from pydantic_ai.messages import ModelResponse, ToolCallPart
from pydantic_ai.models.test import TestModel

from blueagent.agent import build_agent


def tool_names(result: AgentRunResult[str]) -> list[str]:
    return [
        part.tool_name
        for message in result.all_messages()
        if isinstance(message, ModelResponse)
        for part in message.parts
        if isinstance(part, ToolCallPart)
    ]


def test_agent_calls_greet_over_mcp(server_url: str) -> None:
    async def check() -> None:
        agent = build_agent(model=TestModel(), url=server_url)
        result = await agent.run("greet someone")
        assert tool_names(result) == ["greet"]
        assert "Hello," in result.output

    asyncio.run(check())


def test_agent_spawns_the_server_over_stdio_when_no_url_is_given() -> None:
    """The default path: no running server, no port, the agent starts its own."""

    async def check() -> None:
        agent = build_agent(model=TestModel(), url=None)
        result = await agent.run("greet someone")
        assert tool_names(result) == ["greet"]
        assert "Hello," in result.output

    asyncio.run(check())


def test_agent_exposes_no_tools_but_the_server_has(server_url: str) -> None:
    """The agent's toolset is the server's, nothing invented locally."""

    async def check() -> None:
        agent = build_agent(model=TestModel(), url=server_url)
        result = await agent.run("something unrelated")
        assert set(tool_names(result)) == {"greet"}

    asyncio.run(check())
