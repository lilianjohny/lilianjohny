# Lab 04 — Multi-Tenant Isolation

**Skills practiced:** tenant isolation models (silo / pool / bridge) · IAM-based
tenant boundaries · data isolation (per-tenant keys, row/prefix scoping) ·
network isolation · the "noisy/malicious neighbor" threat · dynamic
per-request tenant scoping.
**Proves (JD):** *"securing … deployments … to multi-tenant use"* — the cloud
analogue of securing a datacenter shared by many tenants.

## Objective
Model a SaaS-style multi-tenant system and enforce that **Tenant A can never
reach Tenant B's data or compute**, at every layer (identity, data, network),
even when a tenant is actively malicious. This is the datacenter multi-tenancy
problem expressed in AWS.

## Est. time / cost
2–3 h · **~$0–1**.

## Prerequisites
- Labs 00–01 done (IAM fluency).
- AWS CLI v2, Python 3.

---

## Background — the three isolation models
| Model | What's shared | Isolation strength | Cost |
|-------|---------------|--------------------|------|
| **Silo** | nothing (account/VPC per tenant) | strongest | highest |
| **Pool** | everything (shared infra, logical separation) | weakest, needs care | lowest |
| **Bridge** | mix (shared compute, isolated data) | middle | middle |
You'll build a **pool** model (hardest to secure) and prove isolation, then note
when to reach for **silo**.

## Part A — Build: a shared (pool) setup with two tenants
1. One S3 bucket, tenant data under prefixes: `tenantA/…`, `tenantB/…`.
2. One DynamoDB table with a `tenant_id` partition key.
3. Two roles, `tenant-A-role` / `tenant-B-role`, both **initially over-broad**
   (full bucket + full table).

## Part B — Attack / observe: cross-tenant access
1. Assume `tenant-A-role` and read **Tenant B's** objects and items:
   ```bash
   aws s3 cp s3://<bucket>/tenantB/secret.txt -    # should be impossible, isn't yet
   aws dynamodb get-item --table-name <t> --key '{"tenant_id":{"S":"tenantB"}}'
   ```
2. That's the multi-tenant failure: shared infra + broad IAM = data crossover.
3. Run `python3 ../../cloud/aws/s3_public_check.py` and
   `python3 ../../cloud/ciem/aws_least_privilege.py` to catch the broad grants.

## Part C — Harden: isolation at every layer
1. **Identity/data scoping with IAM conditions** — scope each tenant role to its
   own prefix and partition key:
   - S3: `Condition` on `s3:prefix` and resource `.../tenantA/*`.
   - DynamoDB: `dynamodb:LeadingKeys` condition = `${aws:PrincipalTag/tenant}`.
2. **Dynamic per-request scoping (pool at scale):** instead of a role per tenant,
   use **session tags / `sts:AssumeRole` with a scoped session policy** so one
   app role is downscoped to the caller's tenant at request time (ABAC).
3. **Per-tenant encryption:** a **KMS key per tenant**; a tenant's role can use
   only its own key — even a data leak is unreadable across tenants.
4. **Network isolation** (if tenants get compute): separate subnets/SGs, or the
   silo option (VPC/account per tenant) for high-sensitivity tenants.
5. **Quotas / throttling:** protect against the **noisy neighbor** (per-tenant
   rate limits, WAF, DynamoDB capacity isolation).

## Part D — Verify
```bash
# Tenant A can reach ONLY tenant A
aws s3 ls s3://<bucket>/tenantA/     # works
aws s3 ls s3://<bucket>/tenantB/     # AccessDenied  ✅
aws dynamodb get-item ... tenantB    # AccessDenied  ✅

# Cross-tenant KMS decrypt fails
aws kms decrypt --key-id <tenantB-key> ...   # AccessDenied for tenant A  ✅

# Toolkit checks
python3 ../../cloud/ciem/aws_least_privilege.py
python3 ../../cloud/aws/s3_public_check.py
```
Success = every cross-tenant read/write/decrypt is denied by IAM/KMS conditions,
verified from the attacking tenant's own credentials.

## Cleanup
Delete the roles, bucket, table, and per-tenant KMS keys (schedule key deletion).

## Portfolio artifact
- A **tenant-isolation decision doc**: silo vs pool vs bridge, when to use each,
  and the controls you used at identity/data/network/key layers.
- The **before/after** cross-tenant access test output (crossover → denied).
- An architecture diagram showing the isolation boundaries.

## Stretch goals
- Rebuild as **silo** (account-per-tenant via Organizations) and compare the
  isolation/cost/ops tradeoff — this is the datacenter "dedicated cage vs shared
  floor" decision.
- Add **per-tenant CloudTrail/log separation** so one tenant's audit data never
  mixes with another's (feeds Lab 06).
- Enforce the data perimeter with an **RCP**
  (`../../iam/policies/aws-rcp-data-perimeter.json`).
