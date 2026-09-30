#!/usr/bin/env bash
# DAST via OWASP ZAP against an authorized target. Supports an optional
# authenticated scan (bearer token) and an OpenAPI import for API coverage.
#
# Usage:
#   bash zap_scan.sh --target https://app.example.com
#   bash zap_scan.sh --target https://api.example.com --openapi openapi.yaml --full
#   bash zap_scan.sh --target https://app.example.com --token "$BEARER"
set -uo pipefail
TARGET=""; MODE=baseline; OPENAPI=""; TOKEN=""; OUT="zap-report.html"
while [[ $# -gt 0 ]]; do case "$1" in
  --target) TARGET="$2"; shift 2 ;;
  --full) MODE=full; shift ;;
  --openapi) OPENAPI="$2"; shift 2 ;;
  --token) TOKEN="$2"; shift 2 ;;
  --out) OUT="$2"; shift 2 ;;
  *) shift ;; esac; done
[[ -z "$TARGET" ]] && { echo "[FAIL] Provide --target <url> (authorized targets only)."; exit 3; }

echo "[WARN] DAST sends active traffic. Confirm you are authorized to test: $TARGET"

WORK="$(pwd)"
HDR_ARGS=()
[[ -n "$TOKEN" ]] && HDR_ARGS=(-config "replacer.full_list(0).description=auth" \
  -config "replacer.full_list(0).enabled=true" \
  -config "replacer.full_list(0).matchtype=REQ_HEADER" \
  -config "replacer.full_list(0).matchstr=Authorization" \
  -config "replacer.full_list(0).replacement=Bearer ${TOKEN}")

run_zap() { # picks CLI or container
  local script="$1"; shift
  if command -v "$script" >/dev/null 2>&1; then
    "$script" "$@"
  elif command -v docker >/dev/null 2>&1; then
    docker run --rm -v "$WORK:/zap/wrk:rw" -t ghcr.io/zaproxy/zaproxy:stable "$script" "$@"
  else
    echo "[FAIL] Install OWASP ZAP or Docker (https://www.zaproxy.org/download/)."; exit 3
  fi
}

if [[ -n "$OPENAPI" ]]; then
  echo "[INFO] API scan importing OpenAPI: $OPENAPI"
  run_zap zap-api-scan.py -t "$OPENAPI" -f openapi -r "$OUT" "${HDR_ARGS[@]}"; rc=$?
elif [[ "$MODE" == full ]]; then
  echo "[INFO] Full active scan of $TARGET"
  run_zap zap-full-scan.py -t "$TARGET" -r "$OUT" "${HDR_ARGS[@]}"; rc=$?
else
  echo "[INFO] Baseline (passive) scan of $TARGET"
  run_zap zap-baseline.py -t "$TARGET" -r "$OUT" "${HDR_ARGS[@]}"; rc=$?
fi

# ZAP: 0 = clean, 1/2 = warnings/fails.
[[ $rc -eq 0 ]] && echo "[OK] DAST: no alerts at threshold. Report: $OUT" \
               || echo "[FAIL] DAST: alerts found. Report: $OUT"
exit $rc
