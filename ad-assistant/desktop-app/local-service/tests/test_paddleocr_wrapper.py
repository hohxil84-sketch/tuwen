"""Unit tests for the PaddleOCR wrapper.

Tests:
1. Parameter whitelist — unknown params rejected
2. File extension validation — accepted and rejected
3. MIME type validation (magic bytes)
4. File size limit rejection
5. Path traversal rejection
6. Error code mapping
7. Image hash computation
"""

import pytest
from pathlib import Path

from wrappers.paddleocr import (
    ALLOWED_EXTENSIONS,
    ALLOWED_PARAMS,
    DEFAULT_MAX_SIZE_MB,
    DEFAULT_TIMEOUT_SEC,
    OCRError,
    PaddleOCREngine,
    compute_image_hash,
    validate_image_file,
)


# ---------------------------------------------------------------------------
# 1. Parameter whitelist
# ---------------------------------------------------------------------------

class TestParameterWhitelist:
    """Ensure only whitelisted parameters reach PaddleOCR."""

    def test_allowed_params_accepted(self):
        """Whitelisted parameters should be stored."""
        engine = PaddleOCREngine(lang="en", use_angle_cls=False, det_db_thresh=0.5, rec_batch_num=6)
        assert engine._params == {
            "lang": "en",
            "use_angle_cls": False,
            "det_db_thresh": 0.5,
            "rec_batch_num": 6,
        }

    def test_unknown_params_filtered_out(self):
        """Parameters not in the whitelist must be silently dropped."""
        engine = PaddleOCREngine(
            lang="ch",
            evil_param="rm -rf /",
            use_gpu=True,  # not in whitelist
            arbitrary_key="value",
        )
        assert "evil_param" not in engine._params
        assert "use_gpu" not in engine._params
        assert "arbitrary_key" not in engine._params
        assert engine._params == {"lang": "ch"}

    def test_empty_params(self):
        """No parameters at all should still work."""
        engine = PaddleOCREngine()
        assert engine._params == {}

    def test_allowed_params_set_is_known(self):
        """Sanity-check the whitelist contains expected params."""
        assert "lang" in ALLOWED_PARAMS
        assert "use_angle_cls" in ALLOWED_PARAMS
        assert "det_db_thresh" in ALLOWED_PARAMS
        assert "rec_batch_num" in ALLOWED_PARAMS
        # Should be exactly 4 params
        assert len(ALLOWED_PARAMS) == 4


# ---------------------------------------------------------------------------
# 2. File extension validation
# ---------------------------------------------------------------------------

class TestFileExtensionValidation:
    """Validate that only whitelisted image extensions are accepted."""

    def test_png_accepted(self, sample_png):
        """PNG files should pass validation."""
        path = validate_image_file(sample_png)
        assert path == sample_png.resolve()

    def test_jpg_accepted(self, sample_jpg):
        """JPEG files should pass validation."""
        path = validate_image_file(sample_jpg)
        assert path == sample_jpg.resolve()

    def test_bmp_accepted(self, sample_bmp):
        """BMP files should pass validation."""
        path = validate_image_file(sample_bmp)
        assert path == sample_bmp.resolve()

    def test_txt_rejected(self, sample_txt):
        """Non-image files (.txt) must be rejected."""
        with pytest.raises(OCRError) as exc_info:
            validate_image_file(sample_txt)
        assert exc_info.value.code == "INVALID_FILE_TYPE"

    def test_no_extension_rejected(self, temp_dir):
        """Files without a recognised image extension must be rejected."""
        f = temp_dir / "noext"
        f.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
        with pytest.raises(OCRError) as exc_info:
            validate_image_file(f)
        assert exc_info.value.code == "INVALID_FILE_TYPE"

    def test_nonexistent_file(self, temp_dir):
        """A path that doesn't exist should return FILE_NOT_FOUND."""
        f = temp_dir / "does_not_exist.png"
        with pytest.raises(OCRError) as exc_info:
            validate_image_file(f)
        assert exc_info.value.code == "FILE_NOT_FOUND"


# ---------------------------------------------------------------------------
# 3. MIME type validation (magic bytes)
# ---------------------------------------------------------------------------

