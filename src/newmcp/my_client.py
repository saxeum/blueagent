import asyncio

from fastmcp import Client
from pydantic import BaseModel

URL = "http://127.0.0.1:8000/mcp"


class ToolInputSchema(BaseModel):
    """The part of a tool's JSON Schema this client reads.

    The wire type is dict[str, Any] because JSON Schema cannot be typed
    statically; validating it here turns that boundary into a checked one.
    """

    properties: dict[str, object] = {}


class GreetResult(BaseModel):
    """Shape of what `greet` returns."""

    result: str


async def main(url: str = URL) -> None:
    async with Client(url) as client:
        for tool in await client.list_tools():
            schema = ToolInputSchema.model_validate(tool.input_schema)
            print(f"{tool.name}({', '.join(schema.properties)}): {tool.description}")

        result = await client.call_tool("greet", {"name": "George"})
        print(GreetResult.model_validate(result.structured_content).result)


if __name__ == "__main__":
    asyncio.run(main())
