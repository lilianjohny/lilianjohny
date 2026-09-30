# AWS Security — Hands-On Lab Track

A progressive, hands-on track to build and **prove** AWS security skills. Do them
in order — each builds on the last — or jump to the gap you're targeting.

> ⚠️ **Sandbox account you own, only.** See `../README.md` ground rules. Attack
> steps hit only the resources you just created. Tear down after every lab.

## Job-description gap → lab map
| Gap called out | Lab(s) that prove it |
|----------------|----------------------|
| Authentication / authorization | `01-authn-authz.md` |
| Container security | `02-container-image-security.md` |
| Orchestration security | `03-eks-orchestration-security.md` |
| Securing multi-tenant deployments (datacenter → cloud) | `04-multi-tenant-isolation.md` |
| Network segmentation (construction → multi-tenant use) | `05-network-segmentation.md` |
| End-to-end detection & response | `06-detection-and-response-capstone.md` |

## Recommended order
```
00 Sandbox setup ─▶ 01 AuthN/AuthZ ─▶ 02 Container image ─▶ 03 EKS orchestration
                                                                   │
        06 Detection & response  ◀── 05 Network segmentation ◀── 04 Multi-tenant
        (capstone: tie it together)
```
- **00** is a one-time safety foundation (budget alarms, guardrails, an admin +
  a low-priv identity). Do it first.
- **01** (identity) underpins everything — the JD's authN/authZ line and the
  foundation of Zero Trust (`../../zero-trust/`).
- **02 → 03** are the container + orchestration core (the biggest JD gaps).
- **04 → 05** are the datacenter/multi-tenant + segmentation story.
- **06** is a capstone: detect and respond to an attack across the stack.

## Labs
| # | Lab | Skills | Est. time | Cost risk |
|---|-----|--------|-----------|-----------|
| 00 | [Sandbox setup & guardrails](00-sandbox-setup.md) | account hardening, budgets, IAM Identity Center | 45–60 min | ~$0 |
| 01 | [Authentication & authorization](01-authn-authz.md) | IAM policies, roles, MFA, Cognito, least privilege | 2–3 h | ~$0 |
| 02 | [Container image security](02-container-image-security.md) | ECR, image scanning, SBOM, signing, hardening | 2–3 h | ~$0–1 |
| 03 | [EKS orchestration security](03-eks-orchestration-security.md) | EKS, RBAC, IRSA, network policy, pod security | 3–4 h | **$$ (EKS/NAT)** |
| 04 | [Multi-tenant isolation](04-multi-tenant-isolation.md) | tenant isolation models, IAM/network/data boundaries | 2–3 h | ~$0–1 |
| 05 | [Network segmentation](05-network-segmentation.md) | VPC design, SGs, private access, egress control | 2–3 h | ~$1–2 (NAT/endpoints) |
| 06 | [Detection & response capstone](06-detection-and-response-capstone.md) | GuardDuty, CloudTrail, hunting, automated response | 3–4 h | ~$1–3 |
| 07 | [CloudWatch observability & response](07-cloudwatch-observability.md) | CloudWatch agent, alarms, dashboards, EventBridge→Lambda→SNS | 2–3 h | ~$0–1 |
| 08 | [Disaster recovery & RTO/RPO](08-disaster-recovery.md) | AWS Backup, cross-region, Elastic DR, DR exercise | 3–4 h | ~$1–3 |
| 09 | [Windows, AD, DISA STIG & RMF](09-windows-ad-stig-rmf.md) | Windows Server, AD/GPO/DNS/IIS, PKI/CAC, STIG, RMF evidence | 3–4 h | ~$1–2 |

> Labs 07–09 target the **KBR Cloud Engineer (AWS GovCloud)** profile — see
> [`../../job-tracks/kbr-cloud-engineer.md`](../../job-tracks/kbr-cloud-engineer.md).

## Tooling you'll use
- **AWS CLI v2** (`aws configure sso` — never long-lived root/user keys).
- **This toolkit** to *verify* your hardening:
  - `../../cloud/aws/iam_audit.py`, `s3_public_check.py`, `sg_audit.py`
  - `../../cloud/ciem/aws_least_privilege.py`
  - `../../cloud/detection/aws_detection_coverage.py`, `cloudtrail_hunt.md`
  - `../../cloud/prowler_scan.sh`, `../../cloud/benchmarks/cis_benchmark.sh`
  - container: `../../appsec/`, `../../devsecops/`, `../../dod/scripts/generate_sbom.sh`
- **Optional:** `eksctl`, `kubectl`, `helm` (Lab 03); `docker`/`trivy`/`grype`/
  `syft`/`cosign` (Lab 02) — each lab lists what it needs and how to install.

## Progress & portfolio
Track completion and evidence in [`PROGRESS.md`](PROGRESS.md). For each lab,
capture: a short writeup (attack → fix → verification), an architecture diagram,
and the hardened config/IaC. That collection *is* your portfolio.
