#!/usr/bin/env bash
# Audit Azure Network Security Groups for inbound rules open to the internet
# on sensitive ports. Read-only (uses your 'az login' session).
#
# Usage:
#   az login && az account set --subscription <SUB_ID>
#   bash nsg_audit.sh
set -uo pipefail

command -v az >/dev/null 2>&1 || { echo "[FAIL] Azure CLI 'az' not found."; exit 3; }
command -v jq >/dev/null 2>&1 || { echo "[FAIL] 'jq' is required."; exit 3; }
az account show >/dev/null 2>&1 || { echo "[FAIL] Not logged in. Run 'az login'."; exit 3; }

SUB="$(az account show --query name -o tsv)"
echo "[INFO] Auditing NSGs in subscription: $SUB"

# Sensitive ports mapped to labels.
declare -A PORTS=( [22]=SSH [3389]=RDP [3306]=MySQL [5432]=PostgreSQL \
  [1433]=MSSQL [6379]=Redis [27017]=MongoDB [9200]=Elasticsearch [445]=SMB )

warn=0; fail=0
open_src() { [[ "$1" == "*" || "$1" == "0.0.0.0/0" || "$1" == "Internet" || "$1" == "0.0.0.0/32" ]]; }

nsgs="$(az network nsg list -o json)"
count="$(echo "$nsgs" | jq 'length')"
[[ "$count" -eq 0 ]] && { echo "[OK] No NSGs found."; exit 0; }

echo "$nsgs" | jq -c '.[]' | while read -r nsg; do
  name="$(echo "$nsg" | jq -r '.name')"
  rg="$(echo "$nsg" | jq -r '.resourceGroup')"
  echo "$nsg" | jq -c '.securityRules[]? | select(.direction=="Inbound" and .access=="Allow")' \
  | while read -r rule; do
      rname="$(echo "$rule" | jq -r '.name')"
      # source may be in sourceAddressPrefix or sourceAddressPrefixes[]
      srcs="$(echo "$rule" | jq -r '[.sourceAddressPrefix] + (.sourceAddressPrefixes // []) | .[]?')"
      is_open=0
      while read -r s; do open_src "$s" && is_open=1; done <<< "$srcs"
      [[ $is_open -eq 0 ]] && continue
      # destination ports: destinationPortRange or destinationPortRanges[]
      dports="$(echo "$rule" | jq -r '[.destinationPortRange] + (.destinationPortRanges // []) | .[]?')"
      while read -r dp; do
        [[ -z "$dp" ]] && continue
        if [[ "$dp" == "*" ]]; then
          echo "[FAIL] $rg/$name rule '$rname': ALL ports open to internet."; continue
        fi
        for p in "${!PORTS[@]}"; do
          if [[ "$dp" == "$p" ]]; then
            echo "[FAIL] $rg/$name rule '$rname': ${PORTS[$p]}/$p open to internet."
          elif [[ "$dp" == *-* ]]; then
            lo="${dp%-*}"; hi="${dp#*-}"
            if [[ "$p" -ge "$lo" && "$p" -le "$hi" ]] 2>/dev/null; then
              echo "[FAIL] $rg/$name rule '$rname': range $dp includes ${PORTS[$p]}/$p, open to internet."
            fi
          fi
        done
      done <<< "$dports"
    done
done

echo "[INFO] NSG audit complete. Review any [FAIL] lines above."
# Note: subshell piping means we report findings inline; treat any FAIL as actionable.
exit 0