class TestMimeTypeValidation:
    """Ensure magic-byte detection correctly identifies image formats."""

    def test_valid_png_magic_bytes(self, sample_png):
        """A file with PNG magic bytes and .png extension should pass."""
        path = validate_image_file(sample_png)
        assert path.suffix == ".png"

    def test_valid_jpg_magic_bytes(self, sample_jpg):
        """A file with JPEG magic bytes and .jpg extension should pass."""
        path = validate_image_file(sample_jpg)
        assert path.suffix == ".jpg"

    def test_wrong_extension_but_valid_magic(self, temp_dir):
        """A .txt file that actually contains PNG data should still be rejected
        based on extension first."""
        f = temp_dir / "fake.txt"
        f.write_bytes(
            b"\x89PNG\r\n\x1a\n"
            b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
            b"\x00\x00\x00\x0eIDATx\x9cc\xf8\xcf\xc0\x00\x00\x01\x01\x00\x05\x18\xd8N"
            b"\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        with pytest.raises(OCRError) as exc_info:
            validate_image_file(f)
        # Extension check comes first
        assert exc_info.value.code == "INVALID_FILE_TYPE"

    def test_garbage_bytes_png_extension(self, temp_dir):
        """A .png file with garbage content should fail magic-byte check."""
        f = temp_dir / "garbage.png"
        f.write_bytes(b"not an image at all")
        with pytest.raises(OCRError) as exc_info:
            validate_image_file(f)
        assert exc_info.value.code == "INVALID_FILE_TYPE"


# ---------------------------------------------------------------------------
# 4. File size limit
# ---------------------------------------------------------------------------

class TestFileSizeLimit:
    """Reject files that exceed the configured size limit."""

    def test_file_too_large_rejected(self, large_file):
        """A file larger than 50 MB must be rejected."""
        with pytest.raises(OCRError) as exc_info:
            validate_image_file(large_file)
        assert exc_info.value.code == "FILE_TOO_LARGE"

    def test_custom_size_limit(self, temp_dir):
        """The size limit should be configurable."""
        f = temp_dir / "small.png"
        f.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 2000)
        # With a 1-byte limit, even this small file should fail
        with pytest.raises(OCRError) as exc_info:
            validate_image_file(f, max_size_mb=0.000001)
        assert exc_info.value.code == "FILE_TOO_LARGE"


# ---------------------------------------------------------------------------
# 5. Path traversal rejection
# ---------------------------------------------------------------------------

class TestPathTraversal:
    """Ensure files outside the allowed directory are rejected."""

    def test_file_outside_allowed_dir(self, outside_file, temp_dir):
        """A file outside the allowed directory must be rejected."""
        with pytest.raises(OCRError) as exc_info:
            validate_image_file(outside_file, allowed_dir=temp_dir)
        assert exc_info.value.code == "PATH_TRAVERSAL_DENIED"

    def test_file_inside_allowed_dir(self, sample_png, temp_dir):
        """A file inside the allowed directory should pass."""
        path = validate_image_file(sample_png, allowed_dir=temp_dir)
        assert path == sample_png.resolve()

    def test_symlink_traversal(self, temp_dir):
        """A symlink pointing outside should still be caught (resolved path check)."""
        import os
        outside = temp_dir.parent / "outside_target.png"
        png_bytes = (
            b"\x89PNG\r\n\x1a\n"
            b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
            b"\x00\x00\x00\x0eIDATx\x9cc\xf8\xcf\xc0\x00\x00\x01\x01\x00\x05\x18\xd8N"
            b"\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        outside.write_bytes(png_bytes)
        symlink = temp_dir / "link_to_outside.png"
        try:
            os.symlink(str(outside), str(symlink))
        except OSError:
            pytest.skip("Symlink creation not available on this platform")
        try:
            with pytest.raises(OCRError) as exc_info:
                validate_image_file(symlink, allowed_dir=temp_dir)
            assert exc_info.value.code == "PATH_TRAVERSAL_DENIED"
        finally:
            outside.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# 6. Error code mapping
# ---------------------------------------------------------------------------

class TestErrorCodeMapping:
    """All OCRError instances must carry a non-empty code and message."""

    def test_ocerror_has_code_and_message(self):
        """OCRError must always have a code and message."""
        err = OCRError("TEST_CODE", "Test message")
        assert err.code == "TEST_CODE"
        assert err.message == "Test message"

    def test_validate_file_error_codes_are_nonempty(self, sample_txt):
        """Validation errors must have meaningful codes."""
        with pytest.raises(OCRError) as exc_info:
            validate_image_file(sample_txt)
        assert exc_info.value.code
        assert exc_info.value.message
        assert isinstance(exc_info.value.code, str)
        assert len(exc_info.value.code) > 0

    def test_error_details_optional(self):
        """The details field is optional."""
        err = OCRError("CODE", "msg")
        assert err.details is None

        err2 = OCRError("CODE", "msg", details={"extra": "info"})
        assert err2.details == {"extra": "info"}


# ---------------------------------------------------------------------------
# 7. Image hash
# ---------------------------------------------------------------------------

class TestImageHash:
    """SHA-256 based image hash for dedup."""

    def test_hash_is_16_hex_chars(self, sample_png):
        """Hash should return exactly 16 hex characters."""
        h = compute_image_hash(sample_png)
        assert len(h) == 16
        assert all(c in "0123456789abcdef" for c in h)

    def test_same_content_same_hash(self, temp_dir):
        """Identical content should produce identical hash."""
        f1 = temp_dir / "a.png"
        f2 = temp_dir / "b.png"
        content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 200
        f1.write_bytes(content)
        f2.write_bytes(content)
        assert compute_image_hash(f1) == compute_image_hash(f2)

    def test_different_content_different_hash(self, temp_dir):
        """Different content should produce different hash."""
        f1 = temp_dir / "a.png"
        f2 = temp_dir / "b.png"
        f1.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 200)
        f2.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x01" * 200)
        assert compute_image_hash(f1) != compute_image_hash(f2)


