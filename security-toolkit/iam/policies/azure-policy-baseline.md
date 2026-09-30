# Azure Policy — IAM/security baseline (management-group scope)

Assign these (built-in where available) at the top management group so they
inherit. Use **Deny** for hard guardrails, **Audit**/**DeployIfNotExists** for
posture. Terraform in `../terraform/azure/` assigns a representative set.

## Identity & access
- **Deny** creation of classic administrators / classic resources.
- **Audit** subscriptions with more than N Owners (limit standing Owner).
- **Deny** guest users being granted privileged roles (governed via PIM instead).
- Require **MFA** for accounts with write/owner permissions (Conditional Access
  + policy audit).

## Network / public exposure
- **Deny** storage accounts / SQL / Key Vault with public network access; require
  **private endpoints**.
- **Deny** NSG rules allowing `Internet`/`*` inbound to management ports.
- **Deny** public IPs on VMs outside approved patterns.

## Data protection
- **Deny** storage without HTTPS-only + minimum **TLS 1.2**.
- Require encryption at rest; require **customer-managed keys** for regulated data.
- **Audit/Deny** Key Vaults without soft-delete + purge protection.

## Logging & governance
- **DeployIfNotExists**: diagnostic settings → central **Log Analytics** for all
  resource types.
- **Deny** deleting/disabling diagnostic settings.
- **Allowed locations** (region lock) for resources and resource groups.

## Privileged access (via Entra PIM, enforced operationally)
- Privileged Entra roles = **eligible only** (no permanent), activation requires
  approval + MFA + justification, time-boxed.
- Access reviews on all eligible privileged assignments (recurring).

## Suggested built-in initiatives
- **Microsoft cloud security benchmark** (default in Defender for Cloud).
- **CIS Microsoft Azure Foundations Benchmark**.
- **NIST SP 800-53 Rev 5** (if in scope).

> Validate exact `policyDefinitionId`s and parameters against your tenant; some
> controls (MFA, CA) are enforced in Entra Conditional Access, audited by policy.
