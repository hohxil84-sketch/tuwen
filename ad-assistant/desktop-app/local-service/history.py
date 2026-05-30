"""Local SQLite OCR History Persistence — Sprint-01 Task-04.

Manages the ``ocr_history`` table in a local SQLite database.

Security guarantees:
- NEVER stores user-original absolute paths (e.g. ``C:\\Users\\张三\\...``)
- ``image_filename`` contains only the basename, no directory components
- ``image_hash`` is the first 16 hex chars of SHA-256 (dedup, not reversible)
- ``local_copy_path`` is a sandbox-relative path (e.g. ``ocr_images/abc.png``)
- No plain-text tokens, passwords, API keys, or original image binaries stored
"""

import json
import logging
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Database location
# ---------------------------------------------------------------------------

DB_PATH: Path = Path(__file__).resolve().parent / "ocr_history.db"

# ---------------------------------------------------------------------------
# DDL
# ---------------------------------------------------------------------------

CREATE_TABLE_SQL: str = """
CREATE TABLE IF NOT EXISTS ocr_history (
    id              TEXT PRIMARY KEY,
    image_filename  TEXT NOT NULL,
    image_hash      TEXT NOT NULL,
    local_copy_path TEXT,
    text            TEXT,
    blocks_json     TEXT,
    engine          TEXT,
    duration_ms     INTEGER,
    created_at      TEXT NOT NULL
)
"""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_connection() -> sqlite3.Connection:
    """Return a new SQLite connection with row-factory set for dict-like access."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    """Convert a :class:`sqlite3.Row` to a plain dict.

    The ``blocks_json`` column is parsed back into a list so consumers
    don't need to call ``json.loads`` themselves.
    """
    d = dict(row)
    if d.get("blocks_json"):
        try:
            d["blocks"] = json.loads(d["blocks_json"])
        except json.JSONDecodeError:
            d["blocks"] = []
    else:
        d["blocks"] = []
    # Remove the raw JSON column — consumers should only see the parsed list
    d.pop("blocks_json", None)
    return d


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def init_db() -> None:
    """Create the ``ocr_history`` table if it does not exist.

    Idempotent — safe to call on every service startup.
    """
    conn = _get_connection()
    try:
        conn.execute(CREATE_TABLE_SQL)
        conn.commit()
    finally:
        conn.close()


def save_history(
    *,
    image_filename: str,
    image_hash: str,
    local_copy_path: Optional[str],
    text: str,
    blocks: list[dict[str, Any]],
    engine: str,
    duration_ms: int,
) -> dict[str, Any]:
    """Persist one OCR result row and return it as a dict.

    **Defence-in-depth:**  This function enforces its own path-safety
    constraints regardless of what the caller passes:

    - *image_filename* is reduced to ``Path(...).name`` (basename only).
    - *local_copy_path* is accepted only when it is a relative path under
      ``ocr_images/``; absolute / UNC paths are silently rejected and
      set to ``None``.

    Parameters
    ----------
    image_filename:
        Original file basename (no directory components).
    image_hash:
        First 16 hex chars of the image SHA-256.
    local_copy_path:
        Sandbox-relative path to the local image copy, or ``None``.
    text:
        Full recognised text (lines joined by ``\\n``).
    blocks:
        List of text-block dicts (``text``, ``confidence``, ``bbox``).
    engine:
        OCR engine identifier (``"paddleocr"``).
    duration_ms:
        OCR wall-clock time in milliseconds.

    Returns
    -------
    dict
        The newly inserted row, with ``blocks`` parsed from JSON.
    """
    # ---- Defence-in-depth: enforce basename only -------------------------
    # The API layer should already strip paths, but this is the final
    # guard — no directory components ever reach the database.
    _safe_filename = Path(image_filename).name

    # ---- Defence-in-depth: enforce sandbox-relative path ------------------
    _safe_local_copy: Optional[str] = None
    if local_copy_path is not None:
        lp = local_copy_path.replace("\\", "/")
        # Must be a relative path under ocr_images/, no absolute / UNC prefix
        if lp.startswith("/") or ":" in lp:
            logger.warning(
                "local_copy_path rejected (absolute or UNC): %s",
                local_copy_path[:80],
            )
        elif not lp.startswith("ocr_images/"):
            logger.warning(
                "local_copy_path rejected (not under ocr_images/): %s",
                local_copy_path[:80],
            )
        else:
            _safe_local_copy = lp

    record_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    blocks_json_str = json.dumps(blocks, ensure_ascii=False)

    conn = _get_connection()
    try:
        conn.execute(
            """INSERT INTO ocr_history
               (id, image_filename, image_hash, local_copy_path,
                text, blocks_json, engine, duration_ms, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                record_id,
                _safe_filename,
                image_hash,
                _safe_local_copy,
                text,
                blocks_json_str,
                engine,
                duration_ms,
                created_at,
            ),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM ocr_history WHERE id = ?", (record_id,)
        ).fetchone()
        return _row_to_dict(row) if row else {}
    finally:
        conn.close()


def get_history_list(limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
    """Return OCR history rows ordered by ``created_at`` descending.

    Parameters
    ----------
    limit:
        Max rows to return (default 50).
    offset:
        Number of rows to skip for pagination.
    """
    conn = _get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM ocr_history ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        conn.close()


def get_history_by_id(record_id: str) -> Optional[dict[str, Any]]:
    """Return a single OCR history row by its UUID primary key.

    Returns ``None`` when no row matches *record_id*.
    """
    conn = _get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM ocr_history WHERE id = ?", (record_id,)
        ).fetchone()
        return _row_to_dict(row) if row else None
    finally:
        conn.close()
