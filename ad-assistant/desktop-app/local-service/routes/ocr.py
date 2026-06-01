"""Local OCR API Routes — Sprint-01 Task-04 + Sprint-04 Task-03.

Endpoints
---------
POST   /local/ocr                  Accept an image file, run PaddleOCR, persist history.
GET    /local/ocr/health            OCR engine readiness check.
GET    /local/ocr/history           Paginated OCR history list.
GET    /local/ocr/history/{id}      Single OCR history detail.
DELETE /local/ocr/history/{id}      Delete a single history record + sandbox file.
DELETE /local/ocr/history           Clear ALL history records + sandbox files.

All responses follow the unified ``{success, data, error, request_id}`` format
defined in ``docs/05-api-contract.md``.
"""

import logging
import shutil
import uuid as _uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, File, Query, Request, UploadFile
from fastapi.responses import JSONResponse

from wrappers.paddleocr import (
    ALLOWED_EXTENSIONS,
    DEFAULT_MAX_SIZE_MB,
    DEFAULT_TIMEOUT_SEC,
    OCRError,
    PaddleOCREngine,
    compute_image_hash,
    validate_image_file,
)
from history import (
    clear_all_history,
    delete_history_by_id,
    get_history_by_id,
    get_history_list,
    init_db,
    save_history,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Sandbox image storage
# ---------------------------------------------------------------------------

# Directory where local copies of uploaded images are stored.
# All paths recorded in ``local_copy_path`` are relative to this directory.
SANDBOX_IMAGES_DIR: Path = Path(__file__).resolve().parent.parent / "ocr_images"


def _ensure_sandbox_dir() -> None:
    """Create the sandbox images directory if it doesn't exist."""
    SANDBOX_IMAGES_DIR.mkdir(parents=True, exist_ok=True)


def _copy_to_sandbox(source_path: Path) -> Optional[str]:
    """Copy *source_path* into the sandbox directory.

    Returns a sandbox-relative path (e.g. ``ocr_images/20250530_abc123.png``)
    or ``None`` if the copy fails.
    """
    _ensure_sandbox_dir()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    unique = _uuid.uuid4().hex[:8]
    ext = source_path.suffix.lower()
    dest_name = f"{timestamp}_{unique}{ext}"
    dest_path = SANDBOX_IMAGES_DIR / dest_name
    try:
        shutil.copy2(source_path, dest_path)
        # Store as relative path from the local-service root
        return f"ocr_images/{dest_name}"
    except OSError as exc:
        logger.error("Failed to copy image to sandbox: %s", exc)
        return None


def _cleanup_sandbox_copy(rel_path: Optional[str]) -> None:
    """Remove a previously created sandbox image copy.

    Called when OCR fails after the copy was already written, and
    when a user deletes a history record.  Gracefully no-ops if the
    file is already gone.

    **Path-safety enforcement:** Only deletes files that pass every
    validation check below.  Any failure logs a warning and returns
    without touching the filesystem.
    """
    if rel_path is None:
        return

    _safe = rel_path.replace("\\", "/")

    # ---- 1. Must be relative (no leading /, no UNC, no drive letter) ----
    if _safe.startswith("/"):
        logger.warning("_cleanup_sandbox_copy rejected (absolute path): %s", rel_path[:120])
        return
    if ":" in _safe:
        logger.warning(
            "_cleanup_sandbox_copy rejected (drive letter or UNC): %s",
            rel_path[:120],
        )
        return

    # ---- 2. Must start with "ocr_images/" ------------------------------
    if not _safe.startswith("ocr_images/"):
        logger.warning(
            "_cleanup_sandbox_copy rejected (not under ocr_images/): %s",
            rel_path[:120],
        )
        return

    # ---- 3. No ".." path traversal -------------------------------------
    if ".." in _safe.split("/"):
        logger.warning(
            "_cleanup_sandbox_copy rejected (path traversal): %s",
            rel_path[:120],
        )
        return

    # ---- 4. Resolve and verify it is still inside SANDBOX_IMAGES_DIR ----
    try:
        abs_path = (SANDBOX_IMAGES_DIR.parent / _safe).resolve()
        sandbox_root = SANDBOX_IMAGES_DIR.resolve()
        if not abs_path.is_relative_to(sandbox_root):
            logger.warning(
                "_cleanup_sandbox_copy rejected (resolved outside sandbox): %s → %s",
                rel_path[:120],
                str(abs_path)[:200],
            )
            return
    except (OSError, ValueError) as exc:
        logger.warning(
            "_cleanup_sandbox_copy rejected (resolve error): %s — %s",
            rel_path[:120],
            exc,
        )
        return

    # ---- 5. Delete the file --------------------------------------------
    try:
        if abs_path.exists():
            abs_path.unlink()
            logger.info("Cleaned up sandbox copy: %s", rel_path)
    except OSError as exc:
        logger.warning("Failed to clean up sandbox copy %s: %s", rel_path, exc)


# ---------------------------------------------------------------------------
# Response helpers (unified format, docs/05-api-contract.md)
# ---------------------------------------------------------------------------


def _ok(data: Any, request_id: Optional[str] = None) -> dict[str, Any]:
    """Build a success response dict."""
    return {
        "success": True,
        "data": data,
        "error": None,
        "request_id": request_id or f"req_{_uuid.uuid4().hex[:12]}",
    }


def _err(
    code: str,
    message: str,
    status_code: int = 400,
    request_id: Optional[str] = None,
    details: Optional[dict[str, Any]] = None,
) -> JSONResponse:
    """Build an error JSONResponse in the unified format."""
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": code,
                "message": message,
                "details": details,
            },
            "request_id": request_id or f"req_{_uuid.uuid4().hex[:12]}",
        },
    )


