#!/usr/bin/env bash
# Control gate 3: SCA + license (hard gate).
# Scans dependencies for known vulnerabilities and license policy violations.
# Default: Grype (Anchore OSS) against an SBOM if present, else Trivy fs.
#
# Usage: gate_sca.sh --path . [--sbom sbom/artifact.cdx.json]
#                     [--severity high] [--evidence cato-evidence]
set -uo pipefail
PATH_TARGET="."; SBOM=""; SEV="high"; EVID="cato-evidence"
while [[ $# -gt 0 ]]; do case "$1" in
  --path) PATH_TARGET="$2"; shift 2 ;;
  --sbom) SBOM="$2"; shift 2 ;;
  --severity) SEV="$2"; shift 2 ;;
  --evidence) EVID="$2"; shift 2 ;;
  *) shift ;; esac; done
mkdir -p "$EVID"

if command -v grype >/dev/null 2>&1; then
  SRC="dir:$PATH_TARGET"
  [[ -n "$SBOM" && -f "$SBOM" ]] && SRC="sbom:$SBOM"
  echo "[INFO] Grype scanning: $SRC (fail >= $SEV)"
  grype "$SRC" --fail-on "$SEV" -o sarif > "$EVID/sca.sarif" 2> "$EVID/sca.log"; rc=$?
  grype "$SRC" -o table 2>/dev/null | tail -n +1 > "$EVID/sca.table.txt" || true
  [[ $rc -eq 0 ]] && { echo "[OK] Gate 3 (SCA): PASS"; exit 0; }
  echo "[FAIL] Gate 3 (SCA): vulnerabilities >= $SEV. Evidence: $EVID/sca.sarif"; exit 2
elif command -v trivy >/dev/null 2>&1; then
  UP="$(echo "$SEV" | tr 'a-z' 'A-Z')"
  echo "[INFO] Trivy fs scanning (fail >= $UP)"
  trivy fs --scanners vuln,license --severity "$UP",CRITICAL --exit-code 1 \
    --format sarif --output "$EVID/sca.sarif" "$PATH_TARGET"; rc=$?
  [[ $rc -eq 0 ]] && { echo "[OK] Gate 3 (SCA): PASS"; exit 0; }
  echo "[FAIL] Gate 3 (SCA): findings. Evidence: $EVID/sca.sarif"; exit 2
fi
echo "[FAIL] Gate 3 (SCA): install grype or trivy."
echo "       curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b /usr/local/bin"
exit 3
