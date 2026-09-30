#!/usr/bin/env bash
# SBOM generation gate (SWFT). Produces machine-readable SBOMs in BOTH
# SPDX and CycloneDX JSON for a source tree or a container image, using Syft.
#
# Per DoD SWFT (2026): SBOMs must be machine-readable and regenerated on every
# code change. Wire this into the build stage so each build emits fresh SBOMs.
#
# Usage:
#   generate_sbom.sh --path .                 --out sbom/
#   generate_sbom.sh --image registry/app:tag --out sbom/ --name app
# Exit: 0 SBOMs written · 3 tool/target error.
set -uo pipefail

TARGET=""; KIND=""; OUT="sbom"; NAME="artifact"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --path)  TARGET="dir:$2"; KIND=path;  shift 2 ;;
    --image) TARGET="$2";     KIND=image; shift 2 ;;
    --out)   OUT="$2";  shift 2 ;;
    --name)  NAME="$2"; shift 2 ;;
    *) echo "[WARN] unknown arg: $1"; shift ;;
  esac
done
[[ -z "$TARGET" ]] && { echo "[FAIL] Provide --path <dir> or --image <ref>."; exit 3; }

if ! command -v syft >/dev/null 2>&1; then
  echo "[FAIL] 'syft' not installed. Install: https://github.com/anchore/syft"
  echo "       curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin"
  exit 3
fi

mkdir -p "$OUT"
SPDX="$OUT/${NAME}.spdx.json"
CDX="$OUT/${NAME}.cdx.json"

echo "[INFO] Generating SBOMs for $KIND target: ${TARGET#dir:}"
syft "$TARGET" -o "spdx-json=$SPDX" -o "cyclonedx-json=$CDX" -q || {
  echo "[FAIL] Syft failed to generate SBOM."; exit 3; }

# Minimal integrity: component count + digest for the evidence bundle.
count=$(grep -o '"name"' "$CDX" 2>/dev/null | wc -l | tr -d ' ')
sha256sum "$SPDX" "$CDX" > "$OUT/${NAME}.sbom.sha256" 2>/dev/null || true

echo "[OK] SPDX     : $SPDX"
echo "[OK] CycloneDX: $CDX"
echo "[OK] Components (approx): $count"
echo "[INFO] SBOMs are machine-readable JSON, regenerated this build (SWFT-compliant)."
exit 0
