#!/usr/bin/env bash
# Sprint-01 Skeleton Validation Script
# Checks: no real keys, no future modules, required dirs exist
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PASS=0
FAIL=0

pass() { echo "  ✅ PASS  $1"; PASS=$((PASS + 1)); }
fail() { echo "  ❌ FAIL  $1"; FAIL=$((FAIL + 1)); }

echo "=============================================="
echo " Sprint-01 Skeleton Validation"
echo " $(date '+%Y-%m-%d %H:%M:%S')"
echo "=============================================="

# ── 1. No real API keys in source files (skip .md docs) ──
echo ""
echo "[1] Security: No real API keys in source files"

check_no_keys() {
  local dir="$1"
  local found=0
  # Only scan source files, not docs
  for f in $(find "$dir" -type f \( -name '*.ts' -o -name '*.tsx' -o -name '*.vue' -o -name '*.py' -o -name '*.js' -o -name '*.json' -o -name '*.toml' \) 2>/dev/null); do
    if grep -qE 'sk-[a-zA-Z0-9]{20,}|sk-ant-[a-zA-Z0-9]|dsk-[a-zA-Z0-9]|AKIA[A-Z0-9]{16}' "$f" 2>/dev/null; then
      echo "    FOUND in $f"
      found=1
    fi
  done
  return $found
}

for dir in desktop-app cloud-backend official-website shared scripts; do
  if [ -d "$ROOT/$dir" ]; then
    if check_no_keys "$ROOT/$dir"; then
      pass "No API keys in $dir"
    else
      fail "API key pattern found in $dir"
    fi
  fi
done

# ── 2. No hardcoded key=value assignments (non-doc) ──
echo ""
echo "[2] Security: No hardcoded key assignments"

check_no_hardcoded() {
  local dir="$1"
  local found=0
  for f in $(find "$dir" -type f \( -name '*.ts' -o -name '*.tsx' -o -name '*.vue' -o -name '*.py' -o -name '*.js' \) 2>/dev/null); do
    if grep -qE "(API_KEY|SECRET_KEY|apiKey|secretKey)\s*[:=]\s*['\"][a-zA-Z0-9_-]{8,}" "$f" 2>/dev/null; then
      echo "    FOUND in $f"
      found=1
    fi
  done
  return $found
}

for dir in desktop-app cloud-backend official-website shared; do
  if [ -d "$ROOT/$dir" ]; then
    if check_no_hardcoded "$ROOT/$dir"; then
      pass "No hardcoded keys in $dir"
    else
      fail "Hardcoded key found in $dir"
    fi
  fi
done

# ── 3. No unexpected route or wrapper files (only Sprint-01 allowed) ──
echo ""
echo "[3] Scope: No unexpected route/wrapper files"

# Sprint-01 only allows ocr.py in routes/ and paddleocr.py in wrappers/
ALLOWED_ROUTES=("__init__.py" "ocr.py")
ALLOWED_WRAPPERS=("__init__.py" "paddleocr.py")

