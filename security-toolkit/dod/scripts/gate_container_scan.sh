#!/usr/bin/env bash
# Control gate 5: Container image vulnerability scan (hard gate).
# Scans a built image for CVEs against a severity policy. Default: Grype, Trivy alt.
# Also flags if the base image is NOT sourced from Iron Bank (registry1.dso.mil).
#
# Usage: gate_container_scan.sh <image-ref> [--severity high]
#                               [--evidence cato-evidence]
set -uo pipefail
IMAGE="${1:-}"; shift || true
SEV="high"; EVID="cato-evidence"
while [[ $# -gt 0 ]]; do case "$1" in
  --severity) SEV="$2"; shift 2 ;;
  --evidence) EVID="$2"; shift 2 ;;
  *) shift ;; esac; done
[[ -z "$IMAGE" ]] && { echo "[FAIL] Provide an image reference."; exit 3; }
mkdir -p "$EVID"

# Iron Bank provenance check (advisory).
case "$IMAGE" in
  registry1.dso.mil/*|ironbank/*) echo "[OK] Base image is from Iron Bank." ;;
  *) echo "[WARN] Image '$IMAGE' is not from Iron Bank (registry1.dso.mil). DoD hardened base images are expected." ;;
esac

if command -v grype >/dev/null 2>&1; then
  grype "$IMAGE" --fail-on "$SEV" -o sarif > "$EVID/container.sarif" 2> "$EVID/container.log"; rc=$?
  [[ $rc -eq 0 ]] && { echo "[OK] Gate 5 (container scan): PASS"; exit 0; }
  echo "[FAIL] Gate 5 (container scan): CVEs >= $SEV. Evidence: $EVID/container.sarif"; exit 2
elif command -v trivy >/dev/null 2>&1; then
  UP="$(echo "$SEV" | tr 'a-z' 'A-Z')"
  trivy image --severity "$UP",CRITICAL --exit-code 1 \
    --format sarif --output "$EVID/container.sarif" "$IMAGE"; rc=$?
  [[ $rc -eq 0 ]] && { echo "[OK] Gate 5 (container scan): PASS"; exit 0; }
  echo "[FAIL] Gate 5 (container scan): findings. Evidence: $EVID/container.sarif"; exit 2
fi
echo "[FAIL] Gate 5: install grype or trivy."; exit 3
