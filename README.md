# 🛠️ MCP Server - Project Architecture & Context

This document serves as the single source of truth for the project's architecture, directory structure, and operational goals. It is designed to quickly bring the AI assistant up to speed at the beginning of each development session.

---

## 🎯 Project Ultimate Goal
To expand the company's data distribution channels and capabilities beyond conventional chat interfaces (such as Claude or ChatGPT apps) towards programmatic platforms, developer environments, and autonomous agents.

The core objective is to build a completely generic, configuration-driven infrastructure. This ensures that adding any new tool or function requires zero code changes and automatically propagates to all external consumption channels.

---

## 📁 Project Directory Structure

```text
MCP-SERVER/
│
├── .gitignore               # Files ignored by Git (e.g., venv/ environment)
├── README.md                # Main repository documentation
├── PROJECT_ARCHITECTURE.md   # Current project architecture and context (for the AI)
├── requirements.txt         # Python package dependencies (fastapi, uvicorn, fastmcp)
├── test_mcp.py              # Programmatic test script for the MCP server (No Node.js required)
│
├── config/                  # Configuration directory (for the future generic architecture)
│   └── settings.json        
│
└── src/                     # Main source code directory
    │
    ├── core_api_mock/       # Step 2.1: Mock Internal Core API (FastAPI)
    │   ├── __init__.py
    │   └── main.py          # Internal endpoints returning hardcoded mock data
    │
    └── mcp_server/          # Step 2.2: Outer Wrapper MCP Server (FastMCP)
        ├── __init__.py
        ├── main.py          # Main FastMCP server exposing capabilities to the outside world
        └── tools/           # Modular tools exposed by the MCP server
            ├── __init__.py
            ├── text_tool.py  # Text tool returning static Markdown content
            └── image_tool.py # Image tool simulating media/image generation