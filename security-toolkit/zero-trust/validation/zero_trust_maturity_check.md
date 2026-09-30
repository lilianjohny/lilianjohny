# Zero Trust Maturity Self-Assessment (CISA ZTMM v2.0)

Score each pillar as **Traditional / Initial / Advanced / Optimal**. Take the
**lowest** pillar as your next priority. Re-score quarterly. Items marked → link
to toolkit scripts for evidence.

**Stages:** Traditional (manual, perimeter, implicit trust) · Initial (some
automation, MFA rolling out, attribute policy starting) · Advanced (centralized
visibility, automated cross-pillar policy, least privilege enforced) · Optimal
(fully automated, dynamic per-request, continuous verification, self-healing).

---

## Pillar 1 — Identity  (DoD: User)
- [ ] SSO to one IdP for all clouds. → `../../sso/`
- [ ] Phishing-resistant MFA (FIDO2/passkeys) enforced; legacy auth blocked.
- [ ] Access by group/attribute; no human local accounts.
- [ ] Zero standing privilege — JIT (Identity Center / PIM / PAM). → `../../iam/`
- [ ] Real-time identity risk feeds access decisions.
- [ ] Continuous session evaluation (revoke on risk).
Stage: ⬜ Traditional ⬜ Initial ⬜ Advanced ⬜ Optimal

## Pillar 2 — Devices
- [ ] All endpoints enrolled/managed (Intune/MDM); inventory complete.
- [ ] Compliance defined (encrypted, patched, EDR) and checked continuously.
- [ ] Device posture is a **required** signal for sensitive access.
- [ ] Non-compliant devices are denied or restricted automatically.
Stage: ⬜ Traditional ⬜ Initial ⬜ Advanced ⬜ Optimal

## Pillar 3 — Networks (DoD: Network & Environment)
- [ ] Default-deny east-west; micro-segmentation by workload/identity. → `../../cloud/`
- [ ] VPN replaced by per-app brokered access (Verified Access / GSA / IAP).
- [ ] Control/data planes private (PrivateLink / Private Endpoint / PSC); no public mgmt.
- [ ] Data-exfil perimeters (RCP / storage firewall / VPC-SC).
- [ ] All traffic encrypted (TLS/mTLS).
Stage: ⬜ Traditional ⬜ Initial ⬜ Advanced ⬜ Optimal

## Pillar 4 — Applications & Workloads
- [ ] Per-request authorization at app/API PEPs; policy-as-code. → `../policies/`, `../../appsec/`
- [ ] Workloads use short-lived federated identity; no static keys. → `../../iam/`
- [ ] Supply chain verified (SBOM, signed artifacts). → `../../devsecops/`, `../../dod/`
- [ ] App access requires identity + device + context.
Stage: ⬜ Traditional ⬜ Initial ⬜ Advanced ⬜ Optimal

## Pillar 5 — Data
- [ ] Data classified; crown jewels identified. → `../../grc/`
- [ ] Encrypted at rest + in transit; keys managed & access-logged.
- [ ] DLP monitors sensitive-data movement (Macie / Purview / DLP).
- [ ] Access authorized per-request by classification + context.
Stage: ⬜ Traditional ⬜ Initial ⬜ Advanced ⬜ Optimal

---

## Cross-cutting

### Visibility & Analytics
- [ ] All auth/authz/admin/network logs centralized, immutable → SIEM. → `../../cloud/detection/`, `../../soc/`
- [ ] Detection catalog covers identity/network/data anomalies.
- [ ] Posture continuously measured.
Stage: ⬜ Traditional ⬜ Initial ⬜ Advanced ⬜ Optimal

### Automation & Orchestration
- [ ] Automated response (revoke/disable/quarantine/step-up). → `../../cloud/cicd/`
- [ ] Policy-as-code deployed via CI with guardrails. → `../../devsecops/`
Stage: ⬜ Traditional ⬜ Initial ⬜ Advanced ⬜ Optimal

### Governance
- [ ] Zero Trust policy adopted & enforced. → `../policy/zero-trust-policy.md`
- [ ] Controls mapped to frameworks. → `../../grc/compliance/crosswalk.py`
- [ ] Access reviews on cadence; exceptions time-boxed & tracked. → `../../grc/risk/`
Stage: ⬜ Traditional ⬜ Initial ⬜ Advanced ⬜ Optimal

---

## Scoring
| Pillar | Current stage | Target | Priority |
|--------|:-------------:|:------:|:--------:|
| Identity |  | Optimal | |
| Devices |  | Advanced | |
| Networks |  | Advanced | |
| Apps & Workloads |  | Advanced | |
| Data |  | Advanced | |
| Visibility & Analytics |  | Advanced | |
| Automation & Orchestration |  | Advanced | |
| Governance |  | Advanced | |

**Target (most orgs, 2026):** Advanced across all, Optimal on Identity first.
**DoD components:** meet **Target Level** activities by **30 Sep 2027**; Advanced
activities by 2032.
