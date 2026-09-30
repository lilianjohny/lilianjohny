#!/usr/bin/env bash
# Control gate 6: STIG / compliance scan (hard gate).
# Runs an OpenSCAP evaluation against a DISA STIG (or SCAP) profile and emits
# HTML + ARF/XCCDF results for the evidence bundle.
#
# DISA SCAP content (the *-scap.zip / benchmark XML) requires download from the
# DoD Cyber Exchange (public.cyber.mil) — supply the datastream via --content.
#
# Usage:
#   gate_stig.sh --content <ssg-or-stig-datastream.xml> --profile <profile-id>
#                [--evidence cato-evidence]
#   gate_stig.sh --list --content <datastream.xml>      # list available profiles
set -uo pipefail
CONTENT=""; PROFILE=""; EVID="cato-evidence"; LIST=0
while [[ $# -gt 0 ]]; do case "$1" in
  --content) CONTENT="$2"; shift 2 ;;
  --profile) PROFILE="$2"; shift 2 ;;
  --evidence) EVID="$2"; shift 2 ;;
  --list) LIST=1; shift ;;
  *) shift ;; esac; done

command -v oscap >/dev/null 2>&1 || {
  echo "[FAIL] OpenSCAP 'oscap' not installed (apt-get install libopenscap8 / dnf install openscap-scanner)."
  echo "       SCAP Security Guide content: package 'scap-security-guide'."
  exit 3; }

if [[ -z "$CONTENT" ]]; then
  echo "[FAIL] Provide --content <SCAP datastream xml> (DISA STIG SCAP or SSG)."
  echo "       DISA STIG SCAP: https://public.cyber.mil/stigs/  (CAC/public downloads)"
  exit 3
fi
[[ -r "$CONTENT" ]] || { echo "[FAIL] Cannot read content: $CONTENT"; exit 3; }
mkdir -p "$EVID"

if [[ $LIST -eq 1 ]]; then
  echo "[INFO] Profiles available in $CONTENT:"
  oscap info "$CONTENT" | sed -n '/Profiles:/,/Referenced/p'
  exit 0
fi
[[ -z "$PROFILE" ]] && { echo "[FAIL] Provide --profile <id> (use --list to discover)."; exit 3; }

echo "[INFO] Evaluating STIG profile '$PROFILE'…"
oscap xccdf eval \
  --profile "$PROFILE" \
  --results-arf "$EVID/stig-arf.xml" \
  --report "$EVID/stig-report.html" \
  "$CONTENT"; rc=$?

# oscap exit: 0 = all pass, 2 = at least one rule failed, 1 = error.
case $rc in
  0) echo "[OK] Gate 6 (STIG): PASS. Report: $EVID/stig-report.html"; exit 0 ;;
  2) echo "[FAIL] Gate 6 (STIG): rule failures. Report: $EVID/stig-report.html"; exit 2 ;;
  *) echo "[FAIL] Gate 6 (STIG): oscap error ($rc)."; exit 3 ;;
esac
