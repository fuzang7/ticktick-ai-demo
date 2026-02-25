import sys, json, asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.server import InitializationOptions
from mcp.types import Tool, TextContent

async def main():
    server = Server("test-server")

    @server.list_tools()
    async def list_tools():
        return [
            Tool(name="echo", description="Echo back the input", inputSchema={"type": "object", "properties": {"message": {"type": "string"}}})
        ]

    @server.call_tool()
    async def call_tool(name, arguments):
        return [TextContent(type="text", text=f"Echo: {arguments.get('message', '')}")]

    async with stdio_server() as (read, write):
        await server.run(read, write, InitializationOptions("test-server", "1.0.0", {}))

if __name__ == "__main__":
    asyncio.run(main())
