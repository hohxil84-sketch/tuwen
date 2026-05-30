"""Cloud Backend FastAPI Application — Sprint-01 skeleton.

Only /health endpoint is active. All business routes are placeholders.
"""

from fastapi import FastAPI

app = FastAPI(
    title="AI 图文广告助手 Cloud Backend",
    version="0.1.0",
    docs_url=None,       # disabled in skeleton
    redoc_url=None,      # disabled in skeleton
)


@app.get("/health")
async def health():
    """Health check — Sprint-01 minimal skeleton."""
    return {"status": "ok", "sprint": "01", "mode": "skeleton"}
