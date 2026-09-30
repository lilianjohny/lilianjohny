# Zero Trust — Policy, Architecture, Diagrams & Implementation (2026)

**Never trust, always verify.** No implicit trust from network location; every
access request is authenticated, authorized, and continuously evaluated against
identity, device, and context signals — per request, least privilege, assume
breach.

This section gives you the **policy**, the **architecture**, the **diagrams**,
and the **implementation process** to apply Zero Trust in **AWS**, **Azure**,
**Google Cloud**, and a **multi-cloud** estate — aligned to the standards that
actually govern this in 2026.

> ⚠️ **Authorized use only.** Reference designs and policy-as-code for
> environments **you own or are contracted to secure**. Zero Trust changes how
> access is granted everywhere — roll out in report-only/audit mode first.

## Standards this is aligned to (2026)
| Standard | What it gives us |
|----------|------------------|
| **NIST SP 800-207** — *Zero Trust Architecture* | The foundational model: PE/PA/PEP, tenets, deployment patterns |
| **NIST SP 800-207A** | ZTA for cloud-native / multi-location app environments (identity-based segmentation) |
| **CISA Zero Trust Maturity Model v2.0** | 5 pillars + 3 cross-cutting capabilities, 4 maturity stages (Traditional→Optimal) |
| **DoD Zero Trust Strategy / Reference Architecture** | 7 pillars, 152 activities (91 **Target** by 30 Sep 2027, 61 **Advanced** by 2032) |
| **NIST SP 800-63B** / FIDO2 | Phishing-resistant authentication assurance |

## How this fits the rest of the toolkit
Zero Trust is the **umbrella**; the other sections are its pillars:
- **Identity** → `../sso/` + `../iam/` (SSO, MFA, JIT, least privilege).
- **Devices** → device compliance / posture signals (Intune, endpoint mgmt).
- **Networks** → micro-segmentation, private access (`../cloud/`).
- **Applications & Workloads** → `../appsec/`, workload identity (`../iam/`).
- **Data** → classification, encryption, DLP (`../cloud/`, `../grc/`).
- **Visibility & Analytics** → `../cloud/detection/`, `../soc/`.
- **Automation & Orchestration** → CI gates (`../cloud/cicd/`, `../devsecops/`).
- **Governance** → `../grc/`.

## Layout
| Path | What it is |
|------|-----------|
| `policy/zero-trust-policy.md` | The Zero Trust **policy** (principles, mandates, roles, exceptions) |
| `architecture/overview.md` | NIST 800-207 model + CISA/DoD pillars, the reference architecture |
| `architecture/aws.md` | Zero Trust on AWS (VPC Lattice, verified access, IAM, GuardDuty) |
| `architecture/azure.md` | Zero Trust on Azure (Entra CA, Defender, Private Link, segmentation) |
| `architecture/gcp.md` | Zero Trust on GCP (BeyondCorp, Context-Aware Access, VPC-SC) |
| `architecture/multicloud.md` | One ZT control plane across the three clouds |
| `architecture/diagram.md` | PDP/PEP flow, per-request decision, pillar map, segmentation |
| `process/implementation.md` | Phased roadmap (assess→pilot→enforce→optimize) + maturity |
| `policies/conditional-access-baseline.md` | Baseline access-policy set (the PDP rules) |
| `policies/opa-abac-example.rego` | Policy-as-code example: ABAC decision at a PEP |
| `validation/zero_trust_maturity_check.md` | Score yourself against CISA ZTMM stages |

## The one-paragraph version
Put a **Policy Decision Point** (your IdP + policy engine) in front of every
resource via **Policy Enforcement Points**. On **every** request, verify the
identity (SSO + phishing-resistant MFA), the device (compliant/managed), and the
context (location, risk, time, sensitivity); grant **least-privilege, time-boxed**
access to *that one resource*; log everything; and re-evaluate continuously.
Network position grants nothing.