def _get_request_id(request: Request) -> str:
    """Extract or generate a request_id from the incoming request."""
    rid = request.headers.get("X-Request-ID", "")
    if not rid:
        rid = f"req_{_uuid.uuid4().hex[:12]}"
    return rid


# ---------------------------------------------------------------------------
# Engine reference (set by main.py on startup)
# ---------------------------------------------------------------------------

_engine: Optional[PaddleOCREngine] = None


def set_ocr_engine(engine: PaddleOCREngine) -> None:
    """Register the global OCR engine instance.

    Called from ``main.py`` during application startup.
    """
    global _engine
    _engine = engine


def _get_engine() -> PaddleOCREngine:
    """Return the current OCR engine, raising if not yet initialized."""
    if _engine is None:
        raise OCRError("OCR_ENGINE_NOT_INITIALIZED", "OCR engine has not been initialized yet.")
    return _engine


# ---------------------------------------------------------------------------
# POST /local/ocr
# ---------------------------------------------------------------------------


@router.post("/local/ocr")
async def ocr_upload(
    request: Request,
    image: UploadFile = File(...),
) -> JSONResponse:
    """Accept an image file, run PaddleOCR, persist history, return results.

    The uploaded file is validated (extension, MIME by magic bytes, size)
    before being copied into the sandbox directory for future reference.
    """
    rid = _get_request_id(request)

    # ---- 1. Validate file presence -----------------------------------------
    if image.filename is None or image.filename == "":
        return _err("MISSING_FILE", "No image file provided.", status_code=422, request_id=rid)

    if image.content_type is None:
        return _err("MISSING_CONTENT_TYPE", "Content-Type header is required.", status_code=422, request_id=rid)

    # ---- 2. Validate extension ---------------------------------------------
    filename = Path(image.filename).name  # basename only, discard any path
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return _err(
            "INVALID_FILE_TYPE",
            f"File type '{ext}' is not supported. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
            status_code=422,
            request_id=rid,
            details={"extension": ext, "allowed": sorted(ALLOWED_EXTENSIONS)},
        )

    # ---- 3. Validate MIME type ---------------------------------------------
    if image.content_type not in {"image/png", "image/jpeg", "image/bmp", "image/tiff", "image/webp"}:
        return _err(
            "INVALID_FILE_TYPE",
            f"Content-Type '{image.content_type}' is not a supported image format.",
            status_code=422,
            request_id=rid,
            details={"content_type": image.content_type},
        )

    # ---- 4. Read file content ----------------------------------------------
    try:
        contents = await image.read()
    except Exception as exc:
        return _err("FILE_READ_ERROR", "Failed to read uploaded file.", status_code=400, request_id=rid)

    if len(contents) == 0:
        return _err("EMPTY_FILE", "Uploaded file is empty.", status_code=422, request_id=rid)

    # ---- 5. Validate size --------------------------------------------------
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > DEFAULT_MAX_SIZE_MB:
        return _err(
            "FILE_TOO_LARGE",
            f"File size ({size_mb:.1f} MB) exceeds the limit of {DEFAULT_MAX_SIZE_MB} MB.",
            status_code=413,
            request_id=rid,
            details={"size_mb": round(size_mb, 2), "limit_mb": DEFAULT_MAX_SIZE_MB},
        )

    # ---- 6. Write to a temp file for validation & processing ---------------
    _ensure_sandbox_dir()
    tmp_name = f"_tmp_{_uuid.uuid4().hex}{ext}"
    tmp_path = SANDBOX_IMAGES_DIR / tmp_name
    try:
        tmp_path.write_bytes(contents)
    except OSError as exc:
        return _err("FILE_WRITE_ERROR", "Failed to save uploaded file.", status_code=500, request_id=rid)

    try:
        # ---- 7. Validate file (magic bytes + path) -------------------------
        try:
            validated_path = validate_image_file(
                tmp_path,
                max_size_mb=DEFAULT_MAX_SIZE_MB,
                allowed_dir=SANDBOX_IMAGES_DIR,
            )
        except OCRError as exc:
            return _err(exc.code, exc.message, status_code=422, request_id=rid, details=exc.details)

        # ---- 8. Compute image hash -----------------------------------------
        image_hash = compute_image_hash(validated_path)

        # ---- 9. Copy to sandbox (permanent copy) ---------------------------
        local_copy_path = _copy_to_sandbox(validated_path)

        # ---- 10. Run OCR ---------------------------------------------------
        try:
            engine = _get_engine()
            result = engine.recognize(validated_path, timeout=DEFAULT_TIMEOUT_SEC)
        except OCRError as exc:
            # Clean up the sandbox copy created in step 9 — no history
            # record references it, so it would be an orphaned user-image
            # copy on disk otherwise.
            _cleanup_sandbox_copy(local_copy_path)
            return _err(exc.code, exc.message, status_code=500, request_id=rid, details=exc.details)

        # ---- 11. Persist history -------------------------------------------
        try:
            init_db()
            history_record = save_history(
                image_filename=filename,
                image_hash=image_hash,
                local_copy_path=local_copy_path,
                text=result["text"],
                blocks=result["blocks"],
                engine=result["engine"],
                duration_ms=result["duration_ms"],
            )
        except Exception as exc:
            logger.error("Failed to save OCR history: %s", exc)
            # History persistence failure is non-fatal — still return OCR result
            history_record = None

        # ---- 12. Build response --------------------------------------------
        response_data = {
            "text": result["text"],
            "blocks": result["blocks"],
            "engine": result["engine"],
            "duration_ms": result["duration_ms"],
            "image_hash": image_hash,
            "history_id": history_record["id"] if history_record else None,
        }
        return JSONResponse(content=_ok(response_data, request_id=rid))

    finally:
        # ---- 13. Cleanup temp file -----------------------------------------
        try:
            if tmp_path.exists():
                tmp_path.unlink()
        except OSError:
            pass


