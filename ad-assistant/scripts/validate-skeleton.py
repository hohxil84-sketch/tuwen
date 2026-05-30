#!/usr/bin/env python3
"""Sprint-01 Skeleton Validation Script (Cross-Platform)

Checks: no real keys, no future modules, required dirs exist.
Works on Windows, Linux, and macOS without bash dependency.

Usage:
    python scripts/validate-skeleton.py
    python scripts/validate-skeleton.py --quiet   # only show failures
"""

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PASS = 0
FAIL = 0


def green(s: str) -> str:
    return f"\033[92m{s}\033[0m" if os.name != "nt" else s


def red(s: str) -> str:
    return f"\033[91m{s}\033[0m" if os.name != "nt" else s


def _pass(msg: str) -> None:
    global PASS
    PASS += 1
    print(f"  {green('PASS')}  {msg}")


def _fail(msg: str) -> None:
    global FAIL
    FAIL += 1
    print(f"  {red('FAIL')}  {msg}")


SOURCE_EXTS = {".ts", ".tsx", ".vue", ".py", ".js", ".json", ".toml"}
CODE_EXTS = {".ts", ".tsx", ".vue", ".py", ".js"}

API_KEY_RE = re.compile(
    r"sk-[a-zA-Z0-9]{20,}|sk-ant-[a-zA-Z0-9]|dsk-[a-zA-Z0-9]|AKIA[A-Z0-9]{16}"
)
HARDCODED_KEY_RE = re.compile(
    r"(API_KEY|SECRET_KEY|apiKey|secretKey)\s*[:=]\s*['\"][a-zA-Z0-9_-]{8,}"
)
BUSINESS_LOGIC_RE = re.compile(
    r"(async def |@app\.|@router\.|def login|def refresh|def logout"
    r"|def bind|def ocr|def charge|def deduct|def create_|def get_)"
)


def collect_source_files(dirs: list[str]) -> list[Path]:
    """Collect all source files (not docs) in given directories."""
    files: list[Path] = []
    for d in dirs:
        p = ROOT / d
        if not p.is_dir():
            continue
        for f in p.rglob("*"):
            if f.is_file() and f.suffix in SOURCE_EXTS:
                files.append(f)
    return files


def collect_code_files(dirs: list[str]) -> list[Path]:
    """Collect code files only (no .json/.toml)."""
    files: list[Path] = []
    for d in dirs:
        p = ROOT / d
        if not p.is_dir():
            continue
        for f in p.rglob("*"):
            if f.is_file() and f.suffix in CODE_EXTS:
                files.append(f)
    return files


# ── 1. No real API keys ──
def check_no_api_keys() -> None:
    print("\n[1] Security: No real API keys in source files")
    scan_dirs = ["desktop-app", "cloud-backend", "official-website", "shared", "scripts"]
    for d in scan_dirs:
        dir_path = ROOT / d
        if not dir_path.is_dir():
            continue
        found = False
        for f in collect_source_files([d]):
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
                if API_KEY_RE.search(content):
                    print(f"    FOUND in {f.relative_to(ROOT)}")
                    found = True
            except Exception:
                pass
        if found:
            _fail(f"API key pattern found in {d}")
        else:
            _pass(f"No API keys in {d}")


# ── 2. No hardcoded key assignments ──
def check_no_hardcoded_keys() -> None:
    print("\n[2] Security: No hardcoded key assignments")
    scan_dirs = ["desktop-app", "cloud-backend", "official-website", "shared"]
    for d in scan_dirs:
        dir_path = ROOT / d
        if not dir_path.is_dir():
            continue
        found = False
        for f in collect_code_files([d]):
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
                if HARDCODED_KEY_RE.search(content):
                    print(f"    FOUND in {f.relative_to(ROOT)}")
                    found = True
            except Exception:
                pass
        if found:
            _fail(f"Hardcoded key found in {d}")
        else:
            _pass(f"No hardcoded keys in {d}")


# ── 3. Only allowed files in routes/ and wrappers/ ──
def check_no_unexpected_files() -> None:
    print("\n[3] Scope: No unexpected route/wrapper files")
    checks = [
        (
            ROOT / "desktop-app" / "local-service" / "routes",
            "local-service/routes/",
            {"__init__.py", "ocr.py"},
        ),
        (
            ROOT / "desktop-app" / "local-service" / "wrappers",
            "local-service/wrappers/",
            {"__init__.py", "paddleocr.py"},
        ),
    ]
    for dir_path, label, allowed in checks:
        if not dir_path.is_dir():
            _pass(f"No {label} directory (skipped)")
            continue
        unexpected = []
        for f in dir_path.iterdir():
            if f.is_file() and f.name not in allowed:
                unexpected.append(f.name)
        if unexpected:
            _fail(f"Unexpected files in {label}: {', '.join(unexpected)}")
        else:
            _pass(f"Only allowed files in {label}")


