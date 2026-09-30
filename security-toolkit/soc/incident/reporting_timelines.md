# Incident Reporting Timelines (verify against current issuance)

The reporting clock and channel depend on your regime. The values below are
commonly documented; **confirm against the governing issuance and your
CSSP/AO/ISSM SOP** — several are being revised (e.g., CIRCIA final rule).

## DoD — CJCSM 6510.01B categories → JIMS → JFHQ-DODIN

Report cyber incidents in the **Joint Incident Management System (JIMS)**;
JFHQ-DODIN escalates to NCSOC/USCYBERCOM. CAT 1/2/4 also to DoD LE/CI.

| CAT | Type | Typical reporting window* |
|-----|------|---------------------------|
| 1 | Root/Admin-level intrusion | ~1 hour |
| 2 | User-level intrusion | ~1 hour |
| 3 | Unsuccessful activity attempt | ~24 hours |
| 4 | Denial of service | ~1 hour |
| 5 | Non-compliance activity | ~72 hours |
| 6 | Reconnaissance | ~72 hours |
| 7 | Malicious logic (malware) | ~1 hour |
| 8 | Investigating (unconfirmed) | update as it develops |
| 9 | Explained anomaly | close-out |

\* Windows vary by edition and command SOP — **verify in CJCSM 6510.01B**.

## Federal civilian — FISMA / OMB M-21-31

- Report confirmed incidents to **CISA within 1 hour** of identification.
- Agencies are **excluded from CIRCIA** and report under FISMA/M-21-31 instead.
- Basis: FISMA (44 U.S.C. 3554); CISA incident reporting guidance.

## Critical infrastructure / covered entities — CIRCIA

- **72 hours** to report a covered cyber incident to CISA.
- **24 hours** to report a ransom payment.
- Final rule expected ~Sept 2026; core 72h/24h timelines not expected to change.

## Cloud service offerings — FedRAMP

- Incident reporting per FISMA (1 hour to US-CERT/CISA) plus notify the agency
  AO and FedRAMP PMO.
- Monthly **ConMon** deliverables (scans, POA&M updates) — see
  `../continuous_monitoring/conmon_metrics.py`.

> The `incident_report.py` tool computes the actual deadline from your
> discovery timestamp using these windows (configurable in the script).
