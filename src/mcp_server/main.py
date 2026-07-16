import json
from pathlib import Path

import httpx  # library for building http requests in py
from mcp.server.fastmcp import FastMCP  # framework for MCP servers

# Path to the config file that defines the server name and every tool it exposes.
# __file__ is src/mcp_server/main.py, so we go up 2 levels to reach the project root, then into config/.
CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "settings.json"


def load_config() -> dict:
    # Reads settings.json once at startup and parses it into a Python dict.
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


async def call_endpoint(url: str) -> str:
    """
    Generic handler shared by every tool: calls the given Core API endpoint
    and turns the JSON response into plain text the LLM can read.
    This replaces the two separate hand-written tool bodies from before.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)  # GET request to the core_api_mock endpoint
            response.raise_for_status()        # raises if status is 4xx/5xx
            data = response.json()             # parse JSON body into a dict
        except httpx.HTTPError as e:
            # network/HTTP failure — return the error as text instead of crashing the server
            return f"Error communicating with Core API: {str(e)}"

    # Some endpoints (like the text report) already have a ready-to-read "content" field.
    if "content" in data:
        return data["content"]

    # Otherwise (like the image metadata), just print every field as "key: value" lines.
    return "\n".join(f"{key}: {value}" for key, value in data.items())


def make_tool(endpoint_url: str):
    """
    Factory that builds a small tool function bound to one specific endpoint_url.
    We need this because the loop below creates several tools, and each one has
    to remember its own URL (a closure) rather than sharing a single variable.
    """
    async def tool_fn() -> str:
        return await call_endpoint(endpoint_url)
    return tool_fn


# Load the config once at import time.
config = load_config()

# The server's display name (what the AI/client sees) now comes from settings.json
# instead of being a hardcoded string.
mcp = FastMCP(config["server_name"])

# Register one MCP tool per entry in settings.json — no hardcoded functions needed.
# To add a new tool in the future: just add an entry to settings.json, no code changes here.
for tool_config in config["tools"]:
    fn = make_tool(tool_config["endpoint_url"])
    # In this FastMCP version, tool() only works as a decorator factory —
    # it must be called first (with name/description) and then applied to fn.
    mcp.tool(name=tool_config["name"], description=tool_config["description"])(fn)

if __name__ == "__main__":
    # Run using the standard MCP protocol over stdio (what Claude/the Inspector connect to).
    mcp.run(transport="stdio")
