#!/usr/bin/env bash
# One-command setup + environment doctor for the security toolkit.
#
#   bash setup.sh            # install core Python deps, make scripts executable
#   bash setup.sh --venv     # also create/use a .venv virtual environment
#   bash setup.sh --cloud    # also install boto3 (AWS scripts)
#   bash setup.sh --doctor   # only run the tool doctor (no install)
#
# After setup, run any script directly, e.g.:
#   python3 vuln/header_check.py https://example.com
#   bash hardening/ssh_audit.sh
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

USE_VENV=0; WITH_CLOUD=0; ONLY_DOCTOR=0
for a in "$@"; do case "$a" in
  --venv) USE_VENV=1 ;;
  --cloud) WITH_CLOUD=1 ;;
  --doctor) ONLY_DOCTOR=1 ;;
  *) echo "[WARN] unknown flag: $a" ;;
esac; done

have() { command -v "$1" >/dev/null 2>&1; }

if [[ $ONLY_DOCTOR -eq 0 ]]; then
  command -v python3 >/dev/null || { echo "[FAIL] python3 not found (need 3.9+)."; exit 3; }
  echo "[INFO] Python: $(python3 --version)"

  if [[ $USE_VENV -eq 1 ]]; then
    [[ -d .venv ]] || python3 -m venv .venv
    # shellcheck disable=SC1091
    source .venv/bin/activate
    echo "[INFO] Using virtualenv: $(pwd)/.venv (activate with: source .venv/bin/activate)"
  fi

  echo "[INFO] Installing core Python dependencies…"
  python3 -m pip install -q -r requirements.txt || echo "[WARN] core deps install had issues."
  if [[ $WITH_CLOUD -eq 1 ]]; then
    echo "[INFO] Installing cloud deps (boto3)…"
    python3 -m pip install -q -r requirements-cloud.txt || echo "[WARN] cloud deps install had issues."
  fi

  echo "[INFO] Making scripts executable…"
  find . -type f \( -name '*.sh' -o -name '*.py' \) -exec chmod +x {} + 2>/dev/null || true
  echo "[OK] Setup complete."
  echo
fi

# ---- Doctor: which optional external tools are present? -------------------
echo "=================================================="
echo " Tool doctor — optional CLIs (scripts use them if present)"
echo "=================================================="
group() {
  local title="$1"; shift
  echo; echo "• $title"
  for t in "$@"; do
    if have "$t"; then printf "   \033[32m✓\033[0m %-16s %s\n" "$t" "$(command -v "$t")"
    else printf "   \033[33m–\033[0m %-16s (not installed)\n" "$t"; fi
  done
}
# Fall back to plain text if not a TTY
[[ -t 1 ]] || group() { local title="$1"; shift; echo; echo "• $title"; for t in "$@"; do have "$t" && echo "   [x] $t" || echo "   [ ] $t (missing)"; done; }

group "Recon / pentest"        nmap masscan subfinder amass httpx katana ffuf gobuster nuclei nikto sqlmap gowitness testssl.sh sslscan whatweb wafw00f
group "Cloud"                  aws az gcloud prowler scout kubectl kube-bench trivy kubescape cloudsplaining pmapper enumerate-iam
group "DevSecOps / supply chain" syft grype cosign conftest opa semgrep gitleaks checkov oscap zap-baseline.py docker
group "Core"                   python3 bash jq git openssl

echo
echo "Legend: ✓/[x] installed · –/[ ] optional, install only what you need."
echo "Python deps (requests, PyYAML) are required; boto3 is needed for the AWS scripts."
echo "See each area's README.md / COMMANDS.md for install links and usage."
