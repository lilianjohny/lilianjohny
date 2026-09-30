# Zero Trust on AWS (2026)

Map the NIST 800-207 PDP/PEP model onto AWS services. The PDP is your IdP
(Identity Center + external IdP) plus policy; the PEPs are the AWS services that
enforce identity-aware, per-request access.

## Pillar → AWS service map
| Pillar | AWS building blocks |
|--------|---------------------|
| **Identity** | IAM Identity Center (SSO), external IdP + phishing-resistant MFA, IAM roles, JIT, IAM Access Analyzer |
| **Devices** | Device trust via IdP/Intune signals; **AWS Verified Access** device posture (trust providers) |
| **Networks** | Segmented VPCs, Security Groups (default-deny), **VPC Lattice** (identity-aware service-to-service), PrivateLink, no public admin planes, WAF |
| **Applications & Workloads** | **AWS Verified Access** (identity+device-aware app access, no VPN), API Gateway authorizers, IRSA/Pod Identity, Cognito |
| **Data** | KMS encryption everywhere, S3 Block Public Access, Macie (classification/DLP), RCPs (data perimeter) |
| **Visibility & Analytics** | CloudTrail (all accounts→Log Archive), GuardDuty, Security Hub, Config, Detective |
| **Automation & Orchestration** | EventBridge + Lambda/SSM automated response, Security Hub automation rules |
| **Governance** | Organizations, SCP + RCP guardrails, Control Tower |

## The PDP/PEP realization
```
  User/workload
      │
      ▼
  PEP:  AWS Verified Access (app)  |  VPC Lattice (service-to-service)  |  API GW authorizer
      │           enforces identity + device posture per request
      ▼
  PDP:  IAM Identity Center + external IdP (SSO, FIDO2 MFA)  +  Verified Access policy (Cedar)
      │  signals: IdP groups, device trust provider, request context
      ▼
  Resource in a segmented VPC  →  short-lived STS creds  →  bounded by SCP/RCP
      │
      ▼
  CloudTrail → GuardDuty/Security Hub → EventBridge automated response
```

## Key moves (in order)
1. **Identity first:** external IdP → **IAM Identity Center**, phishing-resistant
   MFA, permission sets by group, **JIT** elevation, zero standing privilege
   (`../../sso/architecture/aws.md`, `../../iam/architecture/aws.md`).
2. **Guardrails:** attach **SCPs** (deny risky actions org-wide) and **RCPs**
   (data perimeter — only your identities/networks touch your data)
   (`../../iam/policies/`).
3. **Replace VPN with Verified Access:** front internal apps with **AWS Verified
   Access**; policies (Cedar) require IdP identity **and** device posture per
   request — no network-based access.
4. **Identity-aware east-west:** use **VPC Lattice** so service-to-service calls
   are authorized by IAM/auth policy, not just SG/IP. Default-deny SGs; segment by
   workload.
5. **Private everything:** PrivateLink for service access; no public management
   endpoints; WAF on public apps.
6. **Data pillar:** KMS on all stores, S3 Block Public Access (account-level),
   **Macie** for classification/sensitive-data discovery, RCPs enforce the perimeter.
7. **Visibility:** CloudTrail (org trail → Log Archive, immutable), **GuardDuty**,
   **Security Hub**, Config; alert on identity/policy/network anomalies
   (`../../cloud/detection/aws_detection_coverage.py`, `cloudtrail_hunt.md`).
8. **Automate response:** EventBridge → Lambda/SSM to revoke sessions, isolate
   instances, disable keys on high-severity findings.

## Continuous verification
- Short session durations on permission sets; step-up for privileged actions.
- IAM Access Analyzer continuously flags external/over-broad access.
- GuardDuty behavioral findings can trigger automated session revocation.

## Verify with the toolkit
- `../../cloud/aws/iam_audit.py`, `s3_public_check.py`, `sg_audit.py`
- `../../cloud/ciem/aws_least_privilege.py` (right-size, unused access)
- `../../cloud/detection/aws_detection_coverage.py` (are the eyes on?)
- `../../cloud/prowler_scan.sh`, `../../cloud/benchmarks/cis_benchmark.sh`

## Anti-patterns
- ❌ "It's in the VPC, so it's trusted." Network position ≠ authorization.
- ❌ VPN that grants broad network access instead of per-app Verified Access.
- ❌ Long-lived IAM user keys for workloads (use roles / IRSA / OIDC).
- ❌ Public S3 / public RDS / public management endpoints.
