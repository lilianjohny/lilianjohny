# Lab 01 — Incident Response Lifecycle (NIST SP 800-61)

**Skills practiced:** the full IR lifecycle — preparation, detection & analysis,
containment/eradication/recovery, post-incident — coordination, evidence, reporting.
**Proves (JD — SOC/Cyber Eng):** "strong experience across the incident response
lifecycle."

## Objective
Run a simulated incident end to end using the toolkit's triage + reporting tools,
and produce an incident report with a timeline.

## Est. time / cost
3–4 h · **~$0–1** (sample telemetry / sandbox VMs).

## Prerequisites
- Tools: `../../soc/ir/triage.py`, `../../soc/incident/incident_report.py`.
- `jq`, Python 3.

---

## Phase 1 — Preparation
Define the IR plan: severity scale, comms, evidence-handling, and regulatory
clocks (FISMA 1-hour, CIRCIA 72/24h — see `../../soc/`). Confirm telemetry is on
(tie to `../aws/06` / `../../cloud/detection/`).

## Phase 2 — Detection & analysis
```bash
# Simulate an alert stream for a suspicious login + C2 beaconing
cat > /tmp/alerts.json <<'EOF'
[
 {"id":"a1","source":"edr","title":"Beaconing to known C2","severity":"high",
  "category":"c2","asset":"web-prod-01","asset_criticality":"crown_jewel","confidence":0.9},
 {"id":"a2","source":"idp","title":"Impossible travel sign-in","severity":"medium",
  "category":"credential_access","asset":"user-jsmith","asset_criticality":"high","confidence":0.7},
 {"id":"a3","source":"dns","title":"Lookup of low-reputation domain","severity":"low",
  "category":"recon","asset":"workstation-14","asset_criticality":"low","confidence":0.5}
]
EOF
python3 ../../soc/ir/triage.py /tmp/alerts.json --format summary     # P1-P4, NIST phase, first action
python3 ../../soc/ir/triage.py /tmp/alerts.json --format json > /tmp/triage.json   # ticket-ready
```
Investigate the top item (P1 C2 on a crown-jewel): scope affected assets/accounts;
build the timeline from logs (reuse `../../cloud/detection/cloudtrail_hunt.md`).

## Phase 3 — Containment, eradication & recovery
- **Contain:** isolate the host / disable the account / block the C2 indicator
  (the triage tool's first-action hint for `c2`).
- **Eradicate:** remove persistence, rotate compromised creds/secrets
  (`../onprem/03-secret-management.md`), patch the entry vector.
- **Recover:** restore from known-good (`../aws/08-disaster-recovery.md`), verify
  integrity, watch for re-infection.

## Phase 4 — Post-incident
```bash
python3 ../../soc/incident/incident_report.py    # generate the structured report
# Fill: timeline, scope, root cause, actions, lessons learned.
```
Track remediations to closure: `../../soc/poam/poam_tracker.py`, `../../vulnmgmt/`.

## Verify
Success = a complete record: detection evidence → triage decision (P1 first) →
containment/eradication/recovery actions → a written report with timeline + lessons.

## Cleanup
```bash
rm -f /tmp/alerts.json /tmp/triage.json
```

## Portfolio artifact (the big one)
- A polished **incident report** with a timeline, mapped to MITRE ATT&CK.
- The **triage output** showing how you prioritized (medium-on-crown-jewel can
  outrank high-on-sandbox).
- A **lessons-learned** list feeding back into Preparation.

## Stretch goals
- Draft the **regulatory reporting** (which clock applied, who you'd notify).
- Run a **tabletop** with a second person as the adversary.
- Automate part of containment and measure time-to-contain.
