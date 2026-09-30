# Single Sign-On (SSO) — Architecture, Process & Implementation (2026)

**One identity, one login, every cloud.** This section gives you the design,
the diagrams, the step-by-step process, and reference Terraform to stand up
enterprise SSO for **AWS**, **Azure**, **Google Cloud**, and a **multi-cloud**
estate — federated to a single identity provider (IdP), with phishing-resistant
MFA and no per-cloud local accounts.

> ⚠️ **Authorized use only.** These are reference designs and IaC for identity
> systems **you own or are contracted to build**. Federation and SSO changes
> affect who can log in everywhere — apply them through change control in a
> non-production tenant first.

## How SSO fits the rest of the toolkit
SSO is the **authentication** front door. It pairs with:
- `../iam/` — authorization (permission sets, roles, JIT, guardrails) *after* login.
- `../zero-trust/` — SSO is the Identity pillar; ZT adds device, network, session,
  and continuous-verification signals around it.

Read `../iam/architecture/multicloud.md` for the hub-and-spoke identity model;
this section is the **login/federation** half of that picture in depth.

## Layout

| Path | What it is |
|------|-----------|
| `architecture/overview.md` | What SSO is, protocols (SAML/OIDC/SCIM), the reference model |
| `architecture/aws.md` | AWS IAM Identity Center as the SSO front door to all accounts |
| `architecture/azure.md` | Microsoft Entra ID SSO + Conditional Access |
| `architecture/gcp.md` | Google Cloud — Workforce Identity Federation / Cloud Identity SSO |
| `architecture/multicloud.md` | One IdP federating all three clouds + SaaS |
| `architecture/diagram.md` | Login flow, SAML & OIDC sequence diagrams, SCIM provisioning |
| `process/implementation.md` | Step-by-step rollout process (per cloud + multi-cloud), with a checklist |
| `terraform/aws/main.tf` | Reference: Identity Center permission sets + group assignments |
| `terraform/azure/main.tf` | Reference: Entra enterprise app (SAML SSO) + SCIM app role |
| `terraform/gcp/main.tf` | Reference: Workforce Identity Pool + OIDC/SAML provider |
| `validation/sso_posture_check.md` | Checklist to prove SSO is actually enforced |

## Quick mental model

```
Person ──▶ [ Central IdP: authenticate + MFA ]
                     │  SAML assertion / OIDC token (who + which groups)
        ┌────────────┼─────────────┬───────────────┐
        ▼            ▼             ▼               ▼
      AWS          Azure          GCP          SaaS apps
 (Identity Ctr)  (Entra native) (Workforce IF)  (OIDC/SAML)
```

Users authenticate **once** at the IdP; each cloud trusts the IdP's assertion
and maps the user's **groups** to entitlements. SCIM keeps users/groups in sync;
a leaver disabled in the IdP loses access everywhere.

## Requirements
- A central IdP: **Microsoft Entra ID** or **Okta** (examples cover both).
- Admin access to each cloud's identity console (bootstrap only; then IaC).
- Phishing-resistant MFA capability (FIDO2 / passkeys) in the IdP.
