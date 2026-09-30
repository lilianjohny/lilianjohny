# SSO Diagrams

ASCII/Mermaid diagrams for the SSO flows. Paste the Mermaid blocks into any
Mermaid renderer (GitHub, VS Code, mermaid.live) for a rendered view.

---

## 1. High-level: one login, every cloud
```mermaid
flowchart TD
    HR[HR system] -->|joiners/movers/leavers| IdP
    subgraph Hub
      IdP["Central IdP\nEntra ID / Okta\nMFA (FIDO2) + policy + SCIM"]
    end
    IdP -->|SAML + SCIM| AWS["AWS IAM Identity Center\ngroups -> permission sets"]
    IdP -->|native / federated| AZ["Microsoft Entra ID\ngroups -> RBAC + PIM"]
    IdP -->|OIDC/SAML| GCP["GCP Workforce Identity Fed\ngroups -> IAM bindings"]
    IdP -->|OIDC/SAML| SAAS["SaaS / apps"]
    AWS --> AWSACC["AWS accounts (STS short-lived)"]
    AZ --> AZRES["Azure subscriptions"]
    GCP --> GCPPROJ["GCP projects"]
```

---

## 2. SAML browser SSO — sign-in sequence (e.g. AWS Identity Center)
```mermaid
sequenceDiagram
    participant U as User (browser)
    participant SP as Service Provider (AWS Identity Center)
    participant IdP as Central IdP (Entra/Okta)
    U->>SP: Access AWS access portal
    SP-->>U: 302 redirect with SAML AuthnRequest
    U->>IdP: Follow redirect (AuthnRequest)
    IdP->>U: Prompt credentials
    U->>IdP: Credentials
    IdP->>U: Phishing-resistant MFA (FIDO2 / passkey)
    Note over IdP: Evaluate policy (Conditional Access):\ndevice, location, risk, session freshness
    IdP-->>U: Signed SAML assertion (identity + group claims)
    U->>SP: POST SAML assertion
    SP->>SP: Validate signature, map groups -> permission sets
    SP-->>U: Access portal: accounts/roles available
    U->>SP: Choose role
    SP-->>U: Short-lived STS credentials (no long-lived keys)
```

---

## 3. OIDC token flow (modern apps / workload)
```mermaid
sequenceDiagram
    participant App as App / CLI
    participant IdP as IdP (OIDC provider)
    participant API as Protected resource
    App->>IdP: Authorization request (PKCE)
    IdP->>App: Authenticate + MFA, then authorization code
    App->>IdP: Exchange code (+PKCE) for tokens
    IdP-->>App: ID token (who) + access token (scopes/groups)
    App->>API: Call with access token (Bearer)
    API->>API: Validate token, enforce scopes/roles
    API-->>App: Response
```

---

## 4. SCIM provisioning / deprovisioning (lifecycle)
```mermaid
sequenceDiagram
    participant HR as HR system
    participant IdP as Central IdP (SCIM client)
    participant T as Target (AWS Identity Center / SaaS)
    HR->>IdP: New hire / role change / termination
    IdP->>T: SCIM create/update user + group membership
    Note over T: Entitlements appear via group mapping
    HR->>IdP: Termination
    IdP->>T: SCIM deactivate user
    Note over T: Access removed everywhere the user was provisioned
```

---

## 5. Multi-cloud federation (workload + human), text view
```
                         Central IdP (hub)
                         Entra ID / Okta
        ┌───────────────┬───────┴────────┬────────────────┐
   (human SAML/OIDC + SCIM)          (workload OIDC, keyless)
        ▼               ▼                ▼                ▼
   AWS Identity      Entra ID         GCP Workforce    CI/CD (GitHub)
     Center          native           Identity Fed     OIDC -> all 3
   perm sets        RBAC + PIM        IAM bindings     (no stored keys)
        │               │                │
        ▼               ▼                ▼
   AWS accounts    Azure subs        GCP projects
   + SCP/RCP       + Azure Policy    + Org Policy
```

See `../../zero-trust/architecture/diagram.md` for how the Policy Decision Point
wraps these sign-ins with device/network/session signals.