# ---------------------------------------------------------------------------
# GET /local/ocr/health
# ---------------------------------------------------------------------------


@router.get("/local/ocr/health")
async def ocr_health(request: Request) -> JSONResponse:
    """Return OCR engine readiness status.

    Tries to initialise the engine if not already loaded — the first call
    may be slow while models are loaded into memory.
    """
    rid = _get_request_id(request)
    try:
        engine = _get_engine()
        engine._ensure_engine()
        ready = engine.is_ready
    except OCRError as exc:
        return JSONResponse(
            content=_ok(
                {
                    "status": "unavailable",
                    "engine": "paddleocr",
                    "error_code": exc.code,
                    "message": exc.message,
                },
                request_id=rid,
            )
        )

    return JSONResponse(
        content=_ok(
            {
                "status": "ok" if ready else "loading",
                "engine": "paddleocr",
            },
            request_id=rid,
        )
    )


# ---------------------------------------------------------------------------
# GET /local/ocr/history
# ---------------------------------------------------------------------------


@router.get("/local/ocr/history")
async def ocr_history_list(
    request: Request,
    limit: int = Query(50, ge=1, le=200, description="Max records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
) -> JSONResponse:
    """Return a paginated list of OCR history records (most recent first)."""
    rid = _get_request_id(request)
    try:
        init_db()
        rows = get_history_list(limit=limit, offset=offset)
    except Exception as exc:
        logger.error("Failed to query OCR history: %s", exc)
        return _err("HISTORY_QUERY_FAILED", "Failed to query OCR history.", status_code=500, request_id=rid)

    return JSONResponse(content=_ok({"items": rows, "limit": limit, "offset": offset}, request_id=rid))


# ---------------------------------------------------------------------------
# GET /local/ocr/history/{id}
# ---------------------------------------------------------------------------


@router.get("/local/ocr/history/{record_id}")
async def ocr_history_detail(
    request: Request,
    record_id: str,
) -> JSONResponse:
    """Return a single OCR history record by its UUID."""
    rid = _get_request_id(request)
    try:
        init_db()
        record = get_history_by_id(record_id)
    except Exception as exc:
        logger.error("Failed to query OCR history detail: %s", exc)
        return _err("HISTORY_QUERY_FAILED", "Failed to query OCR history detail.", status_code=500, request_id=rid)

    if record is None:
        return _err("NOT_FOUND", f"OCR history record '{record_id}' not found.", status_code=404, request_id=rid)

    return JSONResponse(content=_ok(record, request_id=rid))


# ---------------------------------------------------------------------------
# DELETE /local/ocr/history/{record_id}
# ---------------------------------------------------------------------------


@router.delete("/local/ocr/history/{record_id}")
async def ocr_history_delete(
    request: Request,
    record_id: str,
) -> JSONResponse:
    """Delete a single OCR history record and its sandbox image copy.

    The sandbox file is removed from disk (gracefully skipped if the
    file is already gone).  Returns 404 if the record does not exist.
    """
    rid = _get_request_id(request)
    try:
        init_db()
        found, local_copy_path = delete_history_by_id(record_id)
    except Exception as exc:
        logger.error("Failed to delete OCR history record %s: %s", record_id, exc)
        return _err(
            "HISTORY_DELETE_FAILED",
            "Failed to delete OCR history record.",
            status_code=500,
            request_id=rid,
        )

    if not found:
        return _err(
            "NOT_FOUND",
            f"OCR history record '{record_id}' not found.",
            status_code=404,
            request_id=rid,
        )

    # Clean up sandbox image copy (no-op if path is None or file already gone)
    _cleanup_sandbox_copy(local_copy_path)

    return JSONResponse(content=_ok({"deleted_id": record_id}, request_id=rid))


# ---------------------------------------------------------------------------
# DELETE /local/ocr/history
# ---------------------------------------------------------------------------


@router.delete("/local/ocr/history")
async def ocr_history_clear(request: Request) -> JSONResponse:
    """Delete ALL OCR history records and their sandbox image copies.

    Each sandbox file is removed from disk independently — failure
    to remove one file does not prevent others from being cleaned up.
    """
    rid = _get_request_id(request)
    try:
        init_db()
        deleted_count, local_copy_paths = clear_all_history()
    except Exception as exc:
        logger.error("Failed to clear OCR history: %s", exc)
        return _err(
            "HISTORY_CLEAR_FAILED",
            "Failed to clear OCR history.",
            status_code=500,
            request_id=rid,
        )

    # Clean up all sandbox image copies independently
    for path in local_copy_paths:
        _cleanup_sandbox_copy(path)

    logger.info(
        "Cleared %d OCR history records and %d sandbox files",
        deleted_count,
        len(local_copy_paths),
    )

    return JSONResponse(content=_ok({"deleted_count": deleted_count}, request_id=rid))
