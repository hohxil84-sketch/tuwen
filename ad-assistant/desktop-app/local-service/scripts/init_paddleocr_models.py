"""PaddleOCR Model Initialization Script — Sprint-01 Task-04.

Downloads PaddleOCR model files (detection, recognition, angle classification)
to the local cache directory.  This is a **one-time** operation for development
environment setup.

Usage::

    python scripts/init_paddleocr_models.py

Prerequisites:
    - paddlepaddle (CPU) and paddleocr installed
    - Internet connection (models are ~50-100 MB)

After this script completes successfully, the OCR runtime will load models
from cache without any network access.

Safety:
    - This is the **only** place where PaddleOCR is allowed to download models.
    - Runtime code in ``wrappers/paddleocr.py`` MUST refuse to call the
      PaddleOCR constructor when the cache is empty.
"""

import os
import sys
from pathlib import Path


def main() -> int:
    """Download PaddleOCR models and exit with 0 on success, non-zero on failure."""
    cache_home = os.environ.get("PADDLEOCR_HOME", os.path.expanduser("~/.paddleocr"))
    cache_path = Path(cache_home)

    print("=" * 62)
    print("  PaddleOCR Model Initialization")
    print("=" * 62)
    print()
    print("This script downloads PaddleOCR model files (~50-100 MB total).")
    print("It only needs to run ONCE per environment / cache directory.")
    print()
    print(f"Cache directory: {cache_path}")
    print()

    # ------------------------------------------------------------------
    # 1. Check import
    # ------------------------------------------------------------------
    try:
        from paddleocr import PaddleOCR  # type: ignore[import-untyped]  # noqa: F811
    except ImportError:
        print("ERROR: PaddleOCR is not installed.", file=sys.stderr)
        print(file=sys.stderr)
        print("Install the local-service dependencies first:", file=sys.stderr)
        print("    pip install -r requirements.txt", file=sys.stderr)
        return 1

    # ------------------------------------------------------------------
    # 2. Check existing cache (idempotent)
    # ------------------------------------------------------------------
    if cache_path.exists():
        # Walk the tree looking for .pdmodel files (Paddle inference models)
        for _root, _dirs, files in os.walk(cache_path):
            if any(f.endswith(".pdmodel") for f in files):
                print("Model cache already populated — nothing to download.")
                print(f"({cache_path})")
                return 0

        print(f"Cache directory exists but contains no model files.")
        print(f"Will download models into: {cache_path}")
    else:
        print(f"Cache directory will be created: {cache_path}")

    print()
    print("Downloading models (this may take a few minutes on first run)...")
    print("  - Text detection model")
    print("  - Text recognition model (Chinese)")
    print("  - Angle classification model")
    print()

    # ------------------------------------------------------------------
    # 3. Trigger download by initialising PaddleOCR once
    # ------------------------------------------------------------------
    try:
        # Initialise with default models — PaddleOCR will download on
        # first construction.  Use Chinese language + angle classification.
        _ocr = PaddleOCR(lang="ch", use_angle_cls=True)
    except Exception as exc:
        print(file=sys.stderr)
        print(f"ERROR: Model download failed: {exc}", file=sys.stderr)
        print(file=sys.stderr)
        print("Troubleshooting:", file=sys.stderr)
        print("  1. Check your internet connection.", file=sys.stderr)
        print("  2. Retry — the download is resumable in recent PaddleOCR versions.", file=sys.stderr)
        print(f"  3. Set a custom cache path: set PADDLEOCR_HOME=<path>", file=sys.stderr)
        print("     then re-run this script.", file=sys.stderr)
        print("  4. Manual download: https://github.com/PaddlePaddle/PaddleOCR", file=sys.stderr)
        print("     Place the model files in the cache directory shown above.", file=sys.stderr)
        return 2

    # ------------------------------------------------------------------
    # 4. Verify
    # ------------------------------------------------------------------
    print()
    if cache_path.exists():
        print("SUCCESS: PaddleOCR models downloaded and cached.")
        print(f"Location: {cache_path}")
        print()
        print("You can now start the local OCR service.")
        print("The runtime will load models from cache — no network needed.")
    else:
        print("WARNING: Models may have been downloaded to an unexpected location.")
        print(f"Expected: {cache_path}")
        print("Check PaddleOCR documentation if the service cannot find models.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
