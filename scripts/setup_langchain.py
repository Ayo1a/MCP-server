"""
One-step LangChain + MCP server demo.

Same shape as scripts/setup_llamaindex.py and the same reasoning: LangChain
is a Python library for building agents, not a standalone app, so this
script IS the minimal agent - it connects to our MCP server via the official
langchain-mcp-adapters package, wraps the tools, builds a small LangGraph
ReAct agent around a Gemini model, and drops you into a simple chat loop.

Needs from you: a Gemini API key - the SAME free key already used for
Gemini CLI / Goose / LlamaIndex in this project, not a new provider.

Requires (see requirements.txt): langchain-mcp-adapters, langgraph,
langchain-google-genai.
"""

import asyncio
import getpass
import sys

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

MCP_SERVER_URL = "http://127.0.0.1:9000/mcp"
# Same model verified working end-to-end with this API key elsewhere in this
# project (Goose, LlamaIndex) - reused here rather than guessing a newer name.
MODEL = "gemini-3.5-flash"


async def build_agent(api_key: str):
    client = MultiServerMCPClient({
        "internal-system-bridge": {
            "url": MCP_SERVER_URL,
            "transport": "streamable_http",
        }
    })
    tools = await client.get_tools()

    llm = ChatGoogleGenerativeAI(model=MODEL, google_api_key=api_key)
    return create_react_agent(model=llm, tools=tools)


async def chat_loop(agent) -> None:
    print()
    print("Ready. Type a message (or 'exit' to quit).")
    while True:
        message = input("> ").strip()
        if message.lower() in {"exit", "quit"}:
            break
        if not message:
            continue
        result = await agent.ainvoke({"messages": [{"role": "user", "content": message}]})
        print(result["messages"][-1].content)


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
