# Zero Trust Policy

**Document type:** Security Policy · **Owner:** CISO / Security Architecture ·
**Applies to:** all users, devices, workloads, networks, applications, and data
in cloud and multi-cloud environments · **Review cadence:** annual (or on
significant change).

> This is a template policy. Adapt names, roles, and thresholds to your org, run
> it through your governance process (`../../grc/governance/`), and record
> approval. It states *what must be true*; the architecture and process docs
> state *how*.

---

## 1. Purpose
Establish Zero Trust as the mandatory access-control model: eliminate implicit
trust based on network location, and require explicit, continuous verification of
every access request to every resource. Aligns the organization to NIST SP
800-207, CISA Zero Trust Maturity Model v2.0, and (where applicable) the DoD Zero
Trust Strategy.

## 2. Scope
All identities (human and non-human), endpoints, workloads, networks,
applications, APIs, and data — across AWS, Azure, Google Cloud, SaaS, and
on-premises systems that connect to them. No environment is out of scope by
virtue of being "internal."

## 3. Core principles (mandatory)
1. **Verify explicitly.** Authenticate and authorize every request using all
   available signals: identity, device health, location, workload, data
   sensitivity, and behavior/risk. No access is granted on network position alone.
2. **Use least-privilege access.** Grant the minimum permissions needed, to the
   specific resource, for the shortest time. Default to **zero standing
   privilege**; privileged access is **just-in-time** and time-boxed.
3. **Assume breach.** Design as if the attacker is already inside. Segment
   access, minimize blast radius, encrypt end-to-end, and inspect/log everything
   for detection and response.

## 4. Policy statements (what must be true)

### 4.1 Identity
- All human access uses **SSO** to the central IdP with **phishing-resistant MFA**
  (FIDO2/passkeys). SMS/voice OTP is prohibited for privileged access.
- No local/standalone accounts for humans except approved **break-glass** accounts.
- Non-human (workload/service) identities use **short-lived, federated
  credentials** (OIDC/workload identity federation). Long-lived static keys are
  prohibited; any exception is time-limited and registered.
- Privileged roles are **eligible, not standing** (JIT via Identity Center / PIM /
  PAM), requiring approval, MFA, and justification.

### 4.2 Devices
- Access to sensitive resources requires a **managed, compliant, healthy** device
  (encryption on, patched, EDR running). Device posture is a required input to the
  access decision.
- Unmanaged devices get no access, or restricted/browser-isolated access only.

### 4.3 Networks
- Network location confers **no trust**. Perimeter membership is not authorization.
- Traffic is **micro-segmented** by identity/workload; default-deny east-west.
- Administrative and sensitive access uses **private/brokered** paths (no direct
  public exposure of management planes).
- All traffic is **encrypted in transit** (TLS 1.2+/mTLS where feasible).

### 4.4 Applications & workloads
- Applications enforce authorization **per request** at a Policy Enforcement Point;
  they do not assume a trusted caller.
- Workloads authenticate to each other with verifiable identities; secrets are
  vaulted and short-lived.
- The software supply chain is verified (SBOM, signed artifacts) — see
  `../../devsecops/`, `../../dod/`.

### 4.5 Data
- Data is **classified**; controls scale with sensitivity.
- Data is **encrypted at rest and in transit**; keys are managed and access-logged.
- Access to data is authorized per-request against classification + context; DLP
  monitors sensitive-data movement.

### 4.6 Visibility, analytics & automation
- All authentication, authorization, and administrative events are **logged,
  centralized, and immutable**, retained per policy, and monitored in a SIEM.
- Anomalies drive **automated response** (session revocation, step-up, quarantine)
  where safe.

### 4.7 Governance
- Access is granted by **group/attribute**, reviewed on a recertification cadence.
- Zero Trust controls are mapped to compliance frameworks
  (`../../grc/compliance/crosswalk.py`) and risks tracked in the register.

## 5. Roles & responsibilities
| Role | Responsibility |
|------|----------------|
| CISO / Security Architecture | Owns this policy, the target architecture, and maturity roadmap |
| IAM / Identity team | IdP, SSO, MFA, JIT, federation, access reviews |
| Cloud platform teams | Enforce PEPs, segmentation, guardrails as code per cloud |
| SecOps / SOC | Monitoring, detection, automated response, hunt |
| Application teams | Per-request authorization, workload identity, no static secrets |
| GRC | Framework mapping, exceptions, evidence, audit |

## 6. Exceptions
Any deviation requires a **documented, time-limited exception** with a
compensating control, risk acceptance by the resource owner + CISO, an expiry
date, and an entry in the risk register (`../../grc/risk/risk_register.py`).
Standing exceptions are prohibited.

## 7. Enforcement & maturity
- Controls roll out in **audit/report-only** mode, then move to **enforce**.
- Progress is measured against **CISA ZTMM v2.0** stages
  (`../validation/zero_trust_maturity_check.md`); the target is **Advanced→Optimal**
  across all pillars. DoD components additionally meet **Target Level** activities
  by 30 Sep 2027.
- Non-compliance with mandatory statements is a reportable security finding.

## 8. References
NIST SP 800-207 / 800-207A · CISA Zero Trust Maturity Model v2.0 · DoD Zero Trust
Strategy & Reference Architecture · NIST SP 800-63B · NIST CSF 2.0.
