# Multi-Cloud IAM — Federation Diagram

Rendered by any Mermaid viewer (GitHub renders it inline).

```mermaid
flowchart TB
    HR[HR system\njoiners / movers / leavers] -->|SCIM feed| IDP

    subgraph TIER0[Tier-0 Identity Control Plane]
        IDP[Central IdP\nEntra ID / Okta]
        MFA[Phishing-resistant MFA\nFIDO2 / passkeys]
        CA[Conditional Access\ndevice + risk + context]
        LIFE[Lifecycle & Access Reviews]
        IDP --- MFA --- CA --- LIFE
    end

    IDP -->|SAML + SCIM| AWS
    IDP -->|native / federated| AZ
    IDP -->|Workforce Identity Fed| GCP
    IDP -->|OIDC| SAAS[SaaS / K8s apps]

    subgraph AWS[AWS Organization]
        AIC[IAM Identity Center\npermission sets]
        AJIT[JIT elevation\ntemporary access]
        ASCP[SCP + RCP guardrails]
        AOIDC[GitHub OIDC -> role]
        AIC --> AJIT
    end

    subgraph AZ[Azure / Entra]
        ARBAC[Azure RBAC + Entra roles]
        PIM[Entra PIM\neligible -> activate JIT]
        APOL[Azure Policy guardrails]
        AWIF[Workload Identity Fed]
        ARBAC --> PIM
    end

    subgraph GCP[Google Cloud Org]
        GIAM[IAM roles + Conditions]
        PAM[Privileged Access Manager\nJIT entitlements]
        GORG[Org Policy + PAB guardrails]
        GWIF[Workload Identity Fed]
        GIAM --> PAM
    end

    CI[CI/CD pipeline] -.->|OIDC, no keys| AOIDC
    CI -.->|OIDC, no keys| AWIF
    CI -.->|OIDC, no keys| GWIF

    AWS --> LOGS[(Central SIEM\nall auth + admin logs)]
    AZ --> LOGS
    GCP --> LOGS
    LOGS --> SOC[SOC / detection\n../../soc ../../cloud/detection]

    classDef t0 fill:#1f2937,stroke:#60a5fa,color:#e5e7eb;
    class IDP,MFA,CA,LIFE t0;
```

## Reading it
- **Top-down trust:** one IdP (Tier-0) authenticates every human, with
  phishing-resistant MFA and Conditional Access, and drives lifecycle.
- **Federation, not duplication:** each cloud trusts the IdP; entitlements come
  from IdP groups.
- **JIT everywhere:** privileged use is activated on demand (Identity Center JIT
  / Entra PIM / GCP PAM), never standing.
- **Keyless workloads:** CI/CD and apps use OIDC/workload identity federation
  (dashed lines) — no static keys cross any boundary.
- **Guardrails per cloud** cap behavior regardless of grants.
- **All logs converge** to one SIEM for cross-cloud identity correlation.
