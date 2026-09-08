# Client Setup: Gemini CLI

Connects Gemini CLI to `mcp_server` over HTTP. Verified end-to-end: registered, connected, and confirmed all 3 tools callable.

## Fast path: automated setup script

The MCP server registration (`.gemini/settings.json`) is already committed in this repo, so the only thing a new user actually needs is a **Gemini API key** (free, from Google AI Studio). `scripts/setup_gemini_cli.py` handles the rest — it saves the key, marks this project folder as trusted (so the trust prompt never appears), and launches straight into a working `gemini` session:

```
venv\Scripts\python.exe scripts\setup_gemini_cli.py
```

Note: the first time you run this, `npx` may ask to install `@google/gemini-cli@0.58.0` (or similar) if it isn't cached yet — that's expected, just let it install.

Requires `core_api_mock` and `mcp_server` (HTTP mode) already running — see step 1 below. This is a separate script from `scripts/setup_goose.py` (different tool, different config format, different env var) — don't mix them up.

---

The rest of this doc (steps 1–5) is the **manual** path this script replaces — useful for understanding what's happening under the hood, or if something about the script doesn't fit your setup.

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
Confirm it logs `Uvicorn running on http://127.0.0.1:9000`. Both terminals must stay open — a "Disconnected" status in Gemini CLI most often just means this terminal isn't running.

## 2. Register the server

No persistent install needed — Gemini CLI runs fine via `npx`. From the project root:
```
npx -y @google/gemini-cli mcp add generic-system http://127.0.0.1:9000/mcp --transport http --description "Generic System MCP Server (local)"
```
This is a one-time, non-interactive command — it just writes an entry to `.gemini/settings.json` (project-scoped, already committed in this repo):
```json
{
  "mcpServers": {
    "generic-system": {
      "url": "http://127.0.0.1:9000/mcp",
      "type": "http"
    }
  }
}
```
This file is *what* Gemini CLI reads to know the server exists — `/mcp` doesn't discover anything on its own, it just reports the live status of whatever's listed here.

## 3. First-run trust + auth (interactive, do this yourself in a terminal)

```
npx @google/gemini-cli
```

1. **Folder trust**: first launch in this project prompts to trust the folder — accept it. MCP servers are disabled entirely in untrusted folders.
2. **Authentication**: pick a provider.
   - **"Login with Google"** (OAuth, personal account) — simplest, no key to manage. Recommended if you just want to verify the connection.
   - **"Gemini API Key"** — generate one at **Google AI Studio** (aistudio.google.com → Get API key), then paste it **only when the CLI itself prompts for it**.

   > **⚠️ Never paste a real API key into a chat window, an AI assistant, or anywhere other than the tool's own prompt.** If a key is ever pasted somewhere it shouldn't be, treat it as compromised and rotate/regenerate it immediately from the provider's dashboard.

3. Once past both screens, you can exit (`/quit` or Ctrl+C) — no need to actually chat yet.

## 4. Verify

Either from a plain terminal:
```
npx -y @google/gemini-cli mcp list
```
Expect: `✓ generic-system: http://127.0.0.1:9000/mcp (http) - Connected`

Or inside an interactive `gemini` session:
```
/mcp
```
Expect: `🟢 generic-system - Ready (3 tools)` listing `check_core_api_health`, `fetch_system_image_metadata`, `fetch_system_text_report`. (`/tools` shows the same tools alongside Gemini's built-in ones.)

## 5. Using it

No special syntax — just ask in plain language and it decides when a tool applies, e.g.:
> "Check if the core API is healthy."

Expect a one-time approval prompt for the tool call before it runs.

## Notes / gotchas

- **Project-scoped by default**: `mcp add` defaults to `--scope project`, so `.gemini/settings.json` only applies when Gemini CLI is run from this folder. Use `--scope user` instead if you want it available everywhere.
- **`gemini mcp list` may print a harmless crash line after the real output** (`Assertion failed... UV_HANDLE_CLOSING`) — a known Node/libuv shutdown quirk on Windows, unrelated to the MCP connection itself. Ignore it if the status line above it already showed Connected.
- Adding tools later only requires editing `config/settings.json` — no changes to `.gemini/settings.json` needed; reconnect (`/mcp` or restart the session) to pick up new tools.
