import asyncio
from fastmcp import Client

client = Client("http://127.0.0.1:8000/mcp")


async def call_tool(name: str):
    async with client:
        result = await client.call_tool("add", {"a": 40, "b": 2})
        print(result)


asyncio.run(call_tool("Ford"))
