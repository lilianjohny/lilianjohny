# Zero Trust Implementation Process (2026)

A phased roadmap you can actually execute. Zero Trust is a **program**, not a
product — you advance each pillar through the CISA maturity stages. Do
everything in **audit/report-only** first, then enforce.

> Sequencing principle: **Identity → Devices → Segmentation → Data → Automate**,
> with Visibility and Governance running the whole way. Identity delivers the most
> risk reduction fastest, so it goes first.

---

## Phase 0 — Assess & plan
- [ ] Adopt the **Zero Trust Policy** (`../policy/zero-trust-policy.md`) through
      governance (`../../grc/governance/`).
- [ ] Inventory: identities (human + workload), devices, apps, data stores, network
      paths, clouds (AWS/Azure/GCP/SaaS).
- [ ] Classify **data** and identify crown-jewel resources (protect-surface first).
- [ ] Baseline current maturity per pillar (`../validation/zero_trust_maturity_check.md`).
- [ ] Define target: Advanced→Optimal per pillar (DoD: Target activities by 30 Sep 2027).
- [ ] **Exit:** approved policy, asset/data inventory, maturity baseline, roadmap.

---

## Phase 1 — Identity (the new perimeter) — highest ROI
- [ ] Consolidate to **one IdP**; enable **SSO** to all clouds (`../../sso/`).
- [ ] Enforce **phishing-resistant MFA** (FIDO2/passkeys); block legacy auth.
- [ ] Grant access by **group/attribute**; remove human local accounts.
- [ ] Make privileged access **JIT / zero standing privilege** (Identity Center /
      PIM / PAM) (`../../iam/`).
- [ ] Turn on risk-based signals (Identity Protection / equivalent).
- [ ] **Exit:** 100% interactive logins via SSO+FIDO2; no standing admins; leaver
      test passes across clouds.

---

## Phase 2 — Devices
- [ ] Enrol/manage endpoints (Intune / MDM); define **compliance** (encrypted,
      patched, EDR running).
- [ ] Deploy endpoint posture signals: AWS Verified Access trust provider · Intune
      device compliance · GCP Endpoint Verification.
- [ ] Make **device compliance a required condition** for sensitive access
      (report-only → enforce).
- [ ] **Exit:** sensitive-resource access requires a compliant, managed device.

---

## Phase 3 — Networks & environment (segmentation, kill the VPN)
- [ ] Default-deny east-west; **micro-segment** by workload/identity.
- [ ] Replace broad VPN with **per-app brokered access**: AWS Verified Access ·
      Azure Global Secure Access / App Proxy · GCP IAP / BeyondCorp.
- [ ] Make control/data planes **private** (PrivateLink / Private Endpoints /
      Private Service Connect); no public management ports.
- [ ] Establish **data-exfil perimeters** (RCP data perimeter / storage firewall /
      VPC Service Controls).
- [ ] **Exit:** no network-position-based access; admin planes private; east-west
      default-deny.

---

## Phase 4 — Applications, workloads & data
- [ ] Enforce **per-request authorization** at each app/API PEP (no trusted-caller
      assumptions); policy-as-code where possible (`../policies/opa-abac-example.rego`).
- [ ] Workloads use **short-lived federated identity** (no static keys);
      cross-cloud via workload identity federation (`../../iam/terraform/multicloud/`).
- [ ] Verify the supply chain (SBOM, signed artifacts) — `../../devsecops/`, `../../dod/`.
- [ ] **Data:** encrypt at rest + in transit, classify (Macie/Purview/DLP), apply
      DLP, gate access by classification + context.
- [ ] **Exit:** apps authorize per request; workloads keyless; sensitive data
      encrypted, classified, and DLP-monitored.

---

## Phase 5 — Visibility, analytics & automation (cross-cutting, ongoing)
- [ ] Centralize **all** auth/authz/admin/network logs → one SIEM
      (Sentinel/Chronicle/Splunk); immutable retention.
- [ ] Build the detection catalog (`../../cloud/detection/`, `../../soc/`): new
      admin, privileged use, MFA/policy changes, impossible travel, exfil signals.
- [ ] Enable **continuous evaluation** (CAE / per-request access levels / short
      sessions) so risk changes revoke access mid-session.
- [ ] Add **automated response** playbooks: revoke session, disable identity,
      quarantine host, require re-auth.
- [ ] **Exit:** every access decision logged; high-severity events auto-responded.

---

## Phase 6 — Govern, measure & optimize (continuous)
- [ ] Access reviews / recertification on a cadence (`../../iam/validation/`).
- [ ] Map ZT controls to frameworks (`../../grc/compliance/crosswalk.py`); track
      risks and exceptions in the register (`../../grc/risk/`).
- [ ] Re-score maturity per pillar quarterly; drive the **weakest pillar** up.
- [ ] Tune policy from analytics; expand enforcement scope; reduce standing access.
- [ ] **Exit (ongoing):** Advanced→Optimal across pillars; DoD Target activities
      met by 30 Sep 2027.

---

## Rollout safety
- **Report-only / audit first** for every access policy (CA, access levels, Cedar);
  watch impact, then enforce.
- Keep **break-glass** (cloud-native, outside policy scope) working at all times.
- Roll out **one protect-surface at a time** (start with crown jewels), one cloud
  at a time; keep the old path until the new one is proven.
- Everything as **code**, versioned and reviewed (`../policies/`, `../../iam/terraform/`).

---

## Quick self-assessment
Run through `../validation/zero_trust_maturity_check.md` to place each pillar on
Traditional / Initial / Advanced / Optimal and get your priority order.
