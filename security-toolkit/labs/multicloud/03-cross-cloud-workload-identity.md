# Lab 03 — Cross-Cloud Workload Identity (Multi-Cloud)

**Skills practiced:** workload identity federation *between* clouds · a service in
one cloud calling another with no stored keys · scoped, short-lived cross-cloud
tokens · eliminating the "secret in a config" cross-cloud anti-pattern.
**Proves (JD):** securing multi-cloud deployments + authN/authZ for machines.

## Objective
Have a workload running in **one** cloud authenticate to **another** cloud using
federated, short-lived credentials — **never** a stored key. E.g., a GCP/Azure
workload reads an AWS S3 object by exchanging its native identity token for AWS
credentials via OIDC.

## Est. time / cost
2–3 h · **~$0–1**.

## Prerequisites
- Sandbox in at least two clouds. Per-cloud Lab 01 done.
- Reference: `../../iam/architecture/multicloud.md`,
  `../../iam/terraform/multicloud/README.md`.

---

## Part A — Build the scenario
1. In **Cloud A** (the caller), a workload with a **native identity** (e.g. a GCP
   service running as a GCP SA, or an Azure workload with a managed identity).
2. In **Cloud B** (the target), a resource to reach (e.g. an AWS S3 bucket
   `xcloud-<acct>-data`).

## Part B — Attack / observe: the stored-key anti-pattern
1. The naive approach: put a long-lived **AWS access key** in Cloud A's workload
   config so it can call S3. Show the risk — the key is a standing credential in
   another cloud's environment, easy to leak, never expires.
2. Note: this is exactly the cross-cloud pattern that causes breaches.

## Part C — Harden: federate identity across clouds
1. In **Cloud B (AWS)**, create an **OIDC identity provider** trusting **Cloud A's**
   token issuer (e.g. GCP's / the workload's OIDC issuer), and a **role** whose
   trust policy is scoped to Cloud A's exact workload identity (subject/audience).
2. Grant that role **least privilege** on the target resource only
   (`s3:GetObject` on `xcloud-…-data/*`).
3. In **Cloud A**, the workload obtains its **native identity token** and calls
   `AssumeRoleWithWebIdentity` (or the SDK's web-identity path) to get **short-lived
   AWS credentials** — no stored key.

## Part D — Verify
```bash
# From the Cloud A workload:
#  - it gets short-lived AWS creds via token exchange (no static key present)
aws sts get-caller-identity      # shows the assumed cross-cloud role
aws s3 cp s3://xcloud-<acct>-data/ok.txt -   # works (scoped)
aws s3 ls                                     # denied beyond the bucket
# Prove NO long-lived cross-cloud key exists in the workload config
gitleaks detect --source <workload-config-dir>   # clean
```
Success = the workload reaches the other cloud with **federated, short-lived,
least-privilege** credentials and zero stored keys; trust is pinned to the exact
workload identity.

## Cleanup
Delete the OIDC provider, the cross-cloud role, and the target resource.

## Portfolio artifact
- A **cross-cloud federation diagram** (Cloud A identity → token exchange →
  Cloud B role → resource).
- A writeup contrasting **stored key vs federated token** for cross-cloud access,
  with the scoped trust policy you wrote.

## Stretch goals
- Reverse the direction (AWS workload → GCP resource via Workload Identity
  Federation) so you've done it both ways.
- Add **VPC-SC / RCP** on the target so even the federated identity is confined to
  a network/data perimeter.
- Put the whole trust in Terraform; `checkov` it.
