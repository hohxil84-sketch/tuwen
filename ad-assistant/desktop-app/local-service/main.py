"""Local FastAPI Service Entry Point — Sprint-01 Task-04 implementation.

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

Sprint-01 Task-04: OCR minimal loop (pure local).
"""

import logging
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from wrappers.paddleocr import PaddleOCREngine
from history import init_db

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("local-service")

# ---------------------------------------------------------------------------
# Engine initialisation
# ---------------------------------------------------------------------------

_engine = PaddleOCREngine(
    lang=os.environ.get("PADDLEOCR_LANG", "ch"),
    use_angle_cls=True,
)

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle.

    On startup:
    - Initialise the local SQLite database (creates tables if needed).
    - Pre-warm the OCR engine (optional — can also lazy-load on first request).
    """
    logger.info("Local service starting up...")

    # Initialise SQLite database
    try:
        init_db()
        logger.info("SQLite database initialised")
    except Exception as exc:
        logger.warning("Failed to initialise SQLite database: %s", exc)

    # Pre-warm the OCR engine (attempt lazy load)
    try:
        _engine._ensure_engine()
        logger.info("PaddleOCR engine loaded successfully")
    except Exception as exc:
        logger.warning("PaddleOCR engine not ready (will retry on first request): %s", exc)

    yield

    logger.info("Local service shutting down.")


app = FastAPI(
    title="AI 图文广告助手 Local Service",
    version="0.1.0",
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS — localhost only
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:1420",
        "http://127.0.0.1:1420",
        "tauri://localhost",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Register OCR routes
# ---------------------------------------------------------------------------

from routes.ocr import router as ocr_router, set_ocr_engine

set_ocr_engine(_engine)
app.include_router(ocr_router)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@app.get("/health")
async def health():
    return {"status": "ok", "sprint": "01", "mode": "ocr-minimal"}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=9100)
