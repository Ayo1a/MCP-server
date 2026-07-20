# Client Setup: n8n

How to connect n8n to this project's MCP server over HTTP, and what to do if you need to repeat this on a new machine.

Unlike Claude Desktop (which spawns the server itself over stdio), n8n is a networked client — it connects to the server over HTTP instead. This required one small server-side change plus a few steps inside n8n.

## 1. Server-side change: enable HTTP transport

`src/mcp_server/main.py` now reads its transport from the `MCP_TRANSPORT` env var, defaulting to `stdio` (so Claude Desktop / MCP Inspector are unaffected):

```python
mcp = FastMCP(
    config["server_name"],
    host=os.getenv("MCP_HOST", "127.0.0.1"),
    port=int(os.getenv("MCP_PORT", "9000")),  # 9000, not 8000 — core_api_mock owns 8000
)
...
if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    mcp.run(transport=transport)
```

`settings.json` still defines every tool exactly as before — this change only adds a second way to *reach* the same server, it doesn't change what it exposes.

## 2. Run three processes, each in its own terminal

**Terminal 1 — mock backend:**
```
venv\Scripts\activate
uvicorn src.core_api_mock.main:app --reload
```

**Terminal 2 — MCP server, in HTTP mode** (PowerShell — env vars need their own line, unlike bash):
```powershell
venv\Scripts\activate
$env:MCP_TRANSPORT = "streamable-http"
venv\Scripts\python.exe src\mcp_server\main.py
```
Confirm it logs something like `Uvicorn running on http://127.0.0.1:9000` — the actual MCP endpoint is `http://127.0.0.1:9000/mcp`.

**Terminal 3 — n8n:**
```
npx n8n
```
First run downloads n8n (a minute or two). Once it prints a ready message with `http://localhost:5678`, open that URL in a browser and complete the one-time owner account setup if this is your first run.

## 3. Set up the connection inside n8n

1. Click **"Add workflow"** to start a new, blank workflow.
2. Click **+** to add a node, search **"MCP"**. Two options appear:
   - **MCP Client** — n8n connects *to* an MCP server. This is what we want.
   - **MCP Server Trigger** — the opposite direction (n8n *becomes* an MCP server). Not used here.
3. Add **MCP Client** to the canvas.
4. In its settings:
   - **Server URL / Endpoint**: `http://127.0.0.1:9000/mcp`
   - **Transport / Connection type**: **HTTP Streamable** (not SSE) — must match `MCP_TRANSPORT=streamable-http` on the server side.
   - **Authentication**: None — the server has no auth configured.
   - **Operation**: Execute Tool.
   - **Tool**: "From list" → click **Choose...** — this fetches the live tool list straight from `config/settings.json` over the connection. You should see all tools currently defined there (as of writing: `fetch_system_text_report`, `fetch_system_image_metadata`, `check_core_api_health`).
5. Select a tool (e.g. `check_core_api_health`) and run just that node (its own "Execute step"/play button — no trigger or full workflow run needed).
6. Check the node's output panel — a successful result (e.g. `message: Internal Core API Mock is running successfully!`) confirms the full path works: n8n → `mcp_server` (HTTP) → `core_api_mock`.

No AI Agent, LLM credential, or chat setup is needed for this — the MCP Client node calls a tool directly, like a typed remote-procedure call.

## 4. Using the returned data in a workflow

The MCP Client node's output becomes the input of whatever node you connect after it, exactly like any other n8n node. General shape:

```
Trigger → MCP Client (call a tool) → [do something with the result]
```

- **Transform it**: `Edit Fields` (Set) or `Code` node to reshape/extract parts of the result.
- **Branch on it**: an `IF` node — e.g. "if the health check result contains 'success', continue; otherwise alert."
- **Send it somewhere**: `Send Email`, `Slack`, `Google Sheets`, `HTTP Request`, etc. — reference the tool's output via an expression, e.g. `{{ $json.result }}` (check the node's actual output panel for the exact field name).
- **Automate it**: swap the `Manual Trigger` used above for a `Schedule Trigger` (poll periodically) or `Webhook Trigger` (run on demand from an external call).

This is plain automation — no AI Agent required. An AI Agent + LLM is only needed if you want a model to *decide which tool to call* from free text; for fixed, known workflows (e.g. "check health every 5 minutes"), wiring the MCP Client node directly into the rest of the workflow, as above, is enough.

## Where the data protection guarantee holds

n8n never talks to `core_api_mock` (port `8000`) directly — it only ever reaches `mcp_server` (port `9000`), which is the only thing that calls `core_api_mock`. `config/settings.json` is still the single source of truth for what's exposed, exactly as with Claude Desktop.
