# n8n — one-import setup (no node building)

Your users should **not** have to add or wire the MCP Client Tool node by hand. Ship them this
folder's workflow file; they import it and touch only two things.

## For your users (3 steps)

1. **Import the workflow.** In n8n: top-right menu **⋮ → Import from File →** pick
   `generic-system-mcp-agent.json`. The whole graph appears pre-wired:
   `Chat Trigger → AI Agent → (Chat Model + Generic System MCP Server)`.
2. **Set the LLM credential.** Open the **Chat Model (set your API key)** node → *Credential to
   connect with* → add your OpenAI key. (n8n only calls MCP tools through an AI Agent, so one LLM
   credential is unavoidable. To use a different provider, replace that node with
   `Anthropic Chat Model`, `Google Gemini Chat Model`, or `Ollama Chat Model` for fully local.)
3. **Check the server URL.** Open the **Generic System MCP Server** node. It's preset to
   `http://127.0.0.1:9000/mcp`. Change it only if your MCP server runs elsewhere (see gotchas).

Then click **Chat** and ask e.g. *"What's the weather in Tokyo?"* or *"List open critical incidents."*
The agent discovers all 13 tools from the server automatically — no per-tool setup.

## Prerequisite: the MCP server must be running in Streamable HTTP mode

```bash
make api          # mock backend on :8000
make run-http     # MCP server on http://127.0.0.1:9000/mcp
```

## Gotchas

- **n8n in Docker:** `127.0.0.1` means the *container*, not your Mac. Use
  `http://host.docker.internal:9000/mcp`, or expose a tunnel URL (`make tunnel`) and paste that.
- **n8n Cloud (hosted):** it can't reach your localhost at all — run `make tunnel` and use the
  `https://…/mcp` URL in the node.
- **Transport falls back to SSE:** a known bug on some builds ignores the transport dropdown. This
  template pins **typeVersion 1.2**, where `httpStreamable` is the default. If tools still don't
  appear, update n8n, or set the transport field as an expression `=httpStreamable`.
- **Older n8n** warns on import: lower `agent` to `1.7` and `mcpClientTool` to `1.1` in the JSON
  (and keep `"serverTransport": "httpStreamable"`, since 1.1 defaults to SSE).

## Why a template instead of "add the MCP node"?

n8n's MCP Client Tool is an AI-agent sub-node; used manually it's several nodes to create and
connect. Exporting a working graph once collapses all of that into *import + paste URL* for every
user — while still going through MCP end to end.
