"""Test MCP client connection to ticktick server"""
import asyncio
import sys
sys.path.insert(0, 'D:/program/ticktick-ai-demo')

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_mcp():
    params = StdioServerParameters(
        command="python",
        args=["D:/program/ticktick-ai-demo/server.py"],
        env=None
    )
    
    print("Connecting to MCP server...", file=sys.stderr)
    
    try:
        async with stdio_client(params) as (read, write):
            print("Creating session...", file=sys.stderr)
            async with ClientSession(read, write) as session:
                print("Initializing...", file=sys.stderr)
                await session.initialize()
                
                print("Listing tools...", file=sys.stderr)
                tools = await session.list_tools()
                print(f"Found {len(tools.tools)} tools:", file=sys.stderr)
                for t in tools.tools:
                    print(f"  - {t.name}: {t.description}", file=sys.stderr)
                
                # Test calling get_tasks
                print("Calling get_tasks...", file=sys.stderr)
                result = await session.call_tool("get_tasks", {})
                print(f"Result: {result}", file=sys.stderr)
                
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_mcp())
