# DoD SOC / CSSP compliance reference

A DoD SOC typically operates as, or is subscribed to, a **Cybersecurity Service
Provider (CSSP)**. The obligations below frame what the SOC must do and prove.

> Authoritative issuances (verify current versions; some are CAC/CUI-gated):
> **DoDI 8530.01** & **DoD Manual 8530.01** (cybersecurity activities / CSSP),
> **DoDI 8530.03** (cyber incident response), **DTM-24-001** (2024 update to
> cybersecurity activities), **CJCSM 6510.01B** (Cyber Incident Handling
> Program). RMF per DoDI 8510.01; note the transition toward **CSRMC**.

## CSSP service functions (what the SOC provides)

1. **Protect** — vulnerability management (ACAS/Tenable scanning), STIG
   compliance, patch/config management support, cyber threat intel.
2. **Detect** — sensor management, network/endpoint monitoring, correlation,
   analysis of DoDIN traffic and host telemetry.
3. **Respond** — incident triage, categorization (CJCSM 6510.01B), containment
   coordination, reporting via **JIMS**, forensics/malware analysis support.
4. **Sustain** — training, SOPs, technology refresh, and evaluation readiness.

CSSPs are assessed against **Evaluator Scoring Metrics (ESM)** by an
authorized evaluator; subscribers inherit the CSSP's authorized capabilities.

## Incident handling & reporting chain

```
SOC/CSSP → categorize (CJCSM 6510.01B) → report in JIMS
        → JFHQ-DODIN → NCSOC / USCYBERCOM
        (CAT 1/2/4 also → DoD Law Enforcement / Counterintelligence)
```

See `../incident/reporting_timelines.md` for the category → deadline table and
`../incident/incident_report.py` to generate a categorized report + deadline.

## Continuous monitoring / authorization

- **RMF ConMon** (NIST SP 800-137) — ongoing control assessment, POA&M upkeep,
  security-impact analysis; feeds the AO's ongoing authorization decision.
- Toward **cATO** — see the toolkit's `../../dod/` software factory and its
  cATO evidence bundle, which supply continuous-monitoring artifacts.
- **STIG** compliance evidence — `../../dod/scripts/gate_stig.sh` (OpenSCAP).

## What a SOC must be able to produce on demand
- Current incident log with categories, timelines met, and JIMS references.
- Vulnerability posture (ACAS) + POA&Ms with remediation status.
- Sensor/log coverage of the protected enclaves.
- SOPs, analyst training records, and ESM evidence.
