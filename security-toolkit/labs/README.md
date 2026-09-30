# Hands-On Security Labs

Practice labs to build **demonstrable, portfolio-ready** cloud-security skills by
doing — build a realistic setup, attack/observe it, harden it, and verify the fix
with the tools in this toolkit.

> ⚠️ **Run only in your own sandbox account.** Every lab is designed to be built
> and destroyed in an isolated account **you own**. Never point these at
> employer, client, or shared production resources. Attack steps target only the
> resources *you* just created. Clean up (teardown) at the end of every lab —
> both for security hygiene and to avoid cloud charges.

## Tracks
| Track | Status | Focus |
|-------|--------|-------|
| [`aws/`](aws/) | ✅ available | AWS security — start here; maps to the job-description gaps below |
| [`azure/`](azure/) | ✅ available | Azure equivalents (Entra, AKS, Azure Policy, Sentinel) |
| [`gcp/`](gcp/) | ✅ available | GCP equivalents (IAM/WIF, GKE, Org Policy, SCC) |
| [`multicloud/`](multicloud/) | ✅ available | Securing all three as one system (do after the per-cloud tracks) |
| [`onprem/`](onprem/) | ✅ available | On-prem & datacenter (construction→multi-tenant, bare-metal/firmware, secrets, sensitive-data) |
| [`soc/`](soc/) | ✅ available | SOC & incident response (IR lifecycle, alert triage, M365/Entra hardening) |

Each per-cloud track mirrors the same 7 labs (00–06), so you learn the concept
once and map it across clouds. The `multicloud/` track then unifies them:
federated SSO, keyless CI/CD, single-pane posture, cross-cloud workload identity,
unified detection, and a Zero Trust capstone.

## Why these labs (the job-description gaps)
Built to close the exact skills a role called out. The AWS track targets:
- **Container security** → `aws/02-container-image-security.md`
- **Orchestration security** → `aws/03-eks-orchestration-security.md`
- **Authentication / authorization** → `aws/01-authn-authz.md`
- **Securing multi-tenant deployments / datacenter → cloud** →
  `aws/04-multi-tenant-isolation.md`, `aws/05-network-segmentation.md`

## How each lab is structured
Every lab follows the same arc so you build muscle memory:
1. **Skills practiced** — mapped to the JD line it proves.
2. **Objective & scenario** — what you're securing and why.
3. **Est. time / cost** — plan your session; keep spend near-zero.
4. **Prerequisites** — tools + IAM permissions.
5. **Part A — Build** — stand up a realistic (often deliberately weak) setup.
6. **Part B — Attack / observe** — see the weakness the way an attacker would.
7. **Part C — Harden** — fix it, secure-by-design.
8. **Part D — Verify** — prove the fix, using this toolkit's scanners.
9. **Cleanup** — tear it all down.
10. **Portfolio artifact** — what to capture (writeup, diagram, hardened IaC).
11. **Stretch goals** — go further.

## Track your progress
Use [`aws/PROGRESS.md`](aws/PROGRESS.md) to check off labs and record evidence
links for your portfolio.

## Ground rules
- **Own it:** sandbox account only; you're authorized because it's yours.
- **Least cost:** prefer free-tier; EKS/NAT/ALB cost money — do those in one
  sitting and tear down immediately (each lab flags cost drivers).
- **Least privilege for yourself:** don't practice as account root; use an
  admin-scoped IAM Identity Center user for setup and a lower-priv role to test.
- **Capture as you go:** screenshots + notes become your portfolio writeups.
