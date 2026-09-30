# Lab 04 — Multi-Tenant Isolation (GCP)

**Skills practiced:** tenant isolation models (silo/pool/bridge) · IAM-scoped
tenant boundaries · data isolation (CMEK per tenant, partitioning) ·
folder/project strategy · **VPC Service Controls** perimeters · noisy-neighbor
protection · per-request scoping.
**Proves (JD):** *"securing … deployments … to multi-tenant use."*

## Objective
Model a SaaS multi-tenant system and prove **Tenant A can never reach Tenant B's
data or compute** at identity, data, and network layers — even when malicious.

## Est. time / cost
2–3 h · **~$0–1**.

## Prerequisites
- Labs 00–01 done. gcloud CLI, Python 3.

---

## Isolation models (GCP expression)
| Model | Shared | Isolation | GCP shape |
|-------|--------|-----------|-----------|
| **Silo** | nothing | strongest | **project (or folder) per tenant** |
| **Pool** | everything | weakest, needs care | one project, logical separation |
| **Bridge** | mix | middle | shared compute, isolated data/keys/perimeter |
Build **pool** (hardest), prove isolation, then note when to reach for **silo**
(project-per-tenant under a folder).

## Part A — Build (pool)
1. One bucket, prefixes `tenanta/`, `tenantb/`.
2. One BigQuery dataset (or Firestore) partitioned/labeled by `tenant`.
3. Two service accounts `sa-tenantA` / `sa-tenantB`, **initially broad**
   (`roles/storage.admin` on the whole bucket/project).

## Part B — Attack / observe
1. As `sa-tenantA`, read **Tenant B's** objects — succeeds (the bug):
   ```bash
   gcloud storage cp gs://<bucket>/tenantb/secret.txt - --impersonate-service-account=sa-tenantA@...
   ```
2. Failure = shared infra + broad IAM ⇒ data crossover.

## Part C — Harden (isolation at every layer)
1. **IAM/data scoping:** bind each SA to **its own prefix** with **IAM Conditions**
   (`resource.name.startsWith(".../tenanta/")`), least-privilege role only.
2. **Per-request scoping (pool at scale):** one app SA + **short-lived
   downscoped tokens / Credential Access Boundary** limited to the caller's tenant
   prefix.
3. **Per-tenant CMEK:** a **KMS key per tenant**; a tenant's SA can use only its
   own key — cross-tenant data stays unreadable.
4. **VPC Service Controls:** put tenant data services in a **service perimeter**
   so stolen creds can't exfiltrate across the boundary.
5. **Network isolation** (if tenants get compute): per-tenant subnets/firewall, or
   **silo** (project per tenant) for high-sensitivity customers.
6. **Noisy neighbor:** per-tenant quotas / Cloud Armor / rate limits.

## Part D — Verify
```bash
gcloud storage ls gs://<bucket>/tenanta/ --impersonate-service-account=sa-tenantA@...  # works
gcloud storage cp gs://<bucket>/tenantb/secret.txt - --impersonate-service-account=sa-tenantA@...  # denied ✅
gcloud kms ... decrypt --key=<tenantB-key>   # denied for A ✅
bash ../../cloud/prowler_scan.sh   # (GCP) posture
```
Success = every cross-tenant read/write/decrypt denied by IAM Conditions / CMEK /
VPC-SC, tested from the attacking tenant's SA.

## Cleanup
Delete both SAs, bucket, dataset, per-tenant KMS keys, and the VPC-SC perimeter.

## Portfolio artifact
- Tenant-isolation decision doc (silo/pool/bridge, when each), controls per layer,
  and **where VPC-SC adds an exfiltration boundary** IAM alone can't.
- Before/after cross-tenant test output.
- Isolation-boundary diagram.

## Stretch goals
- Rebuild as **silo** (project-per-tenant under a folder) and compare
  isolation/cost/ops.
- Per-tenant **log sink separation** (feeds Lab 06).
- Bridge two perimeters deliberately and show the controlled path.
