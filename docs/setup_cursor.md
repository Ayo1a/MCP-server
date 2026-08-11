# Client Setup: Cursor (IDE)

Connects Cursor to `mcp_server` over HTTP.

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

No auth — the server has none configured.

## 2. Connect in Cursor — two ways

### Method A: config file + manual enable

`.cursor/mcp.json` (project root) — already in this repo:
```json
{
  "mcpServers": {
    "internal-system-bridge": {
      "url": "http://127.0.0.1:9000/mcp"
    }
  }
}
```
1. Open this project folder in Cursor.
2. **Settings → MCP** — `internal-system-bridge` should be listed; toggle it **on** if not already enabled.
3. Confirm it shows as connected and lists the tools from `config/settings.json`.

### Method B: one-click deeplink install

Cursor supports a **deeplink** — a special `cursor://` URL that, when opened (e.g. clicked from a webpage, README, or chat), launches Cursor and prompts it to install a specific MCP server with its config pre-filled. It skips manually creating/editing `.cursor/mcp.json` or hunting through Settings — you still get one approval prompt from Cursor itself (not bypassable, it's Cursor's own trust gate), but nothing to type.

Format: `cursor://anysphere.cursor-deeplink/mcp/install?name=$NAME&config=$BASE64_ENCODED_CONFIG`, where the config is the same JSON as in `.cursor/mcp.json`'s server entry, base64-encoded.

For this server:
```
cursor://anysphere.cursor-deeplink/mcp/install?name=internal-system-bridge&config=eyJ1cmwiOiAiaHR0cDovLzEyNy4wLjAuMTo5MDAwL21jcCJ9
```
Note this points at `127.0.0.1`, so it only works when opened on the same machine that's running the server locally.

## 3. Verify

With both servers still running, ask Cursor something that should trigger a tool, e.g.:
> "Check if the core API is healthy."

A successful reply using real data from `core_api_mock` confirms the connection works.

## Adding tools later

Edit `config/settings.json` only — no changes needed to `.cursor/mcp.json` or `mcp_server/main.py`. Reconnect the server in Cursor's MCP settings to pick up new tools.

## notes
HTTPS vs HTTP is a separate concern — it's about encrypting the traffic, not about whether Cursor requires a trust/approval step. Switching to HTTPS wouldn't remove the manual enable step; that step exists because Cursor wants a human to approve any MCP server before it runs, regardless of the URL scheme.

What actually would give a cleaner flow: Cursor supports a deep-link "Add to Cursor" install — a special cursor:// URL that, when clicked (e.g. from a webpage or README button), opens Cursor with the server config pre-filled and just asks for one approval click, no manual JSON editing or hunting through Settings needed. That's the real lever for "cleaner," not the transport encryption.

