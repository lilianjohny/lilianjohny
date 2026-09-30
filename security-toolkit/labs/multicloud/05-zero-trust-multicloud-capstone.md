# Lab 05 — Zero Trust Multi-Cloud (Capstone)

**Skills practiced:** applying one Zero Trust policy across three clouds ·
per-request enforcement at each cloud's PEP · device + context signals · measuring
maturity across providers · proving "network position grants nothing" everywhere.
**Proves (JD):** the whole job — securing multi-cloud deployments end to end under
a single, modern security model.

## Objective
Take everything from the per-cloud tracks and the multi-cloud labs and unify it
under **one Zero Trust control plane**: one policy, enforced by each cloud's native
PEPs, verified per request, with unified visibility and response. Then **prove**
it with an attack that tries — and fails — to move laterally across clouds.

## Est. time / cost
3–4 h · **~$1–3**.

## Prerequisites
- Multi-cloud Labs 00–04 done.
- Reference: `../../zero-trust/policy/zero-trust-policy.md`,
  `../../zero-trust/architecture/multicloud.md`,
  `../../zero-trust/process/implementation.md`,
  `../../zero-trust/validation/zero_trust_maturity_check.md`.

---

## Part A — Define the policy once
1. Adopt the **Zero Trust policy** (`../../zero-trust/policy/zero-trust-policy.md`)
   for your estate.
2. Translate the **access-policy baseline**
   (`../../zero-trust/policies/conditional-access-baseline.md`) into each engine:
   Entra Conditional Access · AWS Verified Access (Cedar) · GCP Context-Aware Access.

## Part B — Enforce at each cloud's PEP
1. **Identity** (Lab 00): one IdP, phishing-resistant MFA, JIT everywhere.
2. **Device**: require a compliant/managed device signal for sensitive access in
   all three (Verified Access trust provider / Entra CA device / GCP access level).
3. **Network**: default-deny + private access from each per-cloud Lab 05; no
   network-position trust.
4. **Data**: per-tenant keys + exfil perimeters from each per-cloud Lab 04
   (RCP / Private Link+firewall / VPC-SC).
5. **Per-request authorization** at app/API PEPs — reuse
   `../../zero-trust/policies/opa-abac-example.rego` as the decision model.

## Part C — Attack: attempt cross-cloud lateral movement
Using a compromised low-priv federated identity, try to:
1. Escalate privilege in each cloud (blocked by least privilege + JIT).
2. Reach data from a non-compliant device / untrusted network (blocked by the ZT
   gate — device/context signal fails).
3. Move from one cloud's workload to another's data without federation (blocked by
   Lab 03 controls).
4. Exfiltrate across a data perimeter (blocked by RCP/VPC-SC/firewall).
Each attempt should **fail** *and* generate a correlated detection (Lab 04).

## Part D — Verify + measure
1. Confirm each attack path is denied at the right PEP, and the attempt is visible
   in the unified SIEM.
2. Score maturity per pillar per cloud with
   `../../zero-trust/validation/zero_trust_maturity_check.md`; identify the weakest
   pillar and note the next step.
```bash
bash ../../cloud/multicloud/scan_all.sh && python3 ../../cloud/multicloud/report.py
python3 ../../soc/incident/incident_report.py
```
Success = one policy is enforced across all three clouds; every lateral-movement
attempt is denied per-request and detected; you have a maturity score per pillar
per cloud with a prioritized roadmap.

## Cleanup
Tear down all remaining lab resources across the three clouds; disable SIEM
ingestion and detection plans.

## Portfolio artifact (the capstone)
- A **multi-cloud Zero Trust architecture doc**: one policy → three enforcement
  planes, with the diagram from `../../zero-trust/architecture/diagram.md` adapted
  to your build.
- The **attack-and-deny matrix**: each lateral-movement attempt → which PEP denied
  it → the detection that fired.
- A **maturity scorecard** across AWS+Azure+GCP with your roadmap.
- Together with all per-cloud tracks, this is a complete, senior-level cloud
  security portfolio.

## Stretch goals
- Add **continuous verification** (session revocation on risk) in each cloud and
  demonstrate mid-session containment.
- Present a 5-slide "multi-cloud Zero Trust" deck from your artifacts — interview gold.
- Map your whole build to a framework crosswalk (`../../grc/compliance/crosswalk.py`).
