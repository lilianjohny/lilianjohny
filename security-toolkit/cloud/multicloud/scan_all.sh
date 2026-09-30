#!/usr/bin/env bash
# Unified multi-cloud security scan — runs posture checks across every cloud you
# are authenticated to, in one command. Read-only, uses your own sessions.
#
# For each cloud it detects an active login for, it runs Prowler (severity-gated)
# via the toolkit's wrapper and drops the JSON-OCSF output into <out>/<cloud>/,
# so normalize.py + report.py can build one cross-cloud view.
#
# Usage:
#   bash scan_all.sh                       # scan all logged-in clouds
#   bash scan_all.sh --clouds aws,gcp --out mc-out --severity critical,high
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

CLOUDS=""; OUT="multicloud-out"; SEV="critical,high"
while [[ $# -gt 0 ]]; do case "$1" in
  --clouds) CLOUDS="$2"; shift 2 ;;
  --out) OUT="$2"; shift 2 ;;
  --severity) SEV="$2"; shift 2 ;;
  *) echo "[WARN] unknown arg: $1"; shift ;;
esac; done
have() { command -v "$1" >/dev/null 2>&1; }
mkdir -p "$OUT"

# Auto-detect logged-in clouds if not specified.
detect() {
  local found=""
  have aws && aws sts get-caller-identity >/dev/null 2>&1 && found+="aws,"
  have az && az account show >/dev/null 2>&1 && found+="azure,"
  have gcloud && [ -n "$(gcloud config get-value project 2>/dev/null)" ] && found+="gcp,"
  echo "${found%,}"
}
[[ -z "$CLOUDS" ]] && CLOUDS="$(detect)"
[[ -z "$CLOUDS" ]] && { echo "[FAIL] No authenticated clouds detected. Log in (aws/az/gcloud) or pass --clouds."; exit 3; }

echo "[INFO] Multi-cloud scan — clouds: $CLOUDS (severity $SEV)"
overall=0
IFS=',' read -ra LIST <<< "$CLOUDS"
for c in "${LIST[@]}"; do
  c="$(echo "$c" | tr -d ' ')"
  case "$c" in aws|azure|gcp) ;; *) echo "[WARN] skip unknown cloud: $c"; continue ;; esac
  echo; echo "===== $c ====="
  cdir="$OUT/$c"; mkdir -p "$cdir"
  # Delegate to the toolkit's Prowler wrapper (native binary or container).
  bash "$HERE/../prowler_scan.sh" "$c" --severity "$SEV" --output-dir "$cdir"; rc=$?
  case $rc in
    0) echo "[OK] $c: no findings at/above $SEV." ;;
    2) echo "[WARN] $c: findings present (see $cdir/)."; overall=1 ;;
    3) echo "[WARN] $c: setup/auth issue — skipped."; ;;
    *) echo "[WARN] $c: exit $rc."; overall=1 ;;
  esac
done

echo; echo "[INFO] Scans complete. Build the unified view:"
echo "  python3 $HERE/normalize.py $OUT/*/**.ocsf.json $OUT/*/*.json > $OUT/findings.jsonl"
echo "  python3 $HERE/report.py $OUT/findings.jsonl --baseline $HERE/baseline.csv --out $OUT/report.md"
exit $overall
