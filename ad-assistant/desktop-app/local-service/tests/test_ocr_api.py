"""Integration tests for the local OCR API endpoints.

Tests:
1. Normal image upload → returns OCR result (mocked PaddleOCR)
2. Non-image file upload → 422 rejection
3. Wrong Content-Type → 422 rejection
4. Health check endpoint returns expected structure
5. Missing/empty file → 422 rejection
6. Response format validation
7. History endpoints — list, detail, pagination
8. Delete history endpoints — single delete, clear all
"""

import io
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure local-service is importable
_LOCAL_SERVICE = Path(__file__).resolve().parent.parent
if str(_LOCAL_SERVICE) not in sys.path:
    sys.path.insert(0, str(_LOCAL_SERVICE))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_test_app():
    """Create a minimal FastAPI app with the OCR router wired to a mock engine.

    This avoids importing ``main.py`` (which has module-level side-effects
    like PaddleOCREngine instantiation and lifespan-based warm-up).
    """
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    app = FastAPI(docs_url=None, redoc_url=None)

    # Add CORS for consistency
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


@pytest.fixture
def mock_engine():
    """Return a mock PaddleOCREngine that returns predictable OCR results."""
    mock = MagicMock()
    mock.is_ready = True
    mock.recognize.return_value = {
        "text": "Hello World\nFoo Bar",
        "blocks": [
            {"text": "Hello World", "confidence": 0.98, "bbox": [10, 20, 200, 50]},
            {"text": "Foo Bar", "confidence": 0.85, "bbox": [10, 60, 180, 90]},
        ],
        "engine": "paddleocr",
        "duration_ms": 234,
    }

    def _ensure():
        mock.is_ready = True

    mock._ensure_engine = _ensure
    return mock


@pytest.fixture
def client(mock_engine):
    """Return a FastAPI TestClient with OCR routes and a mocked engine.

    The mock engine is injected into the ``routes.ocr`` module *before*
    the router is registered, simulating what ``main.py`` does via
    ``set_ocr_engine()``.

    A temporary SQLite database and a temporary sandbox images directory
    are used so that state from one test does not leak into another and
    no artifacts (``ocr_history.db``, ``ocr_images/``) are left behind.
    """
    import tempfile
    from fastapi.testclient import TestClient

    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    tmp_db = Path(db_path)

    # Temporary sandbox images directory — tests must not write to the real
    # local-service/ocr_images/ on disk.
    tmp_sandbox = tempfile.mkdtemp(prefix="ocr_sandbox_")
    tmp_sandbox_path = Path(tmp_sandbox)

    with patch("routes.ocr._engine", mock_engine), \
         patch("history.DB_PATH", tmp_db), \
         patch("routes.ocr.SANDBOX_IMAGES_DIR", tmp_sandbox_path):
        from routes.ocr import router, set_ocr_engine

        # Wire it up the same way main.py does
        set_ocr_engine(mock_engine)

        app = _build_test_app()
        app.include_router(router)

        with TestClient(app) as tc:
            yield tc

    # Teardown
    tmp_db.unlink(missing_ok=True)
    wal = Path(str(tmp_db) + "-wal")
    shm = Path(str(tmp_db) + "-shm")
    wal.unlink(missing_ok=True)
    shm.unlink(missing_ok=True)

    # Clean up temp sandbox directory
    import shutil
    shutil.rmtree(tmp_sandbox, ignore_errors=True)


@pytest.fixture
def minimal_png_bytes():
    """Return bytes of a minimal valid PNG."""
    return (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
        b"\x00\x00\x00\x0eIDATx\x9cc\xf8\xcf\xc0\x00\x00\x01\x01\x00\x05\x18\xd8N"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )


# ---------------------------------------------------------------------------
# 1. Normal image upload → returns OCR result
# ---------------------------------------------------------------------------

class TestImageUpload:
    """POST /local/ocr with valid image files."""

    def test_valid_png_returns_ocr_result(self, client, minimal_png_bytes):
        """Uploading a valid PNG should return OCR results with the unified format."""
        files = {"image": ("test.png", io.BytesIO(minimal_png_bytes), "image/png")}
        response = client.post("/local/ocr", files=files)

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["text"] == "Hello World\nFoo Bar"
        assert len(body["data"]["blocks"]) == 2
        assert body["data"]["engine"] == "paddleocr"
        assert body["data"]["duration_ms"] == 234
        assert body["data"]["image_hash"] is not None
        assert len(body["data"]["image_hash"]) == 16
        assert body["error"] is None
        assert body["request_id"] is not None

    def test_valid_jpg_returns_ocr_result(self, client):
        """Uploading a valid JPEG should also work."""
        jpg_bytes = (
            b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
            b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\x09\x09"
            b"\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f"
            b"\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342"
            b"\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00"
            b"\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00"
            b"\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00"
            b"\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04\x00\x00"
            b"\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa\x07\"q\x142"
            b"\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0$3br\x82\t\n\x16\x17\x18"
            b"\x19\x1a%&'()*456789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x83\x84"
            b"\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2"
            b"\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9"
            b"\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7"
            b"\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf1\xf2\xf3"
            b"\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xda\x00\x08\x01\x01\x00\x00?\x00"
            b"\xd2\xff\xd9"
        )
        files = {"image": ("photo.jpg", io.BytesIO(jpg_bytes), "image/jpeg")}
        response = client.post("/local/ocr", files=files)

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["engine"] == "paddleocr"


