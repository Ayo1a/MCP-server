# Client Setup: Goose

Connects Goose to `mcp_server` over HTTP. Verified end-to-end: extension added, and a natural-language request successfully triggered `check_core_api_health` with a real result from `core_api_mock`.

## Why Goose needs an LLM provider before anything else

Goose is an AI **agent**, not just an MCP client — it needs its own LLM ("brain") to understand messages and decide when to call a tool. An MCP server (like ours) only provides tools/data; it doesn't do any reasoning. Unlike Claude Desktop (which already has Claude built in), Goose is deliberately **bring-your-own-model** — provider-agnostic by design — so it insists on provider setup before anything else, regardless of which MCP servers get attached later.

**Cost note**: pick a provider/model you're sure is free. Some providers (e.g. OpenRouter) have both free and paid models, and it's easy to end up on a paid one by accident — safer options are reusing an existing free-tier key you already trust (e.g. a Gemini API key from Google AI Studio), or a fully local provider like Ollama, which has no billing account involved at all. We used an existing Gemini API key (already set up for Gemini CLI) to avoid creating a new provider account.

## 1. Install (Windows)

```powershell
irm https://github.com/block/goose/raw/main/download_cli.ps1 | iex
```
Installs to `C:\Users\<you>\.local\bin\goose.exe`.

**Known gotcha**: even after install, a plain `goose` command may not be recognized in new terminals (`PATH` not picked up). Call it by full path instead:
```powershell
& "$env:USERPROFILE\.local\bin\goose.exe" configure
```

## 2. Fast path: automated setup script

We also have `scripts/setup_goose.py`, which automates steps 3 and 4 below — it just asks for your Gemini API key, then drops you straight into a working `goose session`, no manual `goose configure` needed. Requires Goose already installed (step 1) and `core_api_mock` + `mcp_server` (HTTP mode) already running (see step 4).

```
venv\Scripts\python.exe scripts\setup_goose.py
```

---

The rest of this doc (steps 3–5) is the **manual** path this script replaces — useful if you want to understand what's happening under the hood, use a different provider, or something about the script doesn't fit your setup.

## 3. Provider setup (manual)

Run `goose configure` → **Manual Configuration** → search for **Google** → select it → paste your Gemini API key **only into that terminal prompt** (never into a chat window) when asked.

Then:
- **Model**: `gemini-3.6-flash`. We first tried `gemini-2.5-flash`, which failed with `404 ... no longer available to new users` — Google's own error pointed to `gemini-3.6-flash` as the replacement.
- **Thinking effort**: `Off` — we just need reliable tool-calling, not deep reasoning, and it's the fastest/simplest option for testing.

On success: `Configuration saved successfully to C:\Users\<you>\AppData\Roaming\Block\goose\config\config.yaml`.

> Tip (from Goose's own CLI output): run `goose configure` again anytime to adjust your config or add more extensions.

## 4. Add the MCP server (manual)

Run `goose configure` again → **Add Extension** → **Remote Extension (Streamable HTTP)**, then:
- **Name**: `internal-system-bridge`
- **URI**: `http://127.0.0.1:9000/mcp`
- **Description**: any short text, e.g. "Internal Core API tools (system reports, health check, image metadata) - local dev MCP server"
- **Timeout**: accept the default
- **Custom header**: skip — the server has no authentication configured

On success: `Added internal-system-bridge extension` / `Configuration saved successfully...`.

Requires `core_api_mock` and `mcp_server` (HTTP mode) running first, same as every other client:
```
venv\Scripts\activate
uvicorn src.core_api_mock.main:app --reload
```
```powershell
venv\Scripts\activate
$env:MCP_TRANSPORT = "streamable-http"
venv\Scripts\python.exe src\mcp_server\main.py
```

## 5. Verify

Start a session (already done for you if you used the script in step 2):
```powershell
& "$env:USERPROFILE\.local\bin\goose.exe" session
```
Ask something that should trigger a tool, e.g.:
> "Check if the core API is healthy."

Confirmed result: Goose called `check_core_api_health` and replied with the real `core_api_mock` status message.

## Adding tools later

Edit `config/settings.json` only — no changes needed to Goose's own config or `mcp_server/main.py`.
