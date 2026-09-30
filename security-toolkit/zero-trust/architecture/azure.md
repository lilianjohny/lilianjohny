# Zero Trust on Azure (2026)

Azure's Zero Trust story centers on **Microsoft Entra ID** as the PDP and
**Conditional Access (CA)** as the per-request policy engine, with Defender and
network controls covering the other pillars.

## Pillar → Azure service map
| Pillar | Azure building blocks |
|--------|----------------------|
| **Identity** | Entra ID (SSO), **Conditional Access**, phishing-resistant MFA, **PIM** (JIT), Identity Protection (risk), Entra ID Governance (access reviews) |
| **Devices** | Intune (compliance policies), device-based CA, Defender for Endpoint (signals) |
| **Networks** | NSGs (default-deny), Azure Firewall, **Private Link/Private Endpoints**, no public mgmt, DDoS, segmentation by subscription/vNet |
| **Applications & Workloads** | Entra app proxy / **Global Secure Access**, app registrations w/ per-request authz, managed identities, API Management |
| **Data** | Encryption + Key Vault, **Microsoft Purview** (classification/DLP), storage firewall, Defender for Storage |
| **Visibility & Analytics** | Entra sign-in/audit logs, **Microsoft Sentinel** (SIEM), Defender for Cloud, Log Analytics |
| **Automation & Orchestration** | Sentinel playbooks (Logic Apps), Defender automated response |
| **Governance** | Management groups, **Azure Policy**, Entra ID Governance |

## The PDP/PEP realization
```
  User/workload
      │
      ▼
  PEP:  Global Secure Access / App Proxy  |  API Management  |  service front doors
      │        Conditional Access evaluated on EVERY sign-in
      ▼
  PDP:  Entra ID (SSO, FIDO2 MFA)  +  Conditional Access policy engine
      │  signals: user/sign-in risk (Identity Protection), device compliance (Intune),
      │           location, application sensitivity, session controls
      ▼
  Resource  →  RBAC (+ PIM for privileged)  →  bounded by Azure Policy
      │
      ▼
  Entra logs + Defender → Sentinel → automated playbook response
```

## Key moves (in order)
1. **Identity first:** Entra SSO, **phishing-resistant MFA**, **block legacy auth**,
   privileged roles **PIM-eligible** (JIT), zero standing privilege
   (`../../sso/architecture/azure.md`, `../../iam/architecture/azure.md`).
2. **Conditional Access = the PDP rules.** Baseline policies (see
   `../policies/conditional-access-baseline.md`): require MFA, require compliant/
   hybrid-joined device for sensitive apps, block legacy auth, block/ step-up on
   risk, set sign-in frequency, restrict by location. **Roll out report-only first.**
3. **Device pillar:** enrol devices in **Intune**, define compliance policies,
   make device compliance a required CA condition.
4. **Network pillar:** NSGs default-deny, **Private Endpoints** for PaaS (no public
   data planes), Azure Firewall egress control, segment by subscription/vNet, no
   public management ports (use Bastion/JIT VM access).
5. **App/workload pillar:** front internal apps with **Global Secure Access / App
   Proxy** (identity+device-aware, no VPN); workloads use **managed identities**
   (no secrets); API Management enforces per-request authz.
6. **Data pillar:** Key Vault + encryption, **Purview** classification + DLP,
   storage account firewalls, Defender for Storage.
7. **Visibility:** stream Entra + resource logs to **Sentinel**; enable Defender
   for Cloud; alert on Global-Admin use, CA changes, risky sign-ins, new admins.
8. **Automate:** Sentinel playbooks to revoke sessions / require re-auth / disable
   accounts on high-severity detections.

## Continuous verification
- CA **sign-in frequency** + **continuous access evaluation (CAE)** revoke access
  mid-session when risk changes (e.g., token revoked on user disable).
- Identity Protection feeds real-time user/sign-in risk into CA decisions.

## Verify with the toolkit
- `../../cloud/azure/*.sh` (NSG audit, posture)
- `../../cloud/prowler_scan.sh` (Azure checks), `../../cloud/benchmarks/`
- `../../iam/policies/azure-policy-baseline.md` (guardrails)

## Anti-patterns
- ❌ Legacy/basic auth left on (bypasses MFA and CA).
- ❌ Standing Global Admins instead of PIM.
- ❌ Public PaaS endpoints instead of Private Link.
- ❌ CA policies with no break-glass exclusion (lockout risk).
