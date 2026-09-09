"""
One-step LlamaIndex + MCP server demo.

Different shape from the other scripts: LlamaIndex is a Python library for
building agents, not a standalone app - there's nothing to "launch". So this
script IS the minimal agent: it connects to our MCP server, wraps its tools
for LlamaIndex, builds a small agent around them using a Gemini model, and
drops you into a simple chat loop - the same "ready to work immediately"
outcome as the other scripts, just as a small demo app instead of a
pre-built one.

Needs from you: a Gemini API key - the SAME free key already used for
Gemini CLI / Goose in this project, not a new provider.

Requires (see requirements.txt): llama-index-core, llama-index-tools-mcp,
llama-index-llms-google-genai.
"""

import asyncio
import getpass
import sys

from llama_index.core.agent.workflow import FunctionAgent
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.tools.mcp import BasicMCPClient, McpToolSpec

MCP_SERVER_URL = "http://127.0.0.1:9000/mcp"
# Same model verified working end-to-end with this API key for Goose earlier
# in this project - reused here rather than guessing a newer model name.
MODEL = "gemini-3.5-flash"


async def build_agent(api_key: str) -> FunctionAgent:
    mcp_client = BasicMCPClient(MCP_SERVER_URL)
    tool_spec = McpToolSpec(client=mcp_client)
    tools = await tool_spec.to_tool_list_async()

    llm = GoogleGenAI(model=MODEL, api_key=api_key)
    return FunctionAgent(
        name="internal_system_bridge_agent",
        llm=llm,
        tools=tools,
        system_prompt=(
            "You are a helpful assistant with access to internal company "
            "system tools (status reports, health checks, image metadata). "
            "Use them when relevant to the user's question."
        ),
    )


async def chat_loop(agent: FunctionAgent) -> None:
    print()
    print("Ready. Type a message (or 'exit' to quit).")
    while True:
        message = input("> ").strip()
        if message.lower() in {"exit", "quit"}:
            break
        if not message:
            continue
        response = await agent.run(message)
        print(response)


async def main_async() -> None:
    api_key = getpass.getpass("Paste your Gemini API key (hidden, from Google AI Studio): ").strip()
    if not api_key:
        print("No key entered - aborting.")
        sys.exit(1)

    print("Connecting to the MCP server and building the agent...")
    agent = await build_agent(api_key)
    await chat_loop(agent)


if __name__ == "__main__":
    asyncio.run(main_async())
