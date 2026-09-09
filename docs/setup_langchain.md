# Client Setup: LangChain

**Not yet live-verified** — packages installed and script written, but not yet run end-to-end. Update this note once tested.

## What makes this different from every other client

LangChain isn't an app or a CLI — it's a **Python library** developers use to build their own AI applications (chains, RAG pipelines, custom agents), with LangGraph as its agent-orchestration layer. Same shape as LlamaIndex: there's no "LangChain app" to open or launch, so there's also no existing session for a setup script to drop you into.

Instead, `scripts/setup_langchain.py` *is* the minimal agent: it connects to the MCP server, wraps its tools into LangChain's tool format, builds a small LangGraph agent around a Gemini model, and drops you into a simple chat loop — same "ready to work immediately" outcome as the LlamaIndex script.

**What you need**: nothing new — we reuse your existing Gemini API key, the same free key already used for Gemini CLI, Goose, and LlamaIndex in this project, rather than adding a new provider.

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
This pulls in `langchain-mcp-adapters`, `langgraph`, and `langchain-google-genai`.

## 3. Run it

```
venv\Scripts\python.exe scripts\setup_langchain.py
```
Paste your Gemini API key when asked (hidden input, same key as before — **only into this terminal prompt, never elsewhere**).

## How it actually works

The script sends JSON-RPC 2.0 requests over HTTP POST to the server: an `initialize` call to open the session, a `tools/list` call to fetch the tool schemas, and a `tools/call` request each time a tool needs to run — each response comes back in the same JSON-RPC format and is fed into the LLM.

Concretely: it connects via `MultiServerMCPClient`, retrieves the tool schemas with `get_tools()`, and wraps them together with a `ChatGoogleGenerativeAI` LLM (model `gemini-3.5-flash` — the same model already verified working with this API key for Goose/LlamaIndex) into a `create_react_agent` (LangGraph). You then get a plain `> ` prompt — type a message, the agent decides whether to call a tool, and prints the response. Type `exit` to quit.

## Verify

Once running, try:
> "Check if the core API is healthy."

A successful reply using real data from `core_api_mock` confirms the connection works.

## Who this is actually for

Same audience as LlamaIndex — this isn't something to hand an end user, it's for **developers building their own custom AI application**, specifically ones who've already standardized on LangChain/LangGraph rather than LlamaIndex. The script here is a minimal demo of that integration, not a finished product.
