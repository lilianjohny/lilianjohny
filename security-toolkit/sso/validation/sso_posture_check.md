# SSO Posture Checklist (prove SSO is actually enforced)

Use to verify SSO is real and safe, per cloud and across clouds. Items marked →
link to toolkit scripts you can run for evidence.

## Single source of truth
- [ ] Humans exist only in the **one IdP**; no human IAM users / local cloud users.
      → AWS: `../../cloud/ciem/aws_least_privilege.py` (users with keys / count).
- [ ] Each cloud **federates** to that IdP (Identity Center SAML+SCIM · Entra
      native/federated · GCP Workforce Identity Federation).
- [ ] Group membership drives entitlements; no per-user assignments.

## Authentication strength
- [ ] **Phishing-resistant MFA (FIDO2/passkeys)** enforced at the IdP for all users.
- [ ] Legacy/basic auth **blocked** (esp. Entra) — it silently bypasses MFA.
- [ ] Sign-in policy / Conditional Access requires MFA + (where used) device
      compliance; risky sign-ins blocked or stepped-up.
- [ ] Session lifetime bounded; step-up re-auth for sensitive/privileged actions.

## Provisioning & lifecycle (the offboarding test)
- [ ] **SCIM** provisioning live on every target that supports it.
- [ ] **Joiner** test: group add → correct access appears in each cloud.
- [ ] **Mover** test: group change → entitlements shift.
- [ ] **Leaver** test: disable in IdP → access removed **everywhere** within SLA.
      Keep evidence (`../../soc-reports/evidence/evidence_tracker.py`).

## Zero standing privilege
- [ ] Privileged roles are eligible-only: Identity Center JIT / Entra PIM / GCP PAM.
- [ ] Activation requires approval + MFA + justification, time-boxed.
- [ ] Access reviews / recertification scheduled on privileged groups.

## Federation trust hygiene
- [ ] Federation subjects/audiences **pinned** (specific pools/apps, audience,
      subject conditions) — see `../terraform/`.
- [ ] Trusts defined as code, reviewed, revocable.
- [ ] Workload SSO is keyless (OIDC/WIF), no static keys in CI
      (`../../iam/terraform/multicloud/README.md`).

## Guardrails still cap SSO
- [ ] AWS SCP+RCP cap SSO roles (`../../iam/policies/`).
- [ ] Azure Policy assigned at management group (`../../iam/policies/azure-policy-baseline.md`).
- [ ] GCP Org Policy enforced (`../../iam/policies/gcp-org-policy-baseline.md`).

## Break-glass
- [ ] 2+ cloud-native emergency accounts per cloud, FIDO2, **outside federation**,
      excluded from lockout controls, sealed/split, alerted on use, tested quarterly.

## Detection & audit
- [ ] All auth + admin logs centralized & immutable → SIEM
      (`../../cloud/detection/aws_detection_coverage.py`, `../../soc/`).
- [ ] Alerts: new admin, root/Global-Admin use, MFA disabled, CA/policy change,
      permission-set / federation change, impossible-travel.
      → hunt queries: `../../cloud/detection/cloudtrail_hunt.md`.

## Governance mapping
- [ ] SSO controls mapped to frameworks once → many
      (`../../grc/compliance/crosswalk.py`) — NIST/ISO/SOC 2/PCI/CIS/CMMC.
- [ ] Identity risks tracked in `../../grc/risk/risk_register.py`.