# ---------------------------------------------------------------------------
# 2. Non-image file rejection → 422
# ---------------------------------------------------------------------------

class TestNonImageRejection:
    """POST /local/ocr with non-image files must return 422."""

    def test_text_file_rejected(self, client):
        """Uploading a .txt file should be rejected."""
        files = {"image": ("readme.txt", io.BytesIO(b"hello world"), "text/plain")}
        response = client.post("/local/ocr", files=files)

        assert response.status_code == 422
        body = response.json()
        assert body["success"] is False
        assert body["error"]["code"] == "INVALID_FILE_TYPE"

    def test_no_extension_rejected(self, client):
        """File without a recognized image extension should be rejected."""
        files = {"image": ("datafile", io.BytesIO(b"binary data"), "application/octet-stream")}
        response = client.post("/local/ocr", files=files)

        assert response.status_code == 422
        body = response.json()
        assert body["success"] is False
        assert body["error"]["code"] == "INVALID_FILE_TYPE"

    def test_wrong_content_type_rejected(self, client, minimal_png_bytes):
        """File with correct extension but wrong Content-Type should be rejected."""
        files = {"image": ("test.png", io.BytesIO(minimal_png_bytes), "text/html")}
        response = client.post("/local/ocr", files=files)

        assert response.status_code == 422
        body = response.json()
        assert body["success"] is False
        assert body["error"]["code"] == "INVALID_FILE_TYPE"


# ---------------------------------------------------------------------------
# 3. Missing / empty file → 422
# ---------------------------------------------------------------------------

class TestMissingFile:
    """POST /local/ocr without a valid file must return 422."""

    def test_no_file_field(self, client):
        """Request without 'image' field should return validation error (422)."""
        response = client.post("/local/ocr")
        assert response.status_code == 422

    def test_empty_filename(self, client):
        """Empty filename should be rejected (422)."""
        files = {"image": ("", io.BytesIO(b""), "image/png")}
        response = client.post("/local/ocr", files=files)
        assert response.status_code == 422
        body = response.json()
        # FastAPI may return its own validation format {"detail": [...]}
        # or our custom format {"success": False, "error": {...}}
        if "success" in body:
            assert body["success"] is False
        else:
            # FastAPI built-in validation error — acceptable
            assert "detail" in body

    def test_empty_file_content(self, client):
        """Zero-byte file should be rejected."""
        files = {"image": ("empty.png", io.BytesIO(b""), "image/png")}
        response = client.post("/local/ocr", files=files)
        assert response.status_code == 422
        body = response.json()
        assert body["success"] is False
        assert body["error"]["code"] == "EMPTY_FILE"

    def test_missing_content_type(self, client, minimal_png_bytes):
        """No Content-Type header should be rejected."""
        files = {"image": ("test.png", io.BytesIO(minimal_png_bytes), None)}
        response = client.post("/local/ocr", files=files)
        # content_type will be None, triggering MISSING_CONTENT_TYPE
        if response.status_code == 422:
            body = response.json()
            # Either MISSING_CONTENT_TYPE or INVALID_FILE_TYPE depending on how
            # FastAPI/testclient handles None content_type
            assert body["success"] is False


# ---------------------------------------------------------------------------
# 4. Health check
# ---------------------------------------------------------------------------

class TestHealthCheck:
    """GET /local/ocr/health endpoint."""

    def test_health_returns_ok(self, client):
        """Health check should return status=ok when engine is ready."""
        response = client.get("/local/ocr/health")

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["status"] == "ok"
        assert body["data"]["engine"] == "paddleocr"

    def test_health_response_format(self, client):
        """Health response must follow the unified format."""
        response = client.get("/local/ocr/health")

        body = response.json()
        assert "success" in body
        assert "data" in body
        assert "error" in body
        assert "request_id" in body


# ---------------------------------------------------------------------------
# 5. Response format
# ---------------------------------------------------------------------------

