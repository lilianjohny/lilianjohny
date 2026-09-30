#!/usr/bin/env bash
# Control gate 2: SAST — Static Application Security Testing (hard gate).
# Default engine: Semgrep (OSS). DoD programs may substitute Fortify/SonarQube.
#
# Usage: gate_sast.sh --path . [--severity ERROR] [--evidence cato-evidence]
set -uo pipefail
PATH_TARGET="."; SEV="ERROR"; EVID="cato-evidence"
while [[ $# -gt 0 ]]; do case "$1" in
  --path) PATH_TARGET="$2"; shift 2 ;;
  --severity) SEV="$2"; shift 2 ;;
  --evidence) EVID="$2"; shift 2 ;;
  *) shift ;; esac; done
mkdir -p "$EVID"

if command -v semgrep >/dev/null 2>&1; then
  # 'p/ci' + security audit rulesets; SARIF for the evidence bundle.
  semgrep scan --config p/ci --config p/security-audit \
    --sarif --output "$EVID/sast.sarif" --error --severity "$SEV" "$PATH_TARGET"; rc=$?
  [[ $rc -eq 0 ]] && { echo "[OK] Gate 2 (SAST): PASS"; exit 0; }
  echo "[FAIL] Gate 2 (SAST): findings at severity >= $SEV. Evidence: $EVID/sast.sarif"; exit 2
fi
echo "[FAIL] Gate 2 (SAST): no SAST engine found."
echo "       Install Semgrep: pip install semgrep   (or wire in Fortify/SonarQube)"
exit 3
