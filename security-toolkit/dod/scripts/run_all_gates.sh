#!/usr/bin/env bash
# DoD Software Factory — run all mandatory control gates and produce a cATO
# evidence bundle. Any hard-gate FAIL blocks promotion (exit 2).
#
# Gates: secrets, SAST, SCA, SBOM, container scan, STIG, DAST, signing.
# Each gate degrades gracefully if its tool is absent and records that state;
# a gate whose tool is missing is reported as SKIP and (by default) blocks,
# because a mandatory gate cannot be silently waived. Use --allow-skips only in
# a non-authoritative dev run.
#
# Usage:
#   run_all_gates.sh --path . [--image <ref>] [--dast-target <url>]
#                    [--stig-content <xml> --stig-profile <id>]
#                    [--severity high] [--evidence cato-evidence] [--allow-skips]
set -uo pipefail
# Uses associative arrays → needs bash 4+ (macOS default bash is 3.2).
if [[ "${BASH_VERSINFO:-0}" -lt 4 ]]; then
  echo "[FAIL] Needs bash 4+ (found ${BASH_VERSION:-unknown}). On macOS: 'brew install bash' then run with it, or use Linux/WSL/Cloud Shell." >&2
  exit 3
fi
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PATH_TARGET="."; IMAGE=""; DAST_TARGET=""; STIG_CONTENT=""; STIG_PROFILE=""
SEV="high"; EVID="cato-evidence"; ALLOW_SKIPS=0
while [[ $# -gt 0 ]]; do case "$1" in
  --path) PATH_TARGET="$2"; shift 2 ;;
  --image) IMAGE="$2"; shift 2 ;;
  --dast-target) DAST_TARGET="$2"; shift 2 ;;
  --stig-content) STIG_CONTENT="$2"; shift 2 ;;
  --stig-profile) STIG_PROFILE="$2"; shift 2 ;;
  --severity) SEV="$2"; shift 2 ;;
  --evidence) EVID="$2"; shift 2 ;;
  --allow-skips) ALLOW_SKIPS=1; shift ;;
  *) echo "[WARN] unknown arg: $1"; shift ;; esac; done
mkdir -p "$EVID"

declare -A RESULT
run_gate() { # name  command...
  local name="$1"; shift
  echo; echo "===== GATE: $name ====="
  if "$@"; then RESULT[$name]=PASS
  else
    local rc=$?
    case $rc in
      2) RESULT[$name]=FAIL ;;
      3) RESULT[$name]=SKIP ;;
      *) RESULT[$name]=FAIL ;;
    esac
  fi
  echo "----- $name: ${RESULT[$name]} -----"
}

# 1 secrets
run_gate secrets   bash "$HERE/gate_secrets.sh" --path "$PATH_TARGET" --evidence "$EVID"
# 2 SAST
run_gate sast      bash "$HERE/gate_sast.sh" --path "$PATH_TARGET" --evidence "$EVID"
# 4 SBOM (run before SCA so SCA can consume it)
if bash "$HERE/generate_sbom.sh" --path "$PATH_TARGET" --out "$EVID/sbom" --name artifact; then
  RESULT[sbom]=PASS
else
  RESULT[sbom]=SKIP
fi
# 3 SCA (consume SBOM if present)
run_gate sca       bash "$HERE/gate_sca.sh" --path "$PATH_TARGET" \
                        --sbom "$EVID/sbom/artifact.cdx.json" --severity "$SEV" --evidence "$EVID"
# 5 container scan
if [[ -n "$IMAGE" ]]; then
  run_gate container bash "$HERE/gate_container_scan.sh" "$IMAGE" --severity "$SEV" --evidence "$EVID"
else
  echo; echo "[INFO] No --image; container gate not run."; RESULT[container]=SKIP
fi
# 6 STIG
if [[ -n "$STIG_CONTENT" && -n "$STIG_PROFILE" ]]; then
  run_gate stig    bash "$HERE/gate_stig.sh" --content "$STIG_CONTENT" --profile "$STIG_PROFILE" --evidence "$EVID"
else
  echo; echo "[INFO] No STIG content/profile; STIG gate not run."; RESULT[stig]=SKIP
fi
# 7 DAST
if [[ -n "$DAST_TARGET" ]]; then
  run_gate dast    bash "$HERE/gate_dast.sh" --target "$DAST_TARGET" --evidence "$EVID"
else
  echo; echo "[INFO] No --dast-target; recording DAST as N/A (no runtime endpoint)."
  bash "$HERE/gate_dast.sh" --not-applicable "no runtime endpoint supplied" --evidence "$EVID" >/dev/null
  RESULT[dast]=NA
fi
# 8 signing (verify tooling only here; actual sign happens post-build in the pipeline)
if command -v cosign >/dev/null 2>&1; then RESULT[signing]=PASS; echo "[INFO] cosign available for signing gate."; else RESULT[signing]=SKIP; fi

# --- Emit machine-readable summary for the policy gate ---
SUMMARY="$EVID/summary.json"
{
  echo "{"
  echo "  \"generated\": \"$(date -u +%FT%TZ)\","
  echo "  \"path\": \"$PATH_TARGET\","
  echo "  \"severity_threshold\": \"$SEV\","
  echo "  \"gates\": {"
  keys=(secrets sast sca sbom container stig dast signing)
  for i in "${!keys[@]}"; do
    k="${keys[$i]}"; v="${RESULT[$k]:-SKIP}"
    [[ "$v" == "NA" ]] && v="N/A"
    sep=","; [[ $i -eq $((${#keys[@]}-1)) ]] && sep=""
    echo "    \"$k\": \"$v\"$sep"
  done
  echo "  }"
  echo "}"
} > "$SUMMARY"

echo; echo "=================================================="
echo " Control gate summary (cATO evidence: $EVID/)"
echo "=================================================="
fail=0; skip=0
for k in secrets sast sca sbom container stig dast signing; do
  v="${RESULT[$k]:-SKIP}"
  printf "  %-10s %s\n" "$k" "$v"
  [[ "$v" == "FAIL" ]] && fail=1
  [[ "$v" == "SKIP" ]] && skip=1
done
echo "  summary -> $SUMMARY"

if [[ $fail -eq 1 ]]; then
  echo "[GATE] FAIL — a mandatory control gate failed. Artifact NOT promotable."
  exit 2
fi
if [[ $skip -eq 1 && $ALLOW_SKIPS -eq 0 ]]; then
  echo "[GATE] BLOCKED — a mandatory gate was skipped (tool/input missing)."
  echo "       Provide the missing tool/input, or use --allow-skips for a dev-only run."
  exit 2
fi
echo "[GATE] PASS — all mandatory control gates satisfied."
exit 0
