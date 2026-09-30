# Zero Trust Diagrams

ASCII + Mermaid diagrams. Paste Mermaid blocks into any Mermaid renderer
(GitHub, VS Code, mermaid.live).

---

## 1. NIST 800-207 core: PDP / PEP per-request decision
```mermaid
flowchart LR
    S["Subject\n(user / workload)"] -- request --> PEP
    subgraph DataPlane["Data plane"]
      PEP["Policy Enforcement Point\n(proxy / gateway / sidecar / broker)"]
      R["Resource\n(app / API / data)"]
    end
    subgraph ControlPlane["Control plane"]
      PE["Policy Engine\n(decides)"]
      PA["Policy Administrator\n(issues/revokes session)"]
    end
    ID["Identity / SSO + MFA"] --> PE
    DEV["Device posture"] --> PE
    CTX["Context: location, risk, time, data class"] --> POL["Policy (as code)"] --> PE
    PEP -- "authZ query" --> PE
    PE --> PA
    PA -- "grant / deny / step-up (short-lived session)" --> PEP
    PEP -- "allow (least privilege)" --> R
    PEP -- events --> SIEM["Visibility & Analytics (SIEM)"]
    SIEM --> AUTO["Automation & Orchestration"] --> PA
```

---

## 2. Per-request decision logic (what the PDP evaluates)
```mermaid
flowchart TD
    A["Access request"] --> B{"Identity verified?\n(SSO + phishing-resistant MFA)"}
    B -- No --> DENY["Deny"]
    B -- Yes --> C{"Device compliant?\n(managed, patched, EDR, encrypted)"}
    C -- No --> LIM["Deny / limited or step-up"]
    C -- Yes --> D{"Context OK?\n(location, risk, time)"}
    D -- Risky --> STEP["Step-up auth / re-verify"]
    D -- OK --> E{"Least-privilege authZ\nfor THIS resource?"}
    E -- No --> DENY
    E -- Yes --> F["Grant short-lived, scoped session"]
    F --> G["Continuously evaluate\n(revoke on risk change)"]
    G -->|risk rises| STEP
```

---

## 3. Pillar map (CISA ZTMM v2.0 + DoD)
```
   ┌──────────────────────── Cross-cutting ────────────────────────┐
   │  Visibility & Analytics  ·  Automation & Orchestration  ·  Governance │
   └───────────────────────────────────────────────────────────────┘
        ▲            ▲              ▲                ▲          ▲
   ┌─────────┐  ┌─────────┐  ┌──────────────┐  ┌───────────┐  ┌──────┐
   │Identity │  │ Devices │  │  Networks &  │  │Applications│  │ Data │
   │ (User)  │  │(Device) │  │ Environment  │  │& Workloads │  │      │
   └─────────┘  └─────────┘  └──────────────┘  └───────────┘  └──────┘
      SSO/IAM     Intune/EDR   segmentation      appsec/         classify
      MFA/JIT     posture      private access     workload id     encrypt/DLP
   (DoD pillar names in parentheses)
```

---

## 4. Multi-cloud: one PDP, three PEP planes
```mermaid
flowchart TD
    IdP["Central IdP\nSSO + FIDO2 MFA + policy + device posture\n(PDP)"]
    IdP --> AWS["AWS PEPs\nVerified Access · VPC Lattice\nSCP/RCP · GuardDuty"]
    IdP --> AZ["Azure PEPs\nConditional Access · Global Secure Access\nAzure Policy · Defender"]
    IdP --> GCP["GCP PEPs\nIAP/BeyondCorp · VPC-SC\nOrg Policy · SCC"]
    AWS --> SIEM["Unified SIEM\ncorrelate one identity across clouds"]
    AZ --> SIEM
    GCP --> SIEM
    SIEM --> RESP["Automated response\nrevoke · disable · quarantine"]
    RESP --> IdP
```

---

## 5. Maturity progression (per pillar)
```
 Traditional ──▶ Initial ──▶ Advanced ──▶ Optimal
 perimeter,      MFA rolling  centralized   fully automated,
 implicit trust  out, some    visibility,   dynamic per-request
 manual          automation   least priv    continuous verify
                 attribute    enforced      self-healing
                 policy        across pillars
        (target most orgs 2026: Advanced → Optimal, Identity first)
        (DoD: Target Level activities by 30 Sep 2027)
```
