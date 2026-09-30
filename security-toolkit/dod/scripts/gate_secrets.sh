#!/usr/bin/env bash
# Control gate 1: Secrets detection (hard gate).
# Fails promotion if credentials are present in the working tree or history.
#
# Usage: gate_secrets.sh --path . [--evidence cato-evidence]
set -uo pipefail
PATH_TARGET="."; EVID="cato-evidence"
while [[ $# -gt 0 ]]; do case "$1" in
  --path) PATH_TARGET="$2"; shift 2 ;;
  --evidence) EVID="$2"; shift 2 ;;
  *) shift ;; esac; done
mkdir -p "$EVID"

if command -v gitleaks >/dev/null 2>&1; then
  gitleaks detect --source "$PATH_TARGET" --no-banner --redact \
    --report-format sarif --report-path "$EVID/secrets.sarif"; rc=$?
  [[ $rc -eq 0 ]] && { echo "[OK] Gate 1 (secrets): PASS"; exit 0; }
  echo "[FAIL] Gate 1 (secrets): findings. Evidence: $EVID/secrets.sarif"; exit 2
fi

# Fallback to the toolkit's built-in scanner.
TK="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
if [[ -f "$TK/devsecops/secrets_scan.py" ]]; then
  echo "[INFO] gitleaks not found; using toolkit fallback scanner."
  python3 "$TK/devsecops/secrets_scan.py" "$PATH_TARGET" | tee "$EVID/secrets.txt"
  rc=${PIPESTATUS[0]}
  [[ $rc -eq 0 ]] && { echo "[OK] Gate 1 (secrets): PASS"; exit 0; }
  echo "[FAIL] Gate 1 (secrets): findings. Evidence: $EVID/secrets.txt"; exit 2
fi
echo "[FAIL] No secret scanner available (install gitleaks)."; exit 3
