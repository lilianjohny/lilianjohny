#!/usr/bin/env bash
# Software Composition Analysis for application dependencies.
# Generates an SBOM (via the toolkit's SWFT generator) and scans it with Grype;
# falls back to native package-manager audits.
#
# Usage: bash sca_scan.sh [--path .] [--severity high]
set -uo pipefail
TK="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PATH_TARGET="."; SEV="high"
while [[ $# -gt 0 ]]; do case "$1" in
  --path) PATH_TARGET="$2"; shift 2 ;;
  --severity) SEV="$2"; shift 2 ;;
  *) shift ;; esac; done

# Prefer SBOM-driven SCA (consistent with the DoD/SWFT flow).
if command -v syft >/dev/null 2>&1 && command -v grype >/dev/null 2>&1; then
  echo "[INFO] Generating SBOM + Grype SCA (fail >= $SEV)"
  bash "$TK/dod/scripts/generate_sbom.sh" --path "$PATH_TARGET" --out sbom --name app || true
  grype "sbom:sbom/app.cdx.json" --fail-on "$SEV"; exit $?
fi

# Fallback to the multi-ecosystem native audit.
echo "[INFO] syft/grype not found; using native dependency audit."
bash "$TK/vuln/dependency_audit.sh" "$PATH_TARGET"
