# IAM Architecture & Implementation — AWS · Azure · GCP · Multi-Cloud

A secure-by-design Identity & Access Management architecture and reference
implementation for each major cloud and for a unified multi-cloud environment,
built to **2026 best practice and forward** (Zero Trust, zero standing
privilege, phishing-resistant MFA, no long-lived credentials).

> This is a **reference architecture + IaC baseline**. Validate against your org
> structure and your cloud provider's current features before applying. The
> Terraform is a starting baseline — review, pin provider versions, and plan
> against a non-production org first.

## Layout

```
iam/
├── architecture/
│   ├── principles.md     The 2026 secure-IAM principles every design here follows
│   ├── aws.md            AWS IAM architecture (Identity Center, SCP+RCP, roles, OIDC)
│   ├── azure.md          Entra ID architecture (PIM, Conditional Access, workload identity)
│   ├── gcp.md            GCP architecture (Workforce/Workload Identity Fed, PAM, Org Policy)
│   ├── multicloud.md     One IdP federated to all three clouds; unified model
│   └── diagram.md        Federation architecture diagram (Mermaid)
├── terraform/            Reference IaC baseline per cloud + multicloud federation
│   ├── aws/  azure/  gcp/  multicloud/
├── policies/             Guardrail policies (SCP, RCP, Azure Policy, GCP Org Policy)
└── validation/           Posture checklist + ties to cloud/ciem tooling
```

## The core idea (2026)

**Identify once, authorize everywhere, trust nothing implicitly.**

1. **One source of identity.** Humans live in a single IdP (Entra ID, Okta, or
   AWS Identity Center as hub). Each cloud *federates* to it — no local users,
   no separate passwords.
2. **No long-lived credentials.** Workloads authenticate with **OIDC / workload
   identity federation** (short-lived tokens), never static keys. CI/CD uses
   GitHub/GitLab OIDC → cloud roles.
3. **Zero standing privilege.** Privileged access is **just-in-time** and
   time-boxed (AWS Identity Center + JIT, Entra PIM, GCP PAM). Day-to-day
   identities hold read/limited scopes only.
4. **Phishing-resistant MFA everywhere** (FIDO2 / passkeys), enforced by
   Conditional Access / policy — for every human, always, especially admins.
5. **Guardrails over grants.** Preventive controls at the org edge (SCP + RCP,
   Azure Policy, GCP Org Policy + Principal Access Boundary) cap what *any*
   identity can do, independent of individual permissions.
6. **Least privilege, continuously right-sized.** Start minimal; use CIEM to
   remove unused permissions (`../cloud/ciem/`).
7. **Everything logged & reviewed.** All auth and admin events centralized;
   periodic access reviews / recertification.

Start with **`architecture/principles.md`**, then the per-cloud doc, then the
Terraform baseline.

## How to use
1. Read `architecture/principles.md` (the non-negotiables).
2. Read the per-cloud architecture (`aws.md` / `azure.md` / `gcp.md`) and
   `multicloud.md` for the federation model.
3. Adapt and apply the Terraform in `terraform/<cloud>/` (non-prod first).
4. Enforce the guardrails in `policies/`.
5. Verify with `validation/iam_posture_check.md` + `../cloud/ciem/` and
   `../cloud/multicloud/` for ongoing posture.
