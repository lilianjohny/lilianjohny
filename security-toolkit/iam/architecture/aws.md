# AWS IAM Architecture (2026)

## Foundation: multi-account with AWS Organizations
- **Management account** holds Organizations only — no workloads, minimal
  access, root secured with hardware MFA + centralized root access management.
- **Organizational Units (OUs):** `Security`, `Infrastructure`, `Workloads/Prod`,
  `Workloads/NonProd`, `Sandbox`, `Suspended`. Accounts grouped by function/blast
  radius (Control Tower or an equivalent landing zone).
- Dedicated **Log Archive** and **Security Tooling** accounts (delegated admin
  for GuardDuty, Security Hub, IAM Access Analyzer, Config).

## Human access: IAM Identity Center (federated, no IAM users)
- Identity source = your central IdP (Entra/Okta) via SAML/SCIM, **or** the
  Identity Center store. **No IAM users** for people.
- **Permission sets** = job functions (ReadOnly, PowerUserScoped, DBA,
  SecurityAudit, BreakGlassAdmin), assigned to **groups**, mapped to accounts.
- **Zero standing privilege:** day-to-day = read/limited; elevation is
  **just-in-time** (temporary elevated access), approval + session duration
  capped (e.g., 1h), all via short-lived role credentials.
- **Phishing-resistant MFA** (FIDO2) enforced at the IdP / Identity Center.

## Workload & CI access: roles + OIDC (no keys)
- Applications assume **IAM roles**; never static keys.
  - EKS → **IRSA / EKS Pod Identity**; EC2 → instance roles (IMDSv2 only).
  - Lambda/ECS → task/execution roles.
- CI/CD → **GitHub/GitLab OIDC provider** → role with `sts:AssumeRoleWithWebIdentity`,
  trust policy scoped to repo/branch/environment. No `AWS_ACCESS_KEY_ID` in CI.
- Cross-account = role assumption with `ExternalId`/conditions, never shared keys.

## Guardrails: SCPs + RCPs (neither grants — both cap)
- **Service Control Policies (principals):** deny leaving org, deny disabling
  CloudTrail/Config/GuardDuty, region lock, deny root actions in members,
  require IMDSv2, deny creating IAM users/access keys, protect security roles.
- **Resource Control Policies (resources / data perimeter):** ensure only
  principals from your org (or trusted OIDC) can access S3/KMS/STS/SQS/Secrets
  Manager — closes the confused-deputy / external-access gap. (RCPs currently
  cover S3, STS, KMS, SQS, Secrets Manager; apply at OU/root after testing.)
- **Permission boundaries** cap what delegated admins can grant.

## Least privilege & right-sizing
- Start from AWS-managed read-only + narrowly scoped customer policies; prefer
  **ABAC** with tags (`aws:PrincipalTag`, `aws:ResourceTag`).
- **IAM Access Analyzer**: external-access findings, unused-access findings,
  and policy generation from CloudTrail. Remove unused via `../../cloud/ciem/`.

## Detection & audit
- **CloudTrail** org trail (all regions, log-file validation) → Log Archive
  account (immutable S3 + Object Lock). **GuardDuty**, **Security Hub**,
  **Access Analyzer**, **Config** enabled org-wide (delegated to Security acct).
- Alert on: root usage, IAM user/key creation, policy changes, `StopLogging`.

## Break-glass
- 2 IAM users in the management account (the only human IAM users), hardware-MFA,
  password + MFA split between custodians, no keys, alarmed on any sign-in.

## Terraform baseline
`../terraform/aws/` — Identity Center permission sets & assignments, GitHub
OIDC provider + CI role, SCP + RCP attachment, Access Analyzer, and break-glass
alarms. Region-locked, deny-by-default.
