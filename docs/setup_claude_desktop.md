# Client Setup: Claude Desktop

How to connect Claude Desktop to this project's MCP server (`src/mcp_server/main.py`), and what to do if you need to repeat this on a new machine or after reinstalling.

## Prerequisites

1. `core_api_mock` running:
   ```
   venv\Scripts\uvicorn src.core_api_mock.main:app --reload
   ```
2. `mcp_server/main.py` tested and working on its own via the MCP Inspector:
   ```
   venv\Scripts\python.exe -m pip install uv   # only needed once — Inspector shells out via `uv run`
   mcp dev src/mcp_server/main.py
   ```
   Confirm the tools defined in `config/settings.json` show up and run successfully before touching Claude Desktop.

## Install Claude Desktop

Download from claude.ai/download and launch it once so it initializes its app data.

**Note on packaged/Microsoft Store builds**: this install stores its data in a sandboxed path, not the classic `%APPDATA%\Claude`:
```
C:\Users\User\AppData\Local\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\
```
The exact `Claude_<id>` folder name is specific to this machine's install — if repeating this elsewhere, look under `AppData\Local\Packages\` for a folder starting with `Claude_`.

## Why manual config editing doesn't work (on this build)

The classic documented approach — hand-editing `claude_desktop_config.json`'s `mcpServers` key — **does not work** on this build. The app treats that file as its own managed settings store and overwrites/strips any unrecognized keys (like `mcpServers`) on launch. Don't waste time on this path; go straight to the Extensions method below.

## The working method: MCPB Extensions

Claude Desktop (current builds) installs local MCP servers as **Extensions**, using Anthropic's **MCPB** format (formerly called "dxt"), described by a `manifest.json`.

1. In Claude Desktop: **Settings → Extensions → Advanced settings**.
2. Note the options: *Install Extension*, *Install Unpackaged Extension*, *Open Extension Folder*, *Open Extensions Settings Folder*.
3. We use **Install Unpackaged Extension**, which points at a folder containing a `manifest.json`.

### Building the manifest

Don't hand-guess the schema — scaffold and validate it with the official CLI:
```
npx @anthropic-ai/mcpb init      # scaffolds a manifest.json to inspect the current schema
npx @anthropic-ai/mcpb validate manifest.json   # validates before installing
```

This project's `manifest.json` lives at the **project root** (so `${__dirname}` resolves to the repo, and `entry_point` can point directly at `src/mcp_server/main.py` with no file duplication):

```json
{
  "manifest_version": "0.3",
  "name": "internal-system-bridge",
  "version": "1.0.0",
  "description": "MCP wrapper exposing internal Core API tools, generated dynamically from config/settings.json",
  "author": { "name": "Ayo1a" },
  "server": {
    "type": "python",
    "entry_point": "src/mcp_server/main.py",
    "mcp_config": {
      "command": "C:\\Users\\User\\Documents\\ליה\\final_project\\MCP-server\\venv\\Scripts\\python.exe",
      "args": ["${__dirname}/src/mcp_server/main.py"]
    }
  }
}
```

Key schema notes (from `@anthropic-ai/mcpb`'s `mcpb-manifest-latest.schema.json`):
- Required top-level fields: `name`, `version`, `description`, `author`, `server`.
- `server.type` must be one of `"python"`, `"node"`, `"binary"`.
- `server` requires `type`, `entry_point`, `mcp_config`; `mcp_config` only requires `command`.
- Point `mcp_config.command` at the **venv's `python.exe`** directly (not just `python`) so the correct interpreter/dependencies are used regardless of system PATH.

### Installing

1. Settings → Extensions → Advanced settings → **Install Unpackaged Extension**.
2. Select the project root folder (the one containing `manifest.json`).
3. It should install as **internal-system-bridge**, listing the tools from `config/settings.json`.
4. Set its tool permission to **Always Allow** (or Ask, then approve per call) — not Blocked.

### Verifying it works

1. Make sure `core_api_mock` is still running.
2. Start a **new chat** in Claude Desktop (existing chats don't pick up newly installed extensions).
3. Ask something that should trigger a tool, e.g. "Check if the core API is healthy."
4. Confirm the tool call succeeds and returns real data from `core_api_mock`.

## Adding/changing tools later

Since tools are generated dynamically from `config/settings.json`, adding a new tool only requires editing that file (pointing at an existing or new `core_api_mock` endpoint) — no changes to `manifest.json` or `mcp_server/main.py`, and no re-install of the extension needed for the change to take effect (just start a new chat, or restart Claude Desktop if it doesn't pick it up).
