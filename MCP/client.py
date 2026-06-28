import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    params = StdioServerParameters(command="python3", args=["math_server.py"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            r1 = await session.call_tool("add", {"a": 4, "b": 6})
            v = int(r1.content[0].text) if r1.content else 0
            r2 = await session.call_tool("multiply", {"a": v, "b": 14})
            print(r2.content[0].text if r2.content else None)

if __name__ == "__main__":
    asyncio.run(main())
