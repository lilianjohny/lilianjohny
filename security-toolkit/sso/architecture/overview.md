# SSO Architecture — Overview (2026)

## What SSO is (and isn't)
**Single Sign-On** lets a person authenticate **once** at a trusted identity
provider (IdP) and then access many independent applications and clouds without
re-entering credentials. The IdP proves *who* the user is (authentication);
each downstream system (the *service provider* / relying party) decides *what*
they can do (authorization).

- SSO ≠ password reuse. There is **one** credential, held only at the IdP.
- SSO ≠ authorization. Login gets you in the door; `../iam/` decides the room.
- SSO is the foundation of the **Identity pillar** of Zero Trust (`../zero-trust/`).

## The three protocols you'll use
| Protocol | Purpose | Where it's used |
|----------|---------|-----------------|
| **SAML 2.0** | Browser SSO via signed XML assertions | AWS Identity Center, GCP Workforce IF, most SaaS |
| **OIDC** (OAuth 2.0) | Token-based SSO/authorization for apps, APIs, mobile, CI | Modern apps, GCP/AWS workload federation, GitHub Actions |
| **SCIM 2.0** | Automated user/group **provisioning & deprovisioning** | IdP → AWS Identity Center / SaaS |

**Rule of thumb:** SAML/OIDC = *authenticate at sign-in*; SCIM = *keep the
directory of users and groups in sync so entitlements and offboarding are
automatic*. Use SCIM wherever the target supports it — otherwise a leaver
removed in the IdP can still have a stale local account.

## Reference model: hub-and-spoke federation
```
                 ┌───────────────────────────────┐
                 │      Central IdP (the hub)     │
                 │  Entra ID / Okta               │
                 │  • users & groups (HR-sourced) │
                 │  • phishing-resistant MFA      │
                 │  • Conditional Access / policy │
                 │  • session lifetime & re-auth  │
                 └───────────────┬───────────────┘
     SAML/OIDC (auth) + SCIM (provisioning)
        ┌───────────────┬────────┴───────┬──────────────────┐
        ▼               ▼                ▼                  ▼
   AWS Identity      Entra ID         GCP Workforce      SaaS / apps
     Center          (native)        Identity Fed        (OIDC/SAML)
   groups→permission  groups→roles   groups→role         groups→app
      sets/accounts   /CA scope      bindings            roles
```

### Design principles
1. **Single source of truth.** People and groups live in **one** IdP, fed from
   HR (joiners-movers-leavers). No cloud keeps its own copy of humans.
2. **Group-driven entitlements.** Access is granted by IdP **group membership**,
   mapped to per-cloud roles/permission sets. Grant/revoke in one place.
3. **Phishing-resistant MFA at the IdP.** FIDO2/passkeys enforced there once,
   inherited by every downstream cloud. No SMS OTP for privileged access.
4. **SCIM everywhere it's supported.** Provisioning and (critically)
   **deprovisioning** are automatic — a disabled IdP user loses access globally.
5. **No local break-in accounts** except cloud-native **break-glass** (2+,
   FIDO2, sealed, excluded from federation, alerted on use) so an IdP outage
   never locks you out.
6. **Short sessions + re-auth on sensitivity.** Session lifetime is bounded;
   step-up auth for privileged actions (ties into JIT in `../iam/`).
7. **Everything as code & reviewed.** Federation trusts, permission sets, and
   app assignments are defined in `../terraform/` — reviewable and revocable.

## Authentication vs authorization — the handoff
```
[IdP] authenticate + MFA ──▶ assertion carries: identity + group claims
                                        │
                                        ▼
[Cloud] map groups → permission set / role  ──▶  short-lived credentials
                                        │
                                        ▼
[IAM]  (../iam/) least privilege + JIT elevation + guardrails (SCP/Policy/OrgPolicy)
```
SSO stops at "here is a verified user in these groups." The IAM layer turns that
into scoped, time-boxed, least-privilege access.

## What "good" looks like (2026 baseline)
- One IdP; **0** human IAM users / local cloud accounts (break-glass excepted).
- **100%** of interactive logins go through the IdP with phishing-resistant MFA.
- SCIM provisioning + deprovisioning on every target that supports it.
- Federation subjects **pinned** (specific pools/apps/audiences/conditions).
- Access granted by group; **access reviews** on a cadence (see `../../iam/`).
- All auth events centralized to a SIEM (`../../soc/`, `../../cloud/detection/`).
