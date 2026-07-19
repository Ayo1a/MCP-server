import inspect
import json
import os
from pathlib import Path

import httpx  # library for building http requests in py
from mcp.server.fastmcp import FastMCP  # framework for MCP servers

# Maps the "type" strings used in settings.json to real Python types, so a tool's
# parameters get proper JSON-Schema types advertised to the client.
TYPE_MAP = {"string": str, "integer": int, "number": float, "boolean": bool}

# Path to the config file that defines the server name and every tool it exposes.
# __file__ is src/mcp_server/main.py, so we go up 2 levels to reach the project root, then into config/.
CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "settings.json"


def load_config() -> dict:
    # Reads settings.json once at startup and parses it into a Python dict.
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


async def call_endpoint(method: str, url: str, query: dict | None = None, body: dict | None = None) -> str:
    """
    Generic HTTP handler shared by every tool. Sends `method` to `url` with optional
    query string / JSON body, and turns the response into text the LLM can read.
    Handles error statuses (404/503/...) by RETURNING the error as text, so the model
    can react to it instead of the tool call crashing.
    """
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            response = await client.request(method, url, params=query or None, json=body or None)
            response.raise_for_status()        # raises if status is 4xx/5xx
            data = response.json()             # parse JSON body
        except httpx.HTTPStatusError as e:
            # The server answered with an error status — surface it (e.g. "not found").
            return f"HTTP {e.response.status_code} from {url}: {e.response.text}"
        except httpx.HTTPError as e:
            # Network/timeout failure — return the error as text instead of crashing.
            return f"Error communicating with Core API: {str(e)}"

    # Endpoints with a ready-to-read "content" field (like the text report / joke) return it raw.
    if isinstance(data, dict) and "content" in data:
        return data["content"]

    # Everything else (nested objects, lists, numbers) is returned as pretty JSON so the
    # model sees the full structure regardless of shape.
    return json.dumps(data, indent=2, ensure_ascii=False)


def make_tool(tool_config: dict):
    """
    Factory that builds one tool function from its settings.json entry. It supports:
      - "method": GET (default) / POST / ...
      - "endpoint_url": may contain {placeholders} filled from path params
      - "params": [ {name, type, required, in: path|query|body}, ... ]
    The built function is given a real signature matching the params, so FastMCP
    advertises them to clients as a proper input schema — no per-tool Python needed.
    """
    method = tool_config.get("method", "GET").upper()
    url_template = tool_config["endpoint_url"]
    # Let the Core API live at a different address without editing settings.json — e.g. in Docker
    # the backend is another container. If CORE_API_BASE_URL is set, swap the internal origin for it.
    core_base = os.getenv("CORE_API_BASE_URL")
    if core_base:
        url_template = url_template.replace("http://127.0.0.1:8000", core_base.rstrip("/"))
    params = tool_config.get("params", [])

    async def tool_fn(**kwargs) -> str:
        # Sort the incoming arguments into where they belong in the HTTP request.
        path_vals, query, body = {}, {}, {}
        for p in params:
            name = p["name"]
            if name not in kwargs or kwargs[name] is None:
                continue  # optional param the caller omitted
            where = p.get("in", "query")
            if where == "path":
                path_vals[name] = kwargs[name]
            elif where == "body":
                body[name] = kwargs[name]
            else:
                query[name] = kwargs[name]
        url = url_template.format(**path_vals)  # fill {placeholders}
        return await call_endpoint(method, url, query=query, body=body)

    # Give tool_fn a signature derived from `params` so the schema advertises them.
    sig_params, annotations = [], {}
    for p in params:
        ann = TYPE_MAP.get(p.get("type", "string"), str)
        required = p.get("required", False)
        default = inspect.Parameter.empty if required else None
        annotations[p["name"]] = ann if required else (ann | None)
        sig_params.append(
            inspect.Parameter(p["name"], inspect.Parameter.KEYWORD_ONLY, annotation=annotations[p["name"]], default=default)
        )
    tool_fn.__signature__ = inspect.Signature(sig_params)
    tool_fn.__annotations__ = {**annotations, "return": str}
    return tool_fn


# Load the config once at import time.
config = load_config()

# The server's display name (what the AI/client sees) now comes from settings.json
# instead of being a hardcoded string.
#
# host/port only matter for the HTTP transports (streamable-http / sse); they are ignored
# for stdio. Port defaults to 9000 — NOT 8000, which the mock Core API already owns.
# Override with env vars so the SAME server file can serve every client without code edits.
mcp = FastMCP(
    config["server_name"],
    host=os.getenv("MCP_HOST", "127.0.0.1"),
    port=int(os.getenv("MCP_PORT", "9000")),
)

# Register one MCP tool per entry in settings.json — no hardcoded functions needed.
# To add a new tool in the future: just add an entry to settings.json, no code changes here.
for tool_config in config["tools"]:
    fn = make_tool(tool_config)
    # In this FastMCP version, tool() only works as a decorator factory —
    # it must be called first (with name/description) and then applied to fn.
    mcp.tool(name=tool_config["name"], description=tool_config["description"])(fn)

if __name__ == "__main__":
    # Transport is chosen at launch by the MCP_TRANSPORT env var. One server, every client:
    #   stdio           -> local clients that spawn the server as a subprocess
    #                      (Claude Desktop, MCP Inspector, Goose, LibreChat, Gemini CLI, LlamaIndex)
    #   streamable-http  -> URL-based clients: http://<host>:<port>/mcp
    #                      (n8n, Copilot Studio, and everything above, over the network)
    #   sse              -> legacy URL-based clients only: http://<host>:<port>/sse
    # Default is stdio, so existing local setups keep working with no change.
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    mcp.run(transport=transport)
