import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run_test():
    # הגדרת הפרמטרים להרצת שרת ה-MCP שלך
    server_params = StdioServerParameters(
        command="python",
        args=["src/mcp_server/main.py"],
    )
    
    print("Trying ti connect to the MCP server...")
    
    # יצירת חיבור Stdio אל השרת
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            # אתחול ה-Session
            await session.initialize() #client send message to server and being answered with server name 
            print("Connection worked!")
            
            # שליפת רשימת הכלים שהשרת מציע
            print("\n extract the tool list of the server")
            tools_response = await session.list_tools() #clients ask for tool list, MCP will scan all @mcp.tool()
            
            for tool in tools_response.tools:
                print(f"\n--- tool was found: {tool.name} ---")
                print(f"Description: {tool.description}")
                print(f"Required parameters: {tool.inputSchema}")

if __name__ == "__main__":
    asyncio.run(run_test())