# ── 4. Required directories ──
def check_required_dirs() -> None:
    print("\n[4] Structure: Required directories")
    required = [
        "desktop-app/src/pages", "desktop-app/src/stores", "desktop-app/src/components",
        "desktop-app/src-tauri", "desktop-app/local-service/routes", "desktop-app/local-service/wrappers",
        "desktop-app/local-tools", "desktop-app/migrations", "desktop-app/tests",
        "cloud-backend/app/api", "cloud-backend/app/core", "cloud-backend/app/models",
        "cloud-backend/app/schemas", "cloud-backend/app/services", "cloud-backend/app/providers",
        "cloud-backend/app/workers", "cloud-backend/app/admin", "cloud-backend/migrations", "cloud-backend/tests",
        "official-website/app", "official-website/components", "official-website/content", "official-website/public",
        "shared/openapi", "shared/dto", "shared/typescript", "shared/error-codes", "shared/constants", "shared/sdk",
    ]
    for d in required:
        if (ROOT / d).is_dir():
            _pass(f"Dir exists: {d}")
        else:
            _fail(f"Dir missing: {d}")


# ── 5. Required config files ──
def check_required_files() -> None:
    print("\n[5] Structure: Required config/source files")
    required = [
        "cloud-backend/pyproject.toml",
        "cloud-backend/app/main.py",
        "cloud-backend/app/providers/base.py",
        "cloud-backend/app/providers/__init__.py",
        "cloud-backend/migrations/migration-plan-draft.md",
        "desktop-app/package.json",
        "desktop-app/vite.config.ts",
        "desktop-app/tsconfig.json",
        "desktop-app/index.html",
        "desktop-app/src/main.ts",
        "desktop-app/src/App.vue",
        "desktop-app/src/router.ts",
        "desktop-app/src/pages/LoginPage.vue",
        "desktop-app/src/pages/OcrPage.vue",
        "desktop-app/src/pages/HistoryPage.vue",
        "desktop-app/local-service/main.py",
        "desktop-app/local-service/routes/ocr.py",
        "desktop-app/local-service/wrappers/paddleocr.py",
        "official-website/package.json",
        "official-website/tsconfig.json",
        "official-website/next.config.ts",
        "official-website/app/layout.tsx",
        "official-website/app/page.tsx",
        "shared/package.json",
        "scripts/validate-skeleton.sh",
        "scripts/validate-skeleton.py",
    ]
    for f in required:
        if (ROOT / f).is_file():
            _pass(f"File exists: {f}")
        else:
            _fail(f"File missing: {f}")


# ── 6. No business logic in API route stubs ──
def check_no_business_logic() -> None:
    print("\n[6] Scope: No business logic in API route stubs")
    api_routes = [
        "cloud-backend/app/api/auth.py",
        "cloud-backend/app/api/device.py",
        "cloud-backend/app/api/ocr.py",
        "cloud-backend/app/api/usage.py",
        "cloud-backend/app/api/credit.py",
        "cloud-backend/app/api/provider_log.py",
    ]
    for f in api_routes:
        fp = ROOT / f
        if not fp.is_file():
            continue
        try:
            content = fp.read_text(encoding="utf-8", errors="ignore")
            if BUSINESS_LOGIC_RE.search(content):
                _fail(f"Business logic found in {f}")
            else:
                _pass(f"No business logic in {f}")
        except Exception:
            pass


def main() -> int:
    parser = argparse.ArgumentParser(description="Sprint-01 Skeleton Validation")
    parser.add_argument("--quiet", "-q", action="store_true", help="Only show failures")
    args = parser.parse_args()

    print("=" * 60)
    print(" Sprint-01 Skeleton Validation (Python)")
    print(f" {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f" Platform: {sys.platform}")
    print("=" * 60)

    check_no_api_keys()
    check_no_hardcoded_keys()
    check_no_unexpected_files()
    check_required_dirs()
    check_required_files()
    check_no_business_logic()

    print(f"\n{'=' * 60}")
    print(f" RESULTS: {PASS} passed, {FAIL} failed")
    print(f"{'=' * 60}")

    if FAIL > 0:
        print(f"{red('FAILED')} — fix {FAIL} issue(s) above")
        return 1
    else:
        print(f"{green('PASSED')} — skeleton is clean")
        return 0


if __name__ == "__main__":
    sys.exit(main())
