# Lab 04 — Multi-Tenant Isolation (Azure)

**Skills practiced:** tenant isolation models (silo/pool/bridge) · RBAC-scoped
tenant boundaries · data isolation (per-tenant keys, partitioning) · management-
group/subscription strategy · noisy-neighbor protection · per-request scoping.
**Proves (JD):** *"securing … deployments … to multi-tenant use."*

## Objective
Model a SaaS multi-tenant system and prove **Tenant A can never reach Tenant B's
data or compute** at identity, data, and network layers — even when a tenant is
malicious.

## Est. time / cost
2–3 h · **~$0–1**.

## Prerequisites
- Labs 00–01 done. Azure CLI, Python 3.

---

## Isolation models (Azure expression)
| Model | Shared | Isolation | Azure shape |
|-------|--------|-----------|-------------|
| **Silo** | nothing | strongest | subscription (or tenant) per customer |
| **Pool** | everything | weakest, needs care | one sub, logical separation (RBAC/partition) |
| **Bridge** | mix | middle | shared compute, isolated data/keys |
Build **pool** (hardest), prove isolation, then note when to reach for **silo**
(management-group / subscription-per-tenant).

## Part A — Build (pool)
1. One Storage account, containers `tenanta`, `tenantb`.
2. One Cosmos DB (or a table) partitioned by `tenantId`.
3. Two managed identities `id-tenantA` / `id-tenantB`, **initially broad**
   (Storage Blob Data Owner on the whole account).

## Part B — Attack / observe
1. As `id-tenantA`, read **Tenant B's** blobs / partition — succeeds (the bug):
   ```bash
   az storage blob download --account-name <acct> -c tenantb -n secret.txt --auth-mode login
   ```
2. Failure = shared infra + broad RBAC ⇒ data crossover.

## Part C — Harden (isolation at every layer)
1. **RBAC/data scoping:** scope each identity to **its own container** (role
   assignment at container scope), and use **ABAC conditions** on blob path/tag
   so it can't read other prefixes.
2. **Per-request scoping (pool at scale):** one app identity + **On-Behalf-Of /
   scoped tokens** downscoped to the caller's tenant, rather than an identity per
   tenant.
3. **Per-tenant keys:** a **Key Vault key per tenant** (CMK); a tenant's identity
   can use only its own key — cross-tenant data stays unreadable.
4. **Network isolation** (if tenants get compute): per-tenant subnets/NSGs, or
   **silo** (subscription per tenant) for high-sensitivity customers.
5. **Noisy neighbor:** per-tenant throttling / WAF / Cosmos throughput isolation.

## Part D — Verify
```bash
az storage blob list -c tenanta --account-name <acct> --auth-mode login   # works
az storage blob download -c tenantb ... --auth-mode login                 # denied ✅
az keyvault key decrypt --name <tenantB-key> ...                          # denied for A ✅
bash ../../cloud/prowler_scan.sh    # (Azure) posture
```
Success = every cross-tenant read/write/decrypt denied by RBAC/ABAC/Key Vault,
tested from the attacking tenant's identity.

## Cleanup
Delete both identities, storage, Cosmos/table, and per-tenant Key Vault keys.

## Portfolio artifact
- Tenant-isolation decision doc (silo/pool/bridge, when each), controls per layer.
- Before/after cross-tenant test output (crossover → denied).
- Isolation-boundary diagram.

## Stretch goals
- Rebuild as **silo** (subscription-per-tenant under a management group) and
  compare isolation/cost/ops — the "dedicated cage vs shared floor" call.
- Per-tenant **diagnostic/log separation** (feeds Lab 06).
- Enforce a **data perimeter** with Private Endpoint + storage firewall + policy.
