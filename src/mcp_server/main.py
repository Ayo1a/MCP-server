import httpx # library for building http request in py
from mcp.server.fastmcp import FastMCP #framework for MCP servers

# אתחול שרת ה-MCP עם השם של הפרויקט שלך
mcp = FastMCP("Internal System Bridge") #instance of the server, this is the name that AI will see

CORE_API_URL = "http://127.0.0.1:8000/api/v1" # hold the core mock adress

#decorator that telling the fastMCT to show this function out as a tool
@mcp.tool() 
async def fetch_system_text_report() -> str:
    #explanations to the LLM
    """
    Fetches the latest internal system status report in markdown format.
    Use this when you need logs, uptime data, or infrastructure metrics.
    """
    async with httpx.AsyncClient() as client:
        #wrapping each http call with try to avoid server crashing due to network issues
        try: 
            response = await client.get(f"{CORE_API_URL}/data/text") #free thr CPU to other tasks with await until answer being return
            response.raise_for_status() #http function checking for status
            data = response.json() #convert JSON to py dictionary 
            return data.get("content", "No content found.") #taking contebt key from the dictionary and return it to the LLM, otherwise return follow back 
        except httpx.HTTPError as e:
            return f"Error communicating with Core API: {str(e)}"

@mcp.tool()
async def fetch_system_image_metadata() -> str:
    """
    Fetches metadata for internal simulated image generation pipelines.
    Use this to inspect dimensions, formats, and mock URLs for rendering.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{CORE_API_URL}/data/image")
            response.raise_for_status()
            data = response.json()
            return ( # return JSON object with few keys
                #using f-string to give AI clean string
                f"Image ID: {data.get('image_id')}\n"
                f"Dimensions: {data.get('dimensions')}\n"
                f"Format: {data.get('format')}\n"
                f"Mock URL: {data.get('mock_url')}"
            )
        except httpx.HTTPError as e:
            return f"Error communicating with Core API: {str(e)}"

if __name__ == "__main__":
    # # הרצה במצב פיתוח (UI נוח לבדיקות)
    # mcp.run(transport="dev")
    # הרצה באמצעות הפרוטוקול הסטנדרטי של MCP (קלט/פלט סטנדרטי)
    mcp.run(transport="stdio")