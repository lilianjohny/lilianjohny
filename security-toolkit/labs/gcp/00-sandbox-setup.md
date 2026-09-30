# Lab 00 — GCP Sandbox Setup & Guardrails

**Skills practiced:** project/org hardening · Budgets · Organization Policy ·
Cloud Identity baseline · Cloud Audit Logs.
**Proves (JD):** securing a deployment "from construction" — the safe foundation.

## Objective
A safe, isolated GCP sandbox: a least-privilege day-to-day identity, org-policy
guardrails, budget alerts, and audit logging — before you build anything.

## Est. time / cost
45–60 min · **~$0**.

## Prerequisites
- A GCP **project you own** (ideally under an **organization** so Org Policy
  works; a standalone project still works with fewer guardrails).
- gcloud CLI (`gcloud version`). FIDO2 key / authenticator for MFA.

---

## Part A — Harden identity
1. Ensure **super-admin** (Cloud Identity) accounts have **phishing-resistant
   MFA**; create **2 break-glass** super-admins, FIDO2, sealed, alerted on use
   (see `../../iam/architecture/gcp.md`). Don't operate as super-admin day-to-day.
2. Your day-to-day user gets **least-privilege** IAM (e.g. Viewer at project).
3. gcloud without SA keys:
   ```bash
   gcloud auth login
   gcloud config set project <your-project>
   gcloud auth list          # confirm your user, not a service-account key
   ```

## Part B — Org Policy guardrails (org/folder scope)
Enforce baseline constraints (adapt `../../iam/policies/gcp-org-policy-baseline.md`
and `../../iam/terraform/gcp/main.tf`):
- `iam.disableServiceAccountKeyCreation` = enforced (no exported SA keys).
- `storage.publicAccessPrevention` = enforced.
- `gcp.resourceLocations` = your allowed regions.
- `compute.requireOsLogin`, `compute.vmExternalIpAccess` (restrict public IPs).
```bash
gcloud org-policies set-policy policy.yaml    # or via console at org/folder
```

## Part C — Cost guardrails
1. **Billing → Budgets & alerts:** a **$5/month** budget with 50/80/100% alerts.
2. Cost drivers to watch: **GKE control plane + nodes, LB, Cloud NAT, SCC
   Premium** — labs flag them; tear down same-session.

## Part D — Logging
1. **Cloud Audit Logs:** Admin Activity is always on; enable **Data Access** logs
   for the services you'll test.
2. Create a **log sink** → a dedicated logging bucket / BigQuery (your evidence
   trail; feeds Lab 06).
3. (Optional) Enable **Security Command Center** (Standard is free) for posture.

---

## Verify
```bash
gcloud auth list                                  # scoped user, not SA key
gcloud org-policies list --project=<p>            # guardrails present
bash ../../cloud/prowler_scan.sh                  # (GCP) baseline posture
```
Success = super-admin MFA + break-glass, least-priv daily identity, org policies
enforced, budget alerts, audit logs sinking, SCC on.

## Cleanup
Keep this foundation for later labs.

## Portfolio artifact
- "Secure GCP project baseline" writeup + screenshots of org policies, budget,
  and the log sink.

## Stretch goals
- Enable **Chronicle** / a SIEM sink now (Lab 06).
- Create a second project under a folder — preview Lab 04.
- Codify org policies + sink as Terraform; `checkov` it.
