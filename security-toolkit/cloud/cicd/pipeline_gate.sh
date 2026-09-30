#!/usr/bin/env bash
# DevSecOps CI/CD security gate. Runs the core "shift-left" checks in one pass
# and fails the build (non-zero exit) if any stage reports findings.
#
# Stages (each runs only if its tooling / relevant files are present):
#   1. Secret scanning        (gitleaks, or the toolkit's secrets_scan.py)
#   2. Dependency / SCA audit  (../../vuln/dependency_audit.sh)
#   3. IaC misconfiguration    (../iac/iac_scan.sh)
#   4. Container image scan    (trivy image, if --image given)
#
# Usage:
#   bash pipeline_gate.sh [--path .] [--image registry/app:tag] [--soft]
#
#   --soft   Report findings but exit 0 (for warn-only pipelines / first rollout).
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLKIT="$(cd "$HERE/../.." && pwd)"

PATH_TARGET="."
IMAGE=""
SOFT=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --path) PATH_TARGET="$2"; shift 2 ;;
    --image) IMAGE="$2"; shift 2 ;;
    --soft) SOFT=1; shift ;;
    *) echo "[WARN] Unknown arg: $1"; shift ;;
  esac
done

echo "=================================================="
echo " DevSecOps pipeline gate — target: $PATH_TARGET"
echo "=================================================="
overall=0
fail_stage() { echo "[GATE] Stage '$1' reported findings."; overall=1; }

# --- 1. Secret scanning ---------------------------------------------------
echo; echo "--- [1/4] Secret scanning ---"
if command -v gitleaks >/dev/null 2>&1; then
  gitleaks detect --source "$PATH_TARGET" --no-banner --redact || fail_stage "secrets(gitleaks)"
elif [[ -f "$TOOLKIT/devsecops/secrets_scan.py" ]]; then
  python3 "$TOOLKIT/devsecops/secrets_scan.py" "$PATH_TARGET" || fail_stage "secrets(builtin)"
else
  echo "[WARN] No secret scanner available (install gitleaks)."
fi

# --- 2. Dependency / SCA --------------------------------------------------
echo; echo "--- [2/4] Dependency / SCA audit ---"
if [[ -f "$TOOLKIT/vuln/dependency_audit.sh" ]]; then
  bash "$TOOLKIT/vuln/dependency_audit.sh" "$PATH_TARGET" || fail_stage "dependencies"
else
  echo "[WARN] dependency_audit.sh not found."
fi

# --- 3. IaC misconfiguration ----------------------------------------------
echo; echo "--- [3/4] IaC misconfiguration scan ---"
if [[ -f "$HERE/../iac/iac_scan.sh" ]]; then
  # Exit 3 = no scanner installed; treat as skip, not gate failure.
  bash "$HERE/../iac/iac_scan.sh" "$PATH_TARGET"; rc=$?
  [[ $rc -eq 2 ]] && fail_stage "iac"
else
  echo "[WARN] iac_scan.sh not found."
fi

# --- 4. Container image scan ----------------------------------------------
echo; echo "--- [4/4] Container image scan ---"
if [[ -n "$IMAGE" ]]; then
  if command -v trivy >/dev/null 2>&1; then
    trivy image --exit-code 1 --severity HIGH,CRITICAL "$IMAGE" || fail_stage "image"
  else
    echo "[WARN] --image given but trivy not installed."
  fi
else
  echo "[INFO] No --image supplied; skipping image scan."
fi

echo; echo "=================================================="
if [[ $overall -eq 0 ]]; then
  echo "[GATE] PASS — no blocking findings."
  exit 0
fi
echo "[GATE] FAIL — one or more stages reported findings."
if [[ $SOFT -eq 1 ]]; then
  echo "[GATE] --soft set: exiting 0 despite findings (warn-only mode)."
  exit 0
fi
exit 2