check_dir_only_allowed() {
  local dir="$1"
  local label="$2"
  shift 2
  local allowed=("$@")
  local found=0
  if [ -d "$dir" ]; then
    for f in "$dir"/*; do
      [ -f "$f" ] || continue
      local bn
      bn=$(basename "$f")
      local ok=0
      for a in "${allowed[@]}"; do
        [ "$bn" = "$a" ] && ok=1 && break
      done
      if [ "$ok" -eq 0 ]; then
        echo "    UNEXPECTED: $f"
        found=1
      fi
    done
  fi
  if [ $found -eq 0 ]; then
    pass "Only allowed files in $label"
  else
    fail "Unexpected files in $label"
  fi
}

check_dir_only_allowed "$ROOT/desktop-app/local-service/routes" "local-service/routes/" "${ALLOWED_ROUTES[@]}"
check_dir_only_allowed "$ROOT/desktop-app/local-service/wrappers" "local-service/wrappers/" "${ALLOWED_WRAPPERS[@]}"

# ── 4. Required directories exist ──
echo ""
echo "[4] Structure: Required directories"

REQUIRED_DIRS=(
  "desktop-app/src/pages" "desktop-app/src/stores" "desktop-app/src/components"
  "desktop-app/src-tauri" "desktop-app/local-service/routes" "desktop-app/local-service/wrappers"
  "desktop-app/local-tools" "desktop-app/migrations" "desktop-app/tests"
  "cloud-backend/app/api" "cloud-backend/app/core" "cloud-backend/app/models"
  "cloud-backend/app/schemas" "cloud-backend/app/services" "cloud-backend/app/providers"
  "cloud-backend/app/workers" "cloud-backend/app/admin" "cloud-backend/migrations" "cloud-backend/tests"
  "official-website/app" "official-website/components" "official-website/content" "official-website/public"
  "shared/openapi" "shared/dto" "shared/typescript" "shared/error-codes" "shared/constants" "shared/sdk"
)

for d in "${REQUIRED_DIRS[@]}"; do
  if [ -d "$ROOT/$d" ]; then
    pass "Dir exists: $d"
  else
    fail "Dir missing: $d"
  fi
done

# ── 5. Required config/bin files exist ──
echo ""
echo "[5] Structure: Required config files"

REQUIRED_FILES=(
  "cloud-backend/pyproject.toml"
  "cloud-backend/app/main.py"
  "cloud-backend/app/providers/base.py"
  "cloud-backend/app/providers/__init__.py"
  "cloud-backend/migrations/migration-plan-draft.md"
  "desktop-app/package.json"
  "desktop-app/vite.config.ts"
  "desktop-app/tsconfig.json"
  "desktop-app/index.html"
  "desktop-app/src/main.ts"
  "desktop-app/src/App.vue"
  "desktop-app/src/router.ts"
  "desktop-app/src/pages/LoginPage.vue"
  "desktop-app/src/pages/OcrPage.vue"
  "desktop-app/src/pages/HistoryPage.vue"
  "desktop-app/local-service/main.py"
  "desktop-app/local-service/routes/ocr.py"
  "desktop-app/local-service/wrappers/paddleocr.py"
  "official-website/package.json"
  "official-website/tsconfig.json"
  "official-website/next.config.ts"
  "official-website/app/layout.tsx"
  "official-website/app/page.tsx"
  "shared/package.json"
  "scripts/validate-skeleton.sh"
  "scripts/validate-skeleton.py"
)

for f in "${REQUIRED_FILES[@]}"; do
  if [ -f "$ROOT/$f" ]; then
    pass "File exists: $f"
  else
    fail "File missing: $f"
  fi
done

# ── 6. No business logic handlers in cloud API route stubs ──
echo ""
echo "[6] Scope: No business logic in API route stubs"

API_ROUTES=(
  "cloud-backend/app/api/auth.py"
  "cloud-backend/app/api/device.py"
  "cloud-backend/app/api/ocr.py"
  "cloud-backend/app/api/usage.py"
  "cloud-backend/app/api/credit.py"
  "cloud-backend/app/api/provider_log.py"
)

for f in "${API_ROUTES[@]}"; do
  if [ -f "$ROOT/$f" ]; then
    if grep -qE '(async def |@app\.|@router\.|def login|def refresh|def logout|def bind|def ocr|def charge|def deduct|def create_|def get_)' "$ROOT/$f" 2>/dev/null; then
      fail "Business logic found in $f"
    else
      pass "No business logic in $f"
    fi
  fi
done

# ── Summary ──
echo ""
echo "=============================================="
echo " RESULTS: $PASS passed, $FAIL failed"
echo "=============================================="

if [ "$FAIL" -gt 0 ]; then
  echo "❌ Validation FAILED — fix $FAIL issue(s) above"
  exit 1
else
  echo "✅ Validation PASSED — skeleton is clean"
  exit 0
fi