# ---------------------------------------------------------------------------
# 8. Engine readiness
# ---------------------------------------------------------------------------

class TestEngineReadiness:
    """The engine should report its readiness state."""

    def test_engine_not_ready_initially(self):
        """Before first use, is_ready should be False."""
        engine = PaddleOCREngine()
        assert engine.is_ready is False

    def test_engine_init_without_paddleocr_installed(self):
        """When PaddleOCR / models are not available, _ensure_engine should raise
        OCR_ENGINE_NOT_INSTALLED, OCR_MODEL_NOT_FOUND, or OCR_ENGINE_INIT_FAILED."""
        engine = PaddleOCREngine()
        with pytest.raises(OCRError) as exc_info:
            engine._ensure_engine()
        # May be NOT_INSTALLED (no pip package), MODEL_NOT_FOUND (package
        # installed but cache empty), or INIT_FAILED (other init error).
        assert exc_info.value.code in (
            "OCR_ENGINE_NOT_INSTALLED",
            "OCR_MODEL_NOT_FOUND",
            "OCR_ENGINE_INIT_FAILED",
        )
        assert engine.is_ready is False


# ---------------------------------------------------------------------------
# 9. Model cache detection
# ---------------------------------------------------------------------------

class TestModelCacheDetection:
    """The _check_model_cache method must correctly detect cached models."""

    def test_missing_directory_returns_false(self, temp_dir):
        """A non-existent cache directory should return False."""
        fake_cache = temp_dir / "nonexistent_cache"
        assert PaddleOCREngine._check_model_cache(fake_cache) is False

    def test_empty_directory_returns_false(self, temp_dir):
        """An empty cache directory should return False."""
        empty_cache = temp_dir / "empty_cache"
        empty_cache.mkdir()
        assert PaddleOCREngine._check_model_cache(empty_cache) is False

    def test_directory_with_pdmodel_returns_true(self, temp_dir):
        """A cache directory containing .pdmodel files should return True."""
        cache = temp_dir / "populated_cache"
        sub = cache / "whl" / "det" / "ch"
        sub.mkdir(parents=True)
        (sub / "inference.pdmodel").write_text("mock model")
        assert PaddleOCREngine._check_model_cache(cache) is True

    def test_directory_with_other_files_returns_false(self, temp_dir):
        """A cache directory with non-model files should return False."""
        cache = temp_dir / "junk_cache"
        cache.mkdir()
        (cache / "readme.txt").write_text("hello")
        (cache / "config.yaml").write_text("key: val")
        assert PaddleOCREngine._check_model_cache(cache) is False

    def test_empty_cache_raises_model_not_found(self, monkeypatch, temp_dir):
        """When cache is empty but PaddleOCR is importable, _ensure_engine
        must raise OCR_MODEL_NOT_FOUND *before* calling PaddleOCR()."""
        from wrappers import paddleocr as _mod

        # Simulate "PaddleOCR installed but cache empty"
        monkeypatch.setattr(_mod.PaddleOCREngine, "_check_model_cache", lambda self, cache_path: False)

        engine = PaddleOCREngine()
        # We must NOT reach the real PaddleOCR import — if we do the test
        # will either fail (import missing) or trigger a download (forbidden).
        with pytest.raises(OCRError) as exc_info:
            engine._ensure_engine()
        assert exc_info.value.code == "OCR_MODEL_NOT_FOUND"
        assert engine.is_ready is False
        # The engine must NOT have been set (PaddleOCR constructor never called)
        assert engine._engine is None
