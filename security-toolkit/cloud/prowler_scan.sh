#!/usr/bin/env bash
# Production cloud CSPM via Prowler (https://prowler.com) — the industry
# standard open-source posture scanner for AWS, Azure, GCP, and Kubernetes.
#
# This is a thin, opinionated orchestration wrapper: it authenticates via your
# existing cloud session, runs Prowler with machine-readable + human output,
# and gates the pipeline on findings at/above a severity threshold.
#
# Read-only. Uses your own cloud credentials (never passed as arguments).
#
# Usage:
#   ./prowler_scan.sh aws        --severity critical,high
#   ./prowler_scan.sh azure      --output-dir out/azure
#   ./prowler_scan.sh gcp        --compliance cis_3.0_gcp
#   ./prowler_scan.sh kubernetes --severity critical,high,medium
#
# Exit: 0 no findings at/above threshold · 2 findings · 3 setup/auth error.
set -uo pipefail

PROVIDER="${1:-}"
shift || true
case "$PROVIDER" in
  aws|azure|gcp|kubernetes) ;;
  *) echo "[FAIL] Usage: $0 <aws|azure|gcp|kubernetes> [options]"; exit 3 ;;
esac

SEVERITY="critical,high"
OUTDIR="prowler-output/${PROVIDER}"
COMPLIANCE=""
EXTRA=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --severity)   SEVERITY="$2"; shift 2 ;;
    --output-dir) OUTDIR="$2"; shift 2 ;;
    --compliance) COMPLIANCE="$2"; shift 2 ;;
    *)            EXTRA+=("$1"); shift ;;
  esac
done

# Resolve a Prowler invocation: native binary, else the official container.
if command -v prowler >/dev/null 2>&1; then
  RUN=(prowler)
elif command -v docker >/dev/null 2>&1; then
  echo "[INFO] prowler not installed; using toolkit-pinned container image."
  # Mount cloud cred dirs read-only so the container uses your session.
  RUN=(docker run --rm
       -v "$HOME/.aws:/home/prowler/.aws:ro"
       -v "$HOME/.azure:/home/prowler/.azure:ro"
       -v "$HOME/.config/gcloud:/home/prowler/.config/gcloud:ro"
       -v "$(pwd)/${OUTDIR}:/home/prowler/output"
       -e AWS_PROFILE -e AWS_REGION -e AWS_DEFAULT_REGION
       toniblyx/prowler:latest)
  OUTDIR_CONTAINER="/home/prowler/output"
else
  echo "[FAIL] Neither 'prowler' nor 'docker' is available."
  echo "       Install: pip install prowler   (docs: https://docs.prowler.com)"
  exit 3
fi

mkdir -p "$OUTDIR"
OUT_ARG="${OUTDIR_CONTAINER:-$OUTDIR}"

# Severity as space-separated list for Prowler's --severity flag.
SEV_ARGS=(${SEVERITY//,/ })

CMD=("${RUN[@]}" "$PROVIDER"
     --severity "${SEV_ARGS[@]}"
     --output-formats json-ocsf csv html
     --output-directory "$OUT_ARG"
     --status FAIL)
[[ -n "$COMPLIANCE" ]] && CMD+=(--compliance "$COMPLIANCE")
[[ ${#EXTRA[@]} -gt 0 ]] && CMD+=("${EXTRA[@]}")

echo "[INFO] Scanning '$PROVIDER' (severity: $SEVERITY)"
echo "[INFO] \$ ${CMD[*]}"
"${CMD[@]}"
rc=$?

# Prowler exit codes: 0 = no failed findings, 3 = failed findings present,
# other = execution error.
case $rc in
  0) echo "[OK] No findings at/above severity [$SEVERITY]. Reports in $OUTDIR/"; exit 0 ;;
  3) echo "[FAIL] Prowler reported findings at/above [$SEVERITY]. Reports in $OUTDIR/"; exit 2 ;;
  *) echo "[FAIL] Prowler execution error (exit $rc). Check auth/permissions."; exit 3 ;;
esac
