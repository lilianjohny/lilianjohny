# Azure SSO Architecture — Microsoft Entra ID (2026)

**Microsoft Entra ID** (formerly Azure AD) is *both* the IdP and Azure's native
identity plane, so Azure SSO is the most direct of the three clouds: users
already live in Entra (or are federated into it), and **Conditional Access** is
the policy engine that gates every sign-in.

## Topology
```
  Users (HR-sourced) ──▶ Entra ID (IdP + Azure identity plane)
                              │  Conditional Access evaluated on EVERY sign-in
                              │  (user + device + location + risk + MFA)
        ┌─────────────────────┼──────────────────────┬─────────────────┐
        ▼                     ▼                      ▼                 ▼
   Azure resources      Microsoft 365          Enterprise apps     Other clouds
   (RBAC + PIM)          / Graph               (SAML/OIDC SSO)     (AWS/GCP via
                                                                    federation)
```

Two IdP shapes:
- **Entra-primary:** Entra is your source of truth; users authenticate natively.
- **Entra-federated (e.g. Okta upstream):** Okta authenticates, Entra trusts it.
  Either works; keep exactly one authoritative source.

## Components
- **Enterprise applications** = the SSO registrations for SaaS/business apps
  (SAML or OIDC). Assign **groups**, not users.
- **App roles / group claims** = what the app receives about the user to make
  authorization decisions downstream.
- **Conditional Access (CA)** = the gate: require phishing-resistant MFA, compliant/
  hybrid-joined device, block legacy auth, restrict by location/risk, set sign-in
  frequency (session lifetime). This is the Zero Trust decision point (`../../zero-trust/`).
- **Privileged Identity Management (PIM)** = just-in-time, approval-gated,
  time-boxed activation of privileged roles (zero standing privilege).
- **Provisioning (SCIM)** = Entra pushes users/groups into downstream SaaS and
  into **AWS Identity Center** / **GCP** — one directory, synced outward.

## How a login works
1. User hits an app → redirected to Entra.
2. Entra authenticates and evaluates **Conditional Access**: MFA (FIDO2/passkey),
   device compliance, sign-in risk, location. Fail → block or step-up.
3. On success Entra issues the SAML assertion / OIDC token with group + app-role
   claims.
4. For Azure resources, **RBAC** (+ **PIM** for privileged) decides authorization;
   see `../../iam/architecture/azure.md`.

## Zero standing privilege (PIM)
- Privileged roles (Global Admin, Owner, etc.) are **eligible, not active**.
- Activation = approval + MFA + justification, time-boxed (e.g. 1–4h), logged.
- Access reviews recertify eligibility on a cadence.

## Guardrails
- **Azure Policy** at management-group scope (region lock, deny public network,
  require diagnostics) — `../../iam/policies/azure-policy-baseline.md`.
- **Block legacy/basic authentication** (it bypasses MFA) via CA.
- Sign-in + audit logs → Log Analytics / SIEM; alert on Global Admin use, new
  admin, CA policy change, MFA-method changes.

## Break-glass
- 2+ **cloud-only** emergency Global Admin accounts, FIDO2, **excluded from CA
  policies** (so a bad CA rule can't lock everyone out), sealed/split, alerted on
  every sign-in, tested quarterly.

## Federating other clouds from Entra
- **AWS:** Entra → AWS IAM Identity Center via SAML + SCIM.
- **GCP:** Entra → GCP Workforce Identity Federation (OIDC/SAML).
- Same users, same MFA, same offboarding — configured once in Entra.

## What to define as code (`../terraform/azure/main.tf`)
- Enterprise application (SAML SSO) + service principal + group assignment.
- (Conditional Access, PIM settings, and SCIM provisioning jobs are managed via
  Entra/Graph — see `../process/implementation.md`; some are Terraform-manageable
  via the `azuread`/Graph providers, others via portal/Graph API.)

## Common mistakes to avoid
- ❌ Leaving **legacy auth** enabled (silent MFA bypass).
- ❌ Standing Global Admins instead of PIM-eligible.
- ❌ Break-glass accounts *inside* Conditional Access scope.
- ❌ Assigning apps to individual users instead of groups.
