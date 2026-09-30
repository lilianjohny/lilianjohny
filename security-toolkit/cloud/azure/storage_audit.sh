#!/usr/bin/env bash
# Audit Azure Storage accounts for weak transport / public-access settings.
# Read-only (uses your 'az login' session).
#
# Usage:
#   az login && az account set --subscription <SUB_ID>
#   bash storage_audit.sh
set -uo pipefail

command -v az >/dev/null 2>&1 || { echo "[FAIL] Azure CLI 'az' not found."; exit 3; }
command -v jq >/dev/null 2>&1 || { echo "[FAIL] 'jq' is required."; exit 3; }
az account show >/dev/null 2>&1 || { echo "[FAIL] Not logged in. Run 'az login'."; exit 3; }

echo "[INFO] Auditing Storage accounts in: $(az account show --query name -o tsv)"
status=0

accounts="$(az storage account list -o json)"
[[ "$(echo "$accounts" | jq 'length')" -eq 0 ]] && { echo "[OK] No storage accounts."; exit 0; }

echo "$accounts" | jq -c '.[]' | while read -r acct; do
  name="$(echo "$acct" | jq -r '.name')"
  https_only="$(echo "$acct" | jq -r '.enableHttpsTrafficOnly')"
  public_blob="$(echo "$acct" | jq -r '.allowBlobPublicAccess')"
  min_tls="$(echo "$acct" | jq -r '.minimumTlsVersion')"
  default_action="$(echo "$acct" | jq -r '.networkRuleSet.defaultAction')"

  [[ "$https_only" != "true" ]] && echo "[FAIL] $name: HTTPS-only traffic not enforced."
  [[ "$public_blob" == "true" ]] && echo "[WARN] $name: allowBlobPublicAccess is enabled."
  [[ "$min_tls" != "TLS1_2" ]] && echo "[WARN] $name: minimum TLS is ${min_tls:-unset} (want TLS1_2)."
  [[ "$default_action" == "Allow" ]] && echo "[WARN] $name: network default action is Allow (open)."
  [[ "$https_only" == "true" && "$public_blob" != "true" && "$min_tls" == "TLS1_2" ]] \
    && echo "[OK]   $name: transport & public-access baseline looks good."
done

echo "[INFO] Storage audit complete. Address [FAIL]/[WARN] lines above."
exit $status
