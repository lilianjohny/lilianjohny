# Lab 05 — Zero Trust Multi-Cloud (Capstone)

**Skills practiced:** one Zero Trust policy across three clouds · per-request
enforcement at each PEP · device + context signals · maturity measurement ·
proving "network position grants nothing."
**Proves (JD):** the whole job — securing multi-cloud deployments end to end.

## Objective
Unify everything under **one Zero Trust control plane** and prove it with an
attack that tries — and fails — to move laterally across clouds.

## Est. time / cost
3–4 h · **~$1–3**.

## Prerequisites
- Multi-cloud Labs 00–04 done. Reference: `../../zero-trust/`.

---

## Part A — Define the policy once
1. Adopt `../../zero-trust/policy/zero-trust-policy.md`.
2. Translate `../../zero-trust/policies/conditional-access-baseline.md` into each
   engine: Entra Conditional Access · AWS Verified Access (Cedar) · GCP
   Context-Aware Access.
3. Test the ABAC decision model locally:
   ```bash
   echo '{"subject":{"authenticated":true,"mfa":"fido2","groups":["role-payments-prod-readonly"],"risk":"low"},
          "device":{"managed":true,"compliant":true},
          "resource":{"id":"svc:payments-api","sensitivity":"high","allowed_groups":["role-payments-prod-readonly"]},
          "context":{"ip_trusted":true,"impossible_travel":false}}' > /tmp/req.json
   # If opa is installed:
   opa eval -d ../../zero-trust/policies/opa-abac-example.rego -i /tmp/req.json 'data.zerotrust.authz.decision'
   ```

## Part B — Enforce at each cloud's PEP
1. **Identity** (Lab 00): one IdP, phishing-resistant MFA, JIT everywhere.
2. **Device:** require a compliant/managed-device signal for sensitive access in
   all three (Verified Access trust provider / Entra CA device / GCP access level).
3. **Network:** default-deny + private access from each per-cloud Lab 05.
4. **Data:** per-tenant keys + exfil perimeters from each per-cloud Lab 04
   (RCP / Private Link+firewall / VPC-SC).
5. **Per-request authorization** at app/API PEPs using the Rego model above.

## Part C — Attack: attempt cross-cloud lateral movement
Using a compromised low-priv federated identity, try to:
1. Escalate privilege in each cloud (blocked by least privilege + JIT).
2. Reach data from a non-compliant device / untrusted network (blocked by the ZT gate).
3. Move from one cloud's workload to another's data without federation (blocked by Lab 03).
4. Exfiltrate across a data perimeter (blocked by RCP/VPC-SC/firewall).
Each attempt should **fail** *and* generate a correlated detection (Lab 04).

## Part D — Verify + measure
```bash
bash ../../cloud/multicloud/scan_all.sh && python3 ../../cloud/multicloud/report.py
python3 ../../soc/incident/incident_report.py
```
Score maturity per pillar per cloud with
`../../zero-trust/validation/zero_trust_maturity_check.md`; identify the weakest
pillar and the next step.
Success = one policy enforced across all three clouds; every lateral-movement
attempt denied per-request and detected; a maturity score per pillar per cloud.

## Cleanup
Tear down all remaining lab resources across the three clouds; disable SIEM
ingestion and detection plans.

## Portfolio artifact (the capstone)
- A **multi-cloud Zero Trust architecture doc** (one policy → three enforcement
  planes), diagram adapted from `../../zero-trust/architecture/diagram.md`.
- The **attack-and-deny matrix** (each lateral-movement attempt → which PEP denied
  it → the detection that fired).
- A **maturity scorecard** across AWS+Azure+GCP with a roadmap.

## Stretch goals
- Add **continuous verification** (session revocation on risk) in each cloud;
  demonstrate mid-session containment.
- Build a 5-slide "multi-cloud Zero Trust" deck from your artifacts.
- Map the whole build to a framework crosswalk (`../../grc/compliance/crosswalk.py`).
