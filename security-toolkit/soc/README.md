# SOC Compliance — DoD & Public Sector

Compliance tooling and reference material for a **Security Operations Center**
operating under **DoD** and **U.S. public-sector** authorities: continuous
monitoring, incident detection & mandated reporting, event-logging maturity,
POA&M management, and control assessment.

> ⚠️ **This encodes the *publicly documented* frameworks and is decision
> support, not authority.** Reporting deadlines, categories, and control
> baselines are set by issuances that version frequently and are partly
> CAC/CUI-gated. **Confirm every timeline and requirement against the current
> issuance and your AO / ISSM / CSSP before relying on it.** Sources are listed
> per document.

## Which regime applies?

| Your organization | Primary regime | Incident report to | Key deadline |
|-------------------|----------------|--------------------|--------------|
| **DoD component / mission partner** | DoDI 8530.01/.03, CJCSM 6510.01B, DTM-24-001 | **JIMS** → JFHQ-DODIN → NCSOC/USCYBERCOM | per CJCSM category (high cats ~1 hr) |
| **Federal civilian agency** | FISMA, OMB M-21-31, NIST RMF | **CISA** (CISA/US-CERT) | **within 1 hour** of discovery |
| **Critical infrastructure / covered entity** | **CIRCIA** | **CISA** | **72 hrs** incident / **24 hrs** ransom payment |
| **Cloud service offering (Gov)** | **FedRAMP** ConMon | agency AO + FedRAMP PMO | monthly ConMon; 1-hr incident |

> Federal agencies are **excluded from CIRCIA** — they report under FISMA/M-21-31
> instead. Pick the row that matches your authorizing environment.

## Layout

```
soc/
├── frameworks/
│   ├── dod_cssp.md              CSSP functions, CJCSM 6510 categories, JIMS/JFHQ-DODIN
│   ├── public_sector.md         FISMA, FedRAMP ConMon, CIRCIA, CISA, NIST ISCM
│   └── control_mapping.csv      SOC capability → NIST SP 800-53 control → regime
├── incident/
│   ├── incident_report.py       Classify incident + compute the reporting deadline
│   ├── reporting_timelines.md    Mandated reporting windows (data-driven)
│   └── ir_playbook.md           NIST SP 800-61 aligned SOC IR playbook
├── continuous_monitoring/
│   └── conmon_metrics.py        ConMon KPIs (vuln aging vs SLA, POA&M, coverage)
├── logging/
│   ├── m2131_logging.md         OMB M-21-31 event-logging tiers + retention
│   └── log_coverage_check.py    Assess log-source coverage → EL maturity tier
├── poam/
│   ├── poam_template.csv        POA&M template (FedRAMP/RMF fields)
│   └── poam_tracker.py          POA&M aging / overdue detection
└── reporting/
    └── soc_posture_report.py    Roll ConMon + POA&M + logging into one posture report
```

## Quick start

```bash
# Classify an incident and get the reporting authority + deadline
python soc/incident/incident_report.py --regime dod --category 1 \
    --discovered "2026-02-01T14:30:00Z" --summary "root-level intrusion on host X"

# ConMon KPIs from your scan + POA&M exports
python soc/continuous_monitoring/conmon_metrics.py --vulns scans.json --poam poam.csv

# Event-logging maturity vs OMB M-21-31
python soc/logging/log_coverage_check.py --sources log_sources.json

# POA&M aging / overdue
python soc/poam/poam_tracker.py soc/poam/poam_template.csv
```

## Standards referenced
- **DoD:** DoDI 8530.01, DoD Manual 8530.01, DoDI 8530.03, DTM-24-001, CJCSM 6510.01B
- **Federal:** FISMA (44 U.S.C. 3554), OMB M-21-31, FedRAMP ConMon, CIRCIA
- **NIST:** SP 800-53 Rev 5, SP 800-137 (ISCM), SP 800-61 (IR), SP 800-37 (RMF)
- Ties into the toolkit's `dod/` (cATO evidence) and `cloud/detection/` (log coverage).
