# Lab 01 — Incident Response Lifecycle (NIST SP 800-61)

**Skills practiced:** the full IR lifecycle — preparation, detection & analysis,
containment/eradication/recovery, post-incident — incident coordination,
evidence handling, and reporting.
**Proves (JD — SOC/Cyber Eng):** "strong experience across the incident response
lifecycle, including investigation, coordination, remediation, and resolution."

## Objective
Run a simulated incident end to end against your own sandbox, using the toolkit's
triage and reporting tools, and produce an incident report with a timeline — the
artifact SOC roles interview on.

## Est. time / cost
3–4 h · **~$0–1** (sandbox VMs / sample telemetry).

## Prerequisites
- A sandbox (a couple of VMs or a cloud lab from `../aws/06` etc.).
- Tools: `../../soc/ir/triage.py`, `../../soc/incident/incident_report.py`.

---

## Phase 1 — Preparation
- Define the IR plan: roles, severity scale, comms plan, evidence-handling rules,
  and regulatory clocks (e.g. FISMA 1-hour, CIRCIA 72/24h — see `../../soc/`).
- Confirm logging/telemetry is on (tie to `../aws/06` / `../../cloud/detection/`).

## Phase 2 — Detection & analysis
1. Trigger a simulated incident (e.g. suspicious login + beaconing on a sandbox host).
2. Ingest the alerts and **triage**:
   ```bash
   python3 ../../soc/ir/triage.py alerts.json --format summary
   ```
   Use the P1–P4 priority, NIST phase, and suggested first action to decide fast.
3. **Investigate:** enrich indicators, scope affected assets/accounts, build the
   timeline from logs (reuse hunt queries in `../../cloud/detection/cloudtrail_hunt.md`).

## Phase 3 — Containment, eradication & recovery
1. **Contain:** isolate the host / disable the account / block the indicator
   (the triage tool's first-action hint).
2. **Eradicate:** remove persistence, rotate compromised credentials/secrets
   (`../onprem/03-secret-management.md`), patch the entry vector.
3. **Recover:** restore from known-good (tie to `../aws/08-disaster-recovery.md`),
   verify integrity, watch for re-infection.

## Phase 4 — Post-incident
1. Generate the structured report:
   ```bash
   python3 ../../soc/incident/incident_report.py
   ```
2. Fill in: timeline, scope, root cause, actions, and **lessons learned**; track
   remediations to closure (`../../soc/poam/poam_tracker.py`, `../../vulnmgmt/`).

## Verify
Success = a complete incident record: detection evidence → triage decision →
containment/eradication/recovery actions → a written report with a timeline and
lessons learned.

## Portfolio artifact (the big one)
- A polished **incident report** with a timeline, mapped to MITRE ATT&CK.
- The **triage output** showing how you prioritized.
- A **lessons-learned / improvement** list feeding back into Preparation.

## Stretch goals
- Add **regulatory reporting** drafts (which clock applied, who you'd notify).
- Run a **tabletop** with a second person playing the adversary.
- Automate part of containment (a playbook) and measure time-to-contain.
