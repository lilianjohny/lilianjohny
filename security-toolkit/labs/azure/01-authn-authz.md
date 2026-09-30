# Lab 01 — Authentication & Authorization (Azure)

**Skills practiced:** Azure RBAC scoping · Entra roles vs Azure roles · managed
identities · Conditional Access · PIM (JIT) · custom roles · app auth with Entra
External ID.
**Proves (JD):** *"authentication / authorization."*

## Objective
Grant the minimum with well-scoped RBAC, elevate only JIT via PIM, give workloads
secret-free managed identities, and add real app auth with proper token handling.

## Est. time / cost
2–3 h · **~$0**.

## Prerequisites
- Lab 00 done (`az login`, `SUB`, `LOCATION`). `jq`, Python 3.

---

## Part A — Build: identities and a workload
```bash
az group create -n rg-lab01 -l "$LOCATION"
STG=lab01$RANDOM
az storage account create -n "$STG" -g rg-lab01 -l "$LOCATION" --sku Standard_LRS \
  --allow-blob-public-access false
# A user-assigned managed identity, given a DELIBERATELY BROAD role first
az identity create -n id-app -g rg-lab01
IDPID=$(az identity show -n id-app -g rg-lab01 --query principalId -o tsv)
az role assignment create --assignee "$IDPID" --role "Owner" --scope "/subscriptions/$SUB"   # too broad
```

## Part B — Attack / observe: over-broad RBAC
```bash
az role assignment list --assignee "$IDPID" -o table    # Owner @ subscription = touches everything
# Two failures: role too strong (Owner) + scope too wide (subscription).
```

## Part C — Harden: least privilege + JIT + conditions
```bash
# 1. Replace with the minimum role at the narrowest scope
STGID=$(az storage account show -n "$STG" -g rg-lab01 --query id -o tsv)
az role assignment delete --assignee "$IDPID" --role "Owner" --scope "/subscriptions/$SUB"
az role assignment create --assignee "$IDPID" --role "Storage Blob Data Reader" --scope "$STGID"

# 2. (If no built-in fits) a custom role with only needed actions
cat > /tmp/role.json <<EOF
{"Name":"lab01-blob-lister","IsCustom":true,"Description":"list blobs only",
 "Actions":["Microsoft.Storage/storageAccounts/blobServices/containers/read"],
 "AssignableScopes":["/subscriptions/$SUB"]}
EOF
az role definition create --role-definition /tmp/role.json
```
**Portal — PIM:** Entra → **PIM → Azure resources** → make Owner/Contributor
*Eligible*; set approval + MFA + activation window.
**Portal — Conditional Access:** enforce MFA + compliant device for privileged
sign-ins; block legacy auth (from Lab 00, now move to **On**).

## Part D — Application auth with Entra External ID
**Portal:** Entra admin center → **External Identities → create an External ID
(CIAM) tenant** → add a **sign-up/sign-in user flow** with **MFA required** and a
passkey/strong-password policy → **App registrations → New registration** →
platform = SPA, enable **Auth code + PKCE** (no secret).
Inspect a token you obtain:
```bash
python3 ../../appsec/crypto/jwt_inspect.py <id_or_access_token>
# Confirm: iss/aud, short exp, alg=RS256 (not "none"), roles/scopes present.
```

---

## Verify
```bash
az role assignment list --assignee "$IDPID" -o table    # scoped to the storage account only
# id-app can read the lab storage and nothing else (test with its identity in a VM/function).
python3 ../../appsec/crypto/jwt_inspect.py <token>
```

## Cleanup
```bash
az role definition delete --name lab01-blob-lister 2>/dev/null
az group delete -n rg-lab01 --yes --no-wait
```

## Portfolio artifact
- **Before/after RBAC** (Owner@subscription → data-role@resource) with rationale.
- A note on **Entra roles vs Azure RBAC** (directory vs resource authorization).
- Screenshot of a **PIM** eligible role + a JIT activation.

## Stretch goals
- ABAC with Azure role-assignment **conditions** on blob tags.
- Write the custom role + assignment as Bicep/Terraform; `checkov`.
- Add an **Access Review** on the eligible Owner role.
