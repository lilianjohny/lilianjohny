# Multi-Cloud SSO Architecture (2026)

**Goal:** one login, governed once, works in every cloud and SaaS app. A person
authenticates at a single IdP with phishing-resistant MFA; AWS, Azure, and GCP
each *federate* to that IdP and map the user's **groups** to entitlements. Deprovision
once → access gone everywhere.

## The unified picture
```
                         ┌────────────────────────────────┐
                         │       Central IdP (hub)         │
                         │   Entra ID / Okta               │
   HR feed ─────────────▶│   • users & groups (JML)        │
                         │   • phishing-resistant MFA      │
                         │   • policy (CA) + session limits│
                         │   • SCIM provisioning engine    │
                         └───────────────┬────────────────┘
   SAML/OIDC (auth) + SCIM (provisioning) │  group claims drive entitlements
      ┌──────────────┬───────────────────┼───────────────────┬──────────────┐
      ▼              ▼                   ▼                   ▼              ▼
 AWS Identity     Entra ID           GCP Workforce        SaaS apps      K8s / APIs
   Center         (native)          Identity Fed         (OIDC/SAML)    (OIDC)
 SAML+SCIM      groups→RBAC+PIM     OIDC/SAML+groups     groups→roles   OIDC RBAC
 groups→perm     +Conditional       principalSet
 sets/accounts   Access             IAM bindings
```

## One identity, three federations — how they line up
| Concern | AWS | Azure | GCP |
|---------|-----|-------|-----|
| Federation | Identity Center (SAML+SCIM) | Native Entra / federated | Workforce Identity Federation (OIDC/SAML) |
| Entitlement by group | permission set × account | group → RBAC role | `principalSet://…/group` binding |
| JIT elevation | Identity Center JIT | Entra PIM | GCP PAM |
| ZT gate | (via IdP CA + `../../zero-trust`) | Conditional Access | Context-Aware Access / BeyondCorp |
| Guardrail | SCP + RCP | Azure Policy | Org Policy + PAB |

The **left column is the same person and the same group** — only the mapping
mechanism differs. That's the whole point: change a group in the IdP once, and
the right access appears/disappears in all three clouds.

## Group naming that scales
Adopt a single, cloud-agnostic group taxonomy in the IdP and map it per cloud:
```
role-<function>-<scope>-<privilege>
  e.g.  role-payments-prod-readonly
        role-payments-prod-dba
        role-platform-all-securityaudit
        role-breakglass-<cloud>            (handled out of band)
```
Map each group to the equivalent permission set / RBAC role / IAM binding in each
cloud. Access reviews then review **one** list of groups, not three consoles.

## Provisioning & lifecycle (the part people skip)
- **SCIM from the IdP** into every target that supports it (AWS Identity Center,
  most SaaS). GCP via Workforce Federation needs no user objects; Cloud Identity
  path uses GCDS/SCIM.
- **Joiners:** HR → IdP group membership → access appears in the right clouds.
- **Movers:** group change → entitlements shift automatically.
- **Leavers:** disable in IdP → SCIM deprovisions / federation stops → access
  gone everywhere. **Test a leaver** end-to-end quarterly.

## Workload SSO (machine identities, no keys)
Human SSO's counterpart for pipelines and services:
- CI/CD authenticates via **OIDC** to all three clouds (keyless) — the same
  GitHub Actions run assumes an AWS role, an Entra app credential, and a GCP
  workload identity. See `../../iam/terraform/multicloud/README.md`.
- Cross-cloud service calls use **workload identity federation**, never stored keys.

## Governance & detection (unified)
- **Access reviews / recertification** driven from IdP groups + per-cloud CIEM
  (`../../cloud/ciem/`) on one cadence.
- **All auth/admin logs** → one SIEM; correlate a single identity across clouds
  (`../../cloud/detection/`, `../../soc/`).
- **Compliance** mapped once → many frameworks (`../../grc/compliance/crosswalk.py`).

## Resilience
- The **IdP is Tier-0** — strongest controls, its own admins, hardware MFA,
  PIM/JIT, heavy monitoring. IdP compromise = everything, so protect it hardest.
- **Per-cloud break-glass** stays cloud-native so an IdP outage never locks you
  out of any single cloud.
- Federation trusts are **narrowly scoped** (specific pools/apps/audiences/subject
  conditions) and defined as code — reviewable, revocable.

## Rollout order (summary — full steps in `../process/implementation.md`)
1. Stand up the IdP as the single source (MFA, CA/policy, groups, HR feed, SCIM).
2. Federate AWS (Identity Center), Azure (native/federated), GCP (Workforce IF).
3. Define the group taxonomy; map groups → entitlements per cloud (as code).
4. Turn on SCIM provisioning + deprovisioning; test a leaver.
5. Move privileged access to JIT (Identity Center / PIM / PAM).
6. Add the Zero Trust gate (`../../zero-trust/`): device + network + session signals.
7. Centralize logs + access reviews; iterate.
