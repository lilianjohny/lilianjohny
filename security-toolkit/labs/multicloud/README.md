# Multi-Cloud Security — Hands-On Lab Track

Once you've done the per-cloud tracks (`../aws/`, `../azure/`, `../gcp/`), this
track teaches the harder problem: **securing all three as one system** — one
identity, one posture view, keyless federation everywhere, and unified detection.

> ⚠️ **Sandbox accounts you own, only.** You'll need a sandbox in **each** cloud
> you include (AWS/Azure/GCP) plus a central IdP tenant you control. Tear down
> after each lab.

## Why a separate track
Per-cloud skills don't automatically compose. In multi-cloud, the *same* person
and the *same* pipeline span clouds, so the control plane must be **identity**,
not any one cloud's tools. These labs build that unified plane and prove it.

## Prerequisites
- Per-cloud Lab 01 (authN/authZ) done in each cloud you'll include.
- A central **IdP** (Entra ID or Okta) tenant you control.
- The toolkit's multi-cloud + IAM + SSO + Zero-Trust sections:
  - `../../cloud/multicloud/` (unified CSPM: `scan_all.sh`, `normalize.py`, `report.py`)
  - `../../iam/terraform/multicloud/` (keyless OIDC to all three)
  - `../../sso/` (federation architecture + Terraform)
  - `../../zero-trust/` (the unified control plane)

## Labs
| # | Lab | Focus | Est. time | Cost risk |
|---|-----|-------|-----------|-----------|
| 00 | [Unified identity & SSO](00-unified-identity-sso.md) | one IdP federating AWS+Azure+GCP, phishing-resistant MFA | 3–4 h | ~$0 |
| 01 | [Keyless CI/CD federation](01-keyless-cicd-federation.md) | one pipeline, three OIDC trusts, no stored keys | 2–3 h | ~$0 |
| 02 | [Unified posture (CSPM)](02-unified-posture-cspm.md) | single pane over three clouds, normalized findings | 2–3 h | ~$0–1 |
| 03 | [Cross-cloud workload identity](03-cross-cloud-workload-identity.md) | a workload in one cloud calling another, keyless | 2–3 h | ~$0–1 |
| 04 | [Unified detection & SIEM](04-unified-detection-siem.md) | all clouds' logs → one SIEM, correlate one identity | 3–4 h | ~$1–3 |
| 05 | [Zero Trust multi-cloud capstone](05-zero-trust-multicloud-capstone.md) | one policy, three enforcement planes; prove it | 3–4 h | ~$1–3 |

## The mental model (from `../../zero-trust/architecture/multicloud.md`)
```
                Central IdP  (SSO + phishing-resistant MFA + policy)  ← the control plane
     ┌───────────────┬────────────────────┬───────────────┐
     ▼               ▼                    ▼               ▼
  AWS PEPs        Azure PEPs           GCP PEPs         one SIEM
  (Identity Ctr,  (Entra CA,           (Workforce IF,   (correlate a
   SCP/RCP)        Azure Policy)        Org Policy,       single identity
                                        VPC-SC)           across clouds)
```

## Progress & portfolio
Track completion in [`PROGRESS.md`](PROGRESS.md). The multi-cloud writeups are the
most senior-level artifacts in your portfolio — they show you can reason about
security *across* providers, not just inside one.
