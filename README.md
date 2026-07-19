# 🛠️ Generic System MCP Server

A completely **configuration-driven** MCP server: adding or changing a tool means editing
`config/settings.json` — **no code changes** — and it automatically propagates to every client
(Claude Desktop, Cursor, VS Code, n8n, ChatGPT, and more).

---

## 🎯 Project goal
Expand the company's data-distribution channels beyond chat apps toward programmatic platforms,
developer environments, and autonomous agents — through one generic, config-driven MCP server that
fronts an internal Core API.

---

## ✨ What this server does

- **One server, three transports.** The same `src/mcp_server/main.py` runs over **stdio**,
  **Streamable HTTP**, or **SSE**, chosen at launch by env vars (default: stdio). This is what lets
  a single server reach both local clients and URL-based/cloud clients.
- **Config-driven, parameterized tools.** Each entry in `config/settings.json` becomes an MCP tool.
  Tools can declare `method` and `params` (path / query / body), and the generic handler builds the
  proper input schema automatically — still no per-tool Python.
- **A diverse mock backend** (`src/core_api_mock/main.py`) for realistic testing: weather, staff
  directory, live incidents, metrics time-series, market prices, IoT sensors, a dev joke, plus
  deliberately *challenging* endpoints (a flaky 503, an artificially slow one) for resilience testing.
- **13 example tools** shipped in `config/settings.json`.

---

## 📁 Directory structure

```text
MCP-server/
├── config/
│   └── settings.json          # THE control file — server name + every tool (edit this to add tools)
├── src/
│   ├── core_api_mock/
│   │   └── main.py            # Mock internal Core API (FastAPI) the tools call
│   └── mcp_server/
│       └── main.py           # The MCP server: multi-transport + generic config-driven tools
├── docs/
│   ├── connecting_clients.md # Step-by-step: connect 13 MCP clients (matrix + copy-paste configs)
│   └── setup_claude_desktop.md
├── n8n/
│   ├── generic-system-mcp-agent.json  # Import-ready n8n workflow (connect via MCP, no node building)
│   └── README.md
├── Makefile                   # Run/test/tunnel shortcuts (make help)
├── Dockerfile                 # Container image for the MCP server + mock API
├── test_client.py             # Generic transport-agnostic smoke test (stdio or HTTP)
├── test_mcp.py                # Original stdio test script
├── .env.example               # Env template (LLM switch for the bundled stack)
└── requirements.txt
```

---

## 🚀 Quick start

```bash
# 0. one-time: create venv + install deps
python3 -m venv venv && ./venv/bin/pip install fastapi "uvicorn[standard]" "mcp>=1.28" httpx

# 1. start the mock backend the tools call (own terminal)
make api                # http://127.0.0.1:8000

# 2. prove the server works, independent of any client
make test-stdio         # lists all 13 tools + calls one
```

Run the MCP server in whichever mode a client needs:

| Mode | Command | Client uses |
|---|---|---|
| stdio | `make run-stdio` | command `venv/bin/python src/mcp_server/main.py` |
| Streamable HTTP | `make run-http` | URL `http://127.0.0.1:9000/mcp` |
| SSE (legacy) | `make run-sse` | URL `http://127.0.0.1:9000/sse` |

`make help` lists every shortcut (including `make inspector-stdio` and `make tunnel`).

> **Note:** the MCP server uses port **9000**; the mock Core API uses **8000**. Override with
> `MCP_TRANSPORT`, `MCP_PORT`, `MCP_HOST`, and `CORE_API_BASE_URL` env vars.

---

## 🔌 Connecting clients

Full step-by-step recipes for **13 clients** — Claude Desktop, Gemini CLI, Goose, LibreChat,
LlamaIndex, n8n, Copilot Studio, Cursor, VS Code, Windsurf, Cline, Genspark, ChatGPT — with a
transport matrix and a config-format cheat sheet, are in **[`docs/connecting_clients.md`](docs/connecting_clients.md)**.

Rule of thumb: local clients that spawn a subprocess use **stdio**; URL-based and cloud clients use
**Streamable HTTP** (`make run-http`). Cloud-only clients (ChatGPT, Copilot Studio) need a public
URL — `make tunnel`.

For **n8n**, users don't build the MCP node: they import `n8n/generic-system-mcp-agent.json`
(see [`n8n/README.md`](n8n/README.md)).

---

## ➕ Adding a new tool (no code change)

Append to `config/settings.json` → `tools`:

```json
{
  "name": "get_weather",
  "description": "Current weather + 3-day forecast for a city.",
  "method": "GET",
  "endpoint_url": "http://127.0.0.1:8000/api/v1/weather/{city}",
  "params": [
    { "name": "city", "type": "string", "required": true, "in": "path" }
  ]
}
```

`in` is `path` (fills a `{placeholder}`), `query` (adds `?key=val`), or `body` (JSON field).
Restart the server; every connected client picks it up on reconnect.

---

## 🧰 Mock backend tools (shipped examples)

`get_weather`, `search_users`, `get_user` (404s on bad id), `list_incidents`,
`get_service_metrics` (time-series), `get_price`, `get_sensor_reading`, `get_dev_joke`,
`fetch_system_text_report`, `fetch_system_image_metadata`, `check_core_api_health`,
plus `call_flaky_service` (~40% 503) and `call_slow_service` (timeout testing).
