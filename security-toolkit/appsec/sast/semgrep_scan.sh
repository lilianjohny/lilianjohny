#!/usr/bin/env bash
# SAST for application code using Semgrep with OWASP-aligned rulesets plus the
# toolkit's custom app-security rules. Emits SARIF. Read-only.
#
# Usage: bash semgrep_scan.sh --path . [--severity ERROR] [--sarif out.sarif]
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATH_TARGET="."; SEV="WARNING"; SARIF="semgrep.sarif"
while [[ $# -gt 0 ]]; do case "$1" in
  --path) PATH_TARGET="$2"; shift 2 ;;
  --severity) SEV="$2"; shift 2 ;;
  --sarif) SARIF="$2"; shift 2 ;;
  *) shift ;; esac; done

command -v semgrep >/dev/null 2>&1 || {
  echo "[FAIL] semgrep not installed (pip install semgrep)."; exit 3; }

echo "[INFO] Semgrep SAST on '$PATH_TARGET' (min severity: $SEV)"
# Registry rulesets: OWASP Top 10, secrets, plus our custom rules.
semgrep scan \
  --config p/owasp-top-ten \
  --config p/security-audit \
  --config "$HERE/rules/custom-appsec.yml" \
  --severity "$SEV" \
  --sarif --output "$SARIF" \
  --error \
  "$PATH_TARGET"
rc=$?
[[ $rc -eq 0 ]] && echo "[OK] SAST: no findings at/above $SEV. SARIF: $SARIF" \
               || echo "[FAIL] SAST: findings at/above $SEV. SARIF: $SARIF"
exit $rc
