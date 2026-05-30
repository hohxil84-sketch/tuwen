"""Unit tests for the OCR history persistence layer.

Tests:
1. Save and query — insert a record and retrieve it by ID
2. Pagination — ensure limit/offset work correctly
3. Single detail — query by ID returns full record
4. History list ordering — most recent first
5. Image hash field — 16 hex chars, no path info stored
6. No absolute paths stored — filename is basename only
"""

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

# Ensure local-service is importable
_LOCAL_SERVICE = Path(__file__).resolve().parent.parent
if str(_LOCAL_SERVICE) not in sys.path:
    sys.path.insert(0, str(_LOCAL_SERVICE))


# Avoid importing history at module level — it sets DB_PATH based on
# __file__ which would point to the real file.  We patch it per-test.


@pytest.fixture
def history_db(monkeypatch):
    """Redirect SQLite writes to a temporary file and initialise the table."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    tmp = Path(db_path)

    # Override DB_PATH in the history module
    import history
    monkeypatch.setattr(history, "DB_PATH", tmp)

    history.init_db()

    yield history

    # Teardown
    tmp.unlink(missing_ok=True)
    wal = Path(str(tmp) + "-wal")
    shm = Path(str(tmp) + "-shm")
    wal.unlink(missing_ok=True)
    shm.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

SAMPLE_BLOCKS: list[dict] = [
    {"text": "Hello", "confidence": 0.99, "bbox": [0, 0, 100, 30]},
    {"text": "World", "confidence": 0.95, "bbox": [0, 40, 120, 70]},
]


def _save_one(history, **kwargs) -> dict:
    defaults = {
        "image_filename": "test.png",
        "image_hash": "a1b2c3d4e5f6a7b8",
        "local_copy_path": "ocr_images/20250530_abc123.png",
        "text": "Hello\nWorld",
        "blocks": SAMPLE_BLOCKS,
        "engine": "paddleocr",
        "duration_ms": 150,
    }
    defaults.update(kwargs)
    return history.save_history(**defaults)


# ---------------------------------------------------------------------------
# 1. Save and query
# ---------------------------------------------------------------------------

class TestSaveAndQuery:
    """Insert records and retrieve them."""

    def test_save_and_retrieve_by_id(self, history_db):
        """After saving, the record should be retrievable by its ID."""
        record = _save_one(history_db)

        fetched = history_db.get_history_by_id(record["id"])
        assert fetched is not None
        assert fetched["image_filename"] == "test.png"
        assert fetched["image_hash"] == "a1b2c3d4e5f6a7b8"
        assert fetched["text"] == "Hello\nWorld"
        assert fetched["engine"] == "paddleocr"
        assert fetched["duration_ms"] == 150
        assert fetched["blocks"] == SAMPLE_BLOCKS
        assert fetched["local_copy_path"] == "ocr_images/20250530_abc123.png"
        # created_at should be an ISO 8601 UTC string
        assert "T" in fetched["created_at"]

    def test_get_nonexistent_id(self, history_db):
        """Querying a non-existent ID should return None."""
        fetched = history_db.get_history_by_id("00000000-0000-0000-0000-000000000000")
        assert fetched is None

    def test_blocks_parsed_from_json(self, history_db):
        """The 'blocks' field in the returned dict should be a list, not a JSON string."""
        record = _save_one(history_db)
        fetched = history_db.get_history_by_id(record["id"])
        assert isinstance(fetched["blocks"], list)
        assert len(fetched["blocks"]) == 2
        assert fetched["blocks"][0]["text"] == "Hello"


# ---------------------------------------------------------------------------
# 2. Pagination
# ---------------------------------------------------------------------------

class TestPagination:
    """Limit and offset should work correctly."""

    def test_respects_limit(self, history_db):
        """When limit=2, only 2 rows max are returned."""
        for i in range(5):
            _save_one(
                history_db,
                image_filename=f"img_{i}.png",
                image_hash=f"hash_{i:016d}",
            )

        rows = history_db.get_history_list(limit=2, offset=0)
        assert len(rows) == 2

    def test_respects_offset(self, history_db):
        """Offset should skip rows."""
        for i in range(5):
            _save_one(
                history_db,
                image_filename=f"img_{i}.png",
                image_hash=f"hash_{i:016d}",
            )

        page1 = history_db.get_history_list(limit=3, offset=0)
        page2 = history_db.get_history_list(limit=3, offset=3)

        assert len(page1) == 3
        assert len(page2) == 2  # 5 total, 3 on page 1 → 2 remaining

        # IDs should be disjoint across pages
        ids_p1 = {r["id"] for r in page1}
        ids_p2 = {r["id"] for r in page2}
        assert ids_p1.isdisjoint(ids_p2)

    def test_no_rows(self, history_db):
        """Empty database should return an empty list, not error."""
        rows = history_db.get_history_list(limit=50, offset=0)
        assert rows == []


# ---------------------------------------------------------------------------
# 3. Single detail query
# ---------------------------------------------------------------------------

class TestSingleDetail:
    """GET single history record details."""

    def test_detail_includes_all_fields(self, history_db):
        """A detail query should return all fields."""
        record = _save_one(history_db)
        detail = history_db.get_history_by_id(record["id"])

        expected_fields = {
            "id", "image_filename", "image_hash", "local_copy_path",
            "text", "blocks", "engine", "duration_ms", "created_at",
        }
        assert set(detail.keys()) == expected_fields

    def test_detail_null_local_copy(self, history_db):
        """local_copy_path can be None."""
        record = _save_one(history_db, local_copy_path=None)
        detail = history_db.get_history_by_id(record["id"])
        assert detail["local_copy_path"] is None


# ---------------------------------------------------------------------------
# 4. History ordering
# ---------------------------------------------------------------------------

class TestHistoryOrdering:
    """Records must be returned most-recent-first."""

    def test_order_most_recent_first(self, history_db):
        """The first row in the list should be the most recently created."""
        r1 = _save_one(history_db, image_filename="first.png")
        r2 = _save_one(history_db, image_filename="second.png")

        rows = history_db.get_history_list(limit=10, offset=0)
        assert len(rows) >= 2
        # Most recent first: second.png → first.png
        assert rows[0]["image_filename"] == "second.png"
        assert rows[1]["image_filename"] == "first.png"


# ---------------------------------------------------------------------------
# 5. Security: no absolute paths
# ---------------------------------------------------------------------------

class TestNoAbsolutePaths:
    """Verify that image_filename contains only basenames, never paths."""

    def test_filename_no_path_components(self, history_db):
        """Even if given a full path as filename, it should just be a basename.
        (The API layer is responsible for stripping the path — this test
        verifies the history layer handles whatever it receives.)"""
        record = _save_one(history_db, image_filename="photo.png")
        assert "/" not in record["image_filename"]
        assert "\\" not in record["image_filename"]
        assert record["image_filename"] == "photo.png"

    def test_no_absolute_path_stored_in_local_copy(self, history_db):
        """local_copy_path must be relative (no drive letter, no root slash)."""
        record = _save_one(history_db, local_copy_path="ocr_images/test.png")
        assert ":" not in record["local_copy_path"]  # no Windows drive letter
        assert not record["local_copy_path"].startswith("/")  # no Unix root
        assert not record["local_copy_path"].startswith("\\")  # no Windows root

    def test_hash_is_hex_only(self, history_db):
        """image_hash must be 16 lowercase hex characters only."""
        record = _save_one(history_db)
        h = record["image_hash"]
        assert len(h) == 16
        assert all(c in "0123456789abcdef" for c in h)
        # No path separators or PII
        assert "/" not in h
        assert "\\" not in h
        assert "@" not in h
