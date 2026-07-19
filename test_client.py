"""
Generic MCP smoke-test client — transport-agnostic.

This is the single source of truth for "is my SERVER working?", independent of any
GUI client (n8n, Copilot Studio, Goose, ...). If this passes but a client fails, the
problem is that client's config, not the server.

Usage:
    # stdio (default): spawns the server as a subprocess
    venv/bin/python test_client.py

    # streamable-http: connect to an already-running HTTP server
    #   (start it first with:  MCP_TRANSPORT=streamable-http venv/bin/python src/mcp_server/main.py)
    venv/bin/python test_client.py --http http://127.0.0.1:9000/mcp

It connects, lists every tool the server exposes, then calls one tool and prints the result.
Works no matter how many tools settings.json grows to — it never hardcodes tool names.
"""

import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client


async def exercise(session: ClientSession) -> None:
    await session.initialize()
    print("Connected. Handshake OK.\n")

    tools = (await session.list_tools()).tools
    print(f"Server exposes {len(tools)} tool(s):")
    for t in tools:
        print(f"  - {t.name}: {t.description}")

    if not tools:
        print("\nNo tools registered — check config/settings.json.")
        return

    # Call the first tool as a live end-to-end check.
    first = tools[0].name
    print(f"\nCalling '{first}' ...")
    result = await session.call_tool(first, arguments={})
    for block in result.content:
        text = getattr(block, "text", block)
        print(f"  -> {text}")


async def main() -> None:
    if "--http" in sys.argv:
        url = sys.argv[sys.argv.index("--http") + 1]
        print(f"Transport: streamable-http  ({url})")
        async with streamablehttp_client(url) as (read, write, _):
            async with ClientSession(read, write) as session:
                await exercise(session)
    else:
        print("Transport: stdio  (spawning src/mcp_server/main.py)")
        params = StdioServerParameters(command=sys.executable, args=["src/mcp_server/main.py"])
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await exercise(session)


if __name__ == "__main__":
    asyncio.run(main())
