# Lab 02 — SOC Alert Triage Workflow

**Skills practiced:** alert triage & prioritization · enrichment · correlation
across EDR / DNS / firewall / identity · consistent, auditable decisions · ticket
handoff.
**Proves (JD — SOC/Cyber Eng):** "monitor and respond to SOC escalations and
alerts," own issues to resolution.

## Objective
Turn a noisy alert stream into prioritized, documented, ticket-ready actions,
using the toolkit's triage engine and firewall auditor.

## Est. time / cost
2–3 h · **~$0** (sample exports).

## Prerequisites
- Tools: `../../soc/ir/triage.py`, `../../soc/network/firewall_rule_audit.py`.

---

## Part A — Understand the inputs
Map your sources: **EDR** (SentinelOne/Defender/ThreatLocker) = process/behavior;
**protective DNS / content filtering** = C2/known-bad lookups; **firewall**
(Palo Alto/FortiGate/Meraki/SonicWall) = blocked/allowed flows; **identity**
(Entra/M365) = risky sign-ins, impossible travel, MFA fatigue.

## Part B — Normalize & triage
```bash
# Convert each source's alert into the triage schema, batch them:
cat > /tmp/queue.json <<'EOF'
[
 {"id":"e1","source":"edr","title":"LSASS access by unknown binary","severity":"high","category":"credential_access","asset":"dc-01","asset_criticality":"crown_jewel","confidence":0.85},
 {"id":"f1","source":"firewall","title":"Allowed egress to new IP :4444","severity":"medium","category":"c2","asset":"app-02","asset_criticality":"high","confidence":0.6},
 {"id":"d1","source":"dns","title":"DGA-like domain lookup","severity":"medium","category":"c2","asset":"ws-09","asset_criticality":"medium","confidence":0.55},
 {"id":"i1","source":"idp","title":"MFA fatigue prompts","severity":"medium","category":"credential_access","asset":"user-ceo","asset_criticality":"crown_jewel","confidence":0.7}
]
EOF
python3 ../../soc/ir/triage.py /tmp/queue.json --format summary
python3 ../../soc/ir/triage.py /tmp/queue.json --format json > /tmp/queue.triaged.json
```
Note priority = severity × asset-criticality × category × confidence — so
`user-ceo` MFA fatigue (crown-jewel) can outrank a high alert on a sandbox.

## Part C — Enrich & correlate
- Enrich CVE indicators with KEV/EPSS:
  ```bash
  python3 ../../vulnmgmt/enrich/kev_epss.py --allow-fetch --cve CVE-2024-3400 2>/dev/null \
    || echo "offline: supply --kev-file/--epss-file (see the script docstring)"
  ```
- **Correlate:** a DNS C2 lookup + an EDR execution alert + a firewall allow on
  the same host is **one incident**, not three.
- If a firewall alert points at a risky rule, audit the rule base:
  ```bash
  python3 ../../soc/network/firewall_rule_audit.py ../../soc/network/rules.example.csv
  ```

## Part D — Act & hand off
Take the triage tool's **first-action** hint for the top items (isolate, reset
creds, block indicator, quarantine message). Open tickets from
`/tmp/queue.triaged.json` (map to ConnectWise/ServiceNow fields) and own them to
resolution; escalate P1 per `01-incident-response.md`.

## Verify
Success = a prioritized, documented queue: each alert scored, correlated where
related, with a first action and a ticket — consistent and auditable.

## Cleanup
```bash
rm -f /tmp/queue.json /tmp/queue.triaged.json
```

## Portfolio artifact
- A **triage runbook** + a sample **triaged queue** (`queue.triaged.json`).
- A **correlation example**: 3 raw alerts → 1 incident, with reasoning.
- A firewall-audit finding that came out of an alert.

## Stretch goals
- Extend `triage.py`'s category/action maps for your environment.
- Add an automated enrichment step (threat-intel lookup) before scoring.
- Measure triage throughput / time-to-first-action before vs after.
