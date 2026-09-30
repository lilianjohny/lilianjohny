# Lab 03 — Secret Management & Machine Identity

**Skills practiced:** centralized secret vaulting · dynamic/short-lived secrets ·
rotation · machine identity (no static creds) · secret-sprawl detection ·
encryption of secrets in transit/at rest.
**Proves (JD — OpenAI InfraSec):** *"secret management"* and *"machine identity"*
for large-scale infrastructure.

## Objective
Replace static, sprawled secrets with a vault-backed model: services authenticate
with a **machine identity**, fetch **short-lived** secrets, and everything
rotates. Detect existing secret sprawl first, then fix it.

## Est. time / cost
2–3 h · **~$0** (HashiCorp Vault dev/OSS or a cloud secrets manager free tier).

## Prerequisites
- Docker or a Linux host. Optional: Vault OSS, or AWS/Azure/GCP secrets manager.
- Toolkit: `../../devsecops/` secret scanning, `../../cloud/ciem/` (identity).

---

## Part A — Attack / observe: find the sprawl
1. Scan a repo / config tree for hardcoded secrets:
   ```bash
   bash ../../devsecops/secret_scan.sh .    # or gitleaks
   ```
2. Note the anti-patterns: secrets in env files, container images (see
   `../aws/02-container-image-security.md`), CI variables, and long-lived API
   keys that never rotate.

## Part B — Build: a vault + machine identity
1. Stand up **Vault** (dev mode for the lab) or use a cloud secrets manager.
2. Enable an **auth method for workloads** (Kubernetes SA, AppRole, or cloud IAM)
   so a service proves a **machine identity** — not a shared password — to get
   secrets.
3. Store a secret; have a service fetch it at runtime via its identity.

## Part C — Harden: dynamic, short-lived, rotated
1. Use **dynamic secrets** (e.g. Vault database secrets engine) so each service
   gets **unique, short-TTL** credentials generated on demand — revoked on expiry.
2. Enable **rotation** for static secrets that must exist; set TTLs everywhere.
3. **Encrypt in transit** (TLS to the vault) and **at rest** (vault's own
   encryption / KMS auto-unseal).
4. **Least-privilege policies:** each identity can read only its own secrets
   (the secret-management analogue of `../aws/04-multi-tenant-isolation.md`).
5. Remove the sprawled secrets found in Part A; inject from the vault instead.

## Part D — Verify
```bash
# No secrets left in the tree:
bash ../../devsecops/secret_scan.sh .          # clean
# A service gets a short-lived credential via its machine identity, and a
# different identity CANNOT read it (test cross-identity access → denied).
```
Confirm: no static long-lived creds in code/images/CI; secrets are short-TTL and
rotate; each machine identity is scoped to its own secrets.

## Portfolio artifact
- **Before/after**: secret-scan sprawl → vault-backed, zero hardcoded secrets.
- A **machine-identity diagram**: service → auth method → scoped policy →
  short-lived secret.
- A note on **dynamic vs static** secrets and why short TTL shrinks blast radius.

## Stretch goals
- Wire the vault into **Kubernetes** (CSI driver / agent injector) from
  `../aws/03-eks-orchestration-security.md`.
- Add **secret-access auditing** → your SIEM (`../../soc/`) and alert on anomalies.
- Implement **break-glass** secret access with heavy alerting.
