#!/usr/bin/env bash
# Audit Azure RBAC for privileged-role sprawl at subscription scope.
# Read-only (uses your 'az login' session).
#
# Usage:
#   az login && az account set --subscription <SUB_ID>
#   bash rbac_audit.sh
set -uo pipefail

command -v az >/dev/null 2>&1 || { echo "[FAIL] Azure CLI 'az' not found."; exit 3; }
command -v jq >/dev/null 2>&1 || { echo "[FAIL] 'jq' is required."; exit 3; }
az account show >/dev/null 2>&1 || { echo "[FAIL] Not logged in. Run 'az login'."; exit 3; }

SUB_ID="$(az account show --query id -o tsv)"
echo "[INFO] Auditing RBAC for subscription: $(az account show --query name -o tsv)"

# Owner assignments at subscription scope
owners="$(az role assignment list --role Owner \
  --scope "/subscriptions/$SUB_ID" -o json 2>/dev/null)"
owner_count="$(echo "$owners" | jq 'length')"
echo "[INFO] Owner role assignments at subscription scope: $owner_count"
if [[ "$owner_count" -gt 3 ]]; then
  echo "[WARN] $owner_count subscription Owners — minimize standing Owner access."
fi
echo "$owners" | jq -r '.[] | "  Owner: \(.principalName // .principalId) (\(.principalType))"'

# Guest users holding any role
guests="$(az role assignment list --all -o json 2>/dev/null \
  | jq -r '.[] | select(.principalType=="User") | .principalName' \
  | grep -i "#EXT#" || true)"
if [[ -n "$guests" ]]; then
  echo "[WARN] Guest (external) users hold role assignments:"
  echo "$guests" | sed 's/^/  /'
fi

# Classic administrators (legacy, should be removed)
classic="$(az role assignment list --include-classic-administrators \
  -o json 2>/dev/null | jq -r '.[] | select(.roleDefinitionName | test("Administrator";"i")) | .principalName' | sort -u || true)"
if [[ -n "$classic" ]]; then
  echo "[WARN] Classic administrators present (migrate to RBAC):"
  echo "$classic" | sed 's/^/  /'
fi

echo "[OK] RBAC audit complete. Review [WARN] lines above."
exit 0
