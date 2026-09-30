# Google Cloud IAM Architecture (2026)

## Foundation: resource hierarchy
- **Organization → Folders → Projects.** Folders by function/environment
  (`Platform`, `Prod`, `NonProd`, `Sandbox`), projects as the blast-radius unit.
- Dedicated projects for **logging** (log sink → central bucket/BigQuery),
  **security tooling**, and **shared VPC** host(s).
- IAM applied at the **highest appropriate node** (org/folder) and inherited;
  avoid per-project drift.

## Human access: Workforce Identity Federation (federated, no GCP users)
- Humans authenticate through your **central IdP** via **Workforce Identity
  Federation** (OIDC/SAML) — **no separate Cloud Identity passwords** for
  federated users. Group-based access flows from the IdP.
- Grant **predefined/custom roles** to **groups** at folder/project scope;
  **never** primitive roles (`roles/owner|editor|viewer`) at org level.
- **Zero standing privilege via Privileged Access Manager (PAM):** privileged
  grants are **entitlements** — requested just-in-time, approved, time-boxed,
  auto-expiring. Pair with **IAM Conditions** (time/resource-bound bindings).

## Workload access: Workload Identity Federation (no exported keys)
- **GKE Workload Identity** binds K8s service accounts → Google service accounts
  (no node keys).
- External workloads & **CI/CD** use **Workload Identity Federation**: GitHub/
  GitLab OIDC → workload identity pool → impersonate a service account with
  short-lived tokens. **Never create/export service-account JSON keys.**
- Org Policy `iam.disableServiceAccountKeyCreation` blocks key export org-wide.

## Guardrails: Organization Policy + Principal Access Boundary
- **Org Policy constraints** (inherited):
  - `iam.disableServiceAccountKeyCreation`, `iam.automaticIamGrantsForDefaultServiceAccounts` = off
  - `iam.allowedPolicyMemberDomains` (domain-restricted sharing — blocks
    `allUsers`/external identities)
  - `storage.publicAccessPrevention` = enforced; `storage.uniformBucketLevelAccess`
  - `compute.vmExternalIpAccess` restricted; `sql.restrictPublicIp`
  - `gcp.resourceLocations` (region lock)
- **Principal Access Boundary (PAB):** cap which resources a set of principals
  can *ever* access, independent of their IAM grants.
- **VPC Service Controls** perimeters around sensitive data services to stop
  exfiltration even with valid credentials.

## Least privilege & right-sizing
- **Custom roles** with only needed permissions; prefer **IAM Conditions**
  (resource type, tag, time) to scope bindings.
- **IAM Recommender / Policy Analyzer** to remove unused permissions; feed
  `../../cloud/ciem/` for cross-cloud review.

## Detection & audit
- **Cloud Audit Logs** (Admin Activity always on; Data Access enabled on
  sensitive services) → aggregated **org log sink** → immutable bucket/BigQuery.
- **Security Command Center** for posture + threat detection.
- Alert on: SA key creation, primitive-role or public (`allUsers`) grants,
  org-policy changes, logging-sink deletion.

## Break-glass
- 2 Cloud Identity super-admin emergency accounts (not federated), FIDO2,
  sealed/split credentials, excluded from any lockout-capable controls, alerted
  on use, tested quarterly.

## Terraform baseline
`../terraform/gcp/` — org policy constraints, workforce + workload identity
pools/providers, custom roles, and conditional bindings. Deny-by-default.
