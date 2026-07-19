# Connecting this MCP server to any client

This server is **one file** (`src/mcp_server/main.py`) that speaks three transports. You never
fork it per client — you just launch it in the right mode and hand the client either a **command**
(stdio) or a **URL** (HTTP). Adding new tools is config-only: append an entry to
`config/settings.json`, no code change.

## The one idea that makes everything work

| Transport | Launch | What the client needs | Who uses it |
|---|---|---|---|
| **stdio** | `make run-stdio` | the **command** `venv/bin/python src/mcp_server/main.py` | clients that spawn a local subprocess |
| **Streamable HTTP** | `make run-http` | the **URL** `http://127.0.0.1:9000/mcp` | URL-based clients (n8n, Copilot Studio, …) |
| **SSE** (legacy) | `make run-sse` | the **URL** `http://127.0.0.1:9000/sse` | only old clients that can't do Streamable HTTP |

Chosen by env vars (`MCP_TRANSPORT`, `MCP_PORT`, `MCP_HOST`). Default is stdio, so nothing you
already set up breaks. **Port 9000** is used, not 8000 — the mock Core API owns 8000.

### Which mode does a given client need?

| Client | Use this mode | Can it reach `127.0.0.1`? | Needs a tunnel? |
|---|---|---|---|
| MCP Inspector | either | yes | no |
| Claude Desktop | stdio | yes | no |
| Gemini CLI | stdio (simplest) | yes | no |
| Goose | stdio | yes | no |
| LibreChat | stdio (if self-hosted locally) | yes | no |
| LlamaIndex | stdio or HTTP | yes | no |
| Cursor | stdio or HTTP | yes | no |
| VS Code (Copilot) | stdio or HTTP | yes | no |
| Windsurf | stdio or HTTP | yes | no |
| Cline | stdio or HTTP | yes | no |
| Genspark | Streamable HTTP (URL only) | yes (localhost URL ok) | no |
| **n8n** (built-in node) | **Streamable HTTP** | only if n8n runs locally | if n8n is cloud-hosted |
| **Copilot Studio** | **Streamable HTTP** | **no — it's cloud** | **yes, always** |
| **ChatGPT** | **Streamable HTTP** | **no — public HTTPS only** | **yes, always** |

---

## Always start here (before touching any client)

```bash
# 1. backend the tools call (leave running in its own terminal)
make api                     # mock Core API on http://127.0.0.1:8000

# 2. prove the SERVER works, independent of any client
make test-stdio              # spawns the server over stdio, lists tools, calls one
```
`make test-stdio` is your arbiter: if it prints the 3 tools and a report, the server is fine and
any later failure is a *client config* problem, not the server.

For a visual check, the MCP Inspector works too — and note it must use the **venv python, not `uv`**
(that was the earlier `spawn uv ENOENT` error):

```bash
make inspector-stdio         # = npx @modelcontextprotocol/inspector venv/bin/python src/mcp_server/main.py
```

---

## Exposing localhost to cloud clients (Copilot Studio, hosted n8n)

Cloud clients can't see `127.0.0.1`. Start the HTTP server, then open a public HTTPS tunnel:

```bash
make run-http                # terminal A: server on :9000
make tunnel                  # terminal B: prints https://<random>.trycloudflare.com
```
Give the client `https://<random>.trycloudflare.com/mcp`. (`ngrok http 9000` works too.)

---

## Per-client recipes

> **Config-format cheat sheet** (the JSON keys differ per client and are easy to mix up):
> - **Key for the servers map:** `mcpServers` (Claude Desktop, Cursor, Windsurf, Cline, Gemini CLI) —
>   **except VS Code, which uses `servers` + a required `type` per entry.**
> - **HTTP URL field:** `url` (Cursor, VS Code, Cline) — **except Windsurf, which uses `serverUrl`.**
> - **Cline HTTP** additionally needs `"type": "streamableHttp"` (camelCase, or it 405s).

### 1. Claude Desktop — stdio
Edit `claude_desktop_config.json` (Settings → Developer → Edit Config):
```json
{
  "mcpServers": {
    "generic-system": {
      "command": "/Users/assafspanier/Dropbox/MY_DOC/Teaching/JCE/proj2026.jce.ac.il/MCP-server/venv/bin/python",
      "args": ["/Users/assafspanier/Dropbox/MY_DOC/Teaching/JCE/proj2026.jce.ac.il/MCP-server/src/mcp_server/main.py"]
    }
  }
}
```
Restart Claude Desktop. Use **absolute paths** — it doesn't inherit your shell PATH.

### 2. Gemini CLI — stdio (or HTTP)
`gemini mcp add generic-system venv/bin/python src/mcp_server/main.py`, or edit
`~/.gemini/settings.json`:
```json
{
  "mcpServers": {
    "generic-system": {
      "command": "venv/bin/python",
      "args": ["src/mcp_server/main.py"],
      "cwd": "/Users/assafspanier/Dropbox/MY_DOC/Teaching/JCE/proj2026.jce.ac.il/MCP-server"
    }
  }
}
```
For HTTP instead: `{ "httpUrl": "http://127.0.0.1:9000/mcp" }`. (`trust: true` skips per-tool prompts.)

