#!/usr/bin/env bash
# Audit GCP VPC firewall rules for sensitive ports open to 0.0.0.0/0.
# Read-only (uses your 'gcloud auth' session).
#
# Usage:
#   gcloud config set project <PROJECT_ID>
#   bash firewall_audit.sh [PROJECT_ID]
set -uo pipefail

# Uses associative arrays → needs bash 4+ (macOS default bash is 3.2).
if [[ "${BASH_VERSINFO:-0}" -lt 4 ]]; then
  echo "[FAIL] Needs bash 4+ (found ${BASH_VERSION:-unknown}). On macOS: 'brew install bash' then run with it, or use Linux/WSL/Cloud Shell." >&2
  exit 3
fi

command -v gcloud >/dev/null 2>&1 || { echo "[FAIL] 'gcloud' not found."; exit 3; }
command -v jq >/dev/null 2>&1 || { echo "[FAIL] 'jq' is required."; exit 3; }

PROJECT="${1:-$(gcloud config get-value project 2>/dev/null)}"
[[ -z "$PROJECT" || "$PROJECT" == "(unset)" ]] && { echo "[FAIL] No project set."; exit 3; }
echo "[INFO] Auditing firewall rules for project: $PROJECT"

declare -A PORTS=( [22]=SSH [3389]=RDP [3306]=MySQL [5432]=PostgreSQL \
  [1433]=MSSQL [6379]=Redis [27017]=MongoDB [9200]=Elasticsearch [445]=SMB )

rules="$(gcloud compute firewall-rules list --project "$PROJECT" --format=json 2>/dev/null)" \
  || { echo "[FAIL] Could not list firewall rules."; exit 3; }
[[ "$(echo "$rules" | jq 'length')" -eq 0 ]] && { echo "[OK] No firewall rules."; exit 0; }

echo "$rules" | jq -c '.[] | select(.direction=="INGRESS" and (.disabled|not) and (.sourceRanges // [] | index("0.0.0.0/0")))' \
| while read -r rule; do
    name="$(echo "$rule" | jq -r '.name')"
    # Rule may 'allow' tcp with specific ports or all ports.
    echo "$rule" | jq -c '.allowed[]?' | while read -r allow; do
      proto="$(echo "$allow" | jq -r '.IPProtocol')"
      [[ "$proto" != "tcp" && "$proto" != "all" ]] && continue
      ports="$(echo "$allow" | jq -r '.ports[]?' )"
      if [[ -z "$ports" ]]; then
        echo "[FAIL] $name: $proto ALL ports open to 0.0.0.0/0."
        continue
      fi
      while read -r pr; do
        [[ -z "$pr" ]] && continue
        for p in "${!PORTS[@]}"; do
          if [[ "$pr" == "$p" ]]; then
            echo "[FAIL] $name: ${PORTS[$p]}/$p open to 0.0.0.0/0."
          elif [[ "$pr" == *-* ]]; then
            lo="${pr%-*}"; hi="${pr#*-}"
            if [[ "$p" -ge "$lo" && "$p" -le "$hi" ]] 2>/dev/null; then
              echo "[FAIL] $name: range $pr includes ${PORTS[$p]}/$p, open to 0.0.0.0/0."
            fi
          fi
        done
      done <<< "$ports"
    done
done

echo "[INFO] Firewall audit complete. Review [FAIL] lines above."
exit 0
