# Secure IAM Principles (2026 and forward)

The non-negotiable principles every design in this directory implements. Each
maps to concrete cloud features and to the guardrails/Terraform here.

## 1. Zero Trust identity
- **Never trust, always verify.** Every access decision evaluates identity,
  device posture, and context (location, risk) at request time.
- No implicit trust from network location; the identity *is* the perimeter.
- Enforced via Conditional Access (Entra), IAM Identity Center + context,
  Access Context Manager / VPC Service Controls (GCP).

## 2. One identity source (federate, don't duplicate)
- Humans exist in **one IdP**; every cloud federates to it via SAML/OIDC.
- **No local IAM users**, no per-cloud passwords, no shared accounts.
- Group-based entitlements flow from the IdP → cloud permission sets/roles.

## 3. No long-lived credentials
- **Workloads** use **workload identity federation** (short-lived OIDC tokens):
  - CI/CD (GitHub/GitLab) → OIDC → cloud role (no stored keys).
  - K8s/apps → IRSA (AWS), Workload Identity (GKE), Managed Identity (Azure).
- **Humans** use SSO + short-lived session credentials, never access keys.
- Static keys/SP secrets are the exception, rotated ≤ 90 days, and alerted on.

## 4. Zero Standing Privilege (ZSP) — just-in-time, time-boxed
- Privileged roles are **eligible**, not **active**: activated on demand,
  with approval, for a limited window, then auto-revoked.
- AWS: IAM Identity Center + temporary elevated access / JIT.
- Azure: **Entra PIM** (eligible assignments, approval, activation MFA).
- GCP: **Privileged Access Manager (PAM)** entitlements + IAM Conditions.

## 5. Phishing-resistant MFA — always
- **FIDO2 / passkeys / certificate-based** for all humans; number-matching push
  at minimum. SMS/voice OTP are not acceptable for privileged access.
- Enforced by policy (Conditional Access, Identity Center MFA, Org constraints),
  required especially at privileged-role activation.

## 6. Least privilege, right-sized continuously
- Start from **deny-by-default**; grant the minimum scope, prefer **ABAC**
  (tags/attributes) over sprawling role lists.
- Use **permission boundaries** (AWS) / **Principal Access Boundary** (GCP) to
  cap the *maximum* any principal can reach.
- **CIEM** removes unused entitlements on a cadence (`../../cloud/ciem/`).

## 7. Preventive guardrails at the org edge
Controls that cap behavior regardless of individual grants:
- **AWS:** Service Control Policies (principal guardrails) **+ Resource Control
  Policies** (resource/data-perimeter guardrails) — neither grants access.
- **Azure:** Management-group **Azure Policy** (deny/append/audit).
- **GCP:** **Organization Policy** constraints + IAM Conditions + PAB.
- Common guardrails: region lock, block public data sharing, deny disabling
  logging, require encryption, deny leaving the org, restrict root/owner.

## 8. Separation of duties & tiered admin
- Split identity admin, security admin, and workload admin.
- **Tier-0** (identity/security control plane) isolated from workload admin.
- No single human can both grant privilege and use it unreviewed.

## 9. Break-glass, controlled
- 2+ emergency accounts, cloud-native (not federated), FIDO2-protected,
  credentials split/sealed, **excluded from CA that could lock them out**,
  and **alerted on every use**. Tested quarterly.

## 10. Detect, log, review
- All authentication and admin/IAM changes centralized (CloudTrail, Entra
  audit/sign-in logs, GCP Cloud Audit Logs) — immutable, 12–18 mo retention.
- **Access reviews / recertification** on a schedule; alert on anomalies
  (impossible travel, new admin, MFA disabled, key created).
- Tie to `../../cloud/detection/` and `../../soc/`.

## Anti-patterns (never)
- Long-lived access keys / exported service-account keys.
- Wildcard admin (`*:*`) as a standing grant.
- Local users bypassing the IdP; shared credentials.
- Root/Global Admin used for daily work.
- MFA optional, or SMS OTP for admins.
- Logging that principals can disable without alert.
