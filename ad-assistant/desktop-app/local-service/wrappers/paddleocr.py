"""PaddleOCR Wrapper — Sprint-01 Task-04 implementation.

Safety rules:
- Parameter whitelist (no arbitrary param passthrough)
- File type validation (extension + MIME type, whitelist only)
- File size limit (default 50MB for images)
- Path restriction (only designated directories, no absolute path traversal)
- Timeout control (default 60s for OCR)
- Error code mapping (unified codes, no internal exception leakage)
- Log redaction (no file content, no username in paths)

OCR return structure conforms to ``docs/10-local-ai-tools-guide.md``:
{
    "text": "full recognized text",
    "blocks": [{"text": "...", "confidence": 0.98, "bbox": [0, 0, 100, 40]}],
    "engine": "paddleocr",
    "duration_ms": 1200
}
"""

import hashlib
import logging
import mimetypes
import os
import signal
import time
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ALLOWED_EXTENSIONS: set[str] = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"}
ALLOWED_MIME_TYPES: set[str] = {
    "image/png",
    "image/jpeg",
    "image/bmp",
    "image/tiff",
    "image/webp",
}

DEFAULT_MAX_SIZE_MB: int = 50
DEFAULT_TIMEOUT_SEC: int = 60

# PaddleOCR parameter whitelist — any parameter not in this set is rejected
ALLOWED_PARAMS: set[str] = {"lang", "use_angle_cls", "det_db_thresh", "rec_batch_num"}

# Magic bytes for image format verification
_MAGIC_SIGNATURES: list[tuple[bytes, str]] = [
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"BM", "image/bmp"),
    (b"II*\x00", "image/tiff"),
    (b"MM\x00*", "image/tiff"),
    (b"RIFF", "image/webp"),  # requires further check for WEBP chunk
]

# Size of header to read for magic byte detection
_MAGIC_HEADER_SIZE: int = 12


# ---------------------------------------------------------------------------
# OCRError — unified error type for OCR operations
# ---------------------------------------------------------------------------


class OCRError(Exception):
    """Unified OCR error with a machine-readable code.

    These codes are mapped to the ``{success, data, error, request_id}``
    response format by the route layer.  Codes intentionally do NOT
    expose internal PaddleOCR exception class-names or stack traces.
    """

    def __init__(self, code: str, message: str, details: Optional[dict[str, Any]] = None) -> None:
        self.code = code
        self.message = message
        self.details = details
        super().__init__(message)


# ---------------------------------------------------------------------------
# File validation helpers
# ---------------------------------------------------------------------------


def _read_magic_bytes(file_path: Path) -> bytes:
    """Read the first *N* bytes of a file for magic-byte detection."""
    try:
        with open(file_path, "rb") as fh:
            return fh.read(_MAGIC_HEADER_SIZE)
    except OSError as exc:
        raise OCRError(
            "FILE_NOT_READABLE",
            f"Cannot read file for validation: {file_path.name}",
            details={"reason": str(exc)},
        ) from exc


