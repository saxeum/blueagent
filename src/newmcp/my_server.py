from fastmcp import FastMCP

mcp = FastMCP("My MCP Server")


@mcp.tool(app=True)
def greet(name: str) -> str:
    """Greet someone by name."""
    return f"Hello, {name}!"


if __name__ == "__main__":
    mcp.run(transport="http", port=8000)
