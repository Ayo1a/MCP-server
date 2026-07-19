# Convenience launchers. Nothing here contains logic — just the env vars each mode needs.
# Requires the project venv at ./venv (already present).

PY := venv/bin/python
MCP_PORT ?= 9000

# --- backend the tools talk to ---
api:                       ## Start the mock Core API on :8000 (tools call this)
	$(PY) -m uvicorn src.core_api_mock.main:app --port 8000 --reload

# --- the MCP server, one file, three ways to run it ---
run-stdio:                 ## MCP server over stdio (local subprocess clients)
	$(PY) src/mcp_server/main.py

run-http:                  ## MCP server over Streamable HTTP at http://127.0.0.1:$(MCP_PORT)/mcp
	MCP_TRANSPORT=streamable-http MCP_PORT=$(MCP_PORT) $(PY) src/mcp_server/main.py

run-sse:                   ## MCP server over legacy SSE at http://127.0.0.1:$(MCP_PORT)/sse
	MCP_TRANSPORT=sse MCP_PORT=$(MCP_PORT) $(PY) src/mcp_server/main.py

# --- verification ---
test-stdio:                ## Smoke-test the server over stdio
	$(PY) test_client.py

test-http:                 ## Smoke-test a running HTTP server (run `make run-http` first)
	$(PY) test_client.py --http http://127.0.0.1:$(MCP_PORT)/mcp

inspector-stdio:           ## Open MCP Inspector against the stdio server
	npx @modelcontextprotocol/inspector $(PY) src/mcp_server/main.py

# --- expose localhost to cloud clients (Copilot Studio, hosted n8n) ---
tunnel:                    ## Public HTTPS URL for the HTTP server (needs cloudflared installed)
	cloudflared tunnel --url http://localhost:$(MCP_PORT)

help:                      ## List targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-16s\033[0m %s\n",$$1,$$2}'

.PHONY: api run-stdio run-http run-sse test-stdio test-http inspector-stdio tunnel help
