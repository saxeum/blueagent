import os
import sys
from importlib.metadata import version
from typing import Annotated

from fastmcp import FastMCP
from mcp_types import ToolAnnotations
from pydantic import BaseModel, StringConstraints

# The schema is the only thing an agent sees, so the limits live there: min/max
# length are visible as minLength/maxLength, and `pattern` says the name must
# contain a non-space character. Stripping first makes "  Ada  " usable rather
# than a validation failure an agent cannot explain.
Name = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=80, pattern=r"\S"),
]

INSTRUCTIONS = """
Greets people by name. There is one tool, `greet`: pass the person's name and it
returns a message string. Nothing is persisted and nothing else is exposed.
"""

mcp = FastMCP("greetmcp", version=version("greetmcp"), instructions=INSTRUCTIONS)


class Greeting(BaseModel):
    """What `greet` returns."""

    message: str


@mcp.tool(
    annotations=ToolAnnotations(
        title="Greet someone",
        read_only_hint=True,
        open_world_hint=False,
    )
)
def greet(name: Name) -> Greeting:
    """Greet someone by name."""
    return Greeting(message=f"Hello, {name}!")


def serve(transport: str = "http", port: int = 8000) -> None:
    """Serve over streamable HTTP, or over stdio for an agent that spawns us."""
    if transport == "stdio":
        mcp.run(transport="stdio")
        return
    mcp.run(transport="http", port=port)


def main(argv: list[str] | None = None) -> None:
    """`--stdio` serves stdio; otherwise HTTP on MCP_PORT. Nothing else is accepted."""
    args = sys.argv[1:] if argv is None else argv
    unknown = [arg for arg in args if arg != "--stdio"]
    if unknown:
        raise SystemExit(f"unknown arguments: {' '.join(unknown)}; the only flag is --stdio (port comes from MCP_PORT)")
    serve("stdio" if "--stdio" in args else "http", int(os.environ.get("MCP_PORT", "8000")))


if __name__ == "__main__":
    main()
