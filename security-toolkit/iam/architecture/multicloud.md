# Multi-Cloud IAM Architecture (2026)

The goal: **one identity, governed once, trusted everywhere** — humans and
workloads authenticate through a single source of truth, and each cloud
federates to it. No cloud holds its own copy of your people or long-lived keys.

## Design: hub-and-spoke identity federation

```
                       ┌───────────────────────────┐
                       │   Central IdP (hub)        │
                       │   Entra ID / Okta          │
                       │   • users & groups (HR-fed)│
                       │   • phishing-resistant MFA │
                       │   • Conditional Access     │
                       │   • lifecycle (SCIM/joiners│
                       │     -movers-leavers)       │
                       └────────────┬──────────────┘
        SAML/OIDC + SCIM            │            (groups → entitlements)
      ┌────────────────────┬────────┴────────┬────────────────────┐
      ▼                    ▼                 ▼                     ▼
┌───────────┐      ┌──────────────┐   ┌──────────────┐    ┌──────────────┐
│   AWS     │      │    Azure     │   │     GCP      │    │  SaaS / K8s  │
│ Identity  │      │  (native to  │   │  Workforce   │    │ (OIDC apps)  │
│ Center    │      │   Entra)     │   │  Identity    │    │              │
│ +SCP/RCP  │      │ +Azure Policy│   │  Federation  │    │              │
│ +OIDC(CI) │      │ +PIM         │   │ +Org Policy  │    │              │
└───────────┘      └──────────────┘   │ +PAM         │    └──────────────┘
   JIT roles          Entra PIM       └──────────────┘
                                         PAM/PAB
```

## Human identity (single sign-on to every cloud)
- **One IdP** owns users, groups, MFA, and lifecycle (joiners/movers/leavers via
  SCIM + HR feed). Deprovision once → access removed everywhere.
- Each cloud **federates**:
  - AWS: IdP → **IAM Identity Center** (SAML + SCIM) → permission sets.
  - Azure: native to **Entra** (or Entra federated from Okta).
  - GCP: IdP → **Workforce Identity Federation** → role bindings.
- **Group-driven entitlements:** a person's IdP group memberships map to
  per-cloud roles. Access is granted/revoked by changing group membership, in
  one place, reviewed together.
- **Zero standing privilege** is enforced per-cloud (Identity Center JIT, Entra
  PIM, GCP PAM) but requested through a consistent workflow.

## Workload identity (no keys crossing clouds)
- Each workload gets a **cloud-native short-lived identity**; when a workload in
  one cloud must call another, use **workload identity federation** (OIDC token
  exchange), **never** stored keys.
- **CI/CD once, everywhere:** the pipeline's OIDC identity (GitHub/GitLab)
  federates to AWS roles, Azure app federated credentials, and GCP workload
  identity pools — the same pipeline, three keyless trusts.

## Unified governance
| Concern | How it's unified |
|---------|------------------|
| **Guardrails** | Equivalent preventive controls per cloud (SCP+RCP / Azure Policy / Org Policy+PAB), managed as code from one repo (`../terraform/`). |
| **Entitlement review** | Access reviews driven from the IdP groups + per-cloud CIEM (`../../cloud/ciem/`); one recertification cadence. |
| **Least privilege** | CIEM across clouds → remove unused; one risk view (`../../cloud/multicloud/`). |
| **Detection** | All auth/admin logs → one SIEM; correlate identity across clouds (`../../cloud/detection/`, `../../soc/`). |
| **Compliance** | Controls map once → many frameworks (`../../grc/compliance/crosswalk.py`). |

## Trust boundaries & separation
- The **IdP is Tier-0** — its own admins, hardware MFA, PIM/JIT, isolated from
  cloud workload admin. Compromise of the IdP = compromise of everything, so it
  gets the strongest controls and monitoring.
- Per-cloud **break-glass** stays cloud-native (not dependent on the IdP), so an
  IdP outage never locks you out.
- Federation trust is **narrowly scoped** (specific pools/providers, audiences,
  subject conditions) and defined in code so it's reviewable and revocable.

## Rollout order
1. Stand up the IdP as the single source (MFA, CA, groups, lifecycle).
2. Federate each cloud (Identity Center / Entra / Workforce Identity Fed).
3. Replace all static keys with workload identity federation.
4. Move privileged access to JIT (Identity Center / PIM / PAM).
5. Apply guardrails as code (SCP+RCP / Azure Policy / Org Policy+PAB).
6. Turn on CIEM + access reviews + centralized detection; iterate to ZSP.