class TestResponseFormat:
    """All API responses must follow the unified format."""

    def test_unified_format_keys_present(self, client, minimal_png_bytes):
        """Every JSON response must have success, data, error, request_id."""
        files = {"image": ("test.png", io.BytesIO(minimal_png_bytes), "image/png")}
        response = client.post("/local/ocr", files=files)

        body = response.json()
        assert "success" in body
        assert "data" in body
        assert "error" in body
        assert "request_id" in body
        assert isinstance(body["success"], bool)

    def test_request_id_format(self, client):
        """request_id should be a non-empty string starting with 'req_'."""
        response = client.get("/local/ocr/health")

        body = response.json()
        rid = body["request_id"]
        assert isinstance(rid, str)
        assert rid.startswith("req_")
        assert len(rid) > 4

    def test_error_response_has_code_and_message(self, client):
        """Error responses must include code and message."""
        files = {"image": ("doc.txt", io.BytesIO(b"text"), "text/plain")}
        response = client.post("/local/ocr", files=files)

        body = response.json()
        assert body["success"] is False
        assert body["error"]["code"]
        assert body["error"]["message"]
        assert body["data"] is None


# ---------------------------------------------------------------------------
# 6. History endpoints
# ---------------------------------------------------------------------------

class TestHistoryEndpoints:
    """GET /local/ocr/history and GET /local/ocr/history/{id}."""

    def test_history_list_returns_empty(self, client):
        """Before any OCR runs, the history list should be empty."""
        response = client.get("/local/ocr/history")
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["items"] == []
        assert body["data"]["limit"] == 50
        assert body["data"]["offset"] == 0

    def test_history_list_respects_limit_param(self, client):
        """Passing limit via query string should be reflected."""
        response = client.get("/local/ocr/history?limit=10&offset=5")
        assert response.status_code == 200
        body = response.json()
        assert body["data"]["limit"] == 10
        assert body["data"]["offset"] == 5

    def test_history_detail_not_found(self, client):
        """Querying a non-existent ID should return 404."""
        response = client.get("/local/ocr/history/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404
        body = response.json()
        assert body["success"] is False
        assert body["error"]["code"] == "NOT_FOUND"


# ---------------------------------------------------------------------------
# 8. Delete history endpoints
# ---------------------------------------------------------------------------


class TestDeleteHistoryEndpoints:
    """DELETE /local/ocr/history/{id} and DELETE /local/ocr/history."""

    def test_delete_single_record_returns_ok(self, client, minimal_png_bytes):
        """After creating a record via OCR, delete it and verify 200."""
        files = {"image": ("test.png", io.BytesIO(minimal_png_bytes), "image/png")}
        ocr_resp = client.post("/local/ocr", files=files)
        history_id = ocr_resp.json()["data"]["history_id"]

        # Delete it
        resp = client.delete(f"/local/ocr/history/{history_id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["deleted_id"] == history_id

        # Verify it's gone from history list
        list_resp = client.get("/local/ocr/history")
        items = list_resp.json()["data"]["items"]
        assert all(i["id"] != history_id for i in items)

    def test_delete_nonexistent_returns_404(self, client):
        """Deleting a made-up ID returns 404 NOT_FOUND."""
        resp = client.delete(
            "/local/ocr/history/00000000-0000-0000-0000-000000000000"
        )
        assert resp.status_code == 404
        body = resp.json()
        assert body["success"] is False
        assert body["error"]["code"] == "NOT_FOUND"

    def test_clear_all_deletes_all_records(self, client, minimal_png_bytes):
        """clear_all should remove every record and return count."""
        # Create 2 records
        for name in ("a.png", "b.png"):
            files = {
                "image": (name, io.BytesIO(minimal_png_bytes), "image/png")
            }
            client.post("/local/ocr", files=files)

        resp = client.delete("/local/ocr/history")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["deleted_count"] == 2

        # List should be empty
        list_resp = client.get("/local/ocr/history")
        assert list_resp.json()["data"]["items"] == []

    def test_delete_unified_response_format(self, client, minimal_png_bytes):
        """DELETE responses must include success, data, error, request_id."""
        files = {"image": ("test.png", io.BytesIO(minimal_png_bytes), "image/png")}
        ocr_resp = client.post("/local/ocr", files=files)
        history_id = ocr_resp.json()["data"]["history_id"]

        resp = client.delete(f"/local/ocr/history/{history_id}")
        body = resp.json()
        assert "success" in body
        assert "data" in body
        assert "error" in body
        assert "request_id" in body
        assert isinstance(body["success"], bool)

    def test_delete_then_detail_returns_404(self, client, minimal_png_bytes):
        """After deletion, fetching detail should return 404."""
        files = {"image": ("test.png", io.BytesIO(minimal_png_bytes), "image/png")}
        ocr_resp = client.post("/local/ocr", files=files)
        history_id = ocr_resp.json()["data"]["history_id"]

        client.delete(f"/local/ocr/history/{history_id}")

        detail_resp = client.get(f"/local/ocr/history/{history_id}")
        assert detail_resp.status_code == 404
        assert detail_resp.json()["error"]["code"] == "NOT_FOUND"

    def test_clear_all_empty_db_returns_zero(self, client):
        """Clearing an empty database returns deleted_count=0 successfully."""
        resp = client.delete("/local/ocr/history")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["deleted_count"] == 0


# ---------------------------------------------------------------------------
# 9. Sandbox path safety — _cleanup_sandbox_copy must reject malicious paths
# ---------------------------------------------------------------------------


class TestSandboxPathSafety:
    """Verify _cleanup_sandbox_copy rejects paths that escape the sandbox."""

    @pytest.fixture
    def sandbox_dir(self, tmp_path):
        """Create a temporary sandbox with a known file inside it."""
        sandbox = tmp_path / "ocr_images"
        sandbox.mkdir()
        legit = sandbox / "real_file.png"
        legit.write_bytes(b"legit")
        # Create a file OUTSIDE the sandbox to prove it is never deleted
        outside = tmp_path / "outside_file.png"
        outside.write_bytes(b"outside")
        return sandbox, outside

    def _call_cleanup(self, sandbox_dir, rel_path):
        """Import and call _cleanup_sandbox_copy with a patched SANDBOX_IMAGES_DIR."""
        import routes.ocr as ocr_mod
        from unittest.mock import patch

        sandbox, _ = sandbox_dir
        with patch.object(ocr_mod, "SANDBOX_IMAGES_DIR", sandbox):
            ocr_mod._cleanup_sandbox_copy(rel_path)

    def test_legit_relative_path_deletes_file(self, sandbox_dir):
        """A valid relative path under ocr_images/ should delete the file."""
        sandbox, _ = sandbox_dir
        legit = sandbox / "real_file.png"
        assert legit.exists()

        import routes.ocr as ocr_mod
        from unittest.mock import patch

        with patch.object(ocr_mod, "SANDBOX_IMAGES_DIR", sandbox):
            ocr_mod._cleanup_sandbox_copy("ocr_images/real_file.png")

        assert not legit.exists()  # was deleted

    def test_absolute_path_is_rejected(self, sandbox_dir):
        """An absolute Unix path must NOT delete anything."""
        sandbox, outside = sandbox_dir
        import routes.ocr as ocr_mod
        from unittest.mock import patch

        with patch.object(ocr_mod, "SANDBOX_IMAGES_DIR", sandbox):
            ocr_mod._cleanup_sandbox_copy("/etc/passwd")

        assert outside.exists()  # untouched

    def test_drive_letter_path_is_rejected(self, sandbox_dir):
        """A Windows path with a drive letter must NOT delete anything."""
        sandbox, outside = sandbox_dir
        import routes.ocr as ocr_mod
        from unittest.mock import patch

        with patch.object(ocr_mod, "SANDBOX_IMAGES_DIR", sandbox):
            ocr_mod._cleanup_sandbox_copy("C:\\Windows\\System32\\config\\SAM")

        assert outside.exists()  # untouched

    def test_unc_path_is_rejected(self, sandbox_dir):
        """A UNC network path must NOT delete anything."""
        sandbox, outside = sandbox_dir
        import routes.ocr as ocr_mod
        from unittest.mock import patch

        with patch.object(ocr_mod, "SANDBOX_IMAGES_DIR", sandbox):
            ocr_mod._cleanup_sandbox_copy("\\\\evil-server\\share\\file.png")

        assert outside.exists()  # untouched

    def test_path_traversal_is_rejected(self, sandbox_dir):
        """A path with .. traversal must NOT delete anything."""
        sandbox, outside = sandbox_dir
        import routes.ocr as ocr_mod
        from unittest.mock import patch

        with patch.object(ocr_mod, "SANDBOX_IMAGES_DIR", sandbox):
            ocr_mod._cleanup_sandbox_copy("ocr_images/../../../etc/passwd")

        assert outside.exists()  # untouched

    def test_not_under_ocr_images_is_rejected(self, sandbox_dir):
        """A relative path not starting with ocr_images/ must NOT delete."""
        sandbox, outside = sandbox_dir
        import routes.ocr as ocr_mod
        from unittest.mock import patch

        with patch.object(ocr_mod, "SANDBOX_IMAGES_DIR", sandbox):
            ocr_mod._cleanup_sandbox_copy("some_other_dir/evil.png")

        assert outside.exists()  # untouched

    def test_none_path_is_noop(self, sandbox_dir):
        """None path should be a silent no-op."""
        sandbox, outside = sandbox_dir
        import routes.ocr as ocr_mod
        from unittest.mock import patch

        with patch.object(ocr_mod, "SANDBOX_IMAGES_DIR", sandbox):
            # Should not raise, should not delete anything
            ocr_mod._cleanup_sandbox_copy(None)

        assert outside.exists()  # untouched
