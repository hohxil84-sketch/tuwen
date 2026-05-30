"""PaddleOCR Wrapper — Sprint-01 placeholder.

Safety rules:
- Parameter whitelist (no arbitrary param passthrough)
- File type validation (extension + MIME type, whitelist only)
- File size limit (default 50MB for images)
- Path restriction (only designated directories, no absolute path traversal)
- Timeout control (default 60s for OCR)
- Error code mapping (unified codes, no internal exception leakage)
- Log redaction (no file content, no username in paths)

OCR return structure:
{
    "text": "full recognized text",
    "blocks": [{"text": "...", "confidence": 0.98, "bbox": [0, 0, 100, 40]}],
    "engine": "paddleocr",
    "duration_ms": 1200
}

Sprint-01: skeleton only — no business logic implemented yet.
"""

# Sprint-01: skeleton only
