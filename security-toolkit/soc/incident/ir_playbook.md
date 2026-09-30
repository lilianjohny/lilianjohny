# SOC Incident Response Playbook (NIST SP 800-61 aligned)

A concise, regime-aware IR flow. Fill in tooling/contacts for your environment.
Reporting steps differ by regime — see `reporting_timelines.md`.

## 0. Preparation (before an incident)
- Contacts: SOC lead, ISSM/ISSO, AO, CSSP, legal, PAO, CISA/JFHQ-DODIN POCs.
- Tooling ready: SIEM, EDR, packet capture, forensic images, ticketing.
- Know your regime and its reporting clock (DoD JIMS / CISA 1-hr / CIRCIA 72-hr).

## 1. Detection & Analysis
- Validate the alert; determine scope (hosts, accounts, data, enclaves).
- **Classify** (DoD: CJCSM 6510.01B category; others: severity).
- Start the clock: record discovery time (UTC) — the reporting deadline runs
  from here. Generate the report shell:
  `python incident_report.py --regime <r> [--category N] --discovered <ts> --summary "..."`
- Preserve evidence (memory, disk, logs) with chain of custody.

## 2. Containment
- Short-term: isolate hosts, disable accounts/keys, block indicators.
- Long-term: patch, rebuild from known-good, rotate credentials/secrets.
- Coordinate containment that affects mission systems with the system owner/AO.

## 3. Eradication & Recovery
- Remove malware/persistence; close the initial access vector.
- Restore from validated backups; monitor for reinfection.
- Verify controls that failed are now effective (feeds POA&M).

## 4. Reporting (regime-specific — do not miss the deadline)
- **DoD:** submit/UPDATE in **JIMS**; JFHQ-DODIN escalation; CAT 1/2/4 → LE/CI.
- **Federal agency:** report to **CISA within 1 hour**; update as it develops.
- **Covered entity (CIRCIA):** CISA within **72 hrs** (ransom payment **24 hrs**).
- Mark report classification (e.g., CUI). Keep timestamps for the record.

## 5. Post-Incident Activity
- Lessons-learned within ~2 weeks; update SOPs, detections, and the threat model.
- Open POA&Ms for control gaps (`../poam/poam_template.csv`).
- Feed new IOCs/TTPs (map to MITRE ATT&CK) back into detection.

## Evidence to retain
- Timeline (detection → containment → recovery → report), with UTC timestamps.
- Report references (JIMS ticket / CISA report ID), analyst notes, forensic
  artifacts, and the final incident report (`incident_report.py` output).
