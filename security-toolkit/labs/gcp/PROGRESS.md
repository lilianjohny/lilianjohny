# GCP Lab Track — Progress & Portfolio Tracker

Check off each lab and link the evidence you captured.

## Status
| # | Lab | JD gap proven | Done | Portfolio evidence (link) |
|---|-----|---------------|:----:|---------------------------|
| 00 | Sandbox setup & guardrails | secure foundation | ☐ | |
| 01 | Authentication & authorization | authN / authZ | ☐ | |
| 02 | Container image security | container security | ☐ | |
| 03 | GKE orchestration security | orchestration security | ☐ | |
| 04 | Multi-tenant isolation | multi-tenant deployments | ☐ | |
| 05 | Network segmentation | datacenter → multi-tenant | ☐ | |
| 06 | Detection & response (capstone) | end-to-end blue team | ☐ | |

## For each lab, capture
- [ ] Writeup (attack → fix → verification)
- [ ] Diagram (before/after or threat model)
- [ ] Hardened config/IaC (Terraform/manifests)
- [ ] Tool output (scan flagging → clean)

## Skills evidence map
| Skill claim | Backed by |
|-------------|-----------|
| "GCP IAM least privilege & keyless workloads" | Lab 01 before/after + WIF (no SA keys) |
| "Container supply-chain security + Binary Authorization" | Lab 02 scan + SBOM + attestation |
| "GKE hardening" | Lab 03 RBAC/Workload Identity/PSA/NetworkPolicy/BinAuth |
| "Multi-tenant isolation + VPC-SC" | Lab 04 isolation doc + denied crossover |
| "Secure network / segmentation" | Lab 05 VPC diagram + firewall_audit delta |
| "Cloud detection & response (SCC/Chronicle)" | Lab 06 incident report + automation |

## Notes / log
- 
