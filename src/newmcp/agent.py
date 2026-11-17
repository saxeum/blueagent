"""Minimal pydantic-ai agent that calls the `greet` tool over MCP.

`make agent` starts nothing itself: run the MCP server (`make mcp`) first, then
this. The model is DeepSeek by default, read the same way pydantic-ai reads it —
`DEEPSEEK_API_KEY` in the environment, or in a local `.env`.
"""

from __future__ import annotations

import asyncio
import os

from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPToolset
from pydantic_ai.models import Model

URL = os.environ.get("MCP_URL", "http://127.0.0.1:8000/mcp")
MODEL = os.environ.get("AGENT_MODEL", "deepseek:deepseek-flash")
PROMPT = "Use the greet tool to greet Ada, then reply with what the tool returned."


def build_agent(model: Model | str = MODEL, url: str = URL) -> Agent[None, str]:
    """Agent with the MCP server's tools attached; the transport follows the URL."""
    return Agent(model, toolsets=[MCPToolset(url)])


async def ask(prompt: str) -> str:
    result = await build_agent().run(prompt)
    return result.output


def main() -> None:
    _ = load_dotenv()
    print(asyncio.run(ask(PROMPT)))


if __name__ == "__main__":
    main()
