# Zero Trust across Multi-Cloud (2026)

**One Zero Trust control plane, three enforcement planes.** The policy (who, on
what device, in what context, may reach which resource) is defined **once**,
anchored on a single identity provider; AWS, Azure, and GCP each enforce it with
their native PEPs. Consistency comes from a shared IdP, a shared policy model, and
unified visibility — not from one cloud's tools running everywhere.

## Unified architecture
```
                    ┌──────────────────────────────────────────┐
                    │        CONTROL PLANE (define once)        │
   Signals ────────▶│  Central IdP (SSO + phishing-resistant    │
   • identity        │  MFA)  +  policy model  +  device posture │
   • device (EDR/    │  PDP: identity + policy engine            │
   • Intune/Endpt V) └───────────────────┬──────────────────────┘
   • location/risk                       │  per-request decisions
   • data class                          │
      ┌───────────────────┬──────────────┴───────┬───────────────────┐
      ▼                   ▼                      ▼                   ▼
  AWS enforcement     Azure enforcement      GCP enforcement      SaaS
  Verified Access     Conditional Access     IAP / BeyondCorp     (IdP CA +
  VPC Lattice         Global Secure Access   Context-Aware Access  app policy)
  SCP/RCP, GuardDuty  Azure Policy, Defender VPC-SC, Org Policy, SCC
      │                   │                      │
      ▼                   ▼                      ▼
              Unified visibility & response
        all logs → central SIEM (Sentinel/Chronicle/Splunk)
        correlate one identity across clouds → automated response
```

## What's shared vs per-cloud
| Layer | Shared (define once) | Per-cloud enforcement |
|-------|----------------------|-----------------------|
| **Identity (PDP)** | One IdP, one MFA standard, one group taxonomy, JIT model | Identity Center · Entra CA/PIM · Workforce Fed/PAM |
| **Device posture** | One compliance definition (EDR on, patched, encrypted) | Verified Access trust provider · Intune CA · Endpoint Verification |
| **Access policy** | Common policy intent (least priv, per-request, device-required) | Cedar (Verified Access) · CA policies · Access levels |
| **Segmentation** | Default-deny east-west intent | SG/VPC Lattice · NSG/Priv Link · VPC firewall/VPC-SC |
| **Data** | One classification scheme | Macie/RCP · Purview · DLP/VPC-SC |
| **Visibility** | One SIEM, one detection catalog | CloudTrail/GuardDuty · Sentinel/Defender · SCC/Chronicle |
| **Governance** | One control set mapped to frameworks | SCP · Azure Policy · Org Policy |

## Pillar-by-pillar, across clouds
- **Identity** → `../../sso/architecture/multicloud.md` + `../../iam/` — same
  person, same MFA, same JIT model federated to all three.
- **Devices** → one device-compliance definition; each cloud consumes the posture
  signal (via the IdP or its native agent) as a required access condition.
- **Networks** → default-deny everywhere; private/brokered access (Verified Access
  / Global Secure Access / IAP) replaces VPNs; data perimeters (RCP / storage
  firewall / VPC-SC).
- **Applications & Workloads** → per-request authz at each cloud's PEP; **keyless
  workload identity** for cross-cloud calls (`../../iam/terraform/multicloud/`).
- **Data** → one classification taxonomy; encryption + DLP per cloud; exfil
  perimeters (RCP / Private Link + firewall / VPC-SC).
- **Visibility & Analytics** → all three clouds' logs to **one SIEM**; correlate a
  single identity's activity across clouds (`../../cloud/detection/`, `../../soc/`).
- **Automation & Orchestration** → common playbooks (revoke session, disable
  identity, quarantine) triggered from the unified SIEM.
- **Governance** → controls mapped **once → many** frameworks
  (`../../grc/compliance/crosswalk.py`); risks in one register.

## Why anchor on identity
In multi-cloud, **identity is the only consistent control plane** — networks and
services differ per cloud, but the *same person/workload* spans all of them. Put
the PDP on identity, make device posture and context required signals, and let
each cloud's PEP enforce. This is exactly NIST 800-207A's identity-based
segmentation applied across providers.

## Unified maturity & operating model
- Score every pillar on **CISA ZTMM v2.0** for each cloud, then track the *lowest*
  pillar per cloud as the priority (`../validation/zero_trust_maturity_check.md`).
- One recertification cadence (access reviews from IdP groups + per-cloud CIEM,
  `../../cloud/ciem/`).
- One detection catalog and one response runbook, adapted to each SIEM.
- DoD multi-cloud: meet **Target Level** activities in every enclave by 30 Sep 2027.

## Rollout order (summary — full steps in `../process/implementation.md`)
1. Unify identity: one IdP, SSO, phishing-resistant MFA, JIT (`../../sso/`).
2. Define one device-compliance standard; wire posture into each cloud's PDP.
3. Replace VPNs with per-app brokered access in each cloud (audit mode → enforce).
4. Default-deny segmentation + data perimeters per cloud.
5. Centralize all logs to one SIEM; build the shared detection catalog.
6. Add automated response playbooks; enforce policy-as-code guardrails.
7. Measure maturity across clouds; drive the weakest pillar up; iterate.
