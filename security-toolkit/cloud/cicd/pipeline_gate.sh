#!/usr/bin/env bash
# Production DevSecOps CI/CD security gate.
#
# Orchestrates the industry-standard scanners, writes SARIF + JSON reports to a
# report directory (for upload to GitHub code scanning / any SARIF viewer), and
# fails the build on findings at/above a severity threshold.
#
# Stages (each runs only if its tool / relevant inputs are present):
#   1. Secrets            gitleaks           -> gitleaks.sarif
#   2. Dependencies/SCA   trivy fs (vuln)    -> sca.sarif
#   3. IaC misconfig      checkov / trivy    -> iac.sarif
#   4. Container image    trivy image        -> image.sarif   (needs --image)
#   5. Cloud CSPM         prowler_scan.sh    (needs --cloud <provider>)
#
# Usage:
#   pipeline_gate.sh [--path .] [--report-dir security-reports]
#                    [--severity CRITICAL,HIGH] [--image ref]
#                    [--cloud aws|azure|gcp] [--soft]
#
#   --soft   Report findings but exit 0 (warn-only, e.g. first rollout).
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLKIT="$(cd "$HERE/../.." && pwd)"

PATH_TARGET="."
REPORT_DIR="security-reports"
SEVERITY="CRITICAL,HIGH"
IMAGE=""
CLOUD=""
SOFT=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --path)       PATH_TARGET="$2"; shift 2 ;;
    --report-dir) REPORT_DIR="$2"; shift 2 ;;
    --severity)   SEVERITY="$2"; shift 2 ;;
    --image)      IMAGE="$2"; shift 2 ;;
    --cloud)      CLOUD="$2"; shift 2 ;;
    --soft)       SOFT=1; shift ;;
    *) echo "[WARN] Unknown arg: $1"; shift ;;
  esac
done
mkdir -p "$REPORT_DIR"

echo "=================================================="
echo " DevSecOps gate — target=$PATH_TARGET severity>=$SEVERITY"
echo " reports -> $REPORT_DIR/"
echo "=================================================="
overall=0
fail_stage() { echo "[GATE] Stage '$1' reported blocking findings."; overall=1; }
have() { command -v "$1" >/dev/null 2>&1; }

# --- 1. Secrets -----------------------------------------------------------
echo; echo "--- [1/5] Secrets ---"
if have gitleaks; then
  gitleaks detect --source "$PATH_TARGET" --no-banner --redact \
    --report-format sarif --report-path "$REPORT_DIR/gitleaks.sarif" \
    || fail_stage "secrets(gitleaks)"
elif [[ -f "$TOOLKIT/devsecops/secrets_scan.py" ]]; then
  echo "[INFO] gitleaks not found; using built-in fallback scanner."
  python3 "$TOOLKIT/devsecops/secrets_scan.py" "$PATH_TARGET" || fail_stage "secrets(builtin)"
else
  echo "[WARN] No secret scanner available (install gitleaks)."
fi

# --- 2. Dependencies / SCA ------------------------------------------------
echo; echo "--- [2/5] Dependencies / SCA ---"
if have trivy; then
  trivy fs --scanners vuln --severity "$SEVERITY" \
    --exit-code 1 --format sarif --output "$REPORT_DIR/sca.sarif" "$PATH_TARGET" \
    || fail_stage "dependencies(trivy)"
elif [[ -f "$TOOLKIT/vuln/dependency_audit.sh" ]]; then
  echo "[INFO] trivy not found; using native package-manager audits."
  bash "$TOOLKIT/vuln/dependency_audit.sh" "$PATH_TARGET" || fail_stage "dependencies"
else
  echo "[WARN] No SCA scanner available (install trivy)."
fi

# --- 3. IaC misconfiguration ----------------------------------------------
echo; echo "--- [3/5] IaC misconfiguration ---"
if have checkov; then
  checkov -d "$PATH_TARGET" --compact --quiet \
    -o sarif --output-file-path "$REPORT_DIR" >/dev/null 2>&1
  # checkov writes results.sarif into the dir; normalize the name.
  [[ -f "$REPORT_DIR/results_sarif.sarif" ]] && mv "$REPORT_DIR/results_sarif.sarif" "$REPORT_DIR/iac.sarif"
  [[ -f "$REPORT_DIR/results.sarif" ]] && mv "$REPORT_DIR/results.sarif" "$REPORT_DIR/iac.sarif"
  checkov -d "$PATH_TARGET" --compact --quiet >/dev/null 2>&1 || fail_stage "iac(checkov)"
elif have trivy; then
  trivy config --severity "$SEVERITY" --exit-code 1 \
    --format sarif --output "$REPORT_DIR/iac.sarif" "$PATH_TARGET" \
    || fail_stage "iac(trivy)"
elif [[ -f "$HERE/../iac/iac_scan.sh" ]]; then
  bash "$HERE/../iac/iac_scan.sh" "$PATH_TARGET"; rc=$?
  [[ $rc -eq 2 ]] && fail_stage "iac"
else
  echo "[WARN] No IaC scanner available (install checkov or trivy)."
fi

# --- 4. Container image ---------------------------------------------------
echo; echo "--- [4/5] Container image ---"
if [[ -n "$IMAGE" ]]; then
  if have trivy; then
    trivy image --severity "$SEVERITY" --exit-code 1 \
      --format sarif --output "$REPORT_DIR/image.sarif" "$IMAGE" \
      || fail_stage "image(trivy)"
  else
    echo "[WARN] --image given but trivy not installed."
  fi
else
  echo "[INFO] No --image supplied; skipping."
fi

# --- 5. Cloud CSPM --------------------------------------------------------
echo; echo "--- [5/5] Cloud CSPM ---"
if [[ -n "$CLOUD" ]]; then
  bash "$HERE/../prowler_scan.sh" "$CLOUD" \
    --severity "$(echo "$SEVERITY" | tr 'A-Z' 'a-z')" \
    --output-dir "$REPORT_DIR/prowler-$CLOUD"; rc=$?
  [[ $rc -eq 2 ]] && fail_stage "cloud($CLOUD)"
  [[ $rc -eq 3 ]] && echo "[WARN] Cloud CSPM skipped (setup/auth)."
else
  echo "[INFO] No --cloud supplied; skipping CSPM."
fi

echo; echo "=================================================="
if [[ $overall -eq 0 ]]; then
  echo "[GATE] PASS — no blocking findings at/above $SEVERITY."
  exit 0
fi
echo "[GATE] FAIL — blocking findings. SARIF in $REPORT_DIR/"
[[ $SOFT -eq 1 ]] && { echo "[GATE] --soft: exiting 0 (warn-only)."; exit 0; }
exit 2
