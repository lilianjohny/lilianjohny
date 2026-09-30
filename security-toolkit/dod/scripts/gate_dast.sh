#!/usr/bin/env bash
# Control gate 7: DAST — Dynamic Application Security Testing (hard gate*).
# Runs OWASP ZAP (baseline scan) against a running application endpoint.
#
# *For a library with no running endpoint, record N/A explicitly:
#   gate_dast.sh --not-applicable "library: no runtime endpoint"
#
# Usage:
#   gate_dast.sh --target https://app.internal [--full] [--evidence cato-evidence]
set -uo pipefail
TARGET=""; MODE=baseline; EVID="cato-evidence"; NA=""
while [[ $# -gt 0 ]]; do case "$1" in
  --target) TARGET="$2"; shift 2 ;;
  --full) MODE=full; shift ;;
  --evidence) EVID="$2"; shift 2 ;;
  --not-applicable) NA="$2"; shift 2 ;;
  *) shift ;; esac; done
mkdir -p "$EVID"

if [[ -n "$NA" ]]; then
  echo "{\"gate\":\"dast\",\"status\":\"N/A\",\"justification\":\"$NA\"}" > "$EVID/dast.na.json"
  echo "[OK] Gate 7 (DAST): N/A recorded — $NA"; exit 0
fi
[[ -z "$TARGET" ]] && { echo "[FAIL] Provide --target <url> or --not-applicable <reason>."; exit 3; }

# Prefer a local zap CLI; else the official ZAP container.
REPORT="$EVID/dast-report.html"
if command -v zap-baseline.py >/dev/null 2>&1; then
  RUN=(zap-baseline.py)
  [[ "$MODE" == full ]] && RUN=(zap-full-scan.py)
  "${RUN[@]}" -t "$TARGET" -r "$REPORT"; rc=$?
elif command -v docker >/dev/null 2>&1; then
  echo "[INFO] Using OWASP ZAP container."
  SCRIPT="zap-baseline.py"; [[ "$MODE" == full ]] && SCRIPT="zap-full-scan.py"
  docker run --rm -v "$(pwd)/$EVID:/zap/wrk:rw" -t ghcr.io/zaproxy/zaproxy:stable \
    "$SCRIPT" -t "$TARGET" -r "$(basename "$REPORT")"; rc=$?
else
  echo "[FAIL] Gate 7 (DAST): install OWASP ZAP or Docker."
  echo "       https://www.zaproxy.org/download/"
  exit 3
fi

# ZAP exit: 0 = no alerts at threshold, 1/2 = warnings/failures present.
[[ $rc -eq 0 ]] && { echo "[OK] Gate 7 (DAST): PASS. Report: $REPORT"; exit 0; }
echo "[FAIL] Gate 7 (DAST): alerts found. Report: $REPORT"; exit 2
