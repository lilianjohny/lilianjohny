# Lab 00 — Unified Identity & SSO (Multi-Cloud)

**Skills practiced:** single IdP federation · SSO to AWS + Azure + GCP ·
phishing-resistant MFA once, everywhere · group-driven entitlements · SCIM
lifecycle · the offboarding (leaver) test across clouds.
**Proves (JD):** authN/authZ *at scale* — the hardest identity problem, done right.

## Objective
Make **one identity, governed once, work in every cloud.** A person authenticates
at a single IdP with phishing-resistant MFA; AWS, Azure, and GCP each federate to
it and map the user's **groups** to entitlements. Disable the user once → access
gone everywhere.

## Est. time / cost
3–4 h · **~$0**.

## Prerequisites
- A central **IdP** (Entra ID or Okta) you control.
- Sandbox AWS + Azure + GCP (per-cloud Lab 00 done in each).
- Reference: `../../sso/architecture/multicloud.md`, `../../sso/process/implementation.md`,
  and the Terraform in `../../sso/terraform/`.

---

## Part A — Harden the IdP (the hub)
1. Enforce **phishing-resistant MFA** (FIDO2/passkeys); block legacy auth.
2. Create a **cloud-agnostic group taxonomy**
   (`role-<function>-<scope>-<privilege>`), e.g. `role-platform-all-readonly`.
3. Connect an HR-like source for lifecycle (or simulate joiners/movers/leavers).

## Part B — Federate each cloud
1. **AWS:** IdP → **IAM Identity Center** (SAML + SCIM); map groups → permission
   sets (`../../sso/terraform/aws/main.tf`).
2. **Azure:** **Entra** native (or federated from Okta); map groups → RBAC; enable
   **Conditional Access** (`../../sso/terraform/azure/main.tf`).
3. **GCP:** IdP → **Workforce Identity Federation**; bind IAM by
   `principalSet://…/group/<group>` (`../../sso/terraform/gcp/main.tf`).

## Part C — Attack / observe: what SSO must prevent
1. **No SSO baseline:** show that without federation you'd have 3 separate user
   stores, 3 MFA setups, 3 offboarding steps — and a leaver could linger in one.
2. Create a test user, add to a group, and confirm access appears in all three.

## Part D — Prove the loop (the leaver test)
1. **Joiner:** add the user to `role-…-readonly` → correct access appears in AWS,
   Azure, GCP.
2. **Mover:** change groups → entitlements shift in each cloud.
3. **Leaver:** disable the user in the IdP → SCIM/federation removes access
   **everywhere** within the provisioning SLA. **This is the key test.**
4. Verify federation subjects are **pinned** (specific pools/apps/audiences).

## Verify
```bash
# From each cloud, the federated user has ONLY their group's access:
aws sts get-caller-identity           # SSO role, short-lived
az account show                       # Entra user
gcloud auth list                      # workforce identity
# Toolkit posture across clouds (identity findings)
bash ../../cloud/multicloud/scan_all.sh && python3 ../../cloud/multicloud/report.py
```
Success = one login + one MFA works in all three; access is group-driven; the
leaver test removes access everywhere; no per-cloud human accounts remain
(break-glass excepted).

## Cleanup
Remove the test user/groups and (if just for the lab) the federation trusts —
though you'll likely keep these for later multi-cloud labs.

## Portfolio artifact
- A **federation diagram** (one IdP → three clouds) with the group→entitlement
  mapping per cloud.
- The **leaver-test evidence** (access present → disabled → gone in each cloud) —
  this single artifact impresses identity-focused interviewers.

## Stretch goals
- Add **per-cloud break-glass** (cloud-native, outside federation) and test alerts.
- Enforce **JIT everywhere** (Identity Center JIT / Entra PIM / GCP PAM) through a
  consistent request workflow.
- Run access reviews from IdP groups + per-cloud CIEM (`../../cloud/ciem/`).
