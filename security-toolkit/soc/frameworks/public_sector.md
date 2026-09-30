# Public-sector SOC compliance reference

Obligations for a SOC supporting **federal civilian agencies**, **cloud service
offerings (FedRAMP)**, and **critical-infrastructure covered entities**.

> Verify against current issuances: FISMA (44 U.S.C. 3551–3558), **OMB M-21-31**,
> **FedRAMP** ConMon guidance, **CIRCIA** (final rule ~Sept 2026), CISA
> directives, and NIST SP 800-53 Rev 5 / 800-137 / 800-61 / 800-37.

## FISMA / NIST RMF (federal agencies)

- Implement NIST SP 800-53 controls at the system's categorization
  (FIPS 199 / SP 800-60), authorize via RMF (SP 800-37), and run **ISCM**
  (SP 800-137) continuous monitoring.
- **Report incidents to CISA within 1 hour** of identification.
- Agencies are **excluded from CIRCIA**; FISMA/M-21-31 govern instead.

## OMB M-21-31 — event logging (see `../logging/`)

- Tiered maturity: **EL0** (not effective) → **EL1** (basic) → **EL2**
  (intermediate) → **EL3** (advanced).
- Required log categories across identity, network, DNS, endpoint/EDR, cloud
  control plane, etc.; retention commonly cited as **12 months active + 18
  months cold** (30 months total).
- Centralized, access-controlled logging enabling cross-source correlation.
- Assess with `../logging/log_coverage_check.py`.

## FedRAMP continuous monitoring (cloud service offerings)

- **Monthly ConMon deliverables:** authenticated vulnerability scans (OS, web,
  DB), updated **POA&M**, inventory, and deviation requests.
- Remediation SLAs (commonly): **High 30 / Moderate 90 / Low 180 days**
  (and Critical ~15 where applied) — confirm your package's SLAs.
- **Annual assessment** by a 3PAO; significant-change security assessments.
- KPIs via `../continuous_monitoring/conmon_metrics.py`; POA&M via `../poam/`.

## CIRCIA (critical infrastructure / covered entities)

- **72 hours** to report a covered cyber incident to CISA; **24 hours** to
  report a ransom payment. Applies to covered non-federal entities.

## Incident response (NIST SP 800-61)

- Lifecycle: Preparation → Detection & Analysis → Containment, Eradication &
  Recovery → Post-Incident Activity. See `../incident/ir_playbook.md`.

## What a SOC must be able to produce
- Monthly ConMon package (scans + POA&M) within the SLA windows.
- Incident records with CISA report timestamps (≤1 hr for agencies).
- Event-logging maturity evidence (M-21-31 tier).
- Control assessment results mapped to SP 800-53 (`control_mapping.csv`).
