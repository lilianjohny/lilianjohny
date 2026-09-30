# Zero Trust on Google Cloud (2026)

Google pioneered Zero Trust with **BeyondCorp**. On GCP the PDP is Cloud
Identity/your IdP + **Access Context Manager**; PEPs are **BeyondCorp Enterprise
/ Identity-Aware Proxy** and **VPC Service Controls**.

## Pillar → GCP service map
| Pillar | GCP building blocks |
|--------|---------------------|
| **Identity** | Cloud Identity / Workforce Identity Federation (SSO), phishing-resistant MFA, IAM, **PAM** (JIT), IAM Recommender |
| **Devices** | Endpoint Verification, **Context-Aware Access** device conditions (BeyondCorp) |
| **Networks** | VPC firewall (default-deny), **VPC Service Controls** (data-exfil perimeter), Private Google Access / Private Service Connect, Cloud Armor |
| **Applications & Workloads** | **Identity-Aware Proxy (IAP)** / BeyondCorp Enterprise (no VPN), workload identity, Apigee |
| **Data** | CMEK/KMS, **DLP (Sensitive Data Protection)**, public access prevention, VPC-SC around data |
| **Visibility & Analytics** | Cloud Audit Logs, **Security Command Center**, Chronicle (SIEM) |
| **Automation & Orchestration** | SCC + Cloud Functions/Workflows automated response |
| **Governance** | Org Policy, resource hierarchy (org/folder/project) |

## The PDP/PEP realization
```
  User/workload
      │
      ▼
  PEP:  Identity-Aware Proxy (IAP) / BeyondCorp Enterprise  |  VPC Service Controls perimeter
      │      enforces identity + device + context per request
      ▼
  PDP:  Cloud Identity / Workforce Identity Fed (SSO, FIDO2)  +  Access Context Manager
      │  access levels: device posture, IP/geo, time — evaluated per request
      ▼
  Resource  →  IAM (least privilege, +PAM JIT)  →  bounded by Org Policy + VPC-SC
      │
      ▼
  Cloud Audit Logs → Security Command Center → automated response (Functions)
```

## Key moves (in order)
1. **Identity first:** Workforce Identity Federation / Cloud Identity SSO,
   **phishing-resistant MFA**, IAM by group, **PAM** JIT, zero standing privilege
   (`../../sso/architecture/gcp.md`, `../../iam/architecture/gcp.md`).
2. **Context-Aware Access (the PDP rules):** define **access levels** in **Access
   Context Manager** (require Endpoint-Verification device posture, corporate
   IP/geo, etc.) and bind them to resources/apps.
3. **BeyondCorp / IAP for apps (no VPN):** front internal web apps and SSH/TCP with
   **IAP** — access requires verified identity + device + access level, per request,
   with no network trust.
4. **VPC Service Controls:** draw a **service perimeter** around sensitive data
   services to stop exfiltration even with valid credentials; bridge perimeters
   deliberately.
5. **Network pillar:** default-deny VPC firewall, Private Google Access / Private
   Service Connect (no public data planes), Cloud Armor on public edges.
6. **Data pillar:** CMEK/KMS, **Sensitive Data Protection (DLP)** for
   classification/redaction, public access prevention (org policy), data inside VPC-SC.
7. **Org policies (guardrails):** disable SA key creation, restrict resource
   locations, enforce public access prevention
   (`../../iam/terraform/gcp/main.tf`).
8. **Visibility:** Cloud Audit Logs (Admin Activity always on) + **Security
   Command Center** + Chronicle; alert on IAM/org-policy/perimeter changes.
9. **Automate:** SCC findings → Cloud Functions/Workflows to revoke, quarantine,
   or open tickets.

## Continuous verification
- Access levels are evaluated **per request**; a device falling out of compliance
  loses access on the next check.
- IAM Recommender continuously proposes least-privilege reductions.

## Verify with the toolkit
- `../../cloud/gcp/*.sh` (firewall audit, posture)
- `../../cloud/prowler_scan.sh` (GCP checks), `../../cloud/benchmarks/`
- `../../iam/policies/gcp-org-policy-baseline.md` (guardrails)

## Anti-patterns
- ❌ Exposing apps on public IPs instead of behind IAP/BeyondCorp.
- ❌ No VPC Service Controls around sensitive data (credential theft = exfil).
- ❌ Exported service-account keys (org policy should forbid).
- ❌ Primitive roles (Owner/Editor) at org/folder scope.
