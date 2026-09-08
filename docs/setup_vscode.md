# Client Setup: VS Code (GitHub Copilot, Agent Mode)

Connects VS Code's Copilot Chat to `mcp_server` over HTTP.

**Why VS Code**: it's a developer's primary environment, not a separate chat app — connecting it means internal data (system reports, health checks, and any tool added later via `config/settings.json`) is reachable right where code gets written, and Copilot's Agent Mode can act on it alongside normal coding tasks. This matches the project's stated goal of reaching developer environments, not just chat interfaces.

**Not yet live-verified** — built from Microsoft's official docs (code.visualstudio.com), same rigor as Cursor, but not yet confirmed working end to end in this project. Update this note once tested.

## 1. Start the server side (two terminals)

**Terminal 1 — mock backend:**
```
venv\Scripts\activate
uvicorn src.core_api_mock.main:app --reload
```

**Terminal 2 — MCP server, HTTP mode:**
```powershell
venv\Scripts\activate
$env:MCP_TRANSPORT = "streamable-http"
venv\Scripts\python.exe src\mcp_server\main.py
```
Confirm it logs `Uvicorn running on http://127.0.0.1:9000`. Both terminals must stay open.

## 2. Connection config

`.vscode/mcp.json` (project root) — already in this repo:
```json
{
  "servers": {
    "internal-system-bridge": {
      "type": "http",
      "url": "http://127.0.0.1:9000/mcp"
    }
  }
}
```

**Important — this is different from every other client we've connected**: VS Code's key is `servers`, not `mcpServers`, and each entry needs an explicit `"type": "http"`. Per Microsoft's docs, getting this wrong (wrong key, or missing `type`) tends to fail silently rather than show a clear error — if VS Code doesn't seem to see the server at all, this is the first thing to double-check.

No auth — the server has none configured.

## 3. Connect in VS Code

1. Open this project folder in VS Code (`.vscode/mcp.json` only takes effect for a workspace opened at this folder).
2. Open **Copilot Chat** (chat icon in the sidebar, or `Ctrl+Alt+I`).
3. At the top of the chat panel there's a mode dropdown — switch it from **Ask**/**Edit** to **Agent**. MCP tools are only available to Copilot in Agent Mode.
4. VS Code should pick up `.vscode/mcp.json` automatically and forward it to the Agent Host — no separate "enable" toggle documented, unlike Cursor/Claude Desktop.
5. Look for a tools icon near the chat input (shows a count of available tools) — click it to confirm `internal-system-bridge`'s tools are listed before asking anything.

## 4. Verify

With both servers still running, in Agent Mode ask something that should trigger a tool, e.g.:
> "Check if the core API is healthy."

A successful reply using real data from `core_api_mock` confirms the connection works.

## Adding tools later

Edit `config/settings.json` only — no changes needed to `.vscode/mcp.json` or `mcp_server/main.py`.