### 3. Goose — stdio
`~/.config/goose/config.yaml`:
```yaml
extensions:
  generic-system:
    type: stdio
    cmd: venv/bin/python
    args: ["src/mcp_server/main.py"]
    enabled: true
    timeout: 300
```
Or in the Goose desktop app: Extensions → Add → Command-line (stdio). For a remote server use
`type: streamable_http` with `uri: http://127.0.0.1:9000/mcp`.

### 4. LibreChat — stdio (self-hosted) or HTTP
`librechat.yaml`, then **restart LibreChat** (MCP servers init at startup):
```yaml
mcpServers:
  generic-system:
    type: stdio
    command: venv/bin/python
    args: ["src/mcp_server/main.py"]
```
Remote alternative:
```yaml
mcpServers:
  generic-system:
    type: streamable-http
    url: http://127.0.0.1:9000/mcp
```

### 5. LlamaIndex — library, any transport
```bash
pip install llama-index-tools-mcp
```
```python
from llama_index.tools.mcp import BasicMCPClient, McpToolSpec

client = BasicMCPClient("http://127.0.0.1:9000/mcp")          # HTTP: make run-http first
# client = BasicMCPClient("venv/bin/python", args=["src/mcp_server/main.py"])  # stdio

tools = await McpToolSpec(client=client).to_tool_list_async()  # feed `tools` to any agent
```

### 6. n8n — Streamable HTTP (import the ready template — don't build the node)
Your users should **not** hand-build the MCP node. Ship them `n8n/generic-system-mcp-agent.json`.
Full instructions: **`n8n/README.md`**. In short:
1. Start the server in HTTP mode: `make run-http` (serves `http://127.0.0.1:9000/mcp`).
2. In n8n: **⋮ → Import from File →** `n8n/generic-system-mcp-agent.json` — the whole
   `Chat Trigger → AI Agent → (Chat Model + MCP Server)` graph appears pre-wired.
3. User sets only two things: an **LLM credential** on the Chat Model node, and the **server URL**
   (already `http://127.0.0.1:9000/mcp`). Then click **Chat** and ask a question.

The agent auto-discovers all 13 tools. n8n only invokes MCP tools through an AI Agent, so the one
LLM credential is unavoidable; the template hides everything else.

_Gotchas:_ if n8n runs in Docker/Cloud, `127.0.0.1` won't reach your Mac — use
`host.docker.internal:9000` or a `make tunnel` URL. Template pins `mcpClientTool` **typeVersion 1.2**
so HTTP Streamable is the default (avoids the SSE-fallback bug). Details in `n8n/README.md`.

### 7. Microsoft Copilot Studio — Streamable HTTP, **public URL required**
Cloud service: it must reach a **public HTTPS** endpoint. Run `make run-http` + `make tunnel`.
1. Power Platform → **Custom connectors → New**. Easiest: import the Microsoft
   `MCP-Streamable-HTTP` connector template (it already carries `x-ms-agentic-protocol:
   mcp-streamable-1.0`).
2. **Host** = your tunnel domain (`<random>.trycloudflare.com`); **Base URL** = `/`.
3. Create, then in your agent: **Tools → Add tool → Model Context Protocol →** pick the connector.
4. Turn **generative orchestration ON** for the agent, or the tools won't be callable.

_Gotchas:_ SSE is not accepted (deprecated Aug 2025) — must be Streamable HTTP; supports tools &
resources, not prompts.

### 8. Cursor (IDE) — stdio or HTTP
File: `.cursor/mcp.json` (project) or `~/.cursor/mcp.json` (global). Key is `mcpServers`; HTTP and
stdio share the file. Use `${workspaceFolder}` for a reliable path.
```json
{
  "mcpServers": {
    "generic-system-stdio": {
      "command": "${workspaceFolder}/venv/bin/python",
      "args": ["${workspaceFolder}/src/mcp_server/main.py"]
    },
    "generic-system-http": { "url": "http://127.0.0.1:9000/mcp" }
  }
}
```
_Gotchas:_ toggle the server ON in Settings → MCP after saving; ~40-tool global cap across all servers.

### 9. VS Code (GitHub Copilot agent mode) — stdio or HTTP
File: `.vscode/mcp.json`. **Different from the others:** the key is `servers` (not `mcpServers`) and
each entry needs an explicit `type`.
```json
{
  "servers": {
    "generic-system-stdio": {
      "type": "stdio",
      "command": "${workspaceFolder}/venv/bin/python",
      "args": ["src/mcp_server/main.py"],
      "cwd": "${workspaceFolder}"
    },
    "generic-system-http": { "type": "http", "url": "http://127.0.0.1:9000/mcp" }
  }
}
```
_Gotchas:_ switch Copilot Chat to **Agent Mode** to use the tools. Wrong key (`mcpServers`) or missing
`type` fails silently.

