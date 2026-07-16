from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI(
    title="Core API Mock Server",
    description="Simulates internal company backend systems for MCP infrastructure development",
    version="1.0.0"
)

# דאטה מדומה עבור כלי הטקסט
MOCK_TEXT_DATA = {
    "report_id": "REP-2026-XYZ",
    "status": "Success",
    "generated_at": "2026-06-17T12:00:00Z",
    "content": "### Internal System Status Report\n\nAll core components are operating within normal parameters.\n- **Database:** Stable (99.9% uptime)\n- **Authentication Gateway:** Nominal latency (45ms)\n- **Storage Clusters:** 62% capacity utilized."
}

# דאטה מדומה עבור כלי התמונה
MOCK_IMAGE_DATA = {
    "image_id": "IMG-404-DATA",
    "format": "PNG",
    "dimensions": "1024x1024",
    "mock_url": "https://placeholder.pics/svg/300",
    "status": "Rendered"
}

@app.get("/")
def read_root():
    return {"message": "Internal Core API Mock is running successfully!"}

@app.get("/api/v1/data/text")
def get_mock_text():
    """Returns static, well-formed markdown data mimicking internal database logs."""
    return JSONResponse(content=MOCK_TEXT_DATA)

@app.get("/api/v1/data/image")
def get_mock_image():
    """Returns simulated image metadata mimicking media generation pipelines."""
    return JSONResponse(content=MOCK_IMAGE_DATA)