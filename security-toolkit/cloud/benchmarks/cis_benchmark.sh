#!/usr/bin/env bash
# Run a CIS Benchmark compliance assessment for a cloud account via Prowler.
# Read-only; uses your existing cloud session. Produces compliance-mapped output.
#
# Usage:
#   bash cis_benchmark.sh aws    [--version 3.0]
#   bash cis_benchmark.sh azure  [--version 2.1]
#   bash cis_benchmark.sh gcp    [--version 3.0]
#   bash cis_benchmark.sh --list aws     # list CIS frameworks Prowler knows
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PROVIDER="${1:-}"; shift || true
VERSION=""; LIST=0
while [[ $# -gt 0 ]]; do case "$1" in
  --version) VERSION="$2"; shift 2 ;;
  --list) LIST=1; shift ;;
  *) shift ;; esac; done

case "$PROVIDER" in aws|azure|gcp) ;; *)
  echo "[FAIL] Usage: $0 <aws|azure|gcp> [--version X.Y]"; exit 3 ;; esac

# Default CIS versions per provider (adjust as CIS releases new ones).
if [[ -z "$VERSION" ]]; then
  case "$PROVIDER" in
    aws) VERSION="3.0" ;;
    azure) VERSION="2.1" ;;
    gcp) VERSION="3.0" ;;
  esac
fi
FRAMEWORK="cis_${VERSION}_${PROVIDER}"

if ! command -v prowler >/dev/null 2>&1 && ! command -v docker >/dev/null 2>&1; then
  echo "[FAIL] Need prowler (pip install prowler) or docker."; exit 3
fi

if [[ $LIST -eq 1 ]]; then
  echo "[INFO] CIS compliance frameworks Prowler supports for $PROVIDER:"
  prowler "$PROVIDER" --list-compliance 2>/dev/null | grep -i cis || \
    echo "  (run 'prowler $PROVIDER --list-compliance' — prowler not on PATH here)"
  exit 0
fi

echo "[INFO] CIS Benchmark assessment: $FRAMEWORK"
# Delegate to the toolkit's Prowler wrapper for consistent output/severity gate.
bash "$HERE/../prowler_scan.sh" "$PROVIDER" \
  --compliance "$FRAMEWORK" \
  --output-dir "cis-${PROVIDER}-${VERSION}"
rc=$?
case $rc in
  0) echo "[OK] CIS $VERSION ($PROVIDER): no failing checks at gate severity." ;;
  2) echo "[FAIL] CIS $VERSION ($PROVIDER): failing checks — see cis-${PROVIDER}-${VERSION}/" ;;
  *) echo "[FAIL] CIS assessment error (auth/tooling)." ;;
esac
exit $rc
