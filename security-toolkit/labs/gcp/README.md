# Google Cloud Security — Hands-On Lab Track

A progressive, hands-on track to build and **prove** GCP security skills. Mirrors
the AWS (`../aws/`) and Azure (`../azure/`) tracks so concepts transfer. Do in
order or jump to a gap.

> ⚠️ **Sandbox project you own, only.** See `../README.md` ground rules. Attack
> steps hit only what you just created. Tear down after each lab.

## Job-description gap → lab map
| Gap called out | Lab |
|----------------|-----|
| Authentication / authorization | `01-authn-authz.md` |
| Container security | `02-container-image-security.md` |
| Orchestration security | `03-gke-orchestration-security.md` |
| Securing multi-tenant deployments | `04-multi-tenant-isolation.md` |
| Network segmentation | `05-network-segmentation.md` |
| Detection & response | `06-detection-and-response-capstone.md` |

## AWS → Azure → GCP concept map
| Concept | AWS | Azure | GCP |
|---------|-----|-------|-----|
| Account boundary | Account/Org | Subscription/Mgmt Group | **Project / Folder / Org** |
| Identity plane | IAM+Identity Center | Entra ID | **Cloud Identity / IAM** |
| JIT privilege | Identity Center JIT | Entra PIM | **PAM (Privileged Access Manager)** |
| Workload identity | IAM roles/IRSA | Managed identity | **Workload Identity Federation / GKE Workload Identity** |
| Guardrails | SCP/RCP | Azure Policy | **Org Policy** |
| Registry | ECR | ACR | **Artifact Registry** |
| Kubernetes | EKS | AKS | **GKE** |
| Image admission | (Ratify) | (Ratify/Gatekeeper) | **Binary Authorization** |
| Private service access | VPC endpoints | Private Endpoint | **Private Google Access / PSC** |
| Data perimeter | RCP | Priv Endpoint+firewall | **VPC Service Controls** |
| Detection | GuardDuty | Defender+Sentinel | **Security Command Center + Chronicle** |
| Access to VMs | SSM | Bastion | **IAP TCP forwarding** |

## Labs
| # | Lab | Skills | Est. time | Cost risk |
|---|-----|--------|-----------|-----------|
| 00 | [Sandbox setup & guardrails](00-sandbox-setup.md) | project hardening, budgets, org policy, Cloud Identity | 45–60 min | ~$0 |
| 01 | [Authentication & authorization](01-authn-authz.md) | IAM, service accounts, WIF, PAM, Identity Platform | 2–3 h | ~$0 |
| 02 | [Container image security](02-container-image-security.md) | Artifact Registry, Artifact Analysis, Binary Authorization, cosign | 2–3 h | ~$0–1 |
| 03 | [GKE orchestration security](03-gke-orchestration-security.md) | GKE, RBAC, Workload Identity, PSA, network policy, Binary Auth | 3–4 h | **$$ (GKE/LB)** |
| 04 | [Multi-tenant isolation](04-multi-tenant-isolation.md) | folders/projects, IAM scoping, CMEK, VPC-SC | 2–3 h | ~$0–1 |
| 05 | [Network segmentation](05-network-segmentation.md) | VPC, firewall, Private Google Access, PSC, Cloud NAT, shared VPC | 2–3 h | ~$1–2 |
| 06 | [Detection & response capstone](06-detection-and-response-capstone.md) | SCC, Cloud Audit Logs, hunting, automated response | 3–4 h | ~$1–3 |

> **Each lab is copy-paste runnable:** every step has the actual `gcloud`
> commands inline, with the Cloud Console click-path wherever a console is the
> natural way to do it. Run `gcloud auth login` and set `PROJECT`, `REGION` from
> Lab 00 first.

## Tooling you'll use
- **gcloud CLI** (`gcloud auth login` — short-lived; no exported SA keys).
- **This toolkit** to verify: `../../cloud/gcp/*.sh`, `../../cloud/prowler_scan.sh`
  (GCP checks), `../../cloud/benchmarks/`, `../../iam/policies/gcp-org-policy-baseline.md`,
  container tools in `../../appsec/` and `../../devsecops/`.
- **Optional:** `kubectl`, `helm` (Lab 03); `docker`/`trivy`/`syft`/`cosign` (Lab 02).

## Progress & portfolio
Track completion in [`PROGRESS.md`](PROGRESS.md).
