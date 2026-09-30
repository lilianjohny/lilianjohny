# AWS SSO Architecture — IAM Identity Center (2026)

**AWS IAM Identity Center** (formerly AWS SSO) is the SSO front door to **every
account** in your AWS Organization, plus SAML/OIDC business apps. People log in
once at your IdP; Identity Center brokers short-lived role credentials into the
right accounts.

## Topology
```
  Central IdP (Entra/Okta)
        │  SAML 2.0 (sign-in)  +  SCIM 2.0 (user/group sync)
        ▼
  AWS IAM Identity Center  (in the Organization management or delegated-admin account)
        │  permission sets (job functions) assigned to GROUPS per ACCOUNT
        ├──────────────┬──────────────┬───────────────┐
        ▼              ▼              ▼               ▼
   Prod account   NonProd acct   Security acct    Log Archive acct
   (AssumeRole,   ...            ...              ...
   short-lived)
```

## Components
- **Identity source = external IdP** via **SAML** (sign-in) + **SCIM** (provisioning).
  Do *not* use the built-in Identity Center store for people if you already have
  an IdP — federate to keep one source of truth.
- **Permission sets** = reusable job functions (e.g. `ReadOnly`, `PowerUserScoped`,
  `DBA`, `SecurityAudit`, `BreakGlassAdmin`). Each becomes an IAM role in the
  target accounts on assignment.
- **Assignments** = (group × permission set × account). Users get access by being
  in the group — never assign to individual users.
- **Access portal** = the user's single landing page listing every account/app
  and role they can assume.

## How a login works
1. User opens the AWS access portal (or a SAML app) → redirected to the IdP.
2. IdP authenticates + **phishing-resistant MFA (FIDO2)** → issues SAML assertion
   with the user's group claims.
3. Identity Center matches groups → permission sets → shows available
   accounts/roles.
4. User picks a role → Identity Center issues **short-lived** credentials
   (STS AssumeRole) for that account. No long-lived keys, ever.

## Zero standing privilege (JIT)
- Day-to-day permission sets are **read/limited**.
- Elevation is **just-in-time**: request → approval → time-boxed elevated
  permission set (session capped, e.g. 1h). Detailed in `../../iam/architecture/aws.md`.
- Session duration on each permission set is set explicitly (short for privileged).

## Guardrails around SSO
- **SCPs / RCPs** (`../../iam/policies/`) cap what *any* role — including SSO
  roles — can do, org-wide. SSO grants access; SCPs/RCPs bound it.
- **CloudTrail** in all accounts → Log Archive account (immutable). Alert on
  `sso`/`sso-directory` admin changes, permission-set changes, and
  `AssumeRoleWithSAML` anomalies (`../../cloud/detection/`).
- Identity Center admin is delegated to a dedicated account (not run day-to-day
  from the Org management account).

## Break-glass
- 2+ **cloud-native** IAM users (or isolated roles) with hardware MFA, **outside**
  federation, sealed/split credentials, excluded from Conditional Access,
  **alerted on every use**, tested quarterly. These exist so an IdP outage can't
  lock you out of AWS.

## What to define as code (`../terraform/aws/main.tf`)
- Permission sets (with managed + inline least-privilege policies, session
  duration).
- Group→permission-set→account assignments.
- (SAML/SCIM connection to the IdP is bootstrapped in console/Graph once, then
  group sync is automatic — see `../process/implementation.md`.)

## Common mistakes to avoid
- ❌ Leaving IAM users for humans "just in case" (defeats SSO/offboarding).
- ❌ Assigning permission sets to users instead of groups.
- ❌ Over-broad permission sets (`*:*`) — scope them; let JIT handle elevation.
- ❌ No SCIM → stale users after someone leaves the IdP.
