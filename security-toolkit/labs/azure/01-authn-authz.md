# Lab 01 — Authentication & Authorization (Azure)

**Skills practiced:** Azure RBAC scoping · Entra roles vs Azure roles · managed
identities (no secrets) · Conditional Access · PIM (JIT) · custom roles ·
application auth with **Entra External ID** (CIAM).
**Proves (JD):** *"authentication / authorization."*

## Objective
Grant the minimum with well-scoped RBAC, elevate only just-in-time via PIM,
give workloads secret-free managed identities, and add real application auth
with proper token handling.

## Est. time / cost
2–3 h · **~$0**.

## Prerequisites
- Lab 00 done. Azure CLI. `jq`, Python 3.

---

## Part A — Build: identities and a workload
1. Create a resource group `rg-lab01` and a storage account (public access
   disabled).
2. Create a **user-assigned managed identity** `id-app`.
3. Grant `id-app` a **deliberately broad** role first: **Owner at subscription**.

## Part B — Attack / observe: over-broad RBAC
1. Show `id-app` (Owner at subscription) can touch **every** resource group, not
   just `rg-lab01` — create/delete elsewhere:
   ```bash
   az role assignment list --assignee <id-app-principal-id> -o table
   ```
2. Note the two failures: **role too strong** (Owner) and **scope too wide**
   (subscription). That's lateral movement + escalation waiting to happen.

## Part C — Harden: least privilege + JIT + conditions
1. Replace with the **minimum built-in role at the narrowest scope**:
   e.g. `Storage Blob Data Reader` on **that storage account only**.
2. If no built-in fits, author a **custom role** with just the needed
   `actions`/`dataActions` — no wildcards.
3. **PIM:** make Owner/Contributor **eligible**, not standing; require approval +
   MFA + justification to activate; set a short activation window.
4. **Conditional Access:** enforce MFA + (where available) compliant device for
   privileged sign-ins; block legacy auth.
5. Workloads use **managed identity** (already) — confirm **no secrets/keys** in
   config anywhere.

## Part D — Application auth with Entra External ID
1. Create an **Entra External ID (CIAM)** tenant / user flow: sign-up/sign-in
   with **MFA required**, strong password/passkey policy.
2. Register an app; use **auth code + PKCE** (no secret for SPA).
3. Acquire a token and inspect it:
   ```bash
   python3 ../../appsec/crypto/jwt_inspect.py <id_or_access_token>
   ```
   Confirm `iss`/`aud`, short `exp`, `alg` = RS256 (not `none`), roles/scopes.
4. Map an app **role/group** claim → an Azure RBAC role for that user's access —
   the app-layer version of Part C.

---

## Verify
```bash
# Least privilege holds
az role assignment list --assignee <id-app-principal-id> -o table   # scoped only
# id-app can read the lab storage and NOTHING else
az storage blob list --account-name <acct> --auth-mode login ...    # works
az group delete -n <other-rg>                                       # denied
# Token hygiene
python3 ../../appsec/crypto/jwt_inspect.py <token>
```
Success = managed identity scoped to exactly its job, PIM gates elevation, CA
enforces MFA, External ID issues short-lived correctly-scoped tokens.

## Cleanup
Delete `rg-lab01`, the managed identity, role assignments, and the External ID
app/user flow.

## Portfolio artifact
- **Before/after RBAC** (Owner@subscription → data-role@resource) with rationale.
- A note on **Entra roles vs Azure RBAC** (directory vs resource authorization).
- Screenshot of PIM eligibility + a JIT activation.

## Stretch goals
- Implement **ABAC** with Azure role assignment **conditions** on blob tags.
- Write the custom role + assignment as Bicep/Terraform; `checkov` it.
- Add an **Access Review** on the eligible Owner role.
