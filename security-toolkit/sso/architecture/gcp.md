# Google Cloud SSO Architecture (2026)

Google Cloud gives you two complementary ways to bring your existing IdP's users
in, plus BeyondCorp for context-aware access. The 2026 recommendation for an
**external IdP you already run** (Entra/Okta) is **Workforce Identity
Federation** — federate directly, don't sync passwords.

## Two front doors (pick per use case)
| Mechanism | Use when | How |
|-----------|----------|-----|
| **Workforce Identity Federation** | You have an external IdP (Entra/Okta) and want **no** synced credentials in Google | IdP (OIDC/SAML) → workforce pool → short-lived Google access, groups→IAM |
| **Cloud Identity + SSO** | You want Google as the directory but auth at an external IdP | Cloud Identity users, SAML SSO to IdP, **Directory Sync (GCDS)** or SCIM for provisioning |

Both federate authentication to your IdP. Workforce Identity Federation avoids
provisioning user objects into Google at all (best for "one source of truth").

## Topology (Workforce Identity Federation)
```
  Central IdP (Entra/Okta)
        │  OIDC / SAML  (with group attributes)
        ▼
  Workforce Identity Pool + Provider   (org-level)
        │  attribute mapping: subject + google.groups
        │  IAM policy bindings reference principalSet:// (by group)
        ├─────────────┬──────────────┬───────────────┐
        ▼             ▼              ▼               ▼
   Org / Folder    Project A     Project B      BeyondCorp
   IAM bindings                                 (Context-Aware Access)
```

## Components
- **Workforce Identity Pool + Provider** = the trust to your IdP (OIDC or SAML),
  with **attribute mapping** (subject, and critically `google.groups` so IAM can
  bind by group).
- **IAM bindings by principalSet** = grant roles to
  `principalSet://…/group/<group>` — access follows IdP group membership.
- **Context-Aware Access / BeyondCorp Enterprise** = the Zero Trust gate: allow
  access only from compliant devices, trusted networks, verified location
  (via **Access Context Manager** access levels). See `../../zero-trust/architecture/gcp.md`.
- **PAM (Privileged Access Manager)** = just-in-time, approval-gated, time-boxed
  grants for privileged roles (zero standing privilege).
- **Org Policies** = guardrails (disable SA key creation, restrict locations,
  public access prevention) — `../../iam/policies/gcp-org-policy-baseline.md`.

## How a login works
1. User accesses the Google Cloud console / gcloud with workforce federation.
2. Redirected to the IdP → authenticates + **phishing-resistant MFA (FIDO2)**.
3. IdP returns an OIDC/SAML assertion with group attributes.
4. Workforce pool maps attributes → user assumes short-lived Google credentials;
   **IAM** grants roles based on `google.groups` bindings.
5. **Context-Aware Access** can further require a compliant device / access level
   before the session is allowed.

## Zero standing privilege (PAM)
- Privileged roles granted **just-in-time** via PAM: request → approval →
  time-boxed grant, fully logged. No permanent Owner/Editor at org level.

## Guardrails
- **Organization Policy** constraints enforced org-wide
  (`iam.disableServiceAccountKeyCreation`, `gcp.resourceLocations`,
  `storage.publicAccessPrevention`) — see `../../iam/terraform/gcp/main.tf`.
- **Cloud Audit Logs** (Admin Activity always on) → central log bucket / SIEM;
  alert on IAM policy changes, org-policy changes, key creation, workforce-pool
  changes.

## Break-glass
- 2+ **Google-native** super-admin accounts (Cloud Identity), FIDO2, excluded
  from Context-Aware enforcement that could lock them out, sealed/split, alerted
  on use, tested quarterly.

## What to define as code (`../terraform/gcp/main.tf`)
- Workforce Identity Pool + Provider (OIDC or SAML) with attribute mapping.
- IAM bindings by `principalSet://` group.
- (Access levels / Context-Aware Access bindings are in
  `../../zero-trust/architecture/gcp.md`.)

## Common mistakes to avoid
- ❌ Exporting service-account keys (org policy should forbid it).
- ❌ Granting primitive roles (Owner/Editor) at org/folder level.
- ❌ Federating without mapping **groups** (you'll bind IAM to individuals).
- ❌ No Context-Aware Access → SSO with no device/network posture (not ZT).
