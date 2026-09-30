# Azure Security — Hands-On Lab Track

A progressive, hands-on track to build and **prove** Azure security skills.
Mirrors the AWS track (`../aws/`) one-to-one so you learn the *concepts* once and
map them across clouds. Do them in order, or jump to a specific gap.

> ⚠️ **Sandbox subscription you own, only.** See `../README.md` ground rules.
> Attack steps hit only the resources you just created. Tear down after each lab.

## Job-description gap → lab map
| Gap called out | Lab |
|----------------|-----|
| Authentication / authorization | `01-authn-authz.md` |
| Container security | `02-container-image-security.md` |
| Orchestration security | `03-aks-orchestration-security.md` |
| Securing multi-tenant deployments | `04-multi-tenant-isolation.md` |
| Network segmentation (construction → multi-tenant) | `05-network-segmentation.md` |
| Detection & response | `06-detection-and-response-capstone.md` |

## AWS → Azure concept map (so skills transfer)
| Concept | AWS | Azure |
|---------|-----|-------|
| Account boundary | Account / Organizations | Subscription / Management Groups |
| Identity plane | IAM + Identity Center | Microsoft Entra ID |
| Authorization | IAM policies | Azure RBAC (+ Entra roles) |
| JIT privilege | Identity Center JIT | Entra **PIM** |
| Workload identity | IAM roles / IRSA | Managed identities / **Workload Identity** |
| Guardrails | SCP / RCP | **Azure Policy** (management-group scope) |
| Registry | ECR | **ACR** |
| Kubernetes | EKS | **AKS** |
| Private service access | VPC endpoints / PrivateLink | **Private Endpoint / Private Link** |
| Detection | GuardDuty | **Defender for Cloud** + **Microsoft Sentinel** |
| Access to VMs | SSM Session Manager | **Azure Bastion** / Just-in-time VM access |

## Labs
| # | Lab | Skills | Est. time | Cost risk |
|---|-----|--------|-----------|-----------|
| 00 | [Sandbox setup & guardrails](00-sandbox-setup.md) | subscription hardening, budgets, Entra, PIM | 45–60 min | ~$0 |
| 01 | [Authentication & authorization](01-authn-authz.md) | RBAC, Conditional Access, PIM, managed identity, Entra External ID | 2–3 h | ~$0 |
| 02 | [Container image security](02-container-image-security.md) | ACR, Defender for Containers, Trivy, SBOM, signing | 2–3 h | ~$0–1 |
| 03 | [AKS orchestration security](03-aks-orchestration-security.md) | AKS, RBAC, workload identity, Azure Policy/Gatekeeper, network policy | 3–4 h | **$$ (AKS/LB)** |
| 04 | [Multi-tenant isolation](04-multi-tenant-isolation.md) | mgmt groups, RBAC scoping, per-tenant keys | 2–3 h | ~$0–1 |
| 05 | [Network segmentation](05-network-segmentation.md) | vNet, NSGs, Private Link, Azure Firewall, Bastion | 2–3 h | ~$1–3 (Firewall/Bastion) |
| 06 | [Detection & response capstone](06-detection-and-response-capstone.md) | Defender, Sentinel, KQL hunting, Logic Apps response | 3–4 h | ~$1–3 |

> **Each lab is copy-paste runnable:** every step has the actual `az` CLI
> commands inline, with the Azure Portal click-path wherever a portal is the
> natural way to do it. Run `az login` and set `SUB`, `LOCATION` from Lab 00 first.

## Tooling you'll use
- **Azure CLI** (`az login` — no static secrets; use your Entra user / managed identity).
- **This toolkit** to verify: `../../cloud/azure/*.sh`, `../../cloud/prowler_scan.sh`
  (Azure checks), `../../cloud/benchmarks/`, `../../iam/policies/azure-policy-baseline.md`,
  container tools in `../../appsec/` and `../../devsecops/`.
- **Optional:** `kubectl`, `helm` (Lab 03); `docker`/`trivy`/`syft`/`cosign` (Lab 02).

## Progress & portfolio
Track completion in [`PROGRESS.md`](PROGRESS.md). Capture a writeup, a diagram,
and the hardened config per lab.