### 10. Windsurf (Cascade) — stdio or HTTP
File: `~/.codeium/windsurf/mcp_config.json`. Key is `mcpServers`, but the HTTP field is **`serverUrl`**
(not `url`), and use **absolute paths** (no `${workspaceFolder}`).
```json
{
  "mcpServers": {
    "generic-system-stdio": {
      "command": "/ABSOLUTE/PATH/venv/bin/python",
      "args": ["/ABSOLUTE/PATH/src/mcp_server/main.py"]
    },
    "generic-system-http": { "serverUrl": "http://127.0.0.1:9000/mcp" }
  }
}
```
_Gotchas:_ click **Refresh** in the MCP panel after editing. HTTP field is `serverUrl`, not `url`.

### 11. Cline (VS Code extension) — stdio or HTTP
File: `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`
(macOS). Key is `mcpServers`.
```json
{
  "mcpServers": {
    "generic-system-stdio": {
      "command": "/ABSOLUTE/PATH/venv/bin/python",
      "args": ["/ABSOLUTE/PATH/src/mcp_server/main.py"],
      "disabled": false, "autoApprove": []
    },
    "generic-system-http": {
      "type": "streamableHttp",
      "url": "http://127.0.0.1:9000/mcp",
      "disabled": false, "autoApprove": []
    }
  }
}
```
_Gotchas:_ for HTTP the `type` must be **`streamableHttp`** (camelCase) — `streamable-http` or omitting it
makes Cline fall back to SSE and fail with a 405.

### 12. Genspark (genspark.ai) — Streamable HTTP, URL only (no stdio)
No config file — a UI form. In the Genspark **AI Browser**: **wrench icon → Add → Add new MCP server**,
then fill in:
- **Name:** `generic-system`
- **Server type:** `Streamable HTTP`
- **Server URL:** `http://127.0.0.1:9000/mcp`

_Gotchas:_ Genspark can't spawn a local subprocess (no stdio), but it accepts a **localhost URL**, so no
tunnel is needed for local use. Start the server with `make run-http` first.

### 13. ChatGPT (OpenAI) — Streamable HTTP, **public HTTPS required**
The only client here that **cannot** reach localhost at all — you must expose a public HTTPS URL.
1. `make run-http` + `make tunnel` → get `https://<random>.trycloudflare.com/mcp` (or `ngrok http 9000`).
2. In ChatGPT: **Settings → Connectors → Advanced → Developer Mode** (toggle on) → **Create** → name +
   the tunnel URL + "I trust this provider".
3. In a chat: **+ → More → Developer Mode**, enable the connector.

_Gotchas:_ needs a **paid plan**; Plus/Pro give read/fetch-only connectors, while write-capable custom
connectors need **Business/Enterprise/Edu** (admin must enable it). HTTPS is mandatory — `127.0.0.1` never works.

---

## Adding a new tool (no code change)

Append to `config/settings.json` → `tools`. The generic handler in `main.py` builds the tool —
including its parameters — from this JSON, so there's **no per-tool Python**.

Simple GET, no params:
```json
{
  "name": "fetch_new_thing",
  "description": "What it does and when the model should call it.",
  "endpoint_url": "http://127.0.0.1:8000/api/v1/your/endpoint"
}
```

Parameterized tool — `params` entries become the tool's advertised input schema. Each has a
`name`, a `type` (`string`/`integer`/`number`/`boolean`), `required`, and `in`
(`path` fills a `{placeholder}` in the URL, `query` adds a `?key=val`, `body` adds a JSON field):
```json
{
  "name": "get_weather",
  "description": "Current weather + 3-day forecast for a city.",
  "method": "GET",
  "endpoint_url": "http://127.0.0.1:8000/api/v1/weather/{city}",
  "params": [
    {"name": "city", "type": "string", "required": true, "in": "path"},
    {"name": "units", "type": "string", "required": false, "in": "query"}
  ]
}
```
Restart the server; every connected client picks up the new tool on reconnect.

### What the mock backend already offers (13 tools)
The mock Core API (`src/core_api_mock/main.py`) is intentionally diverse for testing:
weather (`get_weather`), staff directory (`search_users`, `get_user` — 404s on bad ids),
live incidents (`list_incidents`), service metrics time-series (`get_service_metrics`),
market prices (`get_price`), IoT sensors (`get_sensor_reading`), a dev joke (`get_dev_joke`),
plus two **challenging** ones for resilience testing: `call_flaky_service` (fails ~40% with 503)
and `call_slow_service` (artificial delay, for timeout testing).

---

## Quick troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `spawn uv ENOENT` | client told to use `uv` (not installed) | use `venv/bin/python` as the command |
| tools list but calls error | mock Core API not running | `make api` |
| cloud client can't connect | it can't see localhost | `make tunnel`, give it the HTTPS URL |
| n8n in Docker can't reach server | `127.0.0.1` = the container | `host.docker.internal:9000` or tunnel |
| stdio client "server exited" | relative paths / wrong PATH | use absolute paths to venv python + main.py |
