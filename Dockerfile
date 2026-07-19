# Image for the two Python processes: the mock Core API and the MCP server.
# Same image, different start command (set in docker-compose.yml).
FROM python:3.13-slim

WORKDIR /app

# The server needs the MCP SDK (provides mcp.server.fastmcp) + httpx, plus fastapi/uvicorn
# for the mock backend. requirements.txt only lists the backend deps, so install the full set here.
RUN pip install --no-cache-dir \
    "fastapi" \
    "uvicorn[standard]" \
    "mcp>=1.28" \
    "httpx"

# Copy source + config. settings.json is read at startup by the MCP server.
COPY src/ ./src/
COPY config/ ./config/

# Default command is the MCP server over HTTP; compose overrides it for the mock-api service.
# 0.0.0.0 so the server is reachable from other containers (not just localhost inside the container).
ENV MCP_TRANSPORT=streamable-http \
    MCP_HOST=0.0.0.0 \
    MCP_PORT=9000
EXPOSE 9000
CMD ["python", "src/mcp_server/main.py"]
