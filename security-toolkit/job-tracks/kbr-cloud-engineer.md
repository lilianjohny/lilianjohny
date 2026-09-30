# KBR — Cloud Engineer (AWS GovCloud · Navy AvPLM · IL5/6)

**Role:** engineer, administer, secure, monitor, and sustain AWS GovCloud
infrastructure for Navy/DoD aviation systems at Impact Levels 5–6; CloudWatch
specialist; Windows/Linux; containers/Kubernetes; disaster recovery; DISA STIG /
RMF / FedRAMP compliance.
**Certs required:** AWS Certified SysOps Administrator – Associate; CompTIA
Security+ (or IAT Level II). **Preferred:** AWS Solutions Architect – Associate.

> This track shows exactly where the portfolio proves each requirement.
> Legend: ✅ covered by existing work · 🆕 tool/lab built to close a gap · 📁 reference doc.

## Requirement → evidence matrix

### AWS GovCloud infrastructure administration
| JD requirement | Evidence |
|----------------|----------|
| EC2 / S3 / FSx / VPC lifecycle admin | 📁 `../labs/aws/05-network-segmentation.md`, `../cloud/aws/sg_audit.py`, `../cloud/aws/s3_public_check.py` ✅ |
| Secure VPC (subnets, route tables, SGs, NACLs, TGW) | ✅ `../cloud/aws/sg_audit.py`; 📁 `../labs/aws/05-network-segmentation.md` |
| IAM least privilege | ✅ `../cloud/aws/iam_audit.py`, `../cloud/ciem/aws_least_privilege.py`; 📁 `../labs/aws/01-authn-authz.md` |
| IaC (Terraform + CloudFormation) | ✅ `../iam/terraform/aws/`, `../cloud/iac/iac_scan.sh` (+ checkov CI) |
| Python/Bash automation | ✅ entire toolkit (exit-code contract, `lib/common.py`) |
| AWS Systems Manager (config, patch, automation) | 🆕 **`../cloud/aws/ssm_patch_audit.py`** |

### CloudWatch monitoring & alerting  *(core specialty — was a gap)*
| JD requirement | Evidence |
|----------------|----------|
| CloudWatch + Logs + EventBridge monitoring | 🆕 **`../cloud/aws/cloudwatch_audit.py`** |
| Unified agent across VM fleets | 🆕 covered in lab 🆕 **`../labs/aws/07-cloudwatch-observability.md`** |
| Dashboards (KPIs, health, DR readiness) | 🆕 `cloudwatch_audit.py` (dashboard presence) + lab 07 |
| Log groups, metric filters, alarms, alerting | 🆕 `cloudwatch_audit.py` (retention, filters, silent alarms) |
| Event-driven remediation (Alarms→Lambda→SNS→ITSM) | 🆕 lab 07 builds this; `cloudwatch_audit.py` checks SNS/EventBridge wiring |

### Windows Server administration  *(was a gap)*
| JD requirement | Evidence |
|----------------|----------|
| Windows Server on EC2, AD, GPO, DNS, IIS | 🆕 **`../labs/aws/09-windows-ad-stig-rmf.md`** |
| DoD PKI / CAC integration | 🆕 lab 09 (PKI/CAC section) |
| OS patching / vuln remediation (SSM/WSUS) | 🆕 `../cloud/aws/ssm_patch_audit.py` + lab 09 |

### Containers & Kubernetes
| JD requirement | Evidence |
|----------------|----------|
| EKS / self-managed K8s, pods/deploy/svc/ingress/RBAC | ✅ `../cloud/kubernetes/kube_security_scan.sh`; 📁 `../labs/aws/03-eks-orchestration-security.md` |
| Docker image hardening (DoD DevSecOps) | ✅ `../labs/aws/02-container-image-security.md`, `../dod/scripts/generate_sbom.sh`, `../appsec/` |
| ECR secure registry | ✅ lab 02 (ECR lockdown) |
| Helm lifecycle | 📁 lab 03 (stretch) |

### Disaster recovery & contingency  *(core — was a gap)*
| JD requirement | Evidence |
|----------------|----------|
| AWS Backup / Elastic DR / multi-region | 🆕 **`../cloud/dr/dr_readiness.py`** |
| Align configs to documented RTO/RPO | 🆕 `dr_readiness.py` register validation (RPO vs backup interval) |
| Plan/execute/document DR exercises | 🆕 **`../labs/aws/08-disaster-recovery.md`** |
| Verify failover / recovery gaps | 🆕 lab 08 |

### Cybersecurity & compliance
| JD requirement | Evidence |
|----------------|----------|
| DISA STIG hardening (cloud/Windows/Linux/containers) | 🆕 **`../compliance/stig/stig_eval.py`**; 📁 `../dod/` STIG gate |
| FedRAMP / NIST 800-53 | ✅ `../soc/frameworks/control_mapping.csv`, `../grc/compliance/crosswalk.py`, `../soc-reports/` |
| Log aggregation / retention compliance | 🆕 `cloudwatch_audit.py` (retention vs DoD baseline) |
| RMF A&A / continuous monitoring | ✅ `../soc/` (conmon, poam), `../dod/evidence/collect_cato_evidence.sh` |
| Vulnerability remediation / evidence | ✅ `../vulnmgmt/`, `../soc-reports/evidence/` |

## Tools built to close the gaps (run them)
```bash
# CloudWatch observability coverage (DoD-style 365-day retention)
python3 cloud/aws/cloudwatch_audit.py --region us-gov-west-1 --min-retention-days 365

# SSM patch / managed-instance compliance
python3 cloud/aws/ssm_patch_audit.py --region us-gov-west-1

# DR readiness — validate an RTO/RPO register (offline) + live AWS Backup
python3 cloud/dr/dr_readiness.py --register cloud/dr/dr_register.example.csv --aws --region us-gov-west-1

# DISA STIG .ckl evaluation / CI gate (fail on open CAT I)
python3 compliance/stig/stig_eval.py compliance/stig/sample.example.ckl --fail-on cat1
```

## Labs to do (produce portfolio artifacts)
1. `../labs/aws/00`–`06` — the AWS foundation (identity, container, EKS, segmentation, detection).
2. 🆕 `../labs/aws/07-cloudwatch-observability.md` — build the monitoring stack.
3. 🆕 `../labs/aws/08-disaster-recovery.md` — AWS Backup + DR exercise with RTO/RPO.
4. 🆕 `../labs/aws/09-windows-ad-stig-rmf.md` — Windows/AD on EC2, STIG, PKI/CAC, RMF evidence.

## Certs & study
- **AWS SysOps Administrator – Associate** (required) — this track's tools mirror
  the exam's monitoring/automation/DR/security domains.
- **Security+** (required, IAT II) — `../grc/`, `../soc/`, STIG/RMF content here.
- **AWS Solutions Architect – Associate** (preferred).

## Interview talking points
- "I built a CloudWatch coverage auditor that flags never-expiring log groups,
  silent alarms, and missing metric filters — the monitoring gaps that bite IL5/6
  systems on retention and alerting."
- "My DR tool validates a system's RTO/RPO register against actual backup
  frequency and cross-region posture, so I can prove an objective is *achievable*,
  not just documented."
- "I gate pipelines on DISA STIG `.ckl` results — open CAT I fails the build."
