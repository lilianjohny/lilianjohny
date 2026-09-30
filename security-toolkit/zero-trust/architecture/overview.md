# Zero Trust Architecture — Overview (2026)

## The NIST SP 800-207 model
Zero Trust replaces "trusted network inside / untrusted outside" with a
**per-request decision**. Every request flows through logical components:

```
                         ┌──────────────────────────────────────┐
                         │            CONTROL PLANE               │
                         │  ┌────────────────────────────────┐   │
   Signals ─────────────▶│  │  Policy Decision Point (PDP)    │   │
   • identity (IdP/SSO)  │  │   = Policy Engine + Policy Admin│   │
   • device posture      │  │   evaluates policy on EVERY req │   │
   • location / network  │  └───────────────┬────────────────┘   │
   • data sensitivity    │                  │ grant / deny / step-up
   • risk / behavior     └──────────────────┼───────────────────┘
                                            │  (per-session credential)
                         ┌──────────────────▼───────────────────┐
                         │            DATA PLANE                  │
   Subject ───request───▶│  Policy Enforcement Point (PEP) ──────▶│──▶ Resource
   (user / workload)      │  (proxy / gateway / sidecar / broker) │
                         └───────────────────────────────────────┘
```
- **PDP** = **Policy Engine** (decides) + **Policy Administrator** (issues/revokes
  the session credential). In practice: your IdP + policy service.
- **PEP** = where the decision is enforced in the request path (identity-aware
  proxy, API gateway, service mesh sidecar, cloud access broker).
- Decisions use **policy** + live **signals**; access is to **one resource**, and
  the session is **continuously evaluated** (revocable mid-session).

### The tenets (NIST 800-207, condensed)
1. All data sources and services are resources.
2. All communication is secured regardless of network location.
3. Access is granted **per-session**, least privilege.
4. Access is determined by **dynamic policy** (identity, device, behavior, env).
5. The org **monitors and measures integrity/posture** of all assets.
6. Authentication & authorization are **dynamic and strictly enforced** before
   access (continuous).
7. The org **collects data** on posture, traffic, and requests to improve policy.

## The pillars — what you actually build
Zero Trust is delivered across pillars. **CISA ZTMM v2.0** defines 5 + 3
cross-cutting; the **DoD** strategy uses 7. They map cleanly:

| CISA ZTMM v2.0 (5 pillars) | DoD (7 pillars) | This toolkit |
|----------------------------|-----------------|--------------|
| **Identity** | User | `../../sso/`, `../../iam/` |
| **Devices** | Device | endpoint compliance signals (Intune/EDR) |
| **Networks** | Network & Environment | micro-segmentation, private access (`../../cloud/`) |
| **Applications & Workloads** | Application & Workload | `../../appsec/`, workload identity |
| **Data** | Data | classification, encryption, DLP (`../../cloud/`, `../../grc/`) |
| *(cross-cutting)* Visibility & Analytics | Visibility & Analytics | `../../cloud/detection/`, `../../soc/` |
| *(cross-cutting)* Automation & Orchestration | Automation & Orchestration | `../../cloud/cicd/`, `../../devsecops/` |
| *(cross-cutting)* Governance | *(spans all)* | `../../grc/` |

## Maturity stages (CISA ZTMM v2.0)
Each pillar advances through four stages — score yourself in
`../validation/zero_trust_maturity_check.md`:

| Stage | Characteristic |
|-------|----------------|
| **Traditional** | Manual, static, perimeter-based; implicit trust inside |
| **Initial** | Starting automation, some attribute-based policy, MFA rolling out |
| **Advanced** | Centralized visibility, automated policy across pillars, least privilege enforced |
| **Optimal** | Fully automated, dynamic per-request policy, continuous verification, self-healing |

**Target for most orgs (2026):** Advanced, moving to Optimal on Identity first.
**DoD components:** Target Level activities by **30 Sep 2027**.

## Reference architecture (cloud)
```
   Users / workloads
        │
        ▼
   PEP layer:  identity-aware proxy · API gateway · service mesh (mTLS) · cloud access broker
        │              ▲
   per-request         │ decision (grant/deny/step-up) + short-lived session
        ▼              │
   PDP:  IdP (SSO + phishing-resistant MFA)  +  policy engine
        │   signals: device posture, location, risk, data classification, time
        ▼
   Resources: apps, APIs, data, cloud control planes — micro-segmented,
              default-deny, encrypted, logged
        │
        ▼
   Visibility & Analytics (SIEM) ──▶ Automation & Orchestration (respond) ──▶ back to policy
```

## Design rules
1. **Identity is the new perimeter** — start here (SSO + phishing-resistant MFA + JIT).
2. **Every resource behind a PEP** — no direct-to-resource paths that skip the decision.
3. **Least privilege + per-session** — no broad, standing, or network-derived access.
4. **Device posture is a required signal** for sensitive access.
5. **Default-deny micro-segmentation** — earn each east-west path.
6. **Encrypt everything**, in transit and at rest.
7. **Log every decision**; feed analytics; automate response.
8. **Policy as code**, versioned and reviewed (`../policies/`).
9. **Roll out in audit mode**, then enforce; measure maturity continuously.
