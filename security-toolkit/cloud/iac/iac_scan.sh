#!/usr/bin/env bash
# Scan Infrastructure-as-Code (Terraform, CloudFormation, ARM/Bicep, K8s) for
# misconfigurations using whichever scanners are installed. Read-only.
#
# Supports (used if present): checkov, tfsec, trivy config, kube-linter.
# Exit: 0 clean, 2 findings, 3 no scanner available.
#
# Usage: bash iac_scan.sh [target_dir]
set -uo pipefail

DIR="${1:-.}"
[[ -d "$DIR" ]] || { echo "[FAIL] Not a directory: $DIR"; exit 3; }
echo "[INFO] IaC scan of: $(cd "$DIR" && pwd)"

ran=0; status=0
run() { echo "[INFO] \$ $*"; "$@"; }

if command -v checkov >/dev/null 2>&1; then
  ran=1
  echo "[INFO] Running checkov (broad IaC policy scan)…"
  run checkov -d "$DIR" --compact --quiet || status=2
fi

if command -v tfsec >/dev/null 2>&1; then
  ran=1
  echo "[INFO] Running tfsec (Terraform)…"
  run tfsec "$DIR" --no-color || status=2
fi

if command -v trivy >/dev/null 2>&1; then
  ran=1
  echo "[INFO] Running trivy config (IaC misconfig + secrets)…"
  run trivy config "$DIR" --exit-code 2 || status=2
fi

if command -v kube-linter >/dev/null 2>&1; then
  if compgen -G "$DIR/**/*.yaml" >/dev/null 2>&1 || compgen -G "$DIR/*.yaml" >/dev/null 2>&1; then
    ran=1
    echo "[INFO] Running kube-linter (Kubernetes manifests)…"
    run kube-linter lint "$DIR" || status=2
  fi
fi

if [[ $ran -eq 0 ]]; then
  cat <<'EOF'
[FAIL] No IaC scanner found. Install at least one:
  - checkov:      pip install checkov
  - tfsec:        https://github.com/aquasecurity/tfsec
  - trivy:        https://github.com/aquasecurity/trivy
  - kube-linter:  https://github.com/stackrox/kube-linter
EOF
  exit 3
fi

[[ $status -eq 0 ]] && echo "[OK] No IaC misconfigurations reported." \
                     || echo "[FAIL] IaC findings reported — review output above."
exit $status
