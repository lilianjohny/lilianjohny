# Lab 04 — Multi-Tenant Isolation (Azure)

**Skills practiced:** isolation models (silo/pool/bridge) · RBAC-scoped tenant
boundaries · per-tenant Key Vault keys · data partitioning · per-request scoping.
**Proves (JD):** *"securing … deployments … to multi-tenant use."*

## Objective
Model a pooled SaaS system and prove **Tenant A can never reach Tenant B's data**
at identity, data, and key layers.

## Est. time / cost
2–3 h · **~$0–1**.

## Prerequisites
- Labs 00–01 done. `jq`, Python 3.

---

## Part A — Build (pool)
```bash
az group create -n rg-lab04 -l "$LOCATION"
STG=lab04$RANDOM
az storage account create -n "$STG" -g rg-lab04 -l "$LOCATION" --sku Standard_LRS --allow-blob-public-access false
KEY=$(az storage account keys list -n "$STG" -g rg-lab04 --query '[0].value' -o tsv)
az storage container create --account-name "$STG" --account-key "$KEY" -n tenanta
az storage container create --account-name "$STG" --account-key "$KEY" -n tenantb
echo "B-secret" > /tmp/b.txt
az storage blob upload --account-name "$STG" --account-key "$KEY" -c tenantb -n secret.txt -f /tmp/b.txt
# Two managed identities, initially broad (Storage Blob Data Owner on the whole account)
for T in A B; do
  az identity create -n id-tenant$T -g rg-lab04
  PID=$(az identity show -n id-tenant$T -g rg-lab04 --query principalId -o tsv)
  az role assignment create --assignee "$PID" --role "Storage Blob Data Owner" \
    --scope $(az storage account show -n "$STG" -g rg-lab04 --query id -o tsv)
done
```

## Part B — Attack / observe
With Tenant A's identity (e.g. from a VM/function running as `id-tenantA`),
Tenant A can read **tenantb** — the bug:
```bash
# Conceptually: az storage blob download ... -c tenantb (succeeds as id-tenantA) ❌
python3 ../../cloud/ciem/aws_least_privilege.py   # (AWS-side reference; Azure: use prowler)
bash ../../cloud/prowler_scan.sh                  # choose Azure — flags broad grants
```

## Part C — Harden (isolation at every layer)
```bash
STGID=$(az storage account show -n "$STG" -g rg-lab04 --query id -o tsv)
for T in A B; do
  low=$(echo $T | tr A-Z a-z)
  PID=$(az identity show -n id-tenant$T -g rg-lab04 --query principalId -o tsv)
  # Remove the broad grant
  az role assignment delete --assignee "$PID" --role "Storage Blob Data Owner" --scope "$STGID"
  # Scope to its own container only
  az role assignment create --assignee "$PID" --role "Storage Blob Data Reader" \
    --scope "$STGID/blobServices/default/containers/tenant$low"
done
# Per-tenant Key Vault key (a tenant can use only its own)
az keyvault create -n kv-lab04$RANDOM -g rg-lab04 -l "$LOCATION" --enable-rbac-authorization true
```
**Portal:** add **ABAC conditions** on the role assignment (blob path/tag) for
finer control; Key Vault → grant `Key Vault Crypto User` to only the matching
tenant identity.

## Part D — Verify
```bash
# As id-tenantA: read tenanta works; tenantb denied; cross-tenant key decrypt denied.
bash ../../cloud/prowler_scan.sh    # Azure — re-scan clean on the broad-grant finding
```

## Cleanup
```bash
az group delete -n rg-lab04 --yes --no-wait
```

## Portfolio artifact
- Tenant-isolation decision doc (silo/pool/bridge); before/after cross-tenant test
  output; isolation-boundary diagram.

## Stretch goals
- Rebuild as **silo** (subscription-per-tenant under a management group).
- Per-tenant **diagnostic/log separation** (feeds Lab 06).
- Enforce a data perimeter with **Private Endpoint + storage firewall + policy**.
