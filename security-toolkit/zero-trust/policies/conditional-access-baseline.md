# Zero Trust Access-Policy Baseline (the PDP rules)

A baseline set of access policies — the rules your Policy Decision Point
evaluates on every request. Expressed cloud-neutrally, then mapped to each
cloud's engine. **Roll every policy out in report-only/audit mode first**, verify
impact, then enforce. Always exclude break-glass accounts.

## Baseline policies

| # | Policy (intent) | Condition → Action |
|---|-----------------|--------------------|
| P1 | **MFA everywhere** | Any user, any app → require phishing-resistant MFA |
| P2 | **Block legacy/basic auth** | Legacy auth protocol → block |
| P3 | **Compliant device for sensitive apps** | App = sensitive & device not compliant → block (or browser-isolated read-only) |
| P4 | **Risk-based step-up / block** | Sign-in risk = medium → step-up; high → block + revoke session |
| P5 | **Admin = stronger controls** | Privileged role → require FIDO2 + compliant device + JIT activation |
| P6 | **Bounded sessions** | Set sign-in frequency / session lifetime; privileged = short |
| P7 | **Location / impossible travel** | Disallowed geo or impossible travel → block/step-up |
| P8 | **Continuous evaluation** | Token/user revoked or risk rises mid-session → revoke access |
| P9 | **Break-glass exclusion** | Break-glass accounts excluded from P1–P8; **alert on every use** |

## Mapping to each cloud's engine

### Azure — Entra Conditional Access
- P1: Grant control **Require MFA** (authentication strength = phishing-resistant).
- P2: **Block legacy authentication** policy.
- P3: Grant **Require device to be marked compliant** (Intune), scoped to sensitive apps.
- P4: **Sign-in/user risk** conditions (Identity Protection) → require MFA / block.
- P5: Target directory roles; combine compliant device + auth strength; **PIM** for activation.
- P6: Session control **Sign-in frequency** + **Continuous Access Evaluation (CAE)**.
- P7: **Named locations** + risk.
- P8: **CAE** revokes on user disable / risk.
- P9: Exclude break-glass group from all CA policies; alert in Sentinel.
- Reference: `../../iam/policies/azure-policy-baseline.md`.

### AWS — IAM Identity Center + Verified Access (Cedar)
- P1/P5: MFA + auth strength at the IdP; short session durations on permission sets; **JIT** elevation.
- P3: **AWS Verified Access** policy (Cedar) requires a device-trust provider signal per app.
- P4/P7/P8: Verified Access + IdP risk/context conditions; revoke on GuardDuty finding (EventBridge → automation).
- P2: enforce modern auth at IdP; deny legacy at app front doors.
- P6: short permission-set session duration; re-auth for privileged.
- P9: break-glass = separate IAM path outside Identity Center/Verified Access; alert on use.
- Guardrails that always cap: **SCP + RCP** (`../../iam/policies/`).

### GCP — Context-Aware Access (Access Context Manager) + IAP
- P1/P5: FIDO2 at IdP / Cloud Identity; **PAM** for privileged JIT.
- P3/P7: **Access levels** (device posture via Endpoint Verification, IP/geo) bound to resources & **IAP**.
- P4/P8: access levels re-evaluated per request; posture loss → access lost next check.
- P6: short **workforce pool session_duration** (`../../sso/terraform/gcp/main.tf`).
- P2: enforce modern auth at IdP.
- P9: Google-native super-admins excluded from enforcement that could lock out; alert via SCC.
- Data perimeter: **VPC Service Controls**.

## Policy-as-code
For app/API and workload authorization at a PEP, express decisions as code and
test them in CI — see `opa-abac-example.rego` (OPA/Rego ABAC example, evaluatable
with `conftest`/`opa eval`). Keep all access policy versioned and reviewed.

## Verification
Confirm each baseline policy is enforced (not just report-only) and break-glass is
excluded + alerted, via `../validation/zero_trust_maturity_check.md`.
