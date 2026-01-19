import asyncio
from fastmcp import Client 

client = Client("http://localhost:8000/mcp")

async def tool_greet(name: str):
    async with client:
      result = await client.call_tool("greet", {"name": name})
      print(result)

asyncio.run(tool_greet("Saw"))