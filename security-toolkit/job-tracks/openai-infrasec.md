# OpenAI — Security Engineer, Infrastructure Security (InfraSec)

**Role:** design and build security controls across diverse layers — physical
hardware, firmware/BMC, OS, Kubernetes, networks, CI/CD — to protect GPU
supercomputing clusters, multi-cloud infrastructure, datacenters, and sensitive
model weights, against sophisticated adversaries and insiders. Generalist,
automation-first, scalable.

> Legend: ✅ covered · 🆕 built to close a gap · 📁 reference.

## Requirement → evidence matrix
| JD requirement | Evidence |
|----------------|----------|
| Security of cloud platforms (AWS, Azure), **multi-cloud networks & infra**, cloud-agnostic design | ✅ `../cloud/multicloud/`, `../labs/multicloud/`, `../zero-trust/architecture/multicloud.md` |
| **Securing on-prem deployments & datacenters, construction → multi-tenant** | 🆕 **`../labs/onprem/`** (new track: datacenter build, bare-metal/firmware, multi-tenant) |
| **Container security** | ✅ `../labs/aws/02`, `../labs/azure/02`, `../labs/gcp/02`, `../appsec/`, `../dod/scripts/generate_sbom.sh` |
| **Orchestration security** | ✅ `../cloud/kubernetes/kube_security_scan.sh`, `../labs/*/03` (EKS/AKS/GKE), `../cloud/kubernetes/policies/` |
| **Authentication / authorization** | ✅ `../iam/`, `../sso/`, `../labs/*/01`, `../zero-trust/policies/opa-abac-example.rego` |
| Network isolation | ✅ `../labs/*/05` segmentation; 🆕 `../labs/onprem/` (datacenter segmentation) |
| **Secret management** | 🆕 **`../labs/onprem/03-secret-management.md`** + ✅ Vault/KMS patterns in `../labs/*/02` |
| **Machine identity** | ✅ `../iam/` (workload identity, OIDC/WIF), `../labs/multicloud/03-cross-cloud-workload-identity.md` |
| Checkpoint encryption (model-weight protection) | 🆕 `../labs/onprem/04-sensitive-data-protection.md` (encryption-at-rest/in-transit for large artifacts) |
| Firmware / BMC / bare-metal security | 🆕 `../labs/onprem/02-baremetal-firmware.md` |
| CI/CD security | ✅ `../cloud/cicd/pipeline_gate.sh`, `../devsecops/`, `../dod/pipeline/` |
| Automation & tooling to close gaps | ✅ the entire CLI toolkit (consistent exit-code contract) |
| Insider-threat / detection | ✅ `../cloud/detection/`, `../soc/`, `../labs/*/06` |

## Gap analysis
This role is the closest to your existing portfolio — container, orchestration,
authN/authZ, multi-cloud, and CI/CD are already strong. The genuine gaps are the
**physical/on-prem** side (datacenter construction → multi-tenant, bare-metal,
firmware/BMC) and dedicated **secret-management** and **sensitive-data
(model-weight) protection** labs. Those are the 🆕 `../labs/onprem/` track.

## Labs to do
1. ✅ `../labs/*/02`, `03`, `04` (container, orchestration, multi-tenant) across AWS/Azure/GCP.
2. ✅ `../labs/multicloud/` (unified identity, keyless CI/CD, cross-cloud workload identity, ZT capstone).
3. 🆕 `../labs/onprem/01`–`04` (datacenter security, bare-metal/firmware, secret management, sensitive-data protection).

## Certs & study
No certs required; this is a build/design role. Strongest signals: hands-on
multi-cloud + Kubernetes security, and the on-prem/datacenter depth from the new
track. Lead with the **`../labs/multicloud/05-zero-trust-multicloud-capstone.md`**
and the on-prem track artifacts.

## Interview talking points
- "I can reason about security from bare metal and firmware up through Kubernetes
  and multi-cloud — here's my on-prem datacenter track alongside my cloud tracks."
- "For model-weight-style sensitive artifacts I treat it as a data-protection
  problem: encryption at rest/in transit, tight machine identity, and network
  isolation with default-deny — and I verify each with tooling."
- "I close gaps with automation — every control I add ships with a checker that
  fails CI when the control regresses."
