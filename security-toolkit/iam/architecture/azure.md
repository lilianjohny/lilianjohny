# Azure / Entra ID IAM Architecture (2026)

## Foundation: tenant + management-group hierarchy
- Single **Entra ID tenant** as the identity control plane.
- **Management groups:** `Root → Platform (Identity/Management/Connectivity),
  Landing Zones (Corp/Online), Sandbox, Decommissioned`. Subscriptions placed by
  function/blast radius (Azure Landing Zone / CAF).
- Platform subscriptions for logging, security, and connectivity, separate from
  workloads.

## Human access: Entra ID (federated), RBAC, and PIM
- Humans in **one IdP** (Entra as hub, or federated from Okta). **No per-app
  local accounts.**
- **Azure RBAC** (resource control plane) and **Entra roles** (directory) granted
  to **groups**, at the narrowest scope (management group → subscription →
  resource group), never standing at tenant/owner level.
- **Zero standing privilege via Entra PIM:**
  - Privileged roles (Global Admin, Owner, User Access Administrator, etc.) are
    **eligible**, not permanent.
  - Activation requires **approval**, **justification**, **MFA**, and is
    **time-boxed**; auto-deactivates. Access reviews on eligible assignments.
- **Conditional Access:** require **phishing-resistant MFA** + **compliant/hybrid
  device** for all users, hardened further for admins and PIM activation; block
  legacy auth; risk-based (Identity Protection) sign-in controls.

## Workload access: managed identities & workload identity federation (no secrets)
- App/VM/AKS workloads use **managed identities** (system- or user-assigned) —
  no client secrets.
- External workloads & **CI/CD** use **workload identity federation**: GitHub/
  GitLab OIDC → an Entra app registration's federated credential → tokens, **no
  client secret stored**.
- Migrate legacy user-based service accounts → workload identities (which don't
  need interactive MFA), removing standing secrets.

## Guardrails: Azure Policy at management-group scope
- **Deny/Audit/Append** policies inherited down the hierarchy:
  - Deny public network access on storage/SQL/Key Vault; require private endpoints.
  - Require encryption + customer-managed keys where mandated.
  - Allowed locations (region lock); allowed VM SKUs.
  - Deny disabling diagnostic settings; require sending logs to the central
    Log Analytics workspace.
  - Enforce HTTPS-only, minimum TLS 1.2.
- **Entra permission management / access reviews** for entitlement right-sizing.

## Least privilege & right-sizing
- Prefer **custom roles** scoped tightly over built-in Owner/Contributor.
- **Attribute/condition-based** RBAC where supported; **Entra Permissions
  Management (CIEM)** to remove unused permissions across clouds.

## Detection & audit
- **Entra sign-in + audit logs** and **Azure Activity/Diagnostic logs** → central
  **Log Analytics** + Microsoft Sentinel; **Defender for Cloud** enabled.
- Alert on: privileged role activation/assignment, CA policy changes, new
  federated credential, legacy-auth attempts, MFA disabled.

## Break-glass
- 2 cloud-only Global Admin emergency accounts, FIDO2, **excluded from CA
  policies that could lock them out**, credentials sealed/split, sign-in alerts,
  tested quarterly.

## Terraform baseline
`../terraform/azure/` — management-group Azure Policy assignments, PIM role
settings (eligibility + activation requirements), GitHub workload-identity
federated credential, and diagnostic-settings enforcement.
