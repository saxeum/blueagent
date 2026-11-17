"""Minimal pydantic-ai agent that calls the `greet` tool over MCP.

`make agent` needs no running server: with `MCP_URL` unset it spawns
`python -m greetmcp.server --stdio` itself. Set `MCP_URL` to talk to a server
someone else started (`make mcp`) over HTTP instead. The model is DeepSeek by
default, read the same way pydantic-ai reads it — `DEEPSEEK_API_KEY` in the
environment, or in a local `.env`.
"""

from __future__ import annotations

import asyncio
import os
import sys

from dotenv import load_dotenv
from fastmcp.client.transports import StdioTransport
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPToolset
from pydantic_ai.models import Model

# Set MCP_URL to talk to a server someone else is running over HTTP; leave it
# unset and the agent spawns the server itself over stdio, which is the transport
# an agent host uses.
URL = os.environ.get("MCP_URL")
STDIO = StdioTransport(command=sys.executable, args=["-m", "greetmcp.server", "--stdio"])
MODEL = os.environ.get("AGENT_MODEL", "deepseek:deepseek-flash")
PROMPT = "Use the greet tool to greet Ada, then reply with what the tool returned."


def build_agent(model: Model | str = MODEL, url: str | None = URL) -> Agent[None, str]:
    """Agent with the MCP server's tools attached.

    A url means HTTP to that endpoint; no url means spawn the server over stdio.
    """
    toolset = MCPToolset(url) if url else MCPToolset(STDIO)
    return Agent(model, toolsets=[toolset])


async def ask(prompt: str) -> str:
    result = await build_agent().run(prompt)
    return result.output


def main() -> None:
    _ = load_dotenv()
    print(asyncio.run(ask(PROMPT)))


if __name__ == "__main__":
    main()
