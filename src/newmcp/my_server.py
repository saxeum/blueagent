import os

from fastmcp import FastMCP
from pydantic import BaseModel

mcp = FastMCP("My MCP Server")


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
