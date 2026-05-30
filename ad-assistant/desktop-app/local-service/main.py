"""Local FastAPI Service Entry Point — Sprint-01 skeleton.

Responsibilities:
- Wrap local CLI tools (PaddleOCR)
- Provide controlled local processing API
- Listen ONLY on 127.0.0.1 (never expose to network)
- Do NOT hold cloud Provider API Keys
- Do NOT provide remote command execution

Lifecycle:
- Managed by Tauri sidecar
- Auto-restart on crash (max 3 retries)
- Health check endpoint for Tauri to verify readiness

Sprint-01: skeleton only — no business logic implemented yet.
"""

from fastapi import FastAPI

app = FastAPI(
    title="AI 图文广告助手 Local Service",
    version="0.1.0",
    docs_url=None,
    redoc_url=None,
)


@app.get("/health")
async def health():
    return {"status": "ok", "sprint": "01", "mode": "skeleton"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=9100)