def _detect_mime_by_magic(header: bytes) -> Optional[str]:
    """Best-effort MIME detection from magic bytes.

    Returns a MIME string or ``None`` if the signature is unrecognised.
    """
    if header[:4] == b"\x89PNG":
        return "image/png"
    if header[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if header[:2] == b"BM":
        return "image/bmp"
    if header[:4] in (b"II*\x00", b"MM\x00*"):
        return "image/tiff"
    if header[:4] == b"RIFF" and len(header) >= 12 and header[8:12] == b"WEBP":
        return "image/webp"
    return None


def compute_image_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file, returning the first 16 hex characters.

    Used for image dedup in OCR history (``image_hash`` field).
    """
    sha = hashlib.sha256()
    with open(file_path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            sha.update(chunk)
    return sha.hexdigest()[:16]


def validate_image_file(
    file_path: Path,
    max_size_mb: int = DEFAULT_MAX_SIZE_MB,
    allowed_dir: Optional[Path] = None,
) -> Path:
    """Validate an image file before OCR processing.

    Checks (in order):
    1. File existence
    2. Extension whitelist
    3. MIME type (by magic bytes)
    4. Path restriction (must be inside *allowed_dir*)
    5. File size limit

    Returns the resolved absolute ``Path`` on success.

    Raises :exc:`OCRError` on any validation failure.
    """
    path = file_path.resolve()

    # 1. Existence
    if not path.exists():
        raise OCRError("FILE_NOT_FOUND", f"File not found: {file_path.name}")

    if not path.is_file():
        raise OCRError("FILE_NOT_FOUND", f"Path is not a regular file: {file_path.name}")

    # 2. Extension whitelist
    ext = path.suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise OCRError(
            "INVALID_FILE_TYPE",
            f"File extension '{ext}' is not supported. "
            f"Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
            details={"extension": ext, "allowed": sorted(ALLOWED_EXTENSIONS)},
        )

    # 3. MIME type detection by magic bytes (no fallback)
    # We intentionally do NOT fall back to extension-based MIME guessing
    # (mimetypes.guess_type) when magic bytes are unrecognised — that
    # would let garbage content pass just because the file is named .png.
    header = _read_magic_bytes(path)
    magic_mime = _detect_mime_by_magic(header)

    if magic_mime is None:
        raise OCRError(
            "INVALID_FILE_TYPE",
            "File content does not match a supported image format. "
            f"Allowed types: {', '.join(sorted(ALLOWED_MIME_TYPES))}",
            details={"allowed": sorted(ALLOWED_MIME_TYPES)},
        )
    elif magic_mime not in ALLOWED_MIME_TYPES:
        raise OCRError(
            "INVALID_FILE_TYPE",
            f"File detected as '{magic_mime}', which is not in the allowed image types. "
            f"Allowed: {', '.join(sorted(ALLOWED_MIME_TYPES))}",
            details={"detected_mime": magic_mime, "allowed": sorted(ALLOWED_MIME_TYPES)},
        )

    # 4. Path restriction — prevent directory traversal
    if allowed_dir is not None:
        allowed = allowed_dir.resolve()
        try:
            path.relative_to(allowed)
        except ValueError:
            raise OCRError(
                "PATH_TRAVERSAL_DENIED",
                "File is outside the allowed directory.",
                details={
                    "file_path": path.name,  # filename only, no PII leak
                    "allowed_dir": str(allowed),
                },
            )

    # 5. File size limit
    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > max_size_mb:
        raise OCRError(
            "FILE_TOO_LARGE",
            f"File size ({size_mb:.1f} MB) exceeds the limit of {max_size_mb} MB.",
            details={"size_mb": round(size_mb, 2), "limit_mb": max_size_mb},
        )

    logger.info(
        "Image file validated: ext=%s size_mb=%.1f", ext, size_mb
    )
    return path


# ---------------------------------------------------------------------------
# PaddleOCR Engine wrapper
# ---------------------------------------------------------------------------


class PaddleOCREngine:
    """Thin wrapper around PaddleOCR with safety constraints.

    - Only whitelisted parameters are forwarded to PaddleOCR.
    - Lazy-loads the underlying PaddleOCR instance on first use.
    - Handles model-not-found with a clear error code.
    """

    def __init__(self, **kwargs: Any) -> None:
        # Filter to allowed parameters only — silently drop unknowns
        safe: dict[str, Any] = {}
        for key, value in kwargs.items():
            if key in ALLOWED_PARAMS:
                safe[key] = value
            else:
                logger.warning("PaddleOCR param rejected (not in whitelist): %s", key)
        self._params = safe
        self._engine: Any = None

    @property
    def is_ready(self) -> bool:
        """Return ``True`` when the underlying PaddleOCR instance has been loaded."""
        return self._engine is not None

    @staticmethod
    def _check_model_cache(cache_path: Path) -> bool:
        """Return ``True`` if PaddleOCR model files exist in *cache_path*.

        Walks the directory tree looking for ``.pdmodel`` files (Paddle
        inference model format).  An empty or missing directory means
        models have not been downloaded yet.
        """
        if not cache_path.exists():
            return False
        for _root, _dirs, files in os.walk(cache_path):
            if any(f.endswith(".pdmodel") for f in files):
                return True
        return False

    def _ensure_engine(self) -> None:
        """Lazy-initialize the PaddleOCR engine if not already loaded.

        **Runtime constraint (per Task-04 §3):**  PaddleOCR auto-download
        MUST be disabled at runtime.  If the model cache is missing, this
        method raises ``OCR_MODEL_NOT_FOUND`` **before** calling the
        PaddleOCR constructor — the constructor is never reached without
        a confirmed cache, so it cannot trigger a network download.

        Raises :exc:`OCRError` when:
        - PaddleOCR or paddle are not installed
        - Model cache is missing / empty (``OCR_MODEL_NOT_FOUND``)
        - Any other initialization failure occurs
        """
        if self._engine is not None:
            return

        try:
            from paddleocr import PaddleOCR  # type: ignore[import-untyped]
        except ImportError:
            raise OCRError(
                "OCR_ENGINE_NOT_INSTALLED",
                "PaddleOCR is not installed. "
                "Run: pip install paddleocr>=3.0.0",
            )

        # ---- Guard: refuse to call PaddleOCR() when models are missing ----
        # This MUST happen *before* PaddleOCR() is constructed, otherwise
        # PaddleOCR will attempt a network download internally.
        cache_home = os.environ.get("PADDLEOCR_HOME", os.path.expanduser("~/.paddleocr"))
        cache_path = Path(cache_home)

        if not self._check_model_cache(cache_path):
            raise OCRError(
                "OCR_MODEL_NOT_FOUND",
                "OCR model files not found in local cache. "
                "Please run the initialization script first:\n"
                f"    python scripts/init_paddleocr_models.py\n"
                f"Or manually place model files in: {cache_home}",
                details={
                    "cache_dir": str(cache_home),
                    "help": "Run scripts/init_paddleocr_models.py to download models (~50-100 MB, one-time operation).",
                },
            )

        # ---- Cache confirmed — safe to initialise (no network needed) ----
        try:
            self._engine = PaddleOCR(**self._params)
        except Exception as exc:
            raise OCRError(
                "OCR_ENGINE_INIT_FAILED",
                "Failed to initialize PaddleOCR engine.",
            ) from exc

    def recognize(
        self,
        image_path: Path,
        timeout: int = DEFAULT_TIMEOUT_SEC,
    ) -> dict[str, Any]:
        """Run OCR on *image_path* and return a structured result dict.

        The returned dict matches ``docs/10-local-ai-tools-guide.md``::

            {
                "text": "full recognized text (lines joined by \\\\n)",
                "blocks": [{"text": "...", "confidence": 0.98, "bbox": [x1,y1,x2,y2]}],
                "engine": "paddleocr",
                "duration_ms": 1200
            }

        Parameters
        ----------
        image_path:
            Absolute path to the validated image file.
        timeout:
            Maximum seconds for the OCR call (enforced via SIGALRM on Unix,
            best-effort on Windows).

        Raises
        ------
        OCRError
            On recognition failure, timeout, or engine not initialized.
        """
        self._ensure_engine()
        assert self._engine is not None

        start = time.perf_counter()

        # Install alarm-based timeout (Unix only)
        old_handler = None
        timed_out = False

        def _on_timeout(signum, frame):
            nonlocal timed_out
            timed_out = True
            raise TimeoutError(f"OCR timed out after {timeout}s")

        try:
            if hasattr(signal, "SIGALRM"):
                old_handler = signal.signal(signal.SIGALRM, _on_timeout)
                signal.alarm(timeout)

            result = self._engine.ocr(str(image_path))

        except TimeoutError:
            raise OCRError(
                "OCR_TIMEOUT",
                f"OCR recognition exceeded the time limit of {timeout}s.",
                details={"timeout_s": timeout},
            )
        except OCRError:
            raise
        except Exception as exc:
            # Map any unexpected PaddleOCR internal exception to a safe code
            logger.error(
                "PaddleOCR recognition failed for file: %s", image_path.name
            )
            raise OCRError(
                "OCR_RECOGNITION_FAILED",
                "OCR recognition failed. Please try again with a different image.",
            ) from exc
        finally:
            if hasattr(signal, "SIGALRM"):
                signal.alarm(0)
                if old_handler is not None:
                    signal.signal(signal.SIGALRM, old_handler)

        duration_ms = int((time.perf_counter() - start) * 1000)

        # Normalize PaddleOCR result to our standard structure
        blocks: list[dict[str, Any]] = []
        full_text_parts: list[str] = []

        # PaddleOCR returns: [[[bbox, (text, confidence)], ...]]
        if result and result[0]:
            for line in result[0]:
                bbox_points = line[0]  # [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
                text = line[1][0] if isinstance(line[1], (list, tuple)) else str(line[1])
                confidence = line[1][1] if isinstance(line[1], (list, tuple)) and len(line[1]) > 1 else 1.0

                # Convert 4-point polygon to axis-aligned bounding box [x1, y1, x2, y2]
                xs = [p[0] for p in bbox_points]
                ys = [p[1] for p in bbox_points]
                flat_bbox = [int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))]

                blocks.append({
                    "text": text,
                    "confidence": round(float(confidence), 4),
                    "bbox": flat_bbox,
                })
                full_text_parts.append(text)

        return {
            "text": "\n".join(full_text_parts),
            "blocks": blocks,
            "engine": "paddleocr",
            "duration_ms": duration_ms,
        }
