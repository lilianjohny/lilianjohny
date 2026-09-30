# IAM Posture Checklist (verify the architecture is real)

Use to confirm each principle is actually enforced, per cloud and across clouds.
Many items are checkable with the toolkit; those are linked.

## Identity source & federation
- [ ] Humans exist only in the central IdP; **no local IAM users / GCP users**.
      → AWS: `../../cloud/ciem/aws_least_privilege.py` (users w/ keys), IAM users count.
- [ ] Each cloud federates to the IdP (Identity Center SAML/SCIM · Entra · Workforce Identity Fed).
- [ ] Deprovisioning in the IdP removes access everywhere (test a leaver).

## No long-lived credentials
- [ ] No IAM access keys for humans; workloads use roles/managed identities.
      → `../../cloud/ciem/aws_least_privilege.py` (unused/old keys).
- [ ] GCP `iam.disableServiceAccountKeyCreation` enforced (no exported SA keys).
- [ ] CI/CD uses OIDC/workload identity federation (no static keys in secrets).

## Zero standing privilege (JIT)
- [ ] Privileged roles are eligible-only: AWS JIT / **Entra PIM** / **GCP PAM**.
- [ ] Activation requires approval + MFA + justification, time-boxed.
- [ ] Access reviews / recertification scheduled on privileged assignments.

## Phishing-resistant MFA
- [ ] FIDO2/passkeys required for all humans; enforced for admins + JIT activation.
- [ ] Legacy/basic auth blocked; SMS OTP not used for privileged access.

## Guardrails (preventive)
- [ ] AWS **SCP** (`../policies/aws-scp-baseline.json`) + **RCP**
      (`../policies/aws-rcp-data-perimeter.json`) attached at OU/root.
- [ ] Azure Policy baseline assigned at management group (region lock, public
      access denial, diagnostics) — `../policies/azure-policy-baseline.md`.
- [ ] GCP Org Policy baseline enforced — `../policies/gcp-org-policy-baseline.md`.
      → cross-cloud posture: `../../cloud/multicloud/` and `../../cloud/prowler_scan.sh`.

## Least privilege
- [ ] No wildcard admin standing grants; no primitive roles at org level.
      → `../../cloud/ciem/aws_least_privilege.py`, GCP IAM audit.
- [ ] Permission boundaries / Principal Access Boundary in place.
- [ ] CIEM right-sizing on a cadence (unused access removed).

## Detection & audit
- [ ] All auth + IAM-change logs centralized & immutable (12–18 mo).
      → `../../cloud/detection/aws_detection_coverage.py`.
- [ ] Alerts on: root/Global-Admin use, new admin, key creation, MFA disabled,
      logging disabled, org-policy/CA change.
      → hunt queries: `../../cloud/detection/cloudtrail_hunt.md`.

## Break-glass
- [ ] 2+ cloud-native emergency accounts, FIDO2, sealed/split, excluded from
      lockout controls, alerted on use, tested quarterly.

## Governance mapping
- [ ] IAM controls mapped to frameworks once → many:
      `../../grc/compliance/crosswalk.py` (NIST/ISO/SOC 2/PCI/CIS/CMMC).
- [ ] Risks tracked in `../../grc/risk/risk_register.py` (e.g. R-003 insider,
      R-004 third-party).
