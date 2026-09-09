# Client Setup: LlamaIndex

**Not yet live-verified** — packages installed and script written, but not yet run end-to-end. Update this note once tested.

## What makes this different from every other client

LlamaIndex isn't an app or a CLI — it's a **Python library** developers use to build their own AI applications (RAG systems, custom agents) around private data. There's no "LlamaIndex app" to open or launch, so there's also no existing session for a setup script to drop you into.

Instead, `scripts/setup_llamaindex.py` *is* the minimal agent: it connects to the MCP server, wraps its tools into LlamaIndex's tool format, builds a small agent around a Gemini model, and drops you into a simple chat loop — the same "ready to work immediately" outcome as the Goose/Gemini CLI scripts, just implemented as a small demo app instead of launching a pre-built one.

**What you need**: nothing new — we reuse your existing Gemini API key, the same free key already used for Gemini CLI and Goose in this project, rather than adding a new provider.

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

## 2. Install dependencies

Already in `requirements.txt`, but if you haven't run it since this was added:
```
venv\Scripts\python.exe -m pip install -r requirements.txt
```
This pulls in `llama-index-core`, `llama-index-tools-mcp`, and `llama-index-llms-google-genai` — a fairly large install (LlamaIndex core has many dependencies), so it can take a few minutes the first time.

## 3. Run it

```
venv\Scripts\python.exe scripts\setup_llamaindex.py
```
Paste your Gemini API key when asked (hidden input, same key as before — **only into this terminal prompt, never elsewhere**).

## How it actually works

1. Connects to the MCP server via `BasicMCPClient("http://127.0.0.1:9000/mcp")`.
2. Converts our 3 MCP tools into LlamaIndex's tool format via `McpToolSpec`.
3. Creates a `GoogleGenAI` LLM (model `gemini-3.5-flash` — the same model already verified working with this API key for Goose) and wraps it in a `FunctionAgent` along with the tools.
4. Drops you into a plain `> ` prompt — type a message, the agent decides whether to call a tool, and prints the response. Type `exit` to quit.

## Verify

Once running, try:
> "Check if the core API is healthy."

A successful reply using real data from `core_api_mock` confirms the connection works.

## Who this is actually for

Unlike the other 6 clients, this isn't something to hand an end user — it's for **developers building their own custom AI application** who want to pull our internal tools in as building blocks, instead of writing their own integration against `core_api_mock` from scratch. The script here is a minimal demo of that integration, not a finished product.
