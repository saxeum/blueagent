import os
from importlib.metadata import version

from fastmcp import FastMCP
from pydantic import BaseModel

INSTRUCTIONS = """
Greets people by name. There is one tool, `greet`: pass the person's name and it
returns a message string. Nothing is persisted and nothing else is exposed.
"""

mcp = FastMCP("greetmcp", version=version("greetmcp"), instructions=INSTRUCTIONS)


class Greeting(BaseModel):
    """What `greet` returns."""

    message: str


@mcp.tool
def greet(name: str) -> Greeting:
    """Greet someone by name."""
    return Greeting(message=f"Hello, {name}!")


def serve(port: int = 8000) -> None:
    """Run the server over streamable HTTP on `port`."""
    mcp.run(transport="http", port=port)


if __name__ == "__main__":
    serve(int(os.environ.get("MCP_PORT", "8000")))
