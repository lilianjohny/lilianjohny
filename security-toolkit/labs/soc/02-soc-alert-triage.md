# Lab 02 — SOC Alert Triage Workflow

**Skills practiced:** alert triage & prioritization · enrichment · correlation
across EDR / DNS / firewall / identity sources · consistent, auditable decisions ·
ticket handoff.
**Proves (JD — SOC/Cyber Eng):** "monitor and respond to SOC escalations and
alerts," own issues "through to resolution," coordinate stakeholders.

## Objective
Build a repeatable triage workflow that turns a noisy alert stream into
prioritized, documented, ticket-ready actions — using the toolkit's triage engine
and firewall auditor.

## Est. time / cost
2–3 h · **~$0** (sample alert exports).

## Prerequisites
- Sample alerts from EDR (SentinelOne/Defender), protective DNS, firewall, and
  identity — as JSON (or hand-craft representative ones).
- Tools: `../../soc/ir/triage.py`, `../../soc/network/firewall_rule_audit.py`.

---

## Part A — Understand the inputs
List your alert sources and what each tells you:
- **EDR** (SentinelOne/Defender/ThreatLocker): process/behavior, malware, execution.
- **Protective DNS / content filtering**: C2/known-bad domain lookups.
- **Firewall** (Palo Alto/FortiGate/Meraki/SonicWall): blocked/allowed flows.
- **Identity** (Entra/M365): risky sign-ins, impossible travel, MFA fatigue.

## Part B — Normalize & triage
1. Convert each source's alert into the triage schema (id, source, title,
   severity, category, asset, asset_criticality, confidence).
2. Score and prioritize the whole batch:
   ```bash
   python3 ../../soc/ir/triage.py alerts.json --format summary
   python3 ../../soc/ir/triage.py alerts.json --format json > triage.json   # ticket-ready
   ```
3. Note how priority = severity × asset criticality × category × confidence, so a
   medium alert on a crown-jewel asset outranks a high alert on a sandbox.

## Part C — Enrich & correlate
1. For the top items, enrich indicators (reputation, KEV/EPSS for CVEs via
   `../../vulnmgmt/enrich/kev_epss.py`), and **correlate** across sources — e.g. a
   DNS C2 lookup + an EDR execution alert + a firewall allow on the same host is
   one incident, not three.
2. If a firewall alert points at a risky rule, audit the rule base:
   ```bash
   python3 ../../soc/network/firewall_rule_audit.py rules.csv
   ```

## Part D — Act & hand off
1. Take the triage tool's **first-action** hint for the top items (isolate, reset
   creds, block indicator, quarantine message).
2. **Open tickets** from `triage.json` (ConnectWise/ServiceNow schema mapping) and
   own them to resolution; escalate P1 per the IR plan (`01-incident-response.md`).

## Verify
Success = a prioritized, documented queue: each alert scored, correlated where
related, with a first action and a ticket — consistent and auditable.

## Portfolio artifact
- A **triage runbook** (your workflow) + a sample **triaged queue** (`triage.json`).
- A **correlation example**: 3 raw alerts → 1 incident, with reasoning.
- A firewall-audit finding that came out of an alert.

## Stretch goals
- Extend `triage.py`'s category/action maps for your environment's alert types.
- Add an automated enrichment step (threat-intel lookup) before scoring.
- Measure triage throughput / time-to-first-action before vs after the workflow.